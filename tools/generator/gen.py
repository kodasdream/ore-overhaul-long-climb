#!/usr/bin/env python3
"""Writes the two content mods (folders Horizon can load) from design.py: Ore Overhaul Long Climb and DDSS Tinkers."""
import json
import os
import shutil
from collections import defaultdict

import art
from design import DIAMOND, LEVELS, VANILLA_ARMOR, VANILLA_ITEM, VANILLA_ORE_LEVEL, VANILLA_REMOVED_FEATURES, VANILLA_TOOL_LEVEL, build, safe_id

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
SHAPES = {
    "pickaxe": ["MGM", " H ", " H "], "axe": ["MM ", "MH ", " H "], "shovel": [" M ", " H ", " H "],
    "hoe": ["MM ", " H ", " H "], "sword": [" M ", " M ", " H "],
}
ARMOR_SHAPES = {"helmet": ["MMM", "M M"], "chestplate": ["M M", "MMM", "MMM"], "leggings": ["MMM", "M M", "M M"], "boots": ["M M", "M M"]}
# What vanilla's pickaxes really have, for the report (durability, speed, attack bonus).
VANILLA_PICK = {"wood": (59, 2.0, 1.0), "stone": (131, 4.0, 2.0), "copper": (190, 5.0, 2.0), "iron": (250, 6.0, 3.0), "diamond": (1561, 8.0, 4.0), "netherite": (2031, 9.0, 5.0)}
ITEM_LEVEL_RARITY = [(35, "epic"), (20, "rare"), (10, "uncommon"), (0, "common")]

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
    with open(path(rel), "w") as f:
        json.dump(obj, f, indent=1)
    written += 1


def wp(rel, img):
    global written
    img.save(path(rel))
    written += 1


def rarity(level):
    return next(r for lv, r in ITEM_LEVEL_RARITY if (level or 0) >= lv)


def add_item(iid, name, template, texture, tab, handheld=False, extra=None, level=None):
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
                            (TK, "DDSS Tinkers", "The Tinkers materials from DDSS on top of Ore Overhaul Long Climb, which it needs. Tool part textures: Tinkers' Construct (MIT, SlimeKnights).")):
        use_mod(mod)
        if os.path.exists(OUT):
            shutil.rmtree(OUT)
        with open(path("horizon-mod.toml"), "w") as f:
            f.write(f'''id = "{mod}"
name = "{name}"
version = "0.2.0"
description = "{desc}"
authors = ["Zsombor"]
api = "0.2"
side = "both"
capabilities = ["registries"]
''')
    ladder_ids = {m["id"] for m in ladder.values()}

    def home(m):
        """Long Climb owns the ladder and every ore; everything else is Tinkers' own."""
        return LC if m["id"] in ladder_ids or m.get("ore") else TK

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
    for sid, m in sorted(mats.items()):
        ore = m.get("ore")
        if not ore or m["vanilla"] and sid != "diamond" and sid != "netherite" and sid not in ("copper", "iron"):
            continue
        lv = m["level_int"]
        if sid in ("copper", "iron", "diamond", "netherite"):
            # Vanilla's own ore blocks at new levels, in vanilla's stones.
            if sid == "netherite":
                targets = [("minecraft:base_stone_nether", "minecraft:ancient_debris")]
                needs[LC][lv - 1].append("minecraft:ancient_debris")
            else:
                targets = [("minecraft:stone_ore_replaceables", f"minecraft:{sid}_ore"), ("minecraft:deepslate_ore_replaceables", f"minecraft:deepslate_{sid}_ore")]
                needs[LC][lv - 1] += [f"minecraft:{sid}_ore", f"minecraft:deepslate_{sid}_ore"]
            world[ore["dim"]].append(write_feature(sid, ore, targets))
            continue
        hardness = 3 + lv * 0.35
        gemlike = m["gem"]
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
        targets = []
        if ore["dim"] == "overworld":
            stones = [("stone", "minecraft:stone_ore_replaceables", ""), ("deepslate", "minecraft:deepslate_ore_replaceables", "deepslate_")]
        elif ore["dim"] == "nether":
            stones = [("nether", "minecraft:base_stone_nether", "nether_")]
        else:
            stones = [("end", None, "end_")]
        for stone, tag, prefix in stones:
            bid = f"{prefix}{sid}_ore"
            label = {"": "", "deepslate_": "Deepslate ", "nether_": "Nether ", "end_": "End "}[prefix]
            add_block(bid, f"{label}{m['name']} Ore", template, art.ore(sid, stone, m["color"], gemlike), "ores", hardness + (1.5 if prefix == "deepslate_" else 0), 3 + lv * 0.2, level=lv)
            wj(f"{ADATA}/loot_table/blocks/{bid}.json", loot_ore(bid, drop))
            needs[LC][max(lv - 1, 0)].append(f"{MOD}:{bid}")
            targets.append((tag, f"{MOD}:{bid}"))
        world[ore["dim"]].append(write_feature(sid, ore, targets))

    # Worldgen hookup.
    for dim, feats in world.items():
        tag = {"overworld": "#minecraft:is_overworld", "nether": "#minecraft:is_nether", "end": "#minecraft:is_end"}[dim]
        wj(f"{ADATA}/neoforge/biome_modifier/add_ores_{dim}.json", {"type": "neoforge:add_features", "biomes": tag, "features": feats, "step": "underground_ores"})
    for dim, feats in VANILLA_REMOVED_FEATURES.items():
        tag = {"overworld": "#minecraft:is_overworld", "nether": "#minecraft:is_nether"}[dim]
        wj(f"{ADATA}/neoforge/biome_modifier/remove_vanilla_{dim}.json", {"type": "neoforge:remove_features", "biomes": tag, "features": [f"minecraft:{x}" for x in feats], "steps": ["underground_ores"]})

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

    # Plain tools for every ladder level past stone. Vanilla's own gear stands in on the vanilla levels.
    gems = sorted(ladder[lv]["level_int"] for lv in range(LEVELS) if ladder[lv]["gem"] and lv < DIAMOND)
    gems_all = sorted(lv for lv in range(LEVELS) if ladder[lv]["gem"])
    removed = []
    for lv in range(2, LEVELS):
        m = ladder[lv]
        sid = m["id"]
        prev = item_of[ladder[lv - 1]["id"]]
        gate = next((item_of[ladder[g]["id"]] for g in reversed(gems_all) if g < lv), None)
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
        if sid not in item_of or str(item_of[sid]).startswith(("minecraft:", "#")) or m.get("ore"):
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

    # Vanilla gear past stone gets its recipes from here instead.
    use_mod(LC)
    wj(f"{ADATA}/recipe_filter/vanilla_gear.json", {"filters": [{"output": i, "id": "minecraft:*", "remove": True} for i in removed]})

    titles = {LC: "Ore Overhaul", TK: "DDSS Tinkers"}
    for mod in (LC, TK):
        use_mod(mod)
        wj(f"{AASSET}/lang/en_us.json", dict(sorted(lang.items())))
        for t_, label in (("materials", "Materials"), ("ores", "Ores"), ("blocks", "Blocks"), ("tools", "Tools"), ("armor", "Armor")):
            if tabs[mod][t_]:
                wj(f"{ADATA}/horizon/creative_tab/{t_}.json", {"title": f"{titles[mod]}: {label}", "icon": tabs[mod][t_][0], "items": tabs[mod][t_]})

    write_report(d, armor_count)
    print("files", written, {m: len(langs[m]) for m in langs}, "armor pieces", armor_count, "placeholder recipes", len(missing_sources))


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


def write_feature(sid, ore, targets):
    feature = f"ore_{sid}"
    tg = []
    for tag, block in targets:
        if tag is None:
            pred = {"predicate_type": "minecraft:block_match", "block": "minecraft:end_stone"}
        else:
            pred = {"predicate_type": "minecraft:tag_match", "tag": tag}
        tg.append({"target": pred, "state": block})
    wj(f"{ADATA}/worldgen/configured_feature/{feature}.json", {"type": "minecraft:ore", "size": ore["size"], "discard_chance_on_air_exposure": 0.0, "targets": tg})
    placement = []
    if ore.get("rarity"):
        placement.append({"type": "minecraft:rarity_filter", "chance": ore["rarity"]})
    else:
        placement.append({"type": "minecraft:count", "count": ore.get("count", 1)})
    lo, hi = ore["y"]
    placement += [{"type": "minecraft:in_square"},
                  {"type": "minecraft:height_range", "height": {"type": "minecraft:uniform", "min_inclusive": {"absolute": lo}, "max_inclusive": {"absolute": hi}}},
                  {"type": "minecraft:biome"}]
    wj(f"{ADATA}/worldgen/placed_feature/{feature}.json", {"feature": f"{MOD}:{feature}", "placement": placement})
    return f"{MOD}:{feature}"


def write_report(d, armor_count):
    os.makedirs(os.path.join(ROOT, "design"), exist_ok=True)
    lines = ["# Ore Overhaul Long Climb: ore tiers 1 to 50", "", "An ore on tier T needs a pickaxe of tier T-1. Wood is the starting tool (tier 0). Tinkers' DDSS levels 0-12 scale to 0-45 (x3.75).", ""]
    lines += ["| Level | Ladder material | Tinkers level | Where | Vein | Durability | Speed | Attack |", "|---:|---|---:|---|---|---:|---:|---:|"]
    for lv in range(LEVELS):
        m = d["ladder"][lv]
        o = m.get("ore") or {}
        where = f"{o.get('dim', '-')} y{o['y'][0]}..{o['y'][1]}" if o else "-"
        vein = f"size {o['size']}, " + (f"1 in {o['rarity']} chunks" if o.get("rarity") else f"{o.get('count', 1)} per chunk") if o else "-"
        d_, s_, a_ = VANILLA_PICK.get(m["id"], (m["dur"], round(m["speed"], 2), round(m["atk"], 2)))
        lines.append(f"| {lv} | {m['name']}{' (new)' if m['new'] else ''}{' (vanilla gear)' if m['id'] in VANILLA_PICK else ''} | {m['ddss_harvest'] if m['ddss_harvest'] is not None else '-'} | {where} | {vein} | {d_} | {s_} | {a_} |")
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
