"""Which crafting recipes are early game: everything they take can be had before anything past a stone pickaxe.
Those keep vanilla's recipe on a 3x3; the rest go to the 5x5 table (native/longclimb/scale.rs reads the list written here)."""
import glob
import json
import os
import re

VANILLA = "/mnt/c/Users/feri1/AppData/Roaming/horizon-launcher/versions/nightly-2026-11-04-6475f62/.local/horizon-client/26.3/data/minecraft"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# What a player has with wooden and stone tools: wood, stone, dirt and sand, coal, plants, mob drops, food.
RAW_ITEMS = {
    "stick", "cobblestone", "cobbled_deepslate", "blackstone", "stone", "deepslate", "granite", "diorite", "andesite", "tuff", "calcite",
    "dirt", "coarse_dirt", "rooted_dirt", "mud", "sand", "red_sand", "gravel", "flint", "clay_ball", "clay", "coal", "charcoal",
    "string", "leather", "rabbit_hide", "rabbit_foot", "feather", "bone", "bone_meal", "wheat", "wheat_seeds", "beetroot_seeds",
    "melon_seeds", "pumpkin_seeds", "sugar_cane", "bamboo", "kelp", "cactus", "apple", "brown_mushroom", "red_mushroom", "egg",
    "rotten_flesh", "snowball", "vine", "pumpkin", "carved_pumpkin", "melon_slice", "sweet_berries", "glow_berries", "slime_ball",
    "gunpowder", "spider_eye", "ink_sac", "glow_ink_sac", "honeycomb", "moss_block", "pointed_dripstone", "dripstone_block",
    "porkchop", "beef", "chicken", "mutton", "rabbit", "cod", "salmon", "potato", "carrot", "beetroot", "cocoa_beans", "lily_pad",
    "hay_block", "snow_block", "ice", "netherrack", "basalt", "soul_sand", "soul_soil", "nether_wart", "dried_kelp", "sea_pickle",
    "scute", "turtle_scute", "armadillo_scute", "phantom_membrane", "torchflower_seeds", "pitcher_pod", "mangrove_roots",
}
RAW_TAGS = {"logs", "planks", "wool", "flowers", "saplings", "leaves", "small_flowers", "wooden_slabs", "fishes", "coals", "sand"}


def load_tags():
    tags = {}
    for base in [VANILLA] + glob.glob(f"{ROOT}/mod/*/data/minecraft"):
        for p in glob.glob(f"{base}/tags/item/**/*.json", recursive=True):
            name = "minecraft:" + os.path.relpath(p, f"{base}/tags/item")[:-5].replace(os.sep, "/")
            vals = [v if isinstance(v, str) else v.get("id") for v in json.load(open(p)).get("values", [])]
            tags.setdefault(name, []).extend(v for v in vals if v)
    return tags


def expand(tags, name, seen=None):
    seen = seen or set()
    if name in seen:
        return set()
    seen.add(name)
    out = set()
    for v in tags.get(name, []):
        out |= expand(tags, v[1:], seen) if v.startswith("#") else {v}
    return out


def options(ing):
    """The ids one ingredient accepts, each as an item id or '#tag'."""
    if isinstance(ing, str):
        return [ing]
    if isinstance(ing, list):
        return [x for i in ing for x in options(i)]
    if isinstance(ing, dict):
        if "item" in ing:
            return [ing["item"]]
        if "tag" in ing:
            return ["#" + ing["tag"]]
    return []


def recipes():
    out = {}
    for p in glob.glob(f"{VANILLA}/recipe/*.json"):
        out["minecraft:" + os.path.basename(p)[:-5]] = json.load(open(p))
    for mod in ("ddsstinkers", "longclimb"):
        for p in glob.glob(f"{ROOT}/mod/{mod}/data/{mod}/recipe/**/*.json", recursive=True):
            out[f"{mod}:" + os.path.relpath(p, f"{ROOT}/mod/{mod}/data/{mod}/recipe")[:-5]] = json.load(open(p))
    return out


def ingredients(r):
    t = r.get("type", "")
    if t == "minecraft:crafting_shaped":
        return list(r.get("key", {}).values())
    if t == "minecraft:crafting_shapeless":
        return r.get("ingredients", [])
    if t in ("minecraft:smelting", "minecraft:smoking", "minecraft:campfire_cooking", "minecraft:stonecutting"):
        return [r.get("ingredient")]
    return None


def result_id(r):
    res = r.get("result")
    return res if isinstance(res, str) else (res or {}).get("id")


def compute():
    tags = load_tags()
    early = {f"minecraft:{i}" for i in RAW_ITEMS}
    for t in RAW_TAGS:
        early |= expand(tags, f"minecraft:{t}")
    rs = recipes()

    def ok(ing):
        for o in options(ing):
            if o.startswith("#"):
                if expand(tags, o[1:]) & early:
                    return True
            elif o in early:
                return True
        return False

    changed = True
    while changed:
        changed = False
        for rid, r in rs.items():
            ings = ingredients(r)
            res = result_id(r)
            if ings is None or not res or res in early:
                continue
            if all(ok(i) for i in ings):
                early.add(res)
                changed = True
    crafting = sorted(rid for rid, r in rs.items() if r.get("type", "") in ("minecraft:crafting_shaped", "minecraft:crafting_shapeless")
                      and all(ok(i) for i in ingredients(r)))
    return crafting


def write(scale_rs):
    ids = compute()
    body = "".join(f'    "{i}",\n' for i in ids)
    s = open(scale_rs).read()
    s = re.sub(r"// EARLY START\n.*?// EARLY END\n", "// EARLY START\nconst EARLY: &[&str] = &[\n" + body + "];\n// EARLY END\n", s, flags=re.S)
    open(scale_rs, "w").write(s)
    return ids


if __name__ == "__main__":
    ids = write(os.path.join(ROOT, "native", "longclimb", "scale.rs"))
    print(len(ids), "early crafting recipes")
