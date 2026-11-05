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

# Level -> ladder material. Vanilla entries reuse vanilla's ore, item and gear.
# Ore fields: dim, y range, vein size, veins per chunk (or 1 in N chunks when rarity is set).
LADDER = {
    0: {"id": "wood", "vanilla": True},
    1: {"id": "stone", "vanilla": True},
    2: {"id": "tin", "new": True, "dim": "overworld", "y": (40, 110), "size": 9, "count": 6, "color": 0xC9D2D6},
    3: {"id": "zinc", "new": True, "dim": "overworld", "y": (20, 90), "size": 8, "count": 5, "color": 0xA7B8B0},
    4: {"id": "aluminum", "new": True, "dim": "overworld", "y": (0, 70), "size": 8, "count": 4, "color": 0xD9DEE3},
    5: {"id": "copper", "vanilla": True, "dim": "overworld", "y": (-16, 96), "size": 8, "count": 4},
    6: {"id": "silver", "dim": "overworld", "y": (-16, 50), "size": 7, "count": 3},
    7: {"id": "lead", "dim": "overworld", "y": (-32, 40), "size": 7, "count": 3},
    8: {"id": "iron", "vanilla": True, "dim": "overworld", "y": (-64, 64), "size": 7, "count": 3},
    9: {"id": "thorium", "dim": "overworld", "y": (-48, 24), "size": 6, "count": 2},
    10: {"id": "osmium", "dim": "overworld", "y": (-48, 16), "size": 6, "count": 2},
    11: {"id": "boron", "dim": "overworld", "y": (-56, 8), "size": 5, "count": 2},
    12: {"id": "nickel", "dim": "overworld", "y": (-56, 0), "size": 5, "count": 1},
    13: {"id": "platinum_plustic", "dim": "overworld", "y": (-64, -8), "size": 4, "rarity": 2},
    14: {"id": "ruby", "new": True, "gem": True, "dim": "overworld", "y": (-64, -16), "size": 3, "rarity": 3, "color": 0xD3213C},
    15: {"id": "sapphire", "new": True, "gem": True, "dim": "overworld", "y": (-64, -24), "size": 3, "rarity": 4, "color": 0x2747C9},
    16: {"id": "ardite", "dim": "nether", "y": (8, 60), "size": 4, "count": 3},
    17: {"id": "cobalt", "dim": "nether", "y": (8, 120), "size": 3, "count": 2},
    18: {"id": "tungsten", "new": True, "dim": "overworld", "y": (-64, -40), "size": 3, "rarity": 5, "color": 0x5E6670},
    19: {"id": "palladium", "dim": "overworld", "y": (-64, -48), "size": 2, "rarity": 6},
    20: {"id": "diamond", "vanilla": True, "new": True, "gem": True, "dim": "overworld", "y": (-64, -50), "size": 3, "rarity": 8, "color": 0x4AEDD9},
    21: {"id": "titanium", "new": True, "dim": "overworld", "y": (-64, -52), "size": 2, "rarity": 8, "color": 0xB6BCC9},
    22: {"id": "chromium", "new": True, "dim": "nether", "y": (8, 30), "size": 2, "rarity": 3, "color": 0xDCE7EF},
    23: {"id": "tanzanite", "new": True, "gem": True, "dim": "nether", "y": (100, 120), "size": 2, "rarity": 5, "color": 0x5A3FC0},
    24: {"id": "valyrium", "dim": "nether", "y": (8, 40), "size": 2, "rarity": 6},
    25: {"id": "netherite", "vanilla": True, "new": True, "dim": "nether", "y": (8, 24), "size": 2, "rarity": 8, "color": 0x4A3F44},
    26: {"id": "endorium", "new": True, "dim": "end", "y": (0, 90), "size": 4, "count": 1, "color": 0x7CD6C0},
    27: {"id": "vibranium", "dim": "end", "y": (0, 90), "size": 3, "rarity": 2},
    28: {"id": "adamant", "dim": "end", "y": (0, 90), "size": 3, "rarity": 3},
    29: {"id": "mithril", "new": True, "dim": "end", "y": (0, 90), "size": 2, "rarity": 4, "color": 0x9FE8FF},
    30: {"id": "draconium", "new": True, "dim": "end", "y": (0, 70), "size": 2, "rarity": 5, "color": 0x7A2BC2},
    31: {"id": "orichalcum", "new": True, "dim": "end", "y": (0, 70), "size": 2, "rarity": 6, "color": 0xC89B3C},
    32: {"id": "painite", "new": True, "gem": True, "dim": "overworld", "y": (-64, -58), "size": 2, "rarity": 12, "color": 0xB5412F},
    33: {"id": "black_opal", "new": True, "gem": True, "dim": "nether", "y": (8, 20), "size": 2, "rarity": 12, "color": 0x2C2C40},
    34: {"id": "aetherium", "new": True, "dim": "end", "y": (0, 60), "size": 2, "rarity": 10, "color": 0x87F2D4},
    35: {"id": "starsteel", "new": True, "dim": "end", "y": (0, 60), "size": 2, "rarity": 12, "color": 0xF2E8C0},
    36: {"id": "void_crystal", "new": True, "gem": True, "dim": "end", "y": (0, 50), "size": 2, "rarity": 14, "color": 0x3C1E6E},
    37: {"id": "dragonstone", "new": True, "gem": True, "dim": "end", "y": (0, 50), "size": 2, "rarity": 16, "color": 0xE0601C},
    38: {"id": "eternium", "new": True, "dim": "end", "y": (0, 50), "size": 2, "rarity": 18, "color": 0x52E0FF},
    39: {"id": "neutronium", "new": True, "dim": "end", "y": (0, 40), "size": 2, "rarity": 20, "color": 0x3A3D44},
    40: {"id": "cosmite", "new": True, "dim": "nether", "y": (8, 16), "size": 2, "rarity": 24, "color": 0x2A1C6B},
    41: {"id": "celestium", "new": True, "dim": "overworld", "y": (-64, -60), "size": 2, "rarity": 28, "color": 0xE9F6FF},
    42: {"id": "astralite", "new": True, "dim": "end", "y": (0, 40), "size": 2, "rarity": 30, "color": 0x6FA8FF},
    43: {"id": "voidsteel", "new": True, "dim": "end", "y": (0, 40), "size": 2, "rarity": 34, "color": 0x1B1B2E},
    44: {"id": "prismium", "new": True, "gem": True, "dim": "end", "y": (0, 40), "size": 2, "rarity": 38, "color": 0xE66FE0},
    45: {"id": "chaotic_plustic", "dim": "end", "y": (0, 30), "size": 2, "rarity": 42},
    46: {"id": "chronite", "new": True, "dim": "end", "y": (0, 30), "size": 2, "rarity": 48, "color": 0x38E0A0},
    47: {"id": "singularite", "new": True, "gem": True, "dim": "nether", "y": (8, 12), "size": 2, "rarity": 56, "color": 0x101018},
    48: {"id": "primordium", "new": True, "dim": "overworld", "y": (-64, -62), "size": 2, "rarity": 64, "color": 0xFFB347},
    49: {"id": "omnium", "new": True, "gem": True, "dim": "end", "y": (0, 20), "size": 2, "rarity": 80, "color": 0xFFFFFF},
    50: {"id": "genesium", "new": True, "dim": "nether", "y": (8, 10), "size": 1, "rarity": 96, "color": 0xFF3D81},
}

# Ores that DDSS has but that sit beside the ladder, not on it.
SIDE_ORES = {
    "magnesium": {"dim": "overworld", "y": (-8, 56), "size": 5, "count": 2},
    "tiberium": {"dim": "overworld", "y": (-32, 48), "size": 5, "count": 2},
    "uranium": {"dim": "overworld", "y": (-48, 24), "size": 4, "count": 1},
    "iridium": {"dim": "overworld", "y": (-64, 0), "size": 3, "rarity": 3},
    "meteorite": {"dim": "overworld", "y": (-64, -16), "size": 3, "rarity": 3},
    "eezo": {"dim": "end", "y": (0, 90), "size": 3, "count": 1},
    "aurorium": {"dim": "nether", "y": (8, 80), "size": 4, "count": 1},
    "prometheum": {"dim": "nether", "y": (8, 60), "size": 3, "rarity": 3},
    "duranite": {"dim": "overworld", "y": (-64, -40), "size": 2, "rarity": 8},
    "uru": {"dim": "end", "y": (0, 60), "size": 2, "rarity": 6},
}

# TAIGA's ores that are alloy inputs, not tool materials in DDSS: (level, spec, colour).
EXTRA_ORES = {
    "karmesine": (13, {"dim": "overworld", "y": (-48, 16), "size": 4, "rarity": 2}, 0xB0264B),
    "ovium": (14, {"dim": "overworld", "y": (-48, 0), "size": 4, "rarity": 3}, 0x5B8FD9),
    "jauxum": (14, {"dim": "overworld", "y": (-48, 0), "size": 4, "rarity": 3}, 0x83C23A),
    "osram": (15, {"dim": "nether", "y": (8, 90), "size": 3, "rarity": 2}, 0xD9B44A),
    "abyssum": (18, {"dim": "end", "y": (0, 90), "size": 3, "rarity": 2}, 0x20405F),
    "dilithium": (16, {"dim": "nether", "y": (8, 90), "size": 3, "rarity": 3}, 0xE8609A),
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
CURVE = {0: (26, 1.5, 1.5), 1: (90, 3.0, 2.0), 5: (158, 4.0, 2.25), 8: (250, 6, 3), 20: (1561, 8, 5), 25: (2031, 9, 6), 30: (2800, 11, 8),
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
        spec = LADDER.get(lv, {}) if mid in ladder_ids else SIDE_ORES.get(mid)
        hd = m["stats"].get("handle", {})
        mats[sid] = {
            "id": sid, "ddss_id": mid, "name": names.get(mid, title(sid)), "level": lv,
            "dur": h["durability"] if h else None, "speed": h["miningspeed"] if h else None, "atk": h["attack"] if h else None,
            "ddss_harvest": h["harvestLevel"] if h else None,
            "handle": hd.get("modifier"), "handle_dur": hd.get("durability"), "extra": m["stats"].get("extra", {}).get("extraDurability"),
            "stats": m["stats"], "traits": m["traits"], "color": color_of(m["color"]), "fluid": m["fluid"], "rep": m["rep"],
            "ore": dict(spec) if spec and "dim" in spec else None, "gem": bool(spec and spec.get("gem")),
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
            "color": spec["color"], "fluid": None, "rep": None, "ore": dict(spec), "gem": bool(spec.get("gem")),
            "vanilla": spec["id"] in VANILLA_ITEM, "new": True,
        }
    for sid, (lv, spec, col) in EXTRA_ORES.items():
        d, s, a = curve(lv)
        mats[sid] = {
            "id": sid, "ddss_id": None, "name": title(sid), "level": lv, "dur": None, "speed": None, "atk": None,
            "ddss_harvest": None, "handle": None, "handle_dur": None, "extra": None, "stats": {}, "traits": {},
            "color": col, "fluid": sid, "rep": None, "ore": dict(spec), "gem": False, "vanilla": False, "new": True, "ingredient_only": True,
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
        if m["new"] and not m["fluid"]:
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
