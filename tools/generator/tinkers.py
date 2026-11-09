"""Tinkers' Construct content for the ddsstinkers mod: the blocks, items, models and recipes, and the table the native code reads.

Art and models start from Tinkers' Construct 1.12.2 (MIT, SlimeKnights): block and item textures are doubled to 32x32 with
Scale2x so they stay hard-edged; tool and part layers become greyscale masks a material's colour tints.
"""
import io
import json
import os
import zipfile

from PIL import Image

import art
from design import VANILLA_ITEM, safe_id

MODS = os.path.expanduser("~/ddss_horizon_port/DDSS_original_java/.minecraft/mods")
JAR = zipfile.ZipFile(os.path.join(MODS, "TConstruct-1.12.2-2.13.0.183.jar"))
A = "assets/tconstruct/"
NATIVE_DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "native", "ddsstinkers", "data")

# Tool kind -> (attacks per second, damage potential, damage cutoff, knockback, speed modifier, durability modifier, attack added,
#               attack multiplier, mining tags, big tool?). The numbers are read from Tinkers' own classes.
TOOLS = {
    "pickaxe": (1.2, 1.0, 0, 1.0, 1.0, 1.0, 0.0, 1.0, ["pickaxe"], 0),
    "shovel": (1.0, 0.9, 0, 1.0, 1.0, 1.0, 0.0, 1.0, ["shovel"], 0),
    "hatchet": (1.1, 1.1, 0, 1.3, 1.0, 1.0, 0.5, 1.0, ["axe"], 0),
    "mattock": (0.9, 0.9, 0, 1.1, 0.95, 1.0, 0.0, 1.0, ["axe", "shovel"], 0),
    "kama": (1.3, 1.0, 0, 1.0, 1.0, 1.0, 0.0, 1.0, ["hoe"], 0),
    "hammer": (0.8, 1.2, 0, 1.0, 0.4, 2.5, 0.0, 1.0, ["pickaxe"], 1),
    "excavator": (0.7, 1.25, 0, 1.0, 0.28, 1.75, 0.0, 1.0, ["shovel"], 1),
    "lumberaxe": (0.8, 1.2, 0, 1.5, 0.35, 2.0, 2.0, 1.0, ["axe"], 1),
    "scythe": (0.9, 0.75, 0, 1.0, 1.0, 2.2, 0.0, 1.0, ["hoe"], 1),
    "broadsword": (1.6, 1.0, 0, 1.0, 1.0, 1.1, 1.0, 1.0, [], 0),
    "longsword": (1.4, 1.1, 18, 1.0, 1.0, 1.05, 0.5, 1.0, [], 0),
    "rapier": (3.0, 0.55, 13, 0.6, 1.0, 0.8, 0.0, 1.0, [], 0),
    "frypan": (1.4, 1.0, 0, 2.0, 1.0, 1.0, 0.0, 1.0, [], 0),
    "battlesign": (1.2, 0.86, 0, 1.0, 1.0, 1.0, 0.0, 1.0, [], 0),
    "cleaver": (0.7, 1.2, 25, 1.0, 1.0, 2.0, 3.0, 1.3, [], 1),
    "shortbow": (1.0, 0.5, 0, 1.0, 1.0, 1.0, 0.0, 1.0, [], 0),
    "longbow": (0.8, 0.5, 0, 1.0, 1.0, 1.0, 0.0, 1.0, [], 1),
    "crossbow": (0.8, 0.5, 0, 1.0, 1.0, 1.0, 0.0, 1.0, [], 1),
    "arrow": (1.0, 1.0, 0, 1.0, 1.0, 1.0, 0.0, 1.0, [], 0),
    "bolt": (1.0, 1.0, 0, 1.0, 1.0, 1.0, 0.0, 1.0, [], 1),
    "shuriken": (1.0, 0.7, 0, 1.0, 1.0, 1.0, 0.0, 1.0, [], 1),
    "katana": (1.6, 1.0, 16, 1.0, 1.0, 1.0, 0.0, 1.0, [], 1),
    "laser_gun": (1.0, 1.0, 0, 1.0, 1.0, 1.0, 0.0, 1.0, [], 1),
}
# Which part goes in each slot of a tool, and the role that part's material plays in the stats.
TOOL_PARTS = {
    "pickaxe": [("tool_rod", "handle"), ("pick_head", "head"), ("binding", "extra")],
    "shovel": [("tool_rod", "handle"), ("shovel_head", "head"), ("binding", "extra")],
    "hatchet": [("tool_rod", "handle"), ("axe_head", "head"), ("binding", "extra")],
    "mattock": [("tool_rod", "handle"), ("axe_head", "head"), ("shovel_head", "head")],
    "kama": [("tool_rod", "handle"), ("kama_head", "head"), ("binding", "extra")],
    "hammer": [("tough_tool_rod", "handle"), ("hammer_head", "head"), ("large_plate", "head"), ("large_plate", "head")],
    "excavator": [("tough_tool_rod", "handle"), ("excavator_head", "head"), ("large_plate", "head"), ("tough_binding", "extra")],
    "lumberaxe": [("tough_tool_rod", "handle"), ("broad_axe_head", "head"), ("large_plate", "head"), ("tough_binding", "extra")],
    "scythe": [("tough_tool_rod", "handle"), ("scythe_head", "head"), ("tough_binding", "extra"), ("tough_tool_rod", "handle")],
    "broadsword": [("tool_rod", "handle"), ("sword_blade", "head"), ("wide_guard", "extra")],
    "longsword": [("tool_rod", "handle"), ("sword_blade", "head"), ("hand_guard", "extra")],
    "rapier": [("tool_rod", "handle"), ("sword_blade", "head"), ("cross_guard", "extra")],
    "frypan": [("tool_rod", "handle"), ("pan_head", "head")],
    "battlesign": [("tool_rod", "handle"), ("sign_head", "head")],
    "cleaver": [("tough_tool_rod", "handle"), ("large_sword_blade", "head"), ("large_plate", "head"), ("tough_tool_rod", "extra")],
    "shortbow": [("tool_rod", "bow"), ("tool_rod", "bow"), ("bow_string", "bowstring")],
    "longbow": [("bow_limb", "bow"), ("bow_limb", "bow"), ("large_plate", "extra"), ("bow_string", "bowstring")],
    "crossbow": [("tough_tool_rod", "handle"), ("bow_limb", "bow"), ("tough_binding", "extra"), ("bow_string", "bowstring")],
    "arrow": [("arrow_shaft", "shaft"), ("arrow_head", "head"), ("fletching", "fletching")],
    "bolt": [("arrow_shaft", "shaft"), ("bolt_core", "head"), ("fletching", "fletching")],
    "shuriken": [("knife_blade", "head"), ("knife_blade", "head"), ("knife_blade", "head"), ("knife_blade", "head")],
    "katana": [("tool_rod", "handle"), ("large_sword_blade", "head"), ("large_sword_blade", "head"), ("tough_binding", "extra")],
    "laser_gun": [("tool_rod", "handle"), ("pipe_piece", "head"), ("laser_medium", "extra"), ("battery_cell", "extra")],
}
NICE = {"pick_head": "Pickaxe Head", "tool_rod": "Tool Rod", "tough_tool_rod": "Tough Tool Rod", "axe_head": "Axe Head", "kama_head": "Kama Head", "hammer_head": "Hammer Head",
        "excavator_head": "Excavator Head", "broad_axe_head": "Broad Axe Head", "scythe_head": "Scythe Head", "sword_blade": "Sword Blade", "large_sword_blade": "Large Sword Blade",
        "wide_guard": "Wide Guard", "hand_guard": "Hand Guard", "cross_guard": "Cross Guard", "pan_head": "Pan", "sign_head": "Sign Plate", "bow_limb": "Bow Limb", "bow_string": "Bowstring",
        "arrow_shaft": "Arrow Shaft", "arrow_head": "Arrow Head", "bolt_core": "Bolt Core", "knife_blade": "Knife Blade", "shovel_head": "Shovel Head", "binding": "Binding",
        "tough_binding": "Tough Binding", "large_plate": "Large Plate", "sharpening_kit": "Sharpening Kit", "shard": "Shard", "fletching": "Fletching", "pipe_piece": "Pipe Piece",
        "laser_medium": "Laser Medium", "battery_cell": "Battery Cell"}
TOOL_NAMES = {"lumberaxe": "Lumber Axe", "broadsword": "Broadsword", "longsword": "Longsword", "frypan": "Frying Pan", "battlesign": "Battle Sign", "shortbow": "Short Bow", "longbow": "Long Bow", "laser_gun": "Laser Gun"}

# Blocks: id -> (name, template, hardness, jar texture or (top, side, bottom), recipe key).
SEARED = {"seared_stone": "seared_stone", "seared_cobble": "seared_cobble", "seared_paver": "seared_paver", "seared_bricks": "seared_brick", "seared_bricks_cracked": "seared_brick_cracked",
          "seared_bricks_fancy": "seared_brick_fancy", "seared_bricks_square": "seared_brick_square", "seared_bricks_triangle": "seared_brick_triangle", "seared_bricks_small": "seared_brick_small",
          "seared_road": "seared_road", "seared_tile": "seared_tile", "seared_creeper": "seared_creeper"}
METAL_BLOCKS = {"knightslime": 0xC37BFF, "pigiron": 0xF0A8A4, "alubrass": 0xEBC88C, "silky_jewel": 0x7BE7CF}


def jar_image(path):
    return Image.open(io.BytesIO(JAR.read(A + path))).convert("RGBA")


def scale2x(img):
    """Scale2x on colours: doubles the size with no new colours, so it stays sharp."""
    w, h = img.size
    src = img.load()
    out = Image.new("RGBA", (w * 2, h * 2))
    px = out.load()
    for y in range(h):
        for x in range(w):
            p = src[x, y]
            a, b, c, d = src[x, max(y - 1, 0)], src[min(x + 1, w - 1), y], src[max(x - 1, 0), y], src[x, min(y + 1, h - 1)]
            px[x * 2, y * 2] = a if c == a and c != d and a != b else p
            px[x * 2 + 1, y * 2] = b if a == b and a != c and b != d else p
            px[x * 2, y * 2 + 1] = c if d == c and d != b and c != a else p
            px[x * 2 + 1, y * 2 + 1] = d if b == d and b != a and d != c else p
    return out


def block_tex(path):
    img = jar_image("textures/blocks/" + path + ".png")
    return scale2x(img) if img.width <= 16 else img


def mask(path):
    """A Tinkers greyscale item layer as a hard-edged 32x32 tint mask."""
    img = jar_image("textures/items/" + path + ".png")
    img = scale2x(img) if img.width <= 16 else img
    px = img.load()
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = px[x, y]
            if a < 128:
                px[x, y] = (0, 0, 0, 0)
                continue
            v = (r + g + b) / 3
            # The jar's shades squeezed to five hard steps, bright enough that a colour stays vivid when it multiplies them.
            s = 70 if v < 100 else 125 if v < 140 else 175 if v < 180 else 225 if v < 215 else 245 if v < 245 else 255
            px[x, y] = (s, s, s, 255)
    return img


def fix_texture(t):
    t = t.replace("tconstruct:blocks/", "ddsstinkers:block/").replace("minecraft:blocks/planks_oak", "minecraft:block/oak_planks").replace("minecraft:blocks/log_oak", "minecraft:block/oak_log")
    return t.replace("minecraft:blocks/iron_block", "minecraft:block/iron_block").replace("minecraft:blocks/", "minecraft:block/")


def jar_model(name, extra_textures=None):
    """A block model from the jar, with its names moved to this mod. Its textures come along."""
    d = json.loads(JAR.read(A + f"models/block/{name}.json"))
    d.pop("comment", None)
    d.pop("display", None) if name != "faucet" else None
    if d.get("parent", "").startswith("tconstruct:"):
        d["parent"] = d["parent"].replace("tconstruct:block/", "ddsstinkers:block/")
    elif d.get("parent") == "block/block":
        d["parent"] = "minecraft:block/block"
    if extra_textures:
        d.setdefault("textures", {}).update(extra_textures)
    d["textures"] = {k: (fix_texture(v) if not v.startswith("#") else v) for k, v in d.get("textures", {}).items()}
    return d


def tool_layers():
    """Each tool's layers in the jar's order, with which of the tool's parts tints each."""
    out = {}
    for tool in TOOLS:
        name = {"katana": "broadsword", "laser_gun": "crossbow"}.get(tool, tool)
        name = {"lumberaxe": "lumberaxe"}.get(name, name)
        d = json.loads(JAR.read(A + f"models/item/tools/{name}.tcon.json"))
        layers = []
        tex = d["textures"]
        i = 0
        while f"layer{i}" in tex:
            layers.append(tex[f"layer{i}"].split("items/", 1)[1])
            i += 1
        out[tool] = layers
    return out


def run(ctx, mats, ladder, item_of, dump):
    """ctx: gen.py's helpers (use_mod, wj, wp, add_item, add_block, shaped, shapeless, loot_self, lang)."""
    ctx.use_mod(ctx.TK)
    wj, wp, add_item, add_block, shaped, shapeless, loot_self = ctx.wj, ctx.wp, ctx.add_item, ctx.add_block, ctx.shaped, ctx.shapeless, ctx.loot_self
    M = ctx.TK
    D = f"data/{M}"
    AS = f"assets/{M}"
    needs = ctx.needs_tk

    def tex(rel, img):
        wp(f"{AS}/textures/{rel}.png", img)

    def copy_block_tex(path):
        tex(f"block/{path}", block_tex(path))
        meta = A + f"textures/blocks/{path}.png.mcmeta"
        if meta in JAR.namelist():
            with open(ctx.path(f"{AS}/textures/block/{path}.png.mcmeta"), "wb") as f:
                f.write(JAR.read(meta))

    def plain_block(bid, name, jar, template="minecraft:stone", hardness=3.0, level=0, tab="blocks"):
        add_block(bid, name, template, block_tex(jar), tab, hardness, hardness * 2, level=level)
        wj(f"{D}/loot_table/blocks/{bid}.json", loot_self(bid))
        needs[max(level - 1, 0)].append(f"{M}:{bid}") if level else None

    def declared_block(bid, name, template, model, tab="machines", hardness=3.0, states=None, props=None, item_model=None):
        decl = {"template": template, "properties": {"hardness": hardness, "explosion_resistance": hardness * 4}}
        if props:
            decl.update(props)
        wj(f"{D}/horizon/block/{bid}.json", decl)
        wj(f"{AS}/models/block/{bid}.json", model)
        wj(f"{AS}/blockstates/{bid}.json", states or {"variants": {"": {"model": f"{M}:block/{bid}"}}})
        wj(f"{AS}/items/{bid}.json", {"model": {"type": "minecraft:model", "model": item_model or f"{M}:block/{bid}"}})
        ctx.lang[f"block.{M}.{bid}"] = name
        ctx.tabs[M][tab].append(f"{M}:{bid}")
        wj(f"{D}/loot_table/blocks/{bid}.json", loot_self(bid))
        needs[0].append(f"{M}:{bid}")

    # Textures the block models name.
    for t in ("smeltery/castingtable_top", "smeltery/castingtable_side", "smeltery/castingtable_bottom", "smeltery/blockcast_top", "smeltery/blockcast_side", "smeltery/blockcast_bottom",
              "smeltery/faucet", "smeltery/seared_tank_top", "smeltery/seared_tank_side", "smeltery/seared_gauge_side", "smeltery/seared_window_top", "smeltery/seared_window_side",
              "smeltery/drain_front", "smeltery/drain_back", "smeltery/smeltery_active", "smeltery/smeltery_inactive", "smeltery/seared_furnace_active", "smeltery/seared_furnace_inactive",
              "toolstation_top", "partbuilder_top", "stenciltable_top", "toolforge_top", "table_side", "craftingstation_top", "craftingstation_side", "grout", "fluids/molten_metal", "fluids/liquid", "fluids/liquid_stone"):
        copy_block_tex(t)

    # Grout and the seared family. Smelted grout gives a seared brick; four bricks make a block.
    plain_block("grout", "Grout", "grout", "minecraft:clay", 1.0)
    shapeless("grout", ["minecraft:sand", "minecraft:gravel", "minecraft:clay_ball", "minecraft:clay_ball"], f"{M}:grout", 2)
    add_item("seared_brick", "Seared Brick", "minecraft:brick", scale2x(jar_image("textures/items/materials/seared_brick.png")) if A + "textures/items/materials/seared_brick.png" in JAR.namelist() else art.ingot(0x45403C), "materials")
    wj(f"{D}/recipe/seared_brick.json", {"type": "minecraft:smelting", "category": "misc", "ingredient": f"{M}:grout", "result": {"id": f"{M}:seared_brick"}, "experience": 0.3, "cookingtime": 100})
    for bid, jar in SEARED.items():
        plain_block(bid, bid.replace("_", " ").title().replace("Bricks Cracked", "Bricks (Cracked)"), f"smeltery/{jar}", hardness=3.0)
    shaped("seared_bricks", ["BB", "BB"], {"B": f"{M}:seared_brick"}, f"{M}:seared_bricks", category="building")
    seared_tag = [f"{M}:{b}" for b in SEARED]
    # Any seared block turns into the next variety by hand, as Tinkers' stonecutting does.
    names = list(SEARED)
    for a, b in zip(names, names[1:] + names[:1]):
        shapeless(f"{b}_from_{a}", [f"{M}:{a}"], f"{M}:{b}")

    # The smeltery's parts.
    sb = f"{M}:seared_brick"
    bricks_all = f"{M}:block/seared_bricks"
    wj(f"{AS}/models/block/cube_tank.json", {"parent": "minecraft:block/block", "textures": {"particle": "#side"}, "elements": [{"from": [0, 0, 0], "to": [16, 16, 16], "faces": {d: {"texture": "#top" if d in ("up", "down") else "#side", "cullface": d} for d in ("up", "down", "north", "south", "east", "west")}}]})
    for tid, name, side in (("seared_tank", "Seared Tank", "seared_tank_side"), ("seared_gauge", "Seared Gauge", "seared_gauge_side"), ("seared_window", "Seared Window", "seared_window_side")):
        declared_block(tid, name, "minecraft:glass", {"parent": f"{M}:block/cube_tank", "textures": {"top": f"{M}:block/smeltery/seared_tank_top", "side": f"{M}:block/smeltery/{side}"}}, hardness=3.0)
    shaped("seared_tank", ["BBB", "BGB", "BBB"], {"B": sb, "G": "#c:glass_blocks" if False else "minecraft:glass"}, f"{M}:seared_tank", category="building")
    shaped("seared_gauge", ["BGB", "GBG", "BGB"], {"B": sb, "G": "minecraft:glass"}, f"{M}:seared_gauge", category="building")
    shaped("seared_window", ["BGB", "BGB", "BGB"], {"B": sb, "G": "minecraft:glass"}, f"{M}:seared_window", category="building")
    plain_block("seared_glass", "Seared Glass", "smeltery/seared_window_side", "minecraft:glass", 3.0)
    shaped("seared_glass", [" B ", "BGB", " B "], {"B": sb, "G": "minecraft:glass"}, f"{M}:seared_glass", 2, category="building")

    def facing_states(model, y0=0):
        rot = {"north": 0, "east": 90, "south": 180, "west": 270}
        return {"variants": {f"facing={f}": {"model": model, "y": (r + y0) % 360} for f, r in rot.items()}}

    # A furnace-shaped front that lights up: controllers for the smeltery, the seared furnace and the tinker tank.
    for cid, name, off, on, rec in (("smeltery_controller", "Smeltery Controller", "smeltery_inactive", "smeltery_active", ["BBB", "B B", "BBB"]),
                                    ("seared_furnace_controller", "Seared Furnace Controller", "seared_furnace_inactive", "seared_furnace_active", ["BBB", "BFB", "BBB"])):
        front_off = {"parent": "minecraft:block/orientable", "textures": {"top": bricks_all, "side": bricks_all, "front": f"{M}:block/smeltery/{off}"}}
        front_on = {"parent": "minecraft:block/orientable", "textures": {"top": bricks_all, "side": bricks_all, "front": f"{M}:block/smeltery/{on}"}}
        wj(f"{AS}/models/block/{cid}_on.json", front_on)
        rot = {"north": 0, "east": 90, "south": 180, "west": 270}
        states = {"variants": {}}
        for f, r in rot.items():
            states["variants"][f"facing={f},lit=false"] = {"model": f"{M}:block/{cid}", "y": r}
            states["variants"][f"facing={f},lit=true"] = {"model": f"{M}:block/{cid}_on", "y": r}
        declared_block(cid, name, "minecraft:furnace", front_off, hardness=3.0, states=states)
        key = {"B": sb}
        if "F" in "".join(rec):
            key["F"] = "minecraft:furnace"
        shaped(cid, rec, key, f"{M}:{cid}", category="building")
    wj(f"{AS}/models/block/seared_drain.json", {"parent": "minecraft:block/orientable", "textures": {"top": bricks_all, "side": bricks_all, "front": f"{M}:block/smeltery/drain_front"}})
    declared_block("seared_drain", "Seared Drain", "minecraft:carved_pumpkin", {"parent": "minecraft:block/orientable", "textures": {"top": bricks_all, "side": bricks_all, "front": f"{M}:block/smeltery/drain_front"}},
                   states=facing_states(f"{M}:block/seared_drain"))
    shaped("seared_drain", ["B B", "B B", "B B"], {"B": sb}, f"{M}:seared_drain", category="building")
    faucet = jar_model("faucet")
    faucet_states = {"variants": {f"facing={f}": {"model": f"{M}:block/seared_faucet", "y": r} for f, r in {"south": 0, "west": 90, "north": 180, "east": 270}.items()}}
    shape = {"properties": ["facing"], "values": {"south": [[0.25, 0.25, 0.625, 0.75, 0.625, 1]], "north": [[0.25, 0.25, 0, 0.75, 0.625, 0.375]], "east": [[0.625, 0.25, 0.25, 1, 0.625, 0.75]], "west": [[0, 0.25, 0.25, 0.375, 0.625, 0.75]]}}
    declared_block("seared_faucet", "Seared Faucet", "minecraft:tripwire_hook", faucet, hardness=2.0, states=faucet_states, props={"shapes": shape, "collision_shapes": shape})
    shaped("seared_faucet", ["B B", " B "], {"B": sb}, f"{M}:seared_faucet", category="building")
    declared_block("casting_table", "Casting Table", "minecraft:glass", jar_model("casting_table"), hardness=2.5)
    shaped("casting_table", ["BBB", "B B", "B B"], {"B": sb}, f"{M}:casting_table", category="building")
    declared_block("casting_basin", "Casting Basin", "minecraft:glass", jar_model("casting_basin"), hardness=2.5)
    shaped("casting_basin", ["B B", "B B", "BBB"], {"B": sb}, f"{M}:casting_basin", category="building")

    # The crafting tables. Their template is a barrel, which opens a menu; their looks are Tinkers' tables.
    wj(f"{AS}/models/block/table.json", jar_model("table"))
    for tid, name, jarname in (("part_builder", "Part Builder", "partbuilder"), ("tool_station", "Tool Station", "toolstation"), ("stencil_table", "Stencil Table", "stenciltable"), ("crafting_station", "Crafting Station", "craftingstation")):
        if tid == "crafting_station":
            declared_block(tid, name, "minecraft:crafting_table", jar_model(jarname), hardness=2.0)
            continue
        declared_block(tid, name, "minecraft:hopper", jar_model(jarname), hardness=2.0, props={"shapes": {"default": [[0, 0, 0, 1, 1, 1]]}, "collision_shapes": {"default": [[0, 0, 0, 1, 1, 1]]}})
    declared_block("tool_forge", "Tool Forge", "minecraft:hopper", jar_model("toolforge"), hardness=5.0, props={"shapes": {"default": [[0, 0, 0, 1, 1, 1]]}, "collision_shapes": {"default": [[0, 0, 0, 1, 1, 1]]}})

    # Patterns, casts, parts and tools.
    add_item("pattern", "Blank Pattern", "minecraft:paper", scale2x(jar_image("textures/items/pattern.png")), "machines", extra={"components": {"minecraft:max_stack_size": 64}})
    shaped("pattern", ["PS", "SP"], {"P": "#minecraft:planks", "S": "minecraft:stick"}, f"{M}:pattern", 4)
    shaped("stencil_table", ["P", "L"], {"P": f"{M}:pattern", "L": "#minecraft:planks"}, f"{M}:stencil_table")
    shaped("part_builder", ["P", "L"], {"P": f"{M}:pattern", "L": "#minecraft:logs"}, f"{M}:part_builder")
    shaped("tool_station", ["P", "C"], {"P": f"{M}:pattern", "C": "minecraft:crafting_table"}, f"{M}:tool_station")
    shaped("crafting_station", ["C"], {"C": "minecraft:crafting_table"}, f"{M}:crafting_station")
    shaped("tool_forge", ["BBB", "MSM", "M M"], {"B": sb, "M": "minecraft:iron_block", "S": f"{M}:tool_station"}, f"{M}:tool_forge")
    parts = {p["id"].split(":")[1]: p for p in dump["parts"]}
    pat_base = jar_image("textures/items/pattern.png")
    cast_base = jar_image("textures/items/cast.png")
    part_tex = {}
    for pid in parts:
        path = f"parts/{pid}"
        have = A + f"textures/items/{path}.png" in JAR.namelist()
        if not have:
            path = {"pipe_piece": "parts/tool_rod", "laser_medium": "parts/large_plate", "battery_cell": "parts/binding"}.get(pid, "parts/shard")
        part_tex[pid] = path
        tex(f"item/{pid}", mask(path))
        wj(f"{D}/horizon/item/{pid}.json", {"template": "minecraft:paper", "components": {"minecraft:max_stack_size": 64}})
        wj(f"{AS}/models/item/{pid}.json", {"parent": "minecraft:item/generated", "textures": {"layer0": f"{M}:item/{pid}"}})
        wj(f"{AS}/items/{pid}.json", {"model": {"type": "minecraft:model", "model": f"{M}:item/{pid}", "tints": [{"type": "minecraft:custom_model_data", "index": 0, "default": -1}]}})
        ctx.lang[f"item.{M}.{pid}"] = NICE.get(pid, pid.replace("_", " ").title())
        ctx.tabs[M]["parts"].append(f"{M}:{pid}")
        # The pattern and the cast show the part's outline.
        outline = jar_image("textures/items/" + path + ".png")
        for kind, base, label in (("pattern", pat_base, "Pattern"), ("cast", cast_base, "Cast"), ("clay_cast", cast_base, "Clay Cast")):
            icon = base.copy()
            silhouette = Image.new("RGBA", outline.size, {"pattern": (70, 44, 20, 255), "cast": (120, 84, 10, 255), "clay_cast": (110, 70, 50, 255)}[kind])
            icon.paste(silhouette, (0, 0), outline.split()[3])
            if kind == "clay_cast":
                icon = Image.eval(icon.convert("RGB"), lambda v: v).convert("RGBA")
                r, g, b, a = base.split()
                icon = Image.merge("RGBA", (*icon.split()[:3], a))
            iid = f"{kind}_{pid}"
            add_item(iid, f"{NICE.get(pid, pid.replace('_', ' ').title())} {label}", "minecraft:paper", scale2x(icon), "machines", extra={"components": {"minecraft:max_stack_size": 1 if kind != "pattern" else 16}})
    # Plain casts for ingots, nuggets and gems.
    for cid, label in (("ingot", "Ingot"), ("nugget", "Nugget"), ("gem", "Gem"), ("plate", "Plate"), ("gear", "Gear")):
        add_item(f"cast_{cid}", f"{label} Cast", "minecraft:paper", scale2x(jar_image(f"textures/items/cast_{cid}.png")), "machines", extra={"components": {"minecraft:max_stack_size": 1}})
    layers = tool_layers()
    tool_slots = {}
    for tool, stats in TOOLS.items():
        aps, dp, cutoff, kb, sm, dm, add, mul, mining, big = stats
        rel = []
        tints = []
        for i, layer in enumerate(layers[tool]):
            name = f"tool/{tool}_{i}"
            tex(f"item/{name}", mask(layer))
            wj(f"{AS}/models/item/{name}.json", {"parent": "minecraft:item/handheld", "textures": {"layer0": f"{M}:item/{name}"}})
            tints.append({"type": "minecraft:model", "model": f"{M}:item/{name}", "tints": [{"type": "minecraft:custom_model_data", "index": i, "default": -1}]})
        wj(f"{AS}/items/{tool}.json", {"model": {"type": "minecraft:composite", "models": tints}})
        template = {"shortbow": "minecraft:bow", "longbow": "minecraft:bow", "crossbow": "minecraft:crossbow", "battlesign": "minecraft:shield", "arrow": "minecraft:arrow", "bolt": "minecraft:arrow", "shuriken": "minecraft:snowball"}.get(tool, "minecraft:paper")
        if tool == "shuriken":
            wj(f"{D}/horizon/entity_type/shuriken_thrown.json", {"template": "minecraft:snowball", "item": f"{M}:shuriken", "damage": 6.0})
            ctx.lang[f"entity.{M}.shuriken_thrown"] = "Shuriken"
        wj(f"{D}/horizon/item/{tool}.json", {"template": template, "components": {
            "minecraft:max_stack_size": 64 if tool in ("arrow", "bolt") else 16 if tool == "shuriken" else 1, **({} if tool in ("arrow", "bolt", "shuriken") else {"minecraft:max_damage": 1 << 24, "minecraft:damage": 0}),
            "minecraft:tool": {"rules": [{"blocks": f"#{ctx.LC}:incorrect_for_level_0", "correct_for_drops": False}], "damage_per_block": 1},
            "minecraft:attribute_modifiers": [{"type": "minecraft:attack_damage", "id": "minecraft:base_attack_damage", "amount": 0.0, "operation": "add_value", "slot": "mainhand"},
                                              {"type": "minecraft:attack_speed", "id": "minecraft:base_attack_speed", "amount": round(aps - 4.0, 3), "operation": "add_value", "slot": "mainhand"}],
            "minecraft:weapon": {"item_damage_per_attack": 1}}})
        ctx.lang[f"item.{M}.{tool}"] = TOOL_NAMES.get(tool, tool.title())
        ctx.tabs[M]["tinker_tools"].append(f"{M}:{tool}")
        tool_slots[tool] = len(layers[tool])
    # Tinker's books: the jar's manuals as ordinary items for now; pages come from the native mod.
    # The manuals are vanilla written books carrying the jar's pages, crafted like Tinkers' own.
    for bid, title, sections, extra_item in (("book_materials_and_you", "Materials and You", ["intro", "tools"], f"{M}:pattern"), ("book_puny_smelting", "Puny Smelting", ["seared_furnace", "structure"], "minecraft:brick"),
                                             ("book_mighty_smelting", "Mighty Smelting", ["smeltery", "tinker_tank"], f"{M}:seared_brick"), ("book_encyclopedia", "Encyclopedia of Tinkering", ["modifiers"], "minecraft:redstone")):
        wj(f"{D}/recipe/{bid}.json", {"type": "minecraft:crafting_shapeless", "category": "misc", "ingredients": ["minecraft:book", extra_item],
                                      "result": {"id": "minecraft:written_book", "count": 1, "components": {"minecraft:written_book_content": book_pages(title, sections)}}})

    # Materials, modifiers and food as plain items with the jar's art.
    for iid, name, path, tmpl in (
        ("mending_moss", "Mending Moss", "materials/mending_moss", "minecraft:paper"), ("moss", "Ball of Moss", "materials/moss", "minecraft:paper"), ("silky_cloth", "Silky Cloth", "materials/silky_cloth", "minecraft:paper"),
        ("silky_jewel", "Silky Jewel", "materials/silky_jewel", "minecraft:paper"), ("necrotic_bone", "Necrotic Bone", "materials/necrotic_bone", "minecraft:bone"), ("reinforcement", "Reinforcement", "materials/reinforcement", "minecraft:paper"),
        ("expander_h", "Height Expander", "materials/expander_h", "minecraft:paper"), ("expander_w", "Width Expander", "materials/expander_w", "minecraft:paper"), ("slimeball_blue", "Blue Slimeball", "materials/slimeball_blue", "minecraft:slime_ball"),
        ("slimeball_purple", "Purple Slimeball", "materials/slimeball_purple", "minecraft:slime_ball"), ("slimeball_blood", "Blood Slimeball", "materials/slimeball_blood", "minecraft:slime_ball"), ("slimeball_magma", "Magma Slimeball", "materials/slimeball_magma", "minecraft:slime_ball"),
        ("slimecrystal_green", "Green Slime Crystal", "materials/slimecrystal_green", "minecraft:paper"), ("slimecrystal_blue", "Blue Slime Crystal", "materials/slimecrystal_blue", "minecraft:paper"), ("slimecrystal_magma", "Magma Slime Crystal", "materials/slimecrystal_magma", "minecraft:paper"),
        ("stone_rod", "Stone Rod", "materials/stone_rod", "minecraft:stick"), ("glowball", "Glow Ball", "gadgets/glowball", "minecraft:snowball"), ("efln", "EFLN", "gadgets/efln", "minecraft:snowball"), ("slimesling", "Slime Sling", "gadgets/slimesling", "minecraft:paper"), ("slime_boots", "Slime Boots", "armor/slime_boots" if False else "gadgets/slimesling", "minecraft:iron_boots"),
    ):
        add_item(iid, name, tmpl, scale2x(jar_image(f"textures/items/{path}.png")), "gadgets" if path.startswith("gadgets") else "materials")
    for iid, name, path, nut, sat in (("bacon", "Bacon", "bacon", 4, 0.6), ("jerky_monster", "Monster Jerky", "jerky_monster", 4, 0.8), ("jerky_beef", "Beef Jerky", "jerky_beef", 8, 1.0), ("jerky_pork", "Pork Jerky", "jerky_pork", 8, 1.0), ("jerky_chicken", "Chicken Jerky", "jerky_chicken", 6, 0.8),
                                      ("jerky_mutton", "Mutton Jerky", "jerky_mutton", 6, 0.8), ("jerky_rabbit", "Rabbit Jerky", "jerky_rabbit", 5, 0.8), ("jerky_fish", "Fish Jerky", "jerky_fish", 5, 0.8), ("apple_diamond", "Jeweled Apple", "apple_diamond", 4, 1.2), ("moms_spaghetti", "Mom's Spaghetti", "moms_spaghetti", 6, 0.6),
                                      ("slimedrop_green", "Green Slime Drop", "slimedrop_green", 1, 1.0), ("slimedrop_blue", "Blue Slime Drop", "slimedrop_blue", 1, 1.0), ("slimedrop_purple", "Purple Slime Drop", "slimedrop_purple", 1, 2.0), ("slimedrop_magma", "Magma Slime Drop", "slimedrop_magma", 2, 1.0)):
        add_item(iid, name, "minecraft:cooked_porkchop", scale2x(jar_image(f"textures/items/food/{path}.png")), "gadgets", extra={"components": {"minecraft:food": {"nutrition": nut, "saturation": round(nut * sat, 2)}}})
    shaped("silky_jewel", ["CCC", "CEC", "CCC"], {"C": f"{M}:silky_cloth", "E": "minecraft:emerald"}, f"{M}:silky_jewel")
    shaped("silky_cloth", ["SSS", "SGS", "SSS"], {"S": "minecraft:string", "G": "minecraft:gold_ingot"}, f"{M}:silky_cloth")
    shaped("moss", ["LLL", "LLL", "LLL"], {"L": "#minecraft:leaves"}, f"{M}:moss")
    shaped("mending_moss", ["MB", "BM"], {"M": f"{M}:moss", "B": "minecraft:bookshelf"}, f"{M}:mending_moss")
    shaped("reinforcement", ["OOO", "OPO", "OOO"], {"O": "minecraft:obsidian", "P": f"{M}:cast_plate"}, f"{M}:reinforcement")
    shaped("expander_h", ["PCP", "PSP", "PCP"], {"P": "minecraft:piston", "C": "minecraft:copper_ingot", "S": "minecraft:iron_block"}, f"{M}:expander_h")
    shaped("expander_w", ["PPP", "CSC", "PPP"], {"P": "minecraft:piston", "C": "minecraft:copper_ingot", "S": "minecraft:iron_block"}, f"{M}:expander_w")
    shapeless("glowball", ["minecraft:glowstone_dust", "minecraft:snowball"], f"{M}:glowball", 2)
    shapeless("efln", ["minecraft:flint", "minecraft:gunpowder"], f"{M}:efln")
    shaped("slimesling", ["SSS", "L L", " L "], {"S": "minecraft:string", "L": "minecraft:slime_ball"}, f"{M}:slimesling")
    shaped("slime_boots", ["S S", "B B"], {"S": "minecraft:slime_block", "B": "minecraft:slime_ball"}, f"{M}:slime_boots")
    shaped("stone_rod", ["S", "S"], {"S": "minecraft:cobblestone"}, f"{M}:stone_rod", 4)
    for meat, out in (("minecraft:beef", "jerky_beef"), ("minecraft:porkchop", "jerky_pork"), ("minecraft:chicken", "jerky_chicken"), ("minecraft:mutton", "jerky_mutton"), ("minecraft:rabbit", "jerky_rabbit"), ("minecraft:cod", "jerky_fish"), ("minecraft:rotten_flesh", "jerky_monster")):
        wj(f"{D}/recipe/{out}.json", {"type": "minecraft:smoking", "category": "food", "ingredient": meat, "result": {"id": f"{M}:{out}"}, "experience": 0.35, "cookingtime": 2400})
    # Slime blocks, slime ground, trees' leaves and the blocks of its islands.
    for color, tint in (("green", 0x77DD55), ("blue", 0x55BBEE), ("purple", 0xAA55EE), ("magma", 0xFF8833), ("blood", 0xBB2222)):
        ball = {"green": "minecraft:slime_ball", "blue": f"{M}:slimeball_blue", "purple": f"{M}:slimeball_purple", "magma": f"{M}:slimeball_magma", "blood": f"{M}:slimeball_blood"}[color]
        jar = {"green": "slime/slimeblock_green"}.get(color, f"slime/slime_{color}")
        plain_block(f"congealed_{color}_slime", f"Congealed {color.title()} Slime", jar, "minecraft:stone", 0.5, tab="slime")
        shaped(f"congealed_{color}_slime", ["BB", "BB"], {"B": ball}, f"{M}:congealed_{color}_slime", category="building")
        if color != "blood":
            plain_block(f"{color}_slime_dirt", f"{color.title()} Slime Dirt", f"slime/slimedirt_{color}", "minecraft:dirt", 0.5, tab="slime")
            top = block_tex("slime/slimegrass_top")
            r, g, b, a = top.split()
            tinted = Image.merge("RGBA", (Image.eval(r, lambda v: v * ((tint >> 16) & 255) // 255), Image.eval(g, lambda v: v * ((tint >> 8) & 255) // 255), Image.eval(b, lambda v: v * (tint & 255) // 255), a))
            tex(f"block/{color}_slime_grass_top", tinted)
            overlay = block_tex("slime/slimegrass_overlay")
            r, g, b, a = overlay.split()
            over = Image.merge("RGBA", (Image.eval(r, lambda v: v * ((tint >> 16) & 255) // 255), Image.eval(g, lambda v: v * ((tint >> 8) & 255) // 255), Image.eval(b, lambda v: v * (tint & 255) // 255), a))
            side = block_tex(f"slime/slimedirt_{color}").copy()
            side.alpha_composite(over)
            tex(f"block/{color}_slime_grass_side", side)
            copy_block_tex(f"slime/slimedirt_{color}")
            declared_block(f"{color}_slime_grass", f"{color.title()} Slime Grass", "minecraft:dirt", {"parent": "minecraft:block/cube_bottom_top", "textures": {"top": f"{M}:block/{color}_slime_grass_top", "side": f"{M}:block/{color}_slime_grass_side", "bottom": f"{M}:block/slime/slimedirt_{color}"}}, tab="slime", hardness=0.6)
            leaves = block_tex("slime/slimeleaves")
            r, g, b, a = leaves.split()
            lv = Image.merge("RGBA", (Image.eval(r, lambda v: v * ((tint >> 16) & 255) // 255), Image.eval(g, lambda v: v * ((tint >> 8) & 255) // 255), Image.eval(b, lambda v: v * (tint & 255) // 255), a))
            tex(f"block/{color}_slime_leaves", lv)
            declared_block(f"{color}_slime_leaves", f"{color.title()} Slime Leaves", "minecraft:oak_leaves", {"parent": "minecraft:block/leaves", "textures": {"all": f"{M}:block/{color}_slime_leaves"}}, tab="slime", hardness=0.2)
    # The other small things: stone torch and ladder, firewood, brownstone, clear glass, chests.
    for path, bid, name, tmpl, hard in (("firewood", "firewood", "Firewood", "minecraft:oak_planks", 2.0), ("lavawood", "lavawood", "Lavawood", "minecraft:oak_planks", 2.0), ("dried_clay", "dried_clay", "Dried Clay", "minecraft:terracotta", 1.0), ("dried_clay_bricks", "dried_clay_bricks", "Dried Clay Bricks", "minecraft:bricks", 1.5), ("mud_brick", "mud_bricks", "Mud Bricks", "minecraft:bricks", 1.0),
                                        ("brownstone/brick", "brownstone", "Brownstone", "minecraft:stone", 1.5), ("brownstone/brick_fancy", "brownstone_fancy", "Fancy Brownstone", "minecraft:stone", 1.5), ("block_alubrass", "alubrass_block", "Block of Aluminum Brass", "minecraft:iron_block", 4.0), ("block_silky_jewel", "silky_jewel_block", "Block of Silky Jewel", "minecraft:iron_block", 4.0)):
        plain_block(bid, name, path, tmpl, hard, tab="slime")
    shaped("silky_jewel_block", ["JJJ", "JJJ", "JJJ"], {"J": f"{M}:silky_jewel"}, f"{M}:silky_jewel_block", category="building")
    shapeless("firewood", ["#minecraft:planks", "minecraft:blaze_powder"], f"{M}:firewood")
    shapeless("lavawood", ["#minecraft:planks", "minecraft:lava_bucket"], f"{M}:lavawood")
    wj(f"{D}/recipe/dried_clay.json", {"type": "minecraft:smelting", "category": "blocks", "ingredient": "minecraft:clay", "result": {"id": f"{M}:dried_clay"}, "experience": 0.2, "cookingtime": 100})
    shaped("dried_clay_bricks", ["CC", "CC"], {"C": f"{M}:dried_clay"}, f"{M}:dried_clay_bricks", 4, category="building")
    shaped("brownstone", ["SS", "SS"], {"S": "minecraft:red_sandstone"}, f"{M}:brownstone", 4, category="building")
    copy_block_tex("chest/pattern_top") if False else None
    for cid, name, make in (("pattern_chest", "Pattern Chest", f"{M}:pattern"), ("part_chest", "Part Chest", f"{M}:binding")):
        declared_block(cid, name, "minecraft:barrel", {"parent": "minecraft:block/cube_all", "textures": {"all": f"{M}:block/table_side"}}, hardness=2.0)
        shaped(cid, ["P", "C"], {"P": make, "C": "minecraft:chest"}, f"{M}:{cid}")
    # A crafting table in Tinkers' clothes: vanilla's block does the crafting. Its shape is a full cube, so the model is too.
    wj(f"{D}/horizon/block/crafting_station.json", {"template": "minecraft:crafting_table", "properties": {"hardness": 2.0, "explosion_resistance": 8.0}})
    wj(f"{AS}/models/block/crafting_station.json", {"parent": "minecraft:block/cube_bottom_top", "textures": {"top": f"{M}:block/craftingstation_top", "side": f"{M}:block/craftingstation_side", "bottom": "minecraft:block/oak_planks"}})
    # A multiblock tank, and channels between pours.
    declared_block("tinker_tank_controller", "Tinker Tank Controller", "minecraft:furnace", {"parent": "minecraft:block/orientable", "textures": {"top": bricks_all, "side": bricks_all, "front": f"{M}:block/smeltery/seared_furnace_inactive"}},
                   hardness=3.0, states={"variants": {f"facing={f},lit={l}": {"model": f"{M}:block/tinker_tank_controller", "y": r} for f, r in {"north": 0, "east": 90, "south": 180, "west": 270}.items() for l in ("false", "true")}})
    shaped("tinker_tank_controller", ["BGB", "BFB", "BGB"], {"B": sb, "G": "minecraft:glass", "F": "minecraft:furnace"}, f"{M}:tinker_tank_controller", category="building")
    write_islands(ctx)
    # Bows and crossbows draw what's tagged as arrows: Tinkers' own arrows and bolts too.
    wj("data/minecraft/tags/item/arrows.json", {"values": [f"{M}:arrow", f"{M}:bolt"]})

    # Menus.
    wj(f"{D}/horizon/menu/smeltery.json", {"slots": 45, "data_slots": 96})
    wj(f"{D}/horizon/menu/part_builder.json", {"slots": 3, "data_slots": 4, "results": [2]})
    wj(f"{D}/horizon/menu/stencil_table.json", {"slots": 2, "data_slots": 4, "results": [1]})
    wj(f"{D}/horizon/menu/tool_station.json", {"slots": 7, "data_slots": 8, "results": [6]})
    wj(f"{D}/horizon/menu/tool_forge.json", {"slots": 7, "data_slots": 8, "results": [6]})
    # GUI art at its own 256x256 sheet size.
    for g in ("smeltery", "partbuilder", "stenciltable", "toolstation", "generic", "seared_furnace"):
        img = jar_image(f"textures/gui/{g}.png")
        wp(f"{AS}/textures/gui/{g}.png", img)

    write_table(mats, ladder, item_of, dump, parts, part_tex, layers, seared_tag)


def book_pages(title, sections):
    """The jar's manuals as a written book: every page's text, 240 characters a page."""
    import re
    pages = []
    for name in JAR.namelist():
        if not name.startswith(A + "book/en_us/") or not name.endswith(".json"):
            continue
        section = name.split("/")[4]
        if section not in sections:
            continue
        d = json.loads(JAR.read(name))
        head = d.get("title", "") if isinstance(d, dict) else ""
        parts = []

        def walk(x):
            if isinstance(x, dict):
                t = x.get("text")
                if isinstance(t, str) and not x.get("title"):
                    parts.append(t)
                elif isinstance(t, list):
                    walk(t)
                for k, v in x.items():
                    if k not in ("text",) and isinstance(v, (dict, list)):
                        walk(v)
            elif isinstance(x, list):
                for v in x:
                    walk(v)
        walk(d)
        body = re.sub(r"\$\$[a-z_.]+\$\$|\\n", " ", " ".join(p for p in parts if p != "Text Goes Here")).strip()
        if not body:
            continue
        text = (str(head) + "\n\n" if head else "") + body
        while text:
            cut = text[:240].rfind(" ") if len(text) > 240 else len(text)
            cut = cut if cut > 0 else 240
            pages.append(text[:cut].strip())
            text = text[cut:].strip()
    pages = [p for p in pages if p][:100] or ["(empty)"]
    return {"title": {"raw": title}, "author": "SlimeKnights", "generation": 0, "resolved": True, "pages": [{"raw": json.dumps({"text": p}) if False else p} for p in pages]}


def nbt_structure(blocks, size):
    """A structure template: blocks is {(x, y, z): "id"}."""
    import gzip
    import struct

    def t_str(s):
        b = s.encode()
        return struct.pack(">H", len(b)) + b

    def named(tag, name, payload):
        return bytes([tag]) + t_str(name) + payload

    def list_(tag, items):
        return bytes([tag]) + struct.pack(">i", len(items)) + b"".join(items)

    palette = sorted(set(blocks.values()))
    index = {b: i for i, b in enumerate(palette)}
    pal = [named(8, "Name", t_str(b)) + b"\0" for b in palette]
    items = []
    for (x, y, z), b in sorted(blocks.items()):
        pos = list_(3, [struct.pack(">i", v) for v in (x, y, z)])
        items.append(named(9, "pos", pos) + named(3, "state", struct.pack(">i", index[b])) + b"\0")
    body = named(9, "size", list_(3, [struct.pack(">i", v) for v in size])) + named(9, "entities", list_(0, [])) + named(9, "blocks", list_(10, items)) + named(9, "palette", list_(10, pal)) + named(3, "DataVersion", struct.pack(">i", 4800))
    return gzip.compress(b"\x0a" + t_str("") + body + b"\0")


def write_islands(ctx):
    """Slime islands: floating discs of slime dirt with slime grass, a pool of congealed slime and a few slime trees, as Tinkers' generator lays them out."""
    import math
    import random
    M = ctx.TK
    D = f"data/{M}"
    sets = []
    for color, biomes, y, rate in (("green", "#minecraft:is_overworld", 118, 36), ("blue", "#minecraft:is_overworld", 138, 48), ("purple", "#minecraft:is_end", 70, 24), ("magma", "#minecraft:is_nether", 90, 24)):
        rnd = random.Random("island-" + color)
        for variant in range(2):
            r = rnd.randint(9, 14)
            size = (r * 2 + 3, 16, r * 2 + 3)
            cx = cz = r + 1
            blocks = {}
            pool = (cx + rnd.randint(-3, 3), cz + rnd.randint(-3, 3), rnd.randint(2, 4))
            for x in range(size[0]):
                for z in range(size[2]):
                    d = math.hypot(x - cx, z - cz) + math.sin(x * 0.7 + variant) * 0.8 + math.cos(z * 0.6) * 0.8
                    if d > r:
                        continue
                    depth = int((r - d) * 0.55) + 1
                    for k in range(depth):
                        yy = 6 - k
                        if yy < 0:
                            break
                        blocks[(x, yy, z)] = f"{M}:congealed_{color}_slime" if k >= 2 else f"{M}:{color}_slime_dirt"
                    in_pool = math.hypot(x - pool[0], z - pool[1]) <= pool[2]
                    blocks[(x, 6, z)] = f"{M}:congealed_{color}_slime" if in_pool else f"{M}:{color}_slime_grass"
            for _ in range(rnd.randint(3, 5)):
                a, dist = rnd.random() * 6.283, rnd.uniform(0.2, 0.7) * r
                tx, tz = int(cx + math.cos(a) * dist), int(cz + math.sin(a) * dist)
                if blocks.get((tx, 6, tz), "").endswith("_grass"):
                    h = rnd.randint(3, 5)
                    for j in range(1, h + 1):
                        blocks[(tx, 6 + j, tz)] = f"{M}:congealed_{color}_slime"
                    for dx in range(-2, 3):
                        for dz in range(-2, 3):
                            for dy in range(0, 3):
                                if abs(dx) + abs(dz) + dy <= 3 and (dx or dz or dy):
                                    p = (tx + dx, 6 + h + dy, tz + dz)
                                    if 0 <= p[0] < size[0] and 0 <= p[2] < size[2] and p not in blocks:
                                        blocks[p] = f"{M}:{color}_slime_leaves"
            name = f"slime_island_{color}_{variant}"
            with open(ctx.path(f"{D}/structure/{name}.nbt"), "wb") as f:
                f.write(nbt_structure(blocks, size))
        ctx.wj(f"{D}/worldgen/template_pool/slime_island_{color}.json", {"fallback": "minecraft:empty", "elements": [{"weight": 1, "element": {"element_type": "minecraft:single_pool_element", "location": f"{M}:slime_island_{color}_{v}", "projection": "rigid", "processors": "minecraft:empty"}} for v in range(2)]})
        ctx.wj(f"{D}/worldgen/structure/slime_island_{color}.json", {"type": "minecraft:jigsaw", "biomes": biomes, "step": "surface_structures", "spawn_overrides": {}, "terrain_adaptation": "none", "start_pool": f"{M}:slime_island_{color}", "size": 1,
                                                                    "start_height": {"absolute": y}, "max_distance_from_center": 40, "use_expansion_hack": False})
        ctx.wj(f"{D}/worldgen/structure_set/slime_island_{color}.json", {"structures": [{"structure": f"{M}:slime_island_{color}", "weight": 1}], "placement": {"type": "minecraft:random_spread", "spacing": rate, "separation": max(rate // 3, 4), "salt": 20220900 + sum(map(ord, color))}})


def fluid_of(m):
    return (m["fluid"] or "").replace("_fluid", "") or None


def write_table(mats, ladder, item_of, dump, parts, part_tex, layers, seared_tag):
    """Everything the native code reads: materials, parts, tools, melting and alloys."""
    melting_temp = {}
    for e in dump["melting"]:
        o = e.get("output")
        if o:
            melting_temp.setdefault(o["fluid"].replace("_fluid", ""), e["temp"])
    table = {"materials": {}, "parts": {}, "tools": {}, "melting": {}, "alloys": [], "fuels": [], "items": {}, "seared": seared_tag}
    fluids = {}
    for sid, m in sorted(mats.items()):
        s = m.get("stats") or {}
        fl = fluid_of(m)
        entry = {"name": m["name"], "color": m["color"] & 0xFFFFFF, "level": m["level_int"] if m.get("level_int") is not None else 0, "fluid": fl, "item": item_of.get(sid),
                 "head": s.get("head"), "handle": s.get("handle"), "extra": s.get("extra"), "bow": s.get("bow"), "bowstring": s.get("bowstring"), "projectile": s.get("projectile"),
                 "shaft": s.get("shaft"), "fletching": s.get("fletching"), "traits": {k: [t for t in v if not t.startswith("ERR")] for k, v in (m.get("traits") or {}).items()}, "castable": bool(fl), "craftable": False}
        if not m.get("ddss_id"):  # new materials have no Tinkers stats of their own: use the ladder's
            entry["head"] = {"durability": m["dur"], "harvestLevel": 0, "attack": m["atk"], "miningspeed": m["speed"]} if m.get("dur") else None
            entry["handle"] = {"modifier": 1.0, "durability": m.get("handle_dur") or 0} if m.get("dur") else None
            entry["extra"] = {"extraDurability": m.get("extra") or 0} if m.get("dur") else None
        table["materials"][sid] = entry
        if fl:
            fluids[fl] = {"name": m["name"], "color": m["color"] & 0xFFFFFF, "temp": melting_temp.get(fl, 300 + (m["level_int"] or 0) * 25)}
    for extra_fluid, (name, color, temp) in {"stone": ("Seared Stone", 0x77706A, 350), "clay": ("Clay", 0xB4845E, 300), "glass": ("Molten Glass", 0xB8D8E8, 325), "gold": ("Gold", 0xFAD64A, 400),
                                             "obsidian": ("Obsidian", 0x2A1E3A, 500), "blood": ("Blood", 0x8A0F0F, 310), "water": ("Water", 0x3F76E4, 300), "lava": ("Lava", 0xE85A00, 1000), "emerald": ("Emerald", 0x40D070, 700), "alubrass": ("Aluminum Brass", 0xEBC88C, 330)}.items():
        fluids.setdefault(extra_fluid, {"name": name, "color": color, "temp": temp})
    table["fluids"] = fluids
    for pid, p in parts.items():
        table["parts"][pid] = {"cost": p["cost"], "name": NICE.get(pid, pid.title())}
    for tool, stats in TOOLS.items():
        aps, dp, cutoff, kb, sm, dm, add, mul, mining, big = stats
        table["tools"][tool] = {"aps": aps, "damage": dp, "cutoff": cutoff, "knockback": kb, "speed": sm, "durability": dm, "attack_add": add, "attack_mul": mul, "mining": mining, "big": bool(big),
                                "parts": [{"part": p, "role": r} for p, r in TOOL_PARTS[tool]], "layers": len(layers[tool]), "name": TOOL_NAMES.get(tool, tool.title())}
    # Melting: every material's ingot, block, raw form and ores; vanilla's special cases.
    melt = table["melting"]

    def add_melt(item, fluid, amount):
        if item and not str(item).startswith("#") and fluid in fluids:
            melt[item] = {"fluid": fluid, "amount": amount}

    for sid, m in mats.items():
        fl = fluid_of(m)
        if not fl:
            continue
        add_melt(item_of.get(sid), fl, 144)
        mod = "longclimb" if m.get("ore") or sid in {x["id"] for x in ladder.values()} else "ddsstinkers"
        add_melt(f"{mod}:{sid}_block", fl, 1296)
        add_melt(f"longclimb:raw_{sid}", fl, 288)
        for prefix in ("", "deepslate_", "nether_", "end_", "andesite_", "diorite_", "granite_", "molten_", "bedrock_", "meteorite_", "obsidiorite_"):
            add_melt(f"longclimb:{prefix}{sid}_ore", fl, 288)
    for item, fl, n in (("minecraft:iron_ingot", "iron", 144), ("minecraft:iron_nugget", "iron", 16), ("minecraft:iron_block", "iron", 1296), ("minecraft:raw_iron", "iron", 288), ("minecraft:iron_ore", "iron", 288), ("minecraft:deepslate_iron_ore", "iron", 288),
                        ("minecraft:copper_ingot", "copper", 144), ("minecraft:copper_block", "copper", 1296), ("minecraft:raw_copper", "copper", 288), ("minecraft:copper_ore", "copper", 288), ("minecraft:deepslate_copper_ore", "copper", 288),
                        ("minecraft:gold_ingot", "gold", 144), ("minecraft:gold_nugget", "gold", 16), ("minecraft:gold_block", "gold", 1296), ("minecraft:raw_gold", "gold", 288), ("minecraft:gold_ore", "gold", 288), ("minecraft:deepslate_gold_ore", "gold", 288),
                        ("minecraft:cobblestone", "stone", 72), ("minecraft:stone", "stone", 72), ("minecraft:gravel", "stone", 36), ("minecraft:clay_ball", "clay", 72), ("minecraft:clay", "clay", 288), ("minecraft:brick", "clay", 72),
                        ("minecraft:sand", "glass", 144), ("minecraft:glass", "glass", 144), ("minecraft:obsidian", "obsidian", 288), ("minecraft:emerald", "emerald", 666), ("minecraft:rotten_flesh", "blood", 40), ("ddsstinkers:grout", "stone", 144)):
        add_melt(item, fl, n)
    # Alloys from DDSS whose every fluid exists here.
    for a in dump["alloys"]:
        r = a["result"]
        if not isinstance(r, dict):
            continue
        rf = r["fluid"].replace("_fluid", "")
        ins = [{"fluid": i["fluid"].replace("_fluid", ""), "amount": i["amount"]} for i in a["inputs"]]
        if rf in fluids and all(i["fluid"] in fluids for i in ins):
            table["alloys"].append({"result": rf, "amount": r["amount"], "inputs": ins})
    table["fuels"] = [{"fluid": "lava", "amount": 50, "temp": 1000}]
    # What a Part Builder takes for a material, and how much one is worth (in ingots, 144 = one).
    craft = {"wood": [("#minecraft:planks", 144), ("minecraft:stick", 72)], "stone": [("minecraft:cobblestone", 144), ("minecraft:stone", 144)], "flint": [("minecraft:flint", 144)], "bone": [("minecraft:bone", 144)],
             "cactus": [("minecraft:cactus", 144)], "netherrack": [("minecraft:netherrack", 144)], "obsidian": [("minecraft:obsidian", 144)], "endstone": [("minecraft:end_stone", 144)],
             "prismarine": [("minecraft:prismarine_shard", 144)], "sponge": [("minecraft:sponge", 144)], "paper": [("minecraft:paper", 144)], "string": [("minecraft:string", 144)],
             "feather": [("minecraft:feather", 144)], "leaf": [("#minecraft:leaves", 144)], "vine": [("minecraft:vine", 144)], "slime": [("minecraft:slime_ball", 144)], "blaze": [("minecraft:blaze_rod", 144)], "ice": [("minecraft:ice", 144)], "endrod": [("minecraft:end_rod", 144)]}
    for sid, items in craft.items():
        if sid in table["materials"]:
            table["materials"][sid]["craftable"] = True
            table["materials"][sid]["craft"] = [{"item": i, "value": v} for i, v in items]
    os.makedirs(NATIVE_DATA, exist_ok=True)
    with open(os.path.join(NATIVE_DATA, "tinkers.json"), "w") as f:
        json.dump(table, f, separators=(",", ":"))
    print("tinkers table:", len(table["materials"]), "materials", len(table["parts"]), "parts", len(table["tools"]), "tools", len(melt), "melting", len(table["alloys"]), "alloys", len(fluids), "fluids")
