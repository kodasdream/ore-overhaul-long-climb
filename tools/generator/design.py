"""The design table: every material, its level, and the 50-step ladder.

DDSS harvest levels 0-12 scale proportionally to 0-45 (SCALE). Inside a band, stronger materials sit higher.
A few materials are pinned so the ladder has a real ore on every level; PINS lists them.
"""
import json
import math
import os
import re
import zipfile
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DUMP = os.path.join(ROOT, "extract", "ddss_tinkers.clean.json")
MODS = os.path.expanduser("~/ddss_horizon_port/DDSS_original_java/.minecraft/mods")

SCALE = 45 / 12
LEVELS = 51  # wood is the starting tool (level 0); ore tiers run 1 to 50
DIAMOND = 20

# Biome groups used by the ore table. Every id is a 26.3 biome; ids are spelled out because a biome
# modifier's list takes ids, not tags.
COLD = ["snowy_plains", "ice_spikes", "snowy_taiga", "snowy_beach", "snowy_slopes", "frozen_peaks", "jagged_peaks", "grove",
        "frozen_river", "taiga", "old_growth_pine_taiga", "old_growth_spruce_taiga"]
HOT_DRY = ["desert", "badlands", "eroded_badlands", "wooded_badlands", "savanna", "savanna_plateau", "windswept_savanna"]
WET = ["swamp", "mangrove_swamp", "river", "beach"]
HILLS = ["windswept_hills", "windswept_gravelly_hills", "windswept_forest", "stony_peaks", "jagged_peaks", "frozen_peaks",
         "snowy_slopes", "meadow", "grove", "cherry_grove"]
JUNGLE = ["jungle", "sparse_jungle", "bamboo_jungle"]
OCEAN = ["ocean", "deep_ocean", "cold_ocean", "deep_cold_ocean", "lukewarm_ocean", "deep_lukewarm_ocean", "warm_ocean",
         "frozen_ocean", "deep_frozen_ocean"]
WARM_SEA = ["warm_ocean", "lukewarm_ocean", "deep_lukewarm_ocean"]
BLOOM = ["flower_forest", "cherry_grove", "meadow", "dappled_forest"]
GLOOM = ["dark_forest", "pale_garden", "dappled_forest"]
BARE = ["stony_peaks", "jagged_peaks", "stony_shore", "windswept_gravelly_hills"]
BADLANDS = ["badlands", "eroded_badlands", "wooded_badlands"]
PEAKS = ["frozen_peaks", "jagged_peaks", "stony_peaks", "snowy_slopes"]
SNOW = ["snowy_plains", "ice_spikes", "snowy_slopes", "frozen_peaks", "snowy_taiga"]
CAVES = ["deep_dark", "dripstone_caves", "sulfur_caves"]
DESERT_SEA = ["desert", "beach", "snowy_beach", "ocean", "deep_ocean", "frozen_ocean", "frozen_river"]  # TAIGA's dilithium biomes
DESERT_HILLS = ["desert", "windswept_hills", "windswept_gravelly_hills", "windswept_forest", "savanna_plateau"]  # TAIGA's vibranium biomes


def vein(dim, y, size, count=None, rarity=None, biomes=None, host=None, shape="vein", shell=None, why=None):
    """One way an ore generates. count: veins per chunk. rarity: 1 vein in N chunks. biomes: only there (None: all of dim).
    host: what it replaces instead of the dimension's rock. shape: vein, bottom (under End islands), meteor (buried in stone),
    crater (half-sunk into the surface) or cube (floating, as TAIGA's End cubes do): all balls of `shell` with this ore inside. why: where the numbers come from."""
    return {"dim": dim, "y": y, "size": size, "count": count, "rarity": rarity, "biomes": biomes, "host": host, "shape": shape, "shell": shell, "why": why}


# Level -> ladder material. Vanilla entries reuse vanilla's ore, item and gear.
LADDER = {
    0: {"id": "wood", "vanilla": True},
    1: {"id": "stone", "vanilla": True},
    2: {"id": "tin", "new": True, "color": 0xC9D2D6},
    3: {"id": "zinc", "new": True, "color": 0xA7B8B0},
    4: {"id": "aluminum", "new": True, "color": 0xD9DEE3},
    5: {"id": "copper", "vanilla": True},
    6: {"id": "silver"},
    7: {"id": "lead"},
    8: {"id": "iron", "vanilla": True},
    9: {"id": "thorium"},
    10: {"id": "osmium"},
    11: {"id": "boron"},
    12: {"id": "nickel"},
    13: {"id": "platinum_plustic"},
    14: {"id": "ruby", "new": True, "gem": True, "color": 0xD3213C},
    15: {"id": "sapphire", "new": True, "gem": True, "color": 0x2747C9},
    16: {"id": "ardite"},
    17: {"id": "cobalt"},
    18: {"id": "tungsten", "new": True, "color": 0x5E6670},
    19: {"id": "palladium"},
    20: {"id": "diamond", "vanilla": True, "new": True, "gem": True, "color": 0x4AEDD9},
    21: {"id": "titanium", "new": True, "color": 0xB6BCC9},
    22: {"id": "chromium", "new": True, "color": 0xDCE7EF},
    23: {"id": "tanzanite", "new": True, "gem": True, "color": 0x5A3FC0},
    24: {"id": "valyrium"},
    25: {"id": "netherite", "vanilla": True, "new": True, "color": 0x4A3F44},
    26: {"id": "endorium", "new": True, "color": 0x7CD6C0},
    27: {"id": "vibranium"},
    28: {"id": "adamant"},
    29: {"id": "mithril", "new": True, "color": 0x9FE8FF},
    30: {"id": "draconium", "new": True, "color": 0x7A2BC2},
    31: {"id": "orichalcum", "new": True, "color": 0xC89B3C},
    32: {"id": "painite", "new": True, "gem": True, "color": 0xB5412F},
    33: {"id": "black_opal", "new": True, "gem": True, "color": 0x2C2C40},
    34: {"id": "aetherium", "new": True, "color": 0x87F2D4},
    35: {"id": "starsteel", "new": True, "color": 0xF2E8C0},
    36: {"id": "void_crystal", "new": True, "gem": True, "color": 0x3C1E6E},
    37: {"id": "dragonstone", "new": True, "gem": True, "color": 0xE0601C},
    38: {"id": "eternium", "new": True, "color": 0x52E0FF},
    39: {"id": "neutronium", "new": True, "color": 0x3A3D44},
    40: {"id": "cosmite", "new": True, "color": 0x2A1C6B},
    41: {"id": "celestium", "new": True, "color": 0xE9F6FF},
    42: {"id": "astralite", "new": True, "color": 0x6FA8FF},
    43: {"id": "voidsteel", "new": True, "color": 0x1B1B2E},
    44: {"id": "prismium", "new": True, "gem": True, "color": 0xE66FE0},
    45: {"id": "chaotic_plustic"},
    46: {"id": "chronite", "new": True, "color": 0x38E0A0},
    47: {"id": "singularite", "new": True, "gem": True, "color": 0x101018},
    48: {"id": "primordium", "new": True, "color": 0xFFB347},
    49: {"id": "omnium", "new": True, "gem": True, "color": 0xFFFFFF},
    50: {"id": "genesium", "new": True, "color": 0xFF3D81},
}

# Where every ore generates. Sizes and counts for anything DDSS had are at least DDSS's own, read from its
# config (TAIGA.cfg, tconstruct.cfg, cofh/world, mekanism.cfg, nuclearcraft.cfg) and the jars' generators.
OW, NE, EN = "overworld", "nether", "end"
VEINS = {
    "tin": [vein(OW, (0, 96), 9, 10, why="DDSS 6 veins of 7")],
    "zinc": [vein(OW, (-16, 72), 8, 9)],
    "aluminum": [vein(OW, (-32, 64), 8, 8)],
    "copper": [vein(OW, (-16, 112), 10, 12, why="DDSS 12 veins of 5-8"), vein(OW, (-64, 64), 16, 6, biomes=["dripstone_caves"])],
    "silver": [vein(OW, (-32, 96), 7, 8, biomes=COLD + HILLS, why="DDSS 4 veins of 6")],
    "lead": [vein(OW, (-32, 40), 7, 8, why="DDSS 4 veins of 6")],
    "iron": [vein(OW, (-64, 72), 9, 11, why="DDSS 11 veins of 9")],
    "thorium": [vein(OW, (-48, 48), 5, 7, biomes=HOT_DRY, why="DDSS 4 veins of 4")],
    "osmium": [vein(OW, (-48, 48), 8, 5, why="DDSS 4 veins of 8")],
    "boron": [vein(OW, (-56, 40), 6, 8, biomes=WET, why="DDSS 6 veins of 5")],
    "nickel": [vein(OW, (-56, 16), 5, 5, why="DDSS 3 veins of 4")],
    "platinum": [vein(OW, (-64, 48), 4, 6, biomes=HILLS, why="DDSS 1 vein of 1")],
    "ruby": [vein(OW, (-64, 32), 4, 5, biomes=JUNGLE + ["savanna", "savanna_plateau"])],
    "sapphire": [vein(OW, (-64, 32), 4, 5, biomes=OCEAN)],
    "ardite": [vein(NE, (32, 96), 5, 6, why="Tinkers: 12 veins of 5, half at y32-96"), vein(NE, (0, 128), 5, 6, why="the other half at y0-128")],
    "cobalt": [vein(NE, (32, 96), 5, 4, why="Tinkers: 8 veins of 5, half at y32-96"), vein(NE, (0, 128), 5, 4, why="the other half at y0-128")],
    "tungsten": [vein(OW, (-64, 32), 5, 8, biomes=CAVES)],
    "palladium": [vein(EN, (48, 64), 3, 10, why="TAIGA: End y48-64, 7 veins of 2-4"), vein(OW, (-64, 64), 4, 8, biomes=["lush_caves"], why="so it can be had before the End, as tier 19")],
    "diamond": [vein(OW, (-64, 16), 7, 2, why="DDSS 1 vein of 7")],
    "titanium": [vein(OW, (-64, 128), 4, 6, biomes=BARE)],
    "chromium": [vein(NE, (8, 120), 5, 8, biomes=["basalt_deltas"])],
    "tanzanite": [vein(NE, (100, 123), 4, 8)],
    "valyrium": [vein(NE, (0, 128), 4, 14, why="TAIGA: Nether y0-128, 10 veins of 2-4")],
    "netherite": [vein(NE, (8, 24), 3, 2), vein(NE, (8, 119), 2, 3)],
    "endorium": [vein(EN, (30, 80), 5, 16)],
    "vibranium": [vein(OW, (-64, 64), 5, 5, biomes=DESERT_HILLS, why="TAIGA: deserts and extreme hills, y0-64, 2-6"), vein(OW, (-64, 128), 3, rarity=7, why="TAIGA: 15% of chunks anywhere")],
    "adamant": [vein(EN, (40, 90), 4, 20, biomes=["end_highlands"])],
    "mithril": [vein(OW, (-48, 96), 4, 6, biomes=BLOOM)],
    "draconium": [vein(EN, (20, 80), 5, 40, biomes=["small_end_islands", "end_barrens"], why="DDSS 5 veins of 4")],
    "orichalcum": [vein(OW, (-64, 32), 4, 6, biomes=WARM_SEA)],
    "painite": [vein(OW, (-64, 0), 3, 6, biomes=BADLANDS)],
    "black_opal": [vein(NE, (8, 64), 4, 16, biomes=["soul_sand_valley"])],
    "aetherium": [vein(OW, (90, 256), 4, 24, biomes=PEAKS)],
    "starsteel": [vein(EN, (70, 150), 0, rarity=24, shape="cube", shell="obsidiorite")],
    "void_crystal": [vein(EN, (40, 40), 6, 20, shape="bottom")],
    "dragonstone": [vein(NE, (8, 120), 4, 14, biomes=["crimson_forest"])],
    "eternium": [vein(EN, (30, 80), 4, 24, biomes=["end_midlands"])],
    "neutronium": [vein(NE, (122, 127), 4, 6, host="bedrock")],
    "cosmite": [vein(NE, (8, 120), 4, 14, biomes=["warped_forest"])],
    "celestium": [vein(OW, (-64, 64), 3, 12, biomes=SNOW)],
    "astralite": [vein(EN, (70, 150), 0, rarity=24, shape="cube", shell="obsidiorite")],
    "voidsteel": [vein(EN, (40, 40), 6, 24, shape="bottom", biomes=["end_barrens", "small_end_islands", "end_midlands"])],
    "prismium": [vein(OW, (-64, 64), 3, 12, biomes=["lush_caves", "mushroom_fields", "cherry_grove"])],
    "chaotic": [vein(EN, (30, 80), 3, 12)],
    "chronite": [vein(OW, (-64, 48), 3, 12, biomes=GLOOM)],
    "singularite": [vein(NE, (8, 31), 5, 5, host="lava")],
    "primordium": [vein(OW, (-64, -60), 3, 3, host="bedrock")],
    "omnium": [vein(EN, (30, 80), 3, 14)],
    "genesium": [vein(NE, (0, 4), 3, 4, host="bedrock")],
    # Beside the ladder.
    "magnesium": [vein(OW, (-8, 56), 5, 4, why="DDSS 4 veins of 5")],
    "tiberium": [vein(NE, (32, 128), 20, 7, why="TAIGA: Nether y32-128, 7 veins of 10-35")],
    "uranium": [vein(OW, (-48, 24), 5, 4, biomes=HOT_DRY, why="DDSS 4 veins of 4")],
    "iridium": [vein(OW, (-64, 0), 3, 5, biomes=["deep_dark"])],
    # Buried at TAIGA's real rate, so the ore stays as common as in DDSS, and a few crash sites you can see from the surface.
    "duranite": [vein(OW, (-48, 48), 0, rarity=50, shape="meteor", shell="meteorite", why="TAIGA: meteors, 1 in 50 chunks"),
                 vein(OW, (0, 0), 0, rarity=250, shape="crater", shell="meteorite", why="half-sunk into the ground, so none hang in the air")],
    "eezo": [vein(OW, (-64, -60), 3, 5, host="bedrock", why="TAIGA: replaces bedrock, 5 per chunk")],
    "aurorium": [vein(EN, (32, 56), 3, 12, why="TAIGA: End y32-48, 9 veins of 2-4")],
    "prometheum": [vein(NE, (0, 32), 3, 9, why="TAIGA: Nether y0-32, 9 veins of 2-4")],
    "uru": [vein(EN, (70, 150), 0, rarity=12, shape="cube", shell="obsidiorite", why="TAIGA: inside floating obsidiorite cubes")],
    "karmesine": [vein(OW, (0, 128), 10, 12, host="andesite", why="TAIGA: only in andesite, 9 per chunk")],
    "ovium": [vein(OW, (0, 128), 10, 12, host="diorite", why="TAIGA: only in diorite, 9 per chunk")],
    "jauxum": [vein(OW, (0, 128), 10, 11, host="granite", why="TAIGA: only in granite, 8 per chunk")],
    "osram": [vein(NE, (0, 64), 15, 5, host="lava", why="TAIGA: swims in Nether lava, 5 veins of 15")],
    "abyssum": [vein(EN, (40, 40), 5, 20, shape="bottom", why="TAIGA: the undersides of End islands, 5 per chunk")],
    "dilithium": [vein(OW, (-64, 64), 5, 11, biomes=DESERT_SEA, why="TAIGA: deserts, beaches and oceans, 11 veins of 2-8")],
}
# Shell blocks of meteors and floating cubes: a block of their own, with no smelting.
SHELLS = {"meteorite": (0x4A3B33, 19), "obsidiorite": (0x2A2235, 19)}

# Ores that DDSS has but that sit beside the ladder, not on it (their numbers are in VEINS).
SIDE_ORES = ["magnesium", "tiberium", "uranium", "iridium", "eezo", "aurorium", "prometheum", "duranite", "uru"]

# TAIGA's ores that are alloy inputs, not tool materials in DDSS: (level, colour).
EXTRA_ORES = {
    "karmesine": (13, 0xB0264B),
    "ovium": (14, 0x5B8FD9),
    "jauxum": (14, 0x83C23A),
    "osram": (15, 0xD9B44A),
    "abyssum": (18, 0x20405F),
    "dilithium": (16, 0xE8609A),
}

# Vanilla ores with their new level. They replace vanilla's features, except non-tool ones that stay put.
VANILLA_ORE_LEVEL = {
    "gold": 9, "redstone": 9, "lapis": 10, "emerald": 14, "quartz": 6,
}
VANILLA_REMOVED_FEATURES = {
    "overworld": ["ore_copper", "ore_copper_large", "ore_iron_upper", "ore_iron_middle", "ore_iron_small",
                  "ore_diamond", "ore_diamond_medium", "ore_diamond_large", "ore_diamond_buried"],
    "nether": ["ore_ancient_debris_large", "ore_debris_small"],
}

# Level of each vanilla tool family, used for the vanilla incorrect_for_* tags.
VANILLA_TOOL_LEVEL = {"wooden": 0, "stone": 1, "copper": 5, "iron": 8, "golden": 9, "diamond": 20, "netherite": 25}

# Control points the new materials' stats follow: level -> (durability, speed, attack).
CURVE = {0: (59, 2.0, 1.5), 1: (131, 4.0, 2.0), 5: (190, 5.0, 2.25), 8: (250, 6, 3), 20: (1561, 8, 5), 25: (2031, 9, 6), 30: (2800, 11, 8),
         38: (4500, 14, 12), 45: (8000, 18, 24), 49: (20000, 26, 40), 50: (26000, 30, 50)}

KIND_FACTOR = {False: (1.0, 1.0, 1.0), True: (0.8, 1.12, 1.15)}  # metals, gems: gems are fast and hit hard but wear sooner

VANILLA_ITEM = {
    "wood": "#minecraft:planks", "stone": "#minecraft:stone_tool_materials", "copper": "minecraft:copper_ingot",
    "iron": "minecraft:iron_ingot", "diamond": "minecraft:diamond", "netherite": "minecraft:netherite_ingot",
    "paper": "minecraft:paper", "bone": "minecraft:bone", "flint": "minecraft:flint", "cactus": "minecraft:cactus",
    "netherrack": "minecraft:netherrack", "obsidian": "minecraft:obsidian", "endstone": "minecraft:end_stone",
    "prismarine": "minecraft:prismarine", "sponge": "minecraft:sponge",
}
VANILLA_ARMOR = {"copper": "copper", "iron": "iron", "diamond": "diamond", "netherite": "netherite"}


def safe_id(mid):
    s = mid.lower().replace("integrationforegoing.", "").replace("mysticaladaptations.", "").replace("ma.", "")
    s = re.sub(r"(_plustic|_avaritia_plustic|_avaritia|_mat)$", "", s)
    return re.sub(r"[^a-z0-9_]", "_", s)


def curve(level):
    pts = sorted(CURVE)
    for a, b in zip(pts, pts[1:]):
        if a <= level <= b:
            f = (level - a) / (b - a)
            return tuple(math.exp(math.log(x) * (1 - f) + math.log(y) * f) for x, y in zip(CURVE[a], CURVE[b]))
    return CURVE[pts[-1]]


def power(m):
    h = m["stats"]["head"]
    return math.log1p(h["durability"]) * 0.45 + math.log1p(h["miningspeed"]) * 0.35 + math.log1p(max(h["attack"], 0)) * 0.2


def band_levels(heads):
    """Proportional 0-12 -> 0-45, spread inside each band by strength."""
    by = defaultdict(list)
    for m in heads:
        by[m["stats"]["head"]["harvestLevel"]].append(m)
    out = {}
    for hl, ms in sorted(by.items()):
        ms.sort(key=power)
        lo = math.ceil(hl * SCALE)
        hi = max(lo, math.ceil((hl + 1) * SCALE) - 1)
        if hl >= 12:
            lo = hi = 45
        for i, m in enumerate(ms):
            f = i / (len(ms) - 1) if len(ms) > 1 else 0
            out[m["id"]] = round(lo + (hi - lo) * f)
    return out


def lang_names():
    names = {}
    for jar in sorted(os.listdir(MODS)):
        if not jar.endswith(".jar"):
            continue
        try:
            z = zipfile.ZipFile(os.path.join(MODS, jar))
        except zipfile.BadZipFile:
            continue
        for n in z.namelist():
            if n.lower().endswith("en_us.lang"):
                for line in z.read(n).decode("utf-8", "replace").splitlines():
                    m = re.match(r"\s*material\.([A-Za-z0-9_.]+)\.name\s*=\s*(.+)", line)
                    if m:
                        names.setdefault(m.group(1), m.group(2).strip())
    return names


def title(s):
    return " ".join(w.capitalize() for w in s.split("_"))


def color_of(raw):
    return raw & 0xFFFFFF


def build():
    dump = json.load(open(DUMP))
    names = lang_names()
    heads = [m for m in dump["materials"] if "head" in m["stats"]]
    levels = band_levels(heads)
    ladder_ids = {v["id"]: k for k, v in LADDER.items()}
    pinned = {}
    mats = {}
    for m in dump["materials"]:
        mid = m["id"]
        sid = safe_id(mid)
        h = m["stats"].get("head")
        lv = levels.get(mid)
        if mid in ladder_ids:
            pinned[sid] = (lv, ladder_ids[mid])
            lv = ladder_ids[mid]
        spec = LADDER.get(lv, {}) if mid in ladder_ids else {}
        hd = m["stats"].get("handle", {})
        mats[sid] = {
            "id": sid, "ddss_id": mid, "name": names.get(mid, title(sid)), "level": lv,
            "dur": h["durability"] if h else None, "speed": h["miningspeed"] if h else None, "atk": h["attack"] if h else None,
            "ddss_harvest": h["harvestLevel"] if h else None,
            "handle": hd.get("modifier"), "handle_dur": hd.get("durability"), "extra": m["stats"].get("extra", {}).get("extraDurability"),
            "stats": m["stats"], "traits": m["traits"], "color": color_of(m["color"]), "fluid": m["fluid"], "rep": m["rep"],
            "ore": VEINS.get(sid), "gem": bool(spec and spec.get("gem")),
            "vanilla": mid in VANILLA_ITEM, "new": False,
        }
    for lv, spec in LADDER.items():
        sid = safe_id(spec["id"])
        if sid in mats:
            continue
        d, s, a = curve(lv)
        fd, fs, fa = KIND_FACTOR[bool(spec.get("gem"))]
        mats[sid] = {
            "id": sid, "ddss_id": None, "name": title(sid), "level": lv, "dur": round(d * fd), "speed": round(s * fs, 2), "atk": round(a * fa, 2),
            "ddss_harvest": None, "handle": 1.0, "handle_dur": round(d * 0.1), "extra": round(d * 0.08), "stats": {}, "traits": {},
            "color": spec["color"], "fluid": None, "rep": None, "ore": VEINS.get(sid), "gem": bool(spec.get("gem")),
            "vanilla": spec["id"] in VANILLA_ITEM, "new": True,
        }
    for sid, (lv, col) in EXTRA_ORES.items():
        d, s, a = curve(lv)
        mats[sid] = {
            "id": sid, "ddss_id": None, "name": title(sid), "level": lv, "dur": None, "speed": None, "atk": None,
            "ddss_harvest": None, "handle": None, "handle_dur": None, "extra": None, "stats": {}, "traits": {},
            "color": col, "fluid": sid, "rep": None, "ore": VEINS[sid], "gem": False, "vanilla": False, "new": True, "ingredient_only": True,
        }
    # The Age of Ores ores Long Climb didn't have: one or more beside each tier's ladder material.
    import aoo
    for sid, c in aoo.companions(vein).items():
        if sid in mats:
            continue
        mats[sid] = {
            "id": sid, "ddss_id": None, "name": c["name"], "level": c["level"], "dur": None, "speed": None, "atk": None,
            "ddss_harvest": None, "handle": None, "handle_dur": None, "extra": None, "stats": {}, "traits": {},
            "color": c["color"], "fluid": None, "rep": None, "ore": c["veins"], "gem": c["gem"], "vanilla": False, "new": True,
            "ingredient_only": True, "companion": True,
        }
    ladder = {lv: mats[safe_id(s["id"])] for lv, s in LADDER.items()}
    # Every ladder step must beat the one before in at least one stat. A step that doesn't gets its
    # closest stat raised to 5% above the previous step, and is listed in "raised".
    raised = []
    for lv in range(1, LEVELS):
        m, prev = ladder[lv], ladder[lv - 1]
        if any(m[k] > prev[k] for k in ("dur", "speed", "atk")):
            continue
        k = max(("dur", "speed", "atk"), key=lambda s: m[s] / prev[s])
        old = m[k]
        m[k] = round(prev[k] * 1.05, 2) if k != "dur" else round(prev[k] * 1.05)
        raised.append((m["id"], k, old, m[k]))
    for m in mats.values():
        if m["new"] and not m["fluid"] and not m.get("companion"):
            m["fluid"] = m["id"]
    return {"mats": mats, "ladder": ladder, "dump": dump, "pinned": pinned, "raised": raised}


if __name__ == "__main__":
    d = build()
    mats = d["mats"]
    print("materials", len(mats), "with tool stats", sum(1 for m in mats.values() if m["dur"] is not None))
    prev = None
    bad = 0
    for lv in range(LEVELS):
        m = d["ladder"][lv]
        better = []
        if prev:
            for k in ("dur", "speed", "atk"):
                if (m[k] or 0) > (prev[k] or 0):
                    better.append(k)
            if not better:
                bad += 1
        print(f"L{lv:2} {m['id']:18} H={str(m['ddss_harvest']):4} dur={m['dur']} spd={m['speed']} atk={m['atk']} better:{','.join(better)}")
        prev = m
    print("ladder steps with no improvement:", bad)
    print("pinned outside proportional position (band level -> ladder level):")
    for sid, (a, b) in sorted(d["pinned"].items(), key=lambda kv: kv[1][1]):
        if a is not None and abs(a - b) > 0:
            print(f"  {sid}: {a} -> {b}")
    occ = defaultdict(int)
    for m in mats.values():
        if m["level"] is not None:
            occ[m["level"]] += 1
    print("materials per level:", [occ[i] for i in range(LEVELS)])
    print("raised to keep the ladder improving:", d["raised"])
    fl = {m["fluid"] for m in mats.values() if m["fluid"]}
    un = defaultdict(int)
    for a in d["dump"]["alloys"]:
        for x in a["inputs"] + [a["result"]]:
            n = x["fluid"].replace("_fluid", "") if isinstance(x, dict) else None
            if n and x["fluid"] not in fl and n not in fl:
                un[x["fluid"]] += 1
    print("alloy fluids with no material:", dict(un))
