"""The Age of Ores (Crystalcraft Unlimited Java, by Lcs128) ores that Long Climb didn't have, spread over the tiers.
Each sits beside its tier's ladder material: its own ore, raw item or gem, and block, and in that tier's recipes it can
stand in for the ladder material (gen.py's materials_level and gems_level tags). The names and where they spawn follow the
mod's own description; the art Long Climb ships is its own, drawn in that ore's colour. The mod's textures are All Rights
Reserved and go only into a private resource pack (pack/aoo_private.py)."""
import colorsys
import io
import json
import os
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JAR = os.path.join(ROOT, "extract", "aoo", "age_of_ores.jar")
TABLE = os.path.join(ROOT, "extract", "aoo.json")

OW, NE, EN = "overworld", "nether", "end"
SNOW = ["snowy_plains", "ice_spikes", "snowy_taiga", "snowy_slopes", "frozen_peaks", "grove", "frozen_river", "snowy_beach"]
SWAMP = ["swamp", "mangrove_swamp"]
CRIMSON, WARPED, SOUL, WASTES, BASALT = ["crimson_forest"], ["warped_forest"], ["soul_sand_valley"], ["nether_wastes"], ["basalt_deltas"]

# (Age of Ores id, Long Climb id, level, dimension, biomes or None, y range or None). Every ore spawns where the mod puts it.
ORES = [
    # The Overworld, common to rare, everywhere.
    ("calcium", "calcium", 1, OW, None, None), ("silicium", "silicon", 1, OW, None, None), ("amber", "amber", 2, OW, None, None),
    ("jasper", "jasper", 3, OW, None, None), ("onyx", "onyx", 3, OW, None, None), ("lithium", "lithium", 3, OW, None, None),
    ("bismuth", "bismuth", 4, OW, None, None), ("jade", "jade", 4, OW, None, None), ("malachite", "malachite", 5, OW, None, None),
    ("azurite", "azurite", 5, OW, None, None), ("manganese", "manganese", 6, OW, None, None), ("rose_quartz", "rose_quartz", 6, OW, None, None),
    ("smoky_quartz", "smoky_quartz", 7, OW, None, None), ("stibnite", "stibnite", 7, OW, None, None), ("garnet", "garnet", 8, OW, None, None),
    ("vanadium", "vanadium", 8, OW, None, None), ("citrine", "citrine", 9, OW, None, None), ("cinnabar", "cinnabar", 9, OW, None, None),
    ("quicksilver", "quicksilver", 10, OW, None, None), ("amethyst", "amethyst_crystal", 10, OW, None, None), ("scandium", "scandium", 11, OW, None, None),
    ("fluorite", "fluorite", 11, OW, None, None), ("turquoise", "turquoise", 12, OW, None, None), ("molybdenum", "molybdenum", 12, OW, None, None),
    ("peridot", "peridot", 13, OW, None, None), ("topaz", "topaz", 13, OW, None, None), ("yttrium", "yttrium", 14, OW, None, None),
    ("aquamarine", "aquamarine", 14, OW, None, None), ("tourmaline", "tourmaline", 15, OW, None, None), ("indium", "indium", 15, OW, None, None),
    ("cadmium", "cadmium", 16, OW, None, None), ("amazonite", "amazonite", 16, OW, None, None), ("iolite", "iolite", 17, OW, None, None),
    ("zirconium", "zirconium", 17, OW, None, None), ("chrysolite", "chrysolite", 18, OW, None, None), ("olivine", "olivine", 18, OW, None, None),
    ("niobium", "niobium", 19, OW, None, None), ("spinel", "spinel", 19, OW, None, None), ("sardonyx", "sardonyx", 20, OW, None, None),
    ("ruthenium", "ruthenium", 20, OW, None, None), ("sugillite", "sugilite", 21, OW, None, None), ("kunzite", "kunzite", 21, OW, None, None),
    ("tantalum", "tantalum", 22, OW, None, None), ("alexandrite", "alexandrite", 22, OW, None, None), ("ametrine", "ametrine", 23, OW, None, None),
    ("technetium", "technetium", 23, OW, None, None), ("opal", "opal", 24, OW, None, None), ("rutile", "rutile", 24, OW, None, None),
    ("holmium", "holmium", 25, OW, None, None), ("labradorite", "labradorite", 25, OW, None, None), ("zircon", "zircon", 26, OW, None, None),
    ("indigolite", "indigolite", 26, OW, None, None), ("goshenite", "goshenite", 27, OW, None, None), ("hackmantite", "hackmanite", 27, OW, None, None),
    ("vesuvianite", "vesuvianite", 28, OW, None, None), ("hercynite", "hercynite", 28, OW, None, None), ("americium", "americium", 29, OW, None, None),
    ("ammolite", "ammolite", 29, OW, None, None), ("prism", "prism", 30, OW, None, None), ("chloronium", "chloronium", 30, OW, None, None),
    ("sonoranite", "sonoranite", 31, OW, None, None), ("chalcanthite", "chalcanthite", 31, OW, None, None), ("grandidierite", "grandidierite", 32, OW, None, None),
    ("pitambari_neelam", "pitambari_neelam", 32, OW, None, None), ("medusa_quartz", "medusa_quartz", 33, OW, None, None),
    ("peacock_topaz", "peacock_topaz", 33, OW, None, None), ("cyan_emerald", "cyan_emerald", 34, OW, None, None),
    ("watermelon_tourmaline", "watermelon_tourmaline", 34, OW, None, None), ("australian_sapphire", "australian_sapphire", 35, OW, None, None),
    ("palintinium", "palintinium", 35, OW, None, None), ("raspberry_diamond", "raspberry_diamond", 36, OW, None, None),
    ("rare_amethyst", "rare_amethyst", 36, OW, None, None), ("rare_citrine", "rare_citrine", 37, OW, None, None),
    ("matizium", "matizium", 50, OW, None, None), ("rare_tourmaline", "rare_tourmaline", 38, OW, None, None), ("pink_ruby", "pink_ruby", 48, OW, None, None),
    ("rare_sapphire", "rare_sapphire", 46, OW, None, None), ("rare_tanzanite", "rare_tanzanite", 44, OW, None, None),
    ("brickerite", "brickerite", 12, OW, None, None), ("sunset_jasper", "sunset_jasper", 13, OW, None, None), ("iris_agate", "iris_agate", 15, OW, None, None),
    # The Overworld, only in some biomes, as the mod has them.
    ("howlite", "howlite", 9, OW, SNOW, None), ("pietersite", "pietersite", 10, OW, ["desert", "badlands", "eroded_badlands", "wooded_badlands"], None),
    ("moss_agate", "moss_agate", 10, OW, SWAMP, None), ("epitode_crystal", "epidote", 11, OW, ["lush_caves"], None),
    ("blue_john_fluorite", "blue_john_fluorite", 12, OW, ["flower_forest", "sunflower_plains"], None),
    ("shattuckite", "shattuckite", 13, OW, ["dripstone_caves"], None), ("rainbow_fluorite", "rainbow_fluorite", 14, OW, ["cherry_grove"], None),
    ("rainbow_opal", "rainbow_opal", 15, OW, SWAMP, None), ("wernerite", "wernerite", 16, OW, SNOW, None),
    ("yellow_onyx", "yellow_onyx", 17, OW, ["lush_caves"], None), ("aquamorganite", "aquamorganite", 18, OW, ["dripstone_caves"], None),
    ("mystic_topaz", "mystic_topaz", 19, OW, ["badlands", "eroded_badlands", "wooded_badlands"], None),
    ("matrix", "matrix_opal", 23, OW, ["lush_caves"], (0, 8)),
    # The Nether, by biome.
    ("pyrite", "pyrite", 20, NE, WASTES, None), ("sulfur", "sulfur", 21, NE, WASTES + BASALT, None), ("ilmenite", "ilmenite", 21, NE, BASALT, None),
    ("carnotite", "carnotite", 22, NE, BASALT, None), ("pelenium", "pelenium", 23, NE, WASTES, None), ("fire_opal", "fire_opal", 24, NE, CRIMSON, None),
    ("bixbite", "bixbite", 24, NE, CRIMSON + WASTES, None), ("sunstone", "sunstone", 25, NE, CRIMSON, None), ("catseye", "catseye", 26, NE, WARPED, None),
    ("bloodstone", "bloodstone", 26, NE, CRIMSON + WASTES, None), ("green_catseye", "green_catseye", 27, NE, WARPED, None),
    ("humoranium", "humoranium", 28, NE, SOUL, None), ("orange_diamond", "orange_diamond", 29, NE, CRIMSON + WASTES, None),
    ("seaborgium", "seaborgium", 30, NE, CRIMSON + WASTES, None), ("red_diamond", "red_diamond", 31, NE, CRIMSON + WASTES, None),
    ("yurium", "yurium", 32, NE, CRIMSON, None), ("pink_diamond", "pink_diamond", 33, NE, SOUL, None),
    ("anti_humoranium", "anti_humoranium", 34, NE, SOUL, None),
    # The End.
    ("bluestone", "bluestone", 35, EN, None, None), ("rhodonite", "rhodonite", 36, EN, None, None), ("maradonyx", "maradonyx", 37, EN, None, None),
    ("moonstone", "moonstone", 38, EN, None, None), ("serpentine", "serpentine", 39, EN, None, None), ("larimar", "larimar", 40, EN, None, None),
    ("pottasium", "potassium", 41, EN, None, None), ("europium", "europium", 42, EN, None, None), ("white_diamond", "white_diamond", 43, EN, None, None),
    ("purple_diamond", "purple_diamond", 45, EN, None, None), ("cyber_crystal", "cyber_crystal", 47, EN, None, None), ("xernium", "xernium", 49, EN, None, None),
]


def colour(z, path):
    """The ore's own colour: the average of its texture's coloured pixels (the rock around it left out)."""
    from PIL import Image
    img = Image.open(io.BytesIO(z.read(path))).convert("RGBA")
    picked = []
    for r, g, b, a in img.getdata():
        if a < 128:
            continue
        h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        if s > 0.25 and v > 0.2:
            picked.append((r, g, b))
    if not picked:
        picked = [p[:3] for p in img.getdata() if p[3] >= 128] or [(128, 128, 128)]
    r, g, b = (sum(c[i] for c in picked) // len(picked) for i in range(3))
    return r << 16 | g << 8 | b


# Colours, names and metal-or-gem worked out once from the jar and kept here, so the generator runs without it.
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "aoo_ores.json")


def companions(vein):
    """Long Climb id -> its material: level, colour, gem or metal, name and veins (`vein` is design.vein)."""
    table = json.load(open(TABLE)) if os.path.exists(TABLE) else {}
    z = zipfile.ZipFile(JAR) if os.path.exists(JAR) else None
    cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}
    fresh = {}
    out = {}
    for src, sid, lv, dim, biomes, y in ORES:
        info = table.get(src, {})
        if z and info.get("ore_tex"):
            col, metal, name = colour(z, info["ore_tex"]), bool(info.get("metal")), info.get("name")
        else:
            c = cache.get(sid, {})
            col, metal, name = c.get("color", 0x808080), c.get("metal", False), c.get("name")
        fresh[sid] = {"color": col, "metal": metal, "name": name}
        rare = dim == OW and lv >= 30 and not biomes
        if dim == OW:
            yr = y or ((-64, -16) if rare else (-48, 64))
            count, size = (2, 3) if rare else ((8, 6) if biomes else ((6, 7) if metal else (5, 5)))
        elif dim == NE:
            yr, count, size = y or (10, 118), 6, 5
        else:
            yr, count, size = y or (20, 90), 6, 5
        name = name or sid.replace("_", " ").title()
        if sid == "amethyst_crystal":
            name = "Amethyst Crystal"
        out[sid] = {"level": lv, "color": col, "gem": not metal, "name": name, "source": src,
                    "veins": [vein(dim, yr, size, count, biomes=biomes, why="The Age of Ores")]}
    if z:
        json.dump(fresh, open(CACHE, "w"), indent=1, sort_keys=True)
    return out
