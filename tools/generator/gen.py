#!/usr/bin/env python3
"""Writes the two content mods (folders Horizon can load) from design.py: Ore Overhaul Long Climb and Extended Classic Tinkers for Horizon."""
import json
import os
import shutil
from collections import defaultdict

import art
import tinkers
from design import DIAMOND, LEVELS, SHELLS, VANILLA_ARMOR, VANILLA_ITEM, VANILLA_ORE_LEVEL, VANILLA_REMOVED_FEATURES, VANILLA_TOOL_LEVEL, build, safe_id

LC, TK = "longclimb", "ddsstinkers"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PIECES = {"helmet": ("head", 11), "chestplate": ("chest", 16), "leggings": ("legs", 15), "boots": ("feet", 13)}
ARMOR_SHARE = {"helmet": 0.15, "chestplate": 0.40, "leggings": 0.30, "boots": 0.15}
TOOL_KINDS = {
    "pickaxe": ("minecraft:iron_pickaxe", "#minecraft:mineable/pickaxe", 1.0, -2.8),
    "axe": ("minecraft:iron_axe", "#minecraft:mineable/axe", 4.0, -3.1),
    "shovel": ("minecraft:iron_shovel", "#minecraft:mineable/shovel", 1.5, -3.0),
    "hoe": ("minecraft:iron_hoe", "#minecraft:mineable/hoe", 0.0, -1.0),
    "sword": ("minecraft:iron_sword", None, 3.0, -2.4),
}
# The 3x3 tools: template, what they mine, attack base, name, index of the tool they're built on in TOOL_KINDS,
# then durability (4x, the user's call: 9 blocks a swing still wears it 2.25x faster), Tinkers' speed, attack speed and damage multipliers, and the art function.
AREA_TOOLS = {
    "hammer": ("minecraft:iron_pickaxe", "#minecraft:mineable/pickaxe", 1.0, "Hammer", 0, 4.0, 0.4, 0.8, 1.2, "hammer"),
    "excavator": ("minecraft:iron_shovel", "#minecraft:mineable/shovel", 1.5, "Excavator", 2, 4.0, 0.28, 0.7, 1.25, "excavator"),
}
# Crafted on the 5x5 table: every one is wider or taller than 3, so no smaller grid can make it. G is the rarest gem below the tier.
SHAPES = {
    "pickaxe": ["MMGMM", "M H M", "  H  ", "  H  ", "  H  "], "axe": ["MMM  ", "MMGH ", "M  H ", "   H ", "   H "], "shovel": [" MMM ", " MGM ", "  H  ", "  H  ", "  H  "],
    "hoe": ["MMGM ", "   H ", "   H ", "   H ", "   H "], "sword": ["  M  ", "  M  ", " MGM ", "  H  ", "  H  "],
}
ARMOR_SHAPES = {"helmet": ["MMMMM", "M   M", "M   M"], "chestplate": ["MM MM", "MMMMM", "MMMMM", "MMMMM", "MMMMM"], "leggings": ["MMMMM", "M   M", "M   M", "M   M", "M   M"], "boots": ["M   M", "M   M", "MM MM"]}
AREA_SHAPES = {"hammer": ["BBBBB", "GBTBG", "  H  ", "  H  "], "excavator": [" BBB ", "GBTBG", "  H  ", "  H  "]}
# What vanilla's pickaxes really have, for the report (durability, speed, attack bonus).
VANILLA_PICK = {"wood": (59, 2.0, 1.0), "stone": (131, 4.0, 2.0), "copper": (190, 5.0, 2.0), "iron": (250, 6.0, 3.0), "diamond": (1561, 8.0, 4.0), "netherite": (2031, 9.0, 5.0)}
ITEM_LEVEL_RARITY = [(35, "epic"), (20, "rare"), (10, "uncommon"), (0, "common")]

# What an ore can sit in: how the feature finds it, the block id prefix, the name prefix and the art's rock.
HOSTS = {
    "stone": (("tag", "minecraft:stone_ore_replaceables"), "", "", "stone"),
    "deepslate": (("tag", "minecraft:deepslate_ore_replaceables"), "deepslate_", "Deepslate ", "deepslate"),
    "nether": (("tag", "minecraft:base_stone_nether"), "nether_", "Nether ", "nether"),
    "end": (("block", "minecraft:end_stone"), "end_", "End ", "end"),
    "andesite": (("block", "minecraft:andesite"), "andesite_", "Andesite ", "andesite"),
    "diorite": (("block", "minecraft:diorite"), "diorite_", "Diorite ", "diorite"),
    "granite": (("block", "minecraft:granite"), "granite_", "Granite ", "granite"),
    "lava": (("block", "minecraft:lava"), "molten_", "Molten ", "magma"),
    "bedrock": (("block", "minecraft:bedrock"), "bedrock_", "Bedrock ", "bedrock"),
    "meteorite": (None, "meteorite_", "Meteoric ", "meteorite"),
    "obsidiorite": (None, "obsidiorite_", "Obsidiorite ", "obsidiorite"),
}
DIM_HOSTS = {"overworld": ["stone", "deepslate"], "nether": ["nether"], "end": ["end"]}
DIM_TAG = {"overworld": "#minecraft:is_overworld", "nether": "#minecraft:is_nether", "end": "#minecraft:is_end"}
# Vanilla's own ore blocks, which stay what they are at their new level.
VANILLA_ORE_BLOCKS = {
    "copper": {"stone": "minecraft:copper_ore", "deepslate": "minecraft:deepslate_copper_ore"},
    "iron": {"stone": "minecraft:iron_ore", "deepslate": "minecraft:deepslate_iron_ore"},
    "diamond": {"stone": "minecraft:diamond_ore", "deepslate": "minecraft:deepslate_diamond_ore"},
    "netherite": {"nether": "minecraft:ancient_debris"},
}

written = 0
langs = {LC: {}, TK: {}}
tabs = {LC: defaultdict(list), TK: defaultdict(list)}
missing_sources = []
MOD = LC  # the mod the next files go into; use_mod switches it


def use_mod(mod):
    global MOD, OUT, ADATA, AASSET, lang
    MOD = mod
    OUT = os.path.join(ROOT, "mod", mod)
    ADATA = f"data/{mod}"
    AASSET = f"assets/{mod}"
    lang = langs[mod]


def path(*a):
    p = os.path.join(OUT, *a)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    return p


def wj(rel, obj):
    global written
    if "/horizon/item/" in rel and "components" in obj and "minecraft:max_stack_size" in obj["components"]:
        obj["max_stack_size"] = obj["components"].pop("minecraft:max_stack_size")  # an item file says this at its top
    with open(path(rel), "w") as f:
        json.dump(obj, f, indent=1)
    written += 1


def wp(rel, img):
    global written
    img.save(path(rel))
    written += 1


def rarity(level):
    return next(r for lv, r in ITEM_LEVEL_RARITY if (level or 0) >= lv)


# Vanilla's item categories, which every enchantment's tags are built from: Long Climb's gear goes in them, or nothing enchants.
# An AIOT is all five tools at once, so it takes every tool and weapon enchantment.
GEAR_TAGS = {"pickaxe": ["pickaxes"], "axe": ["axes"], "shovel": ["shovels"], "hoe": ["hoes"], "sword": ["swords"],
             "helmet": ["head_armor"], "chestplate": ["chest_armor"], "leggings": ["leg_armor"], "boots": ["foot_armor"],
             "aiot": ["pickaxes", "axes", "shovels", "hoes", "swords"], "hammer": ["pickaxes"], "excavator": ["shovels"]}
gear_tags = {}


def add_item(iid, name, template, texture, tab, handheld=False, extra=None, level=None):
    if "_" in iid:
        for t in GEAR_TAGS.get(iid.rsplit("_", 1)[1], []):
            gear_tags.setdefault(MOD, {}).setdefault(t, []).append(f"{MOD}:{iid}")
    decl = {"template": template, "rarity": rarity(level)}
    if extra:
        decl.update(extra)
    wj(f"{ADATA}/horizon/item/{iid}.json", decl)
    wj(f"{AASSET}/items/{iid}.json", {"model": {"type": "minecraft:model", "model": f"{MOD}:item/{iid}"}})
    wj(f"{AASSET}/models/item/{iid}.json", {"parent": "minecraft:item/handheld" if handheld else "minecraft:item/generated", "textures": {"layer0": f"{MOD}:item/{iid}"}})
    wp(f"{AASSET}/textures/item/{iid}.png", texture)
    lang[f"item.{MOD}.{iid}"] = name
    tabs[MOD][tab].append(f"{MOD}:{iid}")


def add_block(bid, name, template, texture, tab, hardness, resistance, level=None):
    wj(f"{ADATA}/horizon/block/{bid}.json", {"template": template, "properties": {"hardness": round(hardness, 2), "explosion_resistance": round(resistance, 2)},
                                            "components": {"minecraft:rarity": rarity(level)}})
    wj(f"{AASSET}/blockstates/{bid}.json", {"variants": {"": {"model": f"{MOD}:block/{bid}"}}})
    wj(f"{AASSET}/models/block/{bid}.json", {"parent": "minecraft:block/cube_all", "textures": {"all": f"{MOD}:block/{bid}"}})
    wj(f"{AASSET}/items/{bid}.json", {"model": {"type": "minecraft:model", "model": f"{MOD}:block/{bid}"}})
    wp(f"{AASSET}/textures/block/{bid}.png", texture)
    lang[f"block.{MOD}.{bid}"] = name
    tabs[MOD][tab].append(f"{MOD}:{bid}")


def loot_self(bid):
    return {"type": "minecraft:block", "random_sequence": f"{MOD}:blocks/{bid}",
            "pools": [{"rolls": 1, "condition": {"type": "minecraft:survives_explosion"}, "entries": [{"type": "minecraft:item", "name": f"{MOD}:{bid}"}]}]}


def loot_ore(bid, drop, fortune=True):
    silk = {"condition": "minecraft:match_tool", "predicate": {"predicates": {"minecraft:enchantments": [{"enchantments": "minecraft:silk_touch", "levels": {"min": 1}}]}}}
    alt = {"type": "minecraft:item", "name": drop, "functions": ([{"function": "minecraft:apply_bonus", "enchantment": "minecraft:fortune", "formula": "minecraft:ore_drops"}] if fortune else []) + [{"function": "minecraft:explosion_decay"}]}
    return {"type": "minecraft:block", "random_sequence": f"{MOD}:blocks/{bid}",
            "pools": [{"rolls": 1, "entries": [{"type": "minecraft:alternatives", "children": [{"type": "minecraft:item", "name": f"{MOD}:{bid}", "conditions": [silk]}, alt]}]}]}


def ing(ref):
    return ref


def shaped(rid, pattern, key, result, count=1, category="equipment"):
    wj(f"{ADATA}/recipe/{rid}.json", {"type": "minecraft:crafting_shaped", "category": category, "pattern": pattern,
                                     "key": {k: ing(v) for k, v in key.items()}, "result": {"id": result, "count": count}})


def shapeless(rid, items, result, count=1):
    wj(f"{ADATA}/recipe/{rid}.json", {"type": "minecraft:crafting_shapeless", "category": "misc", "ingredients": [ing(i) for i in items], "result": {"id": result, "count": count}})


def tool_rules(kind, level, mineable, speed):
    rules = [{"blocks": f"#{LC}:incorrect_for_level_{level}", "correct_for_drops": False}]
    rules.append({"blocks": mineable, "speed": speed, "correct_for_drops": True})
    return {"rules": rules}


def main():
    d = build()
    mats, ladder = d["mats"], d["ladder"]
    for mod, name, desc in ((LC, "Ore Overhaul Long Climb", "50 ore tiers: every ore needs a pickaxe from the tier below, diamond sits at tier 20, and each tier has its own tools and armor."),
                            (TK, "Extended Classic Tinkers for Horizon", "Tinkers' Construct 1.12 rebuilt for Horizon, with tool leveling and the TAIGA and PlusTiC materials, on top of Ore Overhaul Long Climb, which it needs. Tool part textures: Tinkers' Construct (MIT, SlimeKnights).")):
        use_mod(mod)
        if os.path.exists(OUT):
            shutil.rmtree(OUT)
        with open(path("horizon-mod.toml"), "w") as f:
            f.write(f'''id = "{mod}"
name = "{name}"
version = "0.5.0"
description = "{desc}"
authors = ["Zsombor"]
api = "0.2"
side = "both"
capabilities = ["registries"]
''')
    ladder_ids = {m["id"] for m in ladder.values()}

    def home(m):
        """Long Climb owns the ladder and every ore; everything else is Tinkers' own."""
        return LC if m["id"] in ladder_ids or m.get("ore") or m["id"] in SHELLS else TK

    needs = {LC: defaultdict(list), TK: defaultdict(list)}  # tool level required -> blocks
    item_of = {}
    world = defaultdict(list)

    # Materials: their item, raw item, block and ores.
    for sid, m in sorted(mats.items()):
        lv = m["level"] if m["level"] is not None else 0
        m["level_int"] = lv
        if m["ddss_id"] in VANILLA_ITEM or sid in VANILLA_ITEM:
            item_of[sid] = VANILLA_ITEM.get(m["ddss_id"] or sid)
            continue
        if m["dur"] is None and m["ddss_id"]:  # fletching, string and the like: parts only, added with the Tinkers port
            continue
        use_mod(home(m))
        gemlike = m["gem"]
        is_crystal = str(m["rep"] or "").startswith("environmentaltech:")
        suffix = "gem" if gemlike else ("crystal" if is_crystal else "ingot")
        iid = f"{sid}_{suffix}"
        tex = art.gem(m["color"]) if gemlike else (art.crystal(m["color"]) if is_crystal else art.ingot(m["color"]))
        add_item(iid, f"{m['name']} {'Gem' if gemlike else ('Crystal' if is_crystal else 'Ingot')}", "minecraft:diamond" if gemlike or is_crystal else "minecraft:iron_ingot", tex, "materials", level=lv)
        item_of[sid] = f"{MOD}:{iid}"

        bid = f"{sid}_block"
        add_block(bid, f"Block of {m['name']}", "minecraft:iron_block", art.storage(sid, m["color"]), "blocks", 4 + lv * 0.25, 6 + lv * 0.5, level=lv)
        wj(f"{ADATA}/loot_table/blocks/{bid}.json", loot_self(bid))
        needs[MOD][max(lv - 1, 0)].append(f"{MOD}:{bid}")
        shaped(f"{sid}_block", ["MMM", "MMM", "MMM"], {"M": item_of[sid]}, f"{MOD}:{bid}", category="building")
        shapeless(f"{sid}_from_block", [f"{MOD}:{bid}"], item_of[sid], 9)

    # Ores. An ore on level L needs a tool of level L-1.
    use_mod(LC)
    for sid, (_, _) in sorted(SHELLS.items()):
        m = mats[sid]
        lv = m["level_int"]
        bid = f"{sid}_rock"
        add_block(bid, f"{m['name']} Rock", "minecraft:obsidian" if sid == "obsidiorite" else "minecraft:stone", art.stone_base(sid), "ores", 3 + lv * 0.35, 6 + lv * 0.3, level=lv)
        wj(f"{ADATA}/loot_table/blocks/{bid}.json", loot_self(bid))
        needs[LC][max(lv - 1, 0)].append(f"{MOD}:{bid}")
        wj(f"{ADATA}/recipe/{sid}_rock_smelting.json", {"type": "minecraft:smelting", "category": "misc", "ingredient": f"{MOD}:{bid}", "result": {"id": item_of[sid]}, "experience": 1.0, "cookingtime": 300})
    biome_mods = []
    for sid, m in sorted(mats.items()):
        veins = m.get("ore")
        if not veins:
            continue
        lv = m["level_int"]
        vanilla_blocks = VANILLA_ORE_BLOCKS.get(sid)
        hardness = 3 + lv * 0.35
        gemlike = m["gem"]
        drop = None
        if not vanilla_blocks:
            if gemlike:
                drop = item_of[sid]
            else:
                raw = f"raw_{sid}"
                add_item(raw, f"Raw {m['name']}", "minecraft:raw_iron", art.raw(m["color"]), "materials", level=lv)
                drop = f"{MOD}:{raw}"
                cook = 200 + lv * 10
                wj(f"{ADATA}/recipe/{sid}_smelting.json", {"type": "minecraft:smelting", "category": "misc", "ingredient": drop, "result": {"id": item_of[sid]}, "experience": round(0.3 + lv * 0.05, 2), "cookingtime": cook})
                wj(f"{ADATA}/recipe/{sid}_blasting.json", {"type": "minecraft:blasting", "category": "misc", "ingredient": drop, "result": {"id": item_of[sid]}, "experience": round(0.3 + lv * 0.05, 2), "cookingtime": cook // 2})
        template = "minecraft:diamond_ore" if gemlike else "minecraft:iron_ore"
        made = {}

        def ore_block(host):
            """The ore's block in this rock, made once."""
            if vanilla_blocks and host in vanilla_blocks:
                needs[LC][max(lv - 1, 0)].append(vanilla_blocks[host])
                return vanilla_blocks[host]
            if host not in made:
                _, prefix, label, rock = HOSTS[host]
                bid = f"{prefix}{sid}_ore"
                add_block(bid, f"{label}{m['name']} Ore", template, art.ore(sid, rock, m["color"], gemlike), "ores", hardness + (1.5 if host == "deepslate" else 0), 3 + lv * 0.2, level=lv)
                wj(f"{ADATA}/loot_table/blocks/{bid}.json", loot_ore(bid, drop))
                needs[LC][max(lv - 1, 0)].append(f"{MOD}:{bid}")
                made[host] = f"{MOD}:{bid}"
            return made[host]

        for i, v in enumerate(veins):
            name = f"ore_{sid}" if len(veins) == 1 else f"ore_{sid}_{i + 1}"
            if v["shape"] in ("meteor", "crater", "cube"):
                feature = write_ball(name, ore_block(v["shell"]), f"{MOD}:{v['shell']}_rock", v)
            else:
                hosts = [v["host"]] if v["host"] else DIM_HOSTS[v["dim"]]
                feature = write_feature(name, v, [(HOSTS[h][0], ore_block(h)) for h in hosts])
            biomes = [f"minecraft:{b}" for b in v["biomes"]] if v["biomes"] else DIM_TAG[v["dim"]]
            biome_mods.append((name, biomes, feature))

    # Worldgen hookup: one modifier per generation rule, since each may have its own biomes.
    for name, biomes, feature in biome_mods:
        wj(f"{ADATA}/neoforge/biome_modifier/add_{name}.json", {"type": "neoforge:add_features", "biomes": biomes, "features": feature, "step": "underground_ores"})
    for dim, feats in VANILLA_REMOVED_FEATURES.items():
        wj(f"{ADATA}/neoforge/biome_modifier/remove_vanilla_{dim}.json", {"type": "neoforge:remove_features", "biomes": DIM_TAG[dim], "features": [f"minecraft:{x}" for x in feats], "steps": ["underground_ores"]})

    # Levels of vanilla's other blocks and of vanilla's tool tags.
    needs[LC][1].append("#minecraft:needs_stone_tool")
    needs[LC][8].append("#minecraft:needs_iron_tool")
    needs[LC][DIAMOND].append("#minecraft:needs_diamond_tool")
    for name, lv in VANILLA_ORE_LEVEL.items():
        blocks = {"quartz": ["minecraft:nether_quartz_ore"]}.get(name) or [f"minecraft:{name}_ore", f"minecraft:deepslate_{name}_ore"] + (["minecraft:nether_gold_ore"] if name == "gold" else [])
        needs[LC][lv - 1] += blocks
    for lv in range(LEVELS):
        # Long Climb reads Tinkers' list too when Tinkers is on, so one set of tiers covers both mods.
        wj(f"{ADATA}/tags/block/needs_level_{lv}.json", {"values": sorted(set(needs[LC].get(lv, []))) + [{"id": f"#{TK}:needs_level_{lv}", "required": False}]})
        wj(f"{ADATA}/tags/block/incorrect_for_level_{lv}.json", {"values": [f"#{MOD}:needs_level_{k}" for k in range(lv + 1, LEVELS)]})
    for fam, lv in VANILLA_TOOL_LEVEL.items():
        wj(f"data/minecraft/tags/block/incorrect_for_{'gold' if fam == 'golden' else fam}_tool.json", {"values": [f"#{MOD}:incorrect_for_level_{lv}"]})
    wj("data/minecraft/tags/block/mineable/pickaxe.json", {"values": sorted({b for lv in needs[LC] for b in needs[LC][lv] if b.startswith(MOD)})})
    use_mod(TK)
    for lv in range(LEVELS):
        wj(f"{ADATA}/tags/block/needs_level_{lv}.json", {"values": sorted(set(needs[TK].get(lv, [])))})
    wj("data/minecraft/tags/block/mineable/pickaxe.json", {"values": sorted({b for lv in needs[TK] for b in needs[TK][lv]})})
    use_mod(LC)

    # Each tier's materials as tags: the ladder material and the Age of Ores companions beside it. A tool's handle (the tier
    # below) and its gate gem take any of them, so every ore of a tier is worth mining.
    companions_at = defaultdict(list)
    for csid, cm in sorted(mats.items()):
        if cm.get("companion") and csid in item_of:
            companions_at[cm["level_int"]].append(cm)
    use_mod(LC)
    for lv in range(LEVELS):
        base = item_of.get(ladder[lv]["id"])
        extra = [item_of[c["id"]] for c in companions_at[lv]]
        wj(f"{ADATA}/tags/item/materials_level_{lv}.json", {"values": ([base] if base else []) + extra})
        gems_here = ([base] if base and ladder[lv]["gem"] else []) + [item_of[c["id"]] for c in companions_at[lv] if c["gem"]]
        wj(f"{ADATA}/tags/item/gems_level_{lv}.json", {"values": gems_here})

    def tier_ref(lv, item):
        """A recipe's ingredient for tier `lv`'s material: its tag when companions share the tier, else the item itself."""
        return f"#{LC}:materials_level_{lv}" if companions_at[lv] else item

    def gem_ref(lv, item):
        return f"#{LC}:gems_level_{lv}" if any(c["gem"] for c in companions_at[lv]) else item

    # Plain tools for every ladder level past stone. Vanilla's own gear stands in on the vanilla levels.
    gems = sorted(ladder[lv]["level_int"] for lv in range(LEVELS) if ladder[lv]["gem"] and lv < DIAMOND)
    gems_all = sorted(lv for lv in range(LEVELS) if ladder[lv]["gem"])
    removed = []
    for lv in range(2, LEVELS):
        m = ladder[lv]
        sid = m["id"]
        prev = tier_ref(lv - 1, item_of[ladder[lv - 1]["id"]])
        gate = next((gem_ref(g, item_of[ladder[g]["id"]]) for g in reversed(gems_all) if g < lv), None)
        if lv in VANILLA_TOOL_LEVEL.values() and sid in ("copper", "iron", "diamond", "netherite"):
            fam = sid
            removed += [f"minecraft:{fam}_{k}" for k in TOOL_KINDS] + [f"minecraft:{fam}_{p}" for p in PIECES]
            for kind in TOOL_KINDS:
                pat = [r.replace("G", "M") for r in SHAPES[kind]]
                shaped(f"{fam}_{kind}", pat, {"M": item_of[sid], "H": prev}, f"minecraft:{fam}_{kind}")
            for p in PIECES:
                shaped(f"{fam}_{p}", ARMOR_SHAPES[p], {"M": item_of[sid]}, f"minecraft:{fam}_{p}")
            continue
        for kind, (template, mine, atk_add, atk_speed) in TOOL_KINDS.items():
            iid = f"{sid}_{kind}"
            comps = {"minecraft:max_damage": int(m["dur"]),
                     "minecraft:attribute_modifiers": [
                         {"type": "minecraft:attack_damage", "id": "minecraft:base_attack_damage", "amount": round(m["atk"] + atk_add, 2), "operation": "add_value", "slot": "mainhand"},
                         {"type": "minecraft:attack_speed", "id": "minecraft:base_attack_speed", "amount": atk_speed, "operation": "add_value", "slot": "mainhand"}],
                     "minecraft:repairable": {"items": item_of[sid]}}
            if mine:
                comps["minecraft:tool"] = tool_rules(kind, lv, mine, round(m["speed"], 2))
            add_item(iid, f"{m['name']} {kind.capitalize()}", template, art.tool(kind, m["color"], ladder[lv - 1]["color"] if lv > 2 else 0x8A6A3A), "tools", handheld=True, extra={"components": comps}, level=lv)
            pat = SHAPES[kind]
            key = {"M": item_of[sid], "H": prev}
            if gate and "G" in "".join(pat):
                key["G"] = gate
            else:
                pat = [r.replace("G", "M") for r in pat]
            shaped(iid, pat, key, f"{MOD}:{iid}")

    # An AIOT for every tier: all five tools plus four of the material, in one tool that does all their jobs.
    aiot_count = 0
    for name, lv, label, tools, material, color, handle, dur, speed, attack in aiot_tiers(ladder, item_of):
        iid = f"{name}_aiot"
        rules = [{"blocks": f"#{LC}:incorrect_for_level_{lv}", "correct_for_drops": False}]
        rules += [{"blocks": f"#minecraft:mineable/{kind}", "speed": speed, "correct_for_drops": True} for kind in ("pickaxe", "axe", "shovel", "hoe")]
        rules.append({"blocks": "minecraft:cobweb", "speed": 15.0, "correct_for_drops": True})
        comps = {"minecraft:max_damage": dur * 5, "minecraft:tool": {"rules": rules},
                 "minecraft:attribute_modifiers": [
                     {"type": "minecraft:attack_damage", "id": "minecraft:base_attack_damage", "amount": round(attack, 2), "operation": "add_value", "slot": "mainhand"},
                     {"type": "minecraft:attack_speed", "id": "minecraft:base_attack_speed", "amount": -2.4, "operation": "add_value", "slot": "mainhand"}],
                 "minecraft:weapon": {"item_damage_per_attack": 1}, "minecraft:repairable": {"items": material}}
        add_item(iid, f"{label} AIOT", "minecraft:iron_axe", art.aiot(color, handle), "tools", handheld=True, extra={"components": comps}, level=lv)
        pick, axe, shovel, hoe, sword = tools
        shaped(iid, ["P   A", " MMM ", " MSM ", " MMM ", "O   W"], {"P": pick, "A": axe, "S": shovel, "O": hoe, "W": sword, "M": material}, f"{MOD}:{iid}")
        aiot_count += 1
    print("aiots", aiot_count)

    # The 5x5 table: the first thing past the stone pickaxe, which it takes as an ingredient. The rest of crafting then needs it
    # (native/longclimb/scale.rs rewrites every other recipe as it loads). Its menu and result are native/longclimb/table.rs.
    tid = "crafting_table_5x5"
    wj(f"{ADATA}/horizon/block/{tid}.json", {"template": "minecraft:crafting_table", "properties": {"hardness": 3.5, "explosion_resistance": 8.0}})
    wj(f"{AASSET}/blockstates/{tid}.json", {"variants": {"": {"model": f"{MOD}:block/{tid}"}}})
    wj(f"{AASSET}/models/block/{tid}.json", {"parent": "minecraft:block/cube_bottom_top", "textures": {"top": f"{MOD}:block/{tid}_top", "side": f"{MOD}:block/{tid}_side", "bottom": f"{MOD}:block/{tid}_bottom"}})
    wj(f"{AASSET}/items/{tid}.json", {"model": {"type": "minecraft:model", "model": f"{MOD}:block/{tid}"}})
    wp(f"{AASSET}/textures/block/{tid}_top.png", art.table_top())
    wp(f"{AASSET}/textures/block/{tid}_side.png", art.table_side())
    wp(f"{AASSET}/textures/block/{tid}_bottom.png", art.table_bottom())
    lang[f"block.{MOD}.{tid}"] = "5x5 Crafting Table"
    tabs[MOD]["blocks"].insert(0, f"{MOD}:{tid}")
    wj(f"{ADATA}/loot_table/blocks/{tid}.json", loot_self(tid))
    wj("data/minecraft/tags/block/mineable/axe.json", {"values": [f"{MOD}:{tid}"]})
    wj(f"{ADATA}/horizon/menu/crafting_5x5.json", {"slots": 26, "data_slots": 0, "results": [25]})
    shaped(tid, ["TLT", "LPL", "TLT"], {"T": "minecraft:crafting_table", "L": "#minecraft:logs", "P": "minecraft:stone_pickaxe"}, f"{MOD}:{tid}", category="building")

    # A 3x3 hammer and excavator for every tier. The stats use Tinkers' multipliers: far more durability, much slower.
    # Each is built on its tier's own tool, from storage blocks, the rarest gem below the tier, and a block of the tier below.
    def storage_of(lv):
        sid = ladder[lv]["id"]
        return f"{item_of[sid].split(':')[0]}:{sid}_block"

    area_count = 0
    for name, lv, label, tools, material, color, handle, dur, speed, attack in aiot_tiers(ladder, item_of):
        if name == "wooden":
            block, under = "#minecraft:logs", "minecraft:stick"
        elif name == "stone":
            block, under = "minecraft:smooth_stone", "#minecraft:logs"
        else:
            block = "minecraft:gold_block" if name == "golden" else storage_of(lv)
            under = "minecraft:smooth_stone" if lv == 2 else storage_of(lv - 1)
        gate = next((item_of[ladder[g]["id"]] for g in reversed(gems_all) if g < lv), None)
        for kind, (template, mine, base, per_kind, tool_index, dur_x, speed_x, attacks, hit_x, draw) in AREA_TOOLS.items():
            iid = f"{name}_{kind}"
            comps = {"minecraft:max_damage": int(dur * dur_x), "minecraft:tool": tool_rules(kind, lv, mine, max(1.0, round(speed * speed_x, 2))),
                     "minecraft:attribute_modifiers": [
                         {"type": "minecraft:attack_damage", "id": "minecraft:base_attack_damage", "amount": round((attack - 3.0 + base) * hit_x, 2), "operation": "add_value", "slot": "mainhand"},
                         {"type": "minecraft:attack_speed", "id": "minecraft:base_attack_speed", "amount": round(attacks - 4.0, 2), "operation": "add_value", "slot": "mainhand"}],
                     "minecraft:repairable": {"items": material}}
            add_item(iid, f"{label} {per_kind}", template, getattr(art, draw)(color, handle), "tools", handheld=True, extra={"components": comps}, level=lv)
            key = {"B": block, "T": tools[tool_index], "H": under}
            pattern = AREA_SHAPES[kind]
            if gate:
                key["G"] = gate
            else:
                pattern = [r.replace("G", "B") for r in pattern]
            shaped(iid, pattern, key, f"{MOD}:{iid}")
            area_count += 1
    print("area tools", area_count)

    # Armour for every material with tool stats that has no vanilla armour.
    armor_count = 0
    for sid, m in sorted(mats.items()):
        if m["dur"] is None or sid in VANILLA_ARMOR or m.get("ingredient_only"):
            continue
        use_mod(home(m))
        lv = m["level_int"]
        total, tough, mult, kb = armor_values(lv)
        wj(f"{AASSET}/equipment/{sid}.json", {"layers": {"humanoid": [{"texture": f"{MOD}:{sid}"}], "humanoid_leggings": [{"texture": f"{MOD}:{sid}"}]}})
        wp(f"{AASSET}/textures/entity/equipment/humanoid/{sid}.png", art.equipment(sid, m["color"]))
        wp(f"{AASSET}/textures/entity/equipment/humanoid_leggings/{sid}.png", art.equipment(sid, m["color"], leggings=True))
        for piece, (slot, durbase) in PIECES.items():
            iid = f"{sid}_{piece}"
            points = max(1, round(total * ARMOR_SHARE[piece]))
            mods = [{"type": "minecraft:armor", "id": f"minecraft:armor.{ {'head':'helmet','chest':'chestplate','legs':'leggings','feet':'boots'}[slot] }", "amount": points, "operation": "add_value", "slot": slot}]
            if tough:
                mods.append({"type": "minecraft:armor_toughness", "id": f"minecraft:armor.{ {'head':'helmet','chest':'chestplate','legs':'leggings','feet':'boots'}[slot] }", "amount": round(tough, 1), "operation": "add_value", "slot": slot})
            if kb:
                mods.append({"type": "minecraft:knockback_resistance", "id": f"minecraft:armor.{ {'head':'helmet','chest':'chestplate','legs':'leggings','feet':'boots'}[slot] }", "amount": kb, "operation": "add_value", "slot": slot})
            comps = {"minecraft:max_damage": int(durbase * mult), "minecraft:attribute_modifiers": mods,
                     "minecraft:equippable": {"slot": slot, "equip_sound": "minecraft:item.armor.equip_iron", "asset_id": f"{MOD}:{sid}"}}
            if item_of.get(sid) and not str(item_of[sid]).startswith("#"):
                comps["minecraft:repairable"] = {"items": item_of[sid]}
            add_item(iid, f"{m['name']} {piece.capitalize()}", f"minecraft:iron_{piece}", art.armor_icon(piece, m["color"]), "armor", extra={"components": comps}, level=lv)
            if item_of.get(sid):
                shaped(iid, ARMOR_SHAPES[piece], {"M": item_of[sid]}, f"{MOD}:{iid}")
            armor_count += 1

    # Materials with no ore: alloys from DDSS's own table when every input exists, else a placeholder.
    alloy_of = {}
    fluids = {}
    for sid, m in mats.items():
        if m["fluid"]:
            fluids[m["fluid"]] = sid
            fluids[m["fluid"].replace("_fluid", "")] = sid
    for a in d["dump"]["alloys"]:
        r = a["result"]
        if not isinstance(r, dict):
            continue
        res = fluids.get(r["fluid"]) or fluids.get(r["fluid"].replace("_fluid", ""))
        ins = [fluids.get(i["fluid"]) or fluids.get(i["fluid"].replace("_fluid", "")) for i in a["inputs"] if isinstance(i, dict)]
        if res and all(ins) and res not in alloy_of:
            alloy_of[res] = (ins, a["inputs"], r["amount"])
    for sid, m in sorted(mats.items()):
        if sid not in item_of or str(item_of[sid]).startswith(("minecraft:", "#")) or m.get("ore") or sid in SHELLS:
            continue
        use_mod(home(m))
        if sid in alloy_of:
            ins, raw_in, amt = alloy_of[sid]
            items = []
            for name, x in zip(ins, raw_in):
                items += [item_of.get(name)] * min(int(x["amount"]), 4)
            if all(items) and 1 < len(items) <= 9:
                shapeless(f"{sid}_alloy", items, item_of[sid], max(1, min(int(amt), 9)))
                continue
        missing_sources.append(sid)
        lv = m["level_int"]
        a = item_of[ladder[lv]["id"]] if lv < LEVELS else None
        b = item_of[ladder[max(lv - 1, 0)]["id"]]
        catalyst = "minecraft:redstone" if lv < 12 else ("minecraft:blaze_powder" if lv < 25 else ("minecraft:ender_pearl" if lv < 40 else "minecraft:nether_star"))
        items = [i for i in (a, b, catalyst) if i and not i.startswith("#")] or [catalyst]
        shapeless(f"{sid}_placeholder", items + ["minecraft:redstone"] if len(items) < 2 else items, item_of[sid])

    # Tinkers' own blocks, parts, tools and the table its native code reads.
    import types
    needs_tk = needs[TK]
    tinkers.run(types.SimpleNamespace(use_mod=use_mod, wj=wj, wp=wp, add_item=add_item, add_block=add_block, shaped=shaped, shapeless=shapeless, loot_self=loot_self,
                                      lang=langs[TK], tabs=tabs, TK=TK, LC=LC, path=path, needs_tk=needs_tk), mats, ladder, item_of, d["dump"])
    for lv in range(LEVELS):
        wj(f"{ADATA}/tags/block/needs_level_{lv}.json", {"values": sorted(set(needs[TK].get(lv, [])))})
    wj("data/minecraft/tags/block/mineable/pickaxe.json", {"values": sorted({b for lv in needs[TK] for b in needs[TK][lv]})})

    # Vanilla gear past stone gets its recipes from here instead.
    use_mod(LC)
    wj(f"{ADATA}/recipe_filter/vanilla_gear.json", {"filters": [{"output": i, "id": "minecraft:*", "remove": True} for i in removed]})

    titles = {LC: "Ore Overhaul", TK: "Classic Tinkers"}
    for mod in (LC, TK):
        use_mod(mod)
        for t, ids in sorted(gear_tags.get(mod, {}).items()):
            wj(f"data/minecraft/tags/item/{t}.json", {"values": sorted(ids)})
    use_mod(LC)
    for mod in (LC, TK):
        use_mod(mod)
        wj(f"{AASSET}/lang/en_us.json", dict(sorted(lang.items())))
        for t_, label in (("materials", "Materials"), ("ores", "Ores"), ("blocks", "Blocks"), ("tools", "Tools"), ("armor", "Armor"), ("machines", "Machines"), ("parts", "Parts"), ("tinker_tools", "Tinker Tools"), ("slime", "Slime"), ("gadgets", "Gadgets")):
            if tabs[mod][t_]:
                wj(f"{ADATA}/horizon/creative_tab/{t_}.json", {"title": f"{titles[mod]}: {label}", "icon": tabs[mod][t_][0], "items": tabs[mod][t_]})

    write_report(d, armor_count)
    import manual
    stats = {lv: (dur, speed) for _, lv, _, _, _, _, _, dur, speed, _ in aiot_tiers(ladder, item_of) if lv < LEVELS}
    vanilla = {"wooden": 0, "wood": 0, "stone": 1, "copper": 5, "iron": 8, "gold": 9, "golden": 9, "diamond": 20, "netherite": 25}
    print("manual pages:", manual.write({"ladder": [ladder[lv] for lv in range(LEVELS)], "companions": companions_at}, describe_vein,
                                        [ladder[lv]["name"] for lv in range(LEVELS)], stats, vanilla))
    import early
    print("early recipes kept on 3x3:", len(early.write(os.path.join(os.path.dirname(OUT_ROOT) if False else os.path.expanduser("~/horizon-tiers/native/longclimb"), "scale.rs"))))
    print("files", written, {m: len(langs[m]) for m in langs}, "armor pieces", armor_count, "placeholder recipes", len(missing_sources))


def aiot_tiers(ladder, item_of):
    """(id, level, name, five tools, material, colour, handle colour, durability of one tool, speed, attack bonus) per tier."""
    def vanilla(fam):
        return [f"minecraft:{fam}_{k}" for k in TOOL_KINDS]

    # Vanilla's own tiers keep vanilla's numbers: durability, speed, the sword's attack bonus.
    out = [
        ("wooden", 0, "Wooden", vanilla("wooden"), "#minecraft:planks", 0x8A6A3A, 0x5C4426, 59, 2.0, 3.0),
        ("stone", 1, "Stone", vanilla("stone"), "#minecraft:stone_tool_materials", 0x8C8C8C, 0x8A6A3A, 131, 4.0, 4.0),
        ("golden", VANILLA_TOOL_LEVEL["golden"], "Golden", vanilla("golden"), "minecraft:gold_ingot", 0xFAD64A, 0x8A6A3A, 32, 12.0, 3.0),
    ]
    vanilla_stats = {"copper": (190, 5.0, 4.0), "iron": (250, 6.0, 5.0), "diamond": (1561, 8.0, 6.0), "netherite": (2031, 9.0, 7.0)}
    colors = {"copper": 0xC8703F, "iron": 0xD8D8D8, "diamond": 0x4AEDD9, "netherite": 0x4A3F44}
    for lv in range(2, LEVELS):
        m = ladder[lv]
        sid = m["id"]
        prev = ladder[lv - 1].get("color") or 0x8A6A3A
        if sid in vanilla_stats:
            d, sp, at = vanilla_stats[sid]
            out.append((sid, lv, m["name"], vanilla(sid), item_of[sid], colors[sid], 0x8A6A3A, d, sp, at))
        else:
            out.append((sid, lv, m["name"], [f"{LC}:{sid}_{k}" for k in TOOL_KINDS], item_of[sid], m["color"], prev if lv > 2 else 0x8A6A3A, int(m["dur"]), round(m["speed"], 2), m["atk"] + 3.0))
    return out


def armor_values(lv):
    """Total armour points, toughness, durability multiplier, knockback resistance. 30 points is the game's own cap."""
    pts = [(0, 7), (8, 15), (DIAMOND, 20), (25, 20), (50, 30)]
    tough = [(0, 0), (12, 0), (DIAMOND, 2), (25, 3), (50, 12)]
    mult = [(0, 5), (8, 15), (DIAMOND, 33), (25, 37), (50, 200)]
    kb = [(0, 0), (24, 0), (25, 0.1), (50, 0.25)]

    def interp(tb):
        for (a, x), (b, y) in zip(tb, tb[1:]):
            if a <= lv <= b:
                return x + (y - x) * (lv - a) / (b - a)
        return tb[-1][1]

    return round(interp(pts)), round(interp(tough), 1), round(interp(mult)), round(interp(kb), 2)


def write_feature(name, v, targets):
    """An ore vein: replaces what `targets` name inside a blob of v["size"] blocks."""
    tg = []
    for how, block in targets:
        kind, what = how
        pred = {"predicate_type": "minecraft:tag_match", "tag": what} if kind == "tag" else {"predicate_type": "minecraft:block_match", "block": what}
        tg.append({"target": pred, "state": block})
    wj(f"{ADATA}/worldgen/configured_feature/{name}.json", {"type": "minecraft:ore", "size": v["size"], "discard_chance_on_air_exposure": 0.0, "targets": tg})
    return write_placed(name, v)


def write_ball(name, core, shell, v):
    """A meteor or a floating cube, built from vanilla's geode feature: solid, with ore scattered through its middle."""
    mix = {"type": "minecraft:weighted", "entries": [{"data": core, "weight": 1}, {"data": shell, "weight": 7}]}
    wj(f"{ADATA}/worldgen/configured_feature/{name}.json", {
        "type": "minecraft:geode",
        "blocks": {"filling_provider": mix, "inner_layer_provider": mix, "alternate_inner_layer_provider": {"id": shell}, "middle_layer_provider": {"id": shell}, "outer_layer_provider": {"id": shell},
                   "inner_placements": [core], "cannot_replace": "#minecraft:features_cannot_replace", "invalid_blocks": "#minecraft:geode_invalid_blocks"},
        # A point counts as inside a layer when the sum of 1/distance to the ball's few centres passes 1/sqrt(layer),
        # so these sizes make a ball a few blocks in radius, with ore scattered through its middle.
        "layers": {"filling": 0.2, "inner_layer": 0.35, "middle_layer": 0.6, "outer_layer": 0.9},
        "crack": {"generate_crack_chance": 0.0},
        "invalid_blocks_threshold": 4,
        "use_potential_placements_chance": 0.0,
        "use_alternate_layer0_chance": 0.0,
        "outer_wall_distance": {"type": "minecraft:uniform", "min_inclusive": 1, "max_inclusive": 2},
        "distribution_points": {"type": "minecraft:uniform", "min_inclusive": 3, "max_inclusive": 4},
        "point_offset": {"type": "minecraft:uniform", "min_inclusive": 0, "max_inclusive": 1},
    })
    return write_placed(name, v)


def write_placed(name, v):
    placement = []
    if v.get("rarity"):
        placement.append({"type": "minecraft:rarity_filter", "chance": v["rarity"]})
    else:
        placement.append({"type": "minecraft:count", "count": v.get("count") or 1})
    lo, hi = v["y"]
    placement.append({"type": "minecraft:in_square"})
    if v["shape"] == "bottom":
        # Up from below the islands to the first end stone: the ore grows from its underside.
        placement += [{"type": "minecraft:height_range", "height": {"type": "minecraft:uniform", "min_inclusive": {"absolute": 10}, "max_inclusive": {"absolute": 60}}},
                      {"type": "minecraft:environment_scan", "direction_of_search": "up", "max_steps": 32,
                       "target_condition": {"type": "minecraft:matching_blocks", "blocks": "minecraft:end_stone"},
                       "allowed_search_condition": {"type": "minecraft:matching_blocks", "blocks": "minecraft:air"}}]
    elif v["shape"] == "crater":
        # On the ground and sunk well into it, dry land only: a ball this size can't end up in the air.
        placement += [{"type": "minecraft:heightmap", "heightmap": "OCEAN_FLOOR_WG"},
                      {"type": "minecraft:surface_water_depth_filter", "max_water_depth": 0},
                      {"type": "minecraft:offset", "x": 0, "y": {"type": "minecraft:uniform", "min_inclusive": -4, "max_inclusive": -3}, "z": 0}]
    else:
        placement.append({"type": "minecraft:height_range", "height": {"type": "minecraft:uniform", "min_inclusive": {"absolute": lo}, "max_inclusive": {"absolute": hi}}})
        if v["shape"] == "meteor":
            # Only where its centre is in rock: not hanging in a ravine or above the terrain.
            placement.append({"type": "minecraft:block_predicate_filter", "predicate": {"type": "minecraft:matching_block_tag", "tag": "minecraft:base_stone_overworld"}})
    placement.append({"type": "minecraft:biome"})
    wj(f"{ADATA}/worldgen/placed_feature/{name}.json", {"feature": f"{MOD}:{name}", "placement": placement})
    return f"{MOD}:{name}"


def describe_vein(v):
    rate = f"1 in {v['rarity']} chunks" if v.get("rarity") else f"{v['count']} per chunk"
    if v["shape"] == "meteor":
        how = f"buried meteors of {v['shell']}, {rate}"
    elif v["shape"] == "crater":
        how = f"meteor crash sites of {v['shell']}, half-sunk into the surface, {rate}"
    elif v["shape"] == "cube":
        how = f"floating balls of {v['shell']}, {rate}"
    elif v["shape"] == "bottom":
        how = f"undersides of islands, {rate}, size {v['size']}"
    else:
        how = f"y{v['y'][0]} to {v['y'][1]}, {rate}, size {v['size']}"
    extra = ""
    if v["host"]:
        extra += f", only in {v['host']}"
    if v["biomes"]:
        extra += ", only in " + ", ".join(b.replace("_", " ") for b in list(dict.fromkeys(v["biomes"])))
    return f"{v['dim']}: {how}{extra}"


def write_report(d, armor_count):
    os.makedirs(os.path.join(ROOT, "design"), exist_ok=True)
    lines = ["# Ore Overhaul Long Climb: ore tiers 1 to 50", "", "An ore on tier T needs a pickaxe of tier T-1. Wood is the starting tool (tier 0). Tinkers' DDSS levels 0-12 scale to 0-45 (x3.75).", ""]
    lines += ["| Level | Ladder material | Tinkers level | Where it generates | Durability | Speed | Attack |", "|---:|---|---:|---|---:|---:|---:|"]
    for lv in range(LEVELS):
        m = d["ladder"][lv]
        where = "<br>".join(describe_vein(v) for v in m.get("ore") or []) or "-"
        d_, s_, a_ = VANILLA_PICK.get(m["id"], (m["dur"], round(m["speed"], 2), round(m["atk"], 2)))
        lines.append(f"| {lv} | {m['name']}{' (new)' if m['new'] else ''}{' (vanilla gear)' if m['id'] in VANILLA_PICK else ''} | {m['ddss_harvest'] if m['ddss_harvest'] is not None else '-'} | {where} | {d_} | {s_} | {a_} |")
    lines += ["", f"Stats raised so each step beats the last: {', '.join(f'{a} {b} {c} -> {e}' for a, b, c, e in d['raised']) or 'none'}.", "",
              "## Every material by level", ""]
    by = defaultdict(list)
    for m in d["mats"].values():
        if m["level"] is not None:
            by[m["level"]].append(m["name"])
    for lv in range(LEVELS):
        lines.append(f"- **{lv}**: {', '.join(sorted(by[lv]))}")
    lines += ["", "## Placeholder recipes (no DDSS alloy found; to be designed)", "", ", ".join(missing_sources)]
    with open(os.path.join(ROOT, "design", "levels.md"), "w") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
