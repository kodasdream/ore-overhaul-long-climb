"""Every texture the mod needs, as crisp 32x32 pixel art. No Mojang art is used.

Each image is drawn as a grid of ramp indexes (0 outline .. 5 highlight, None clear), then coloured with one
material's six-colour ramp. Nothing is blended, so edges stay hard. Tool shapes start from Tinkers' MIT-licensed layers.
"""
import colorsys
import io
import os
import random
import zipfile

from PIL import Image, ImageDraw

MODS = os.path.expanduser("~/ddss_horizon_port/DDSS_original_java/.minecraft/mods")
_tcon = zipfile.ZipFile(os.path.join(MODS, "TConstruct-1.12.2-2.13.0.183.jar"))
_cache = {}
OUTLINE, SHADOW, LOW, BASE, LIGHT, SHINE = range(6)
CLEAR = 255


def rgb(c):
    return (c >> 16) & 255, (c >> 8) & 255, c & 255


def ramp(color):
    """Six colours from one: darker shades drift towards blue, lighter ones towards warm, and saturation stays up."""
    r, g, b = (x / 255 for x in rgb(color))
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    grey = s < 0.12
    if grey:
        s = max(s, 0.08)
    else:
        s = min(1.0, s * 1.2 + 0.08)
    v = max(v, 0.36)  # very dark materials still need visible shading
    v = min(v, 0.92)  # very light ones still need room for a highlight

    def tone(vf, sf, shift):
        hh = (h + shift) % 1.0
        ss = max(0.0, min(1.0, s * sf + (0.1 if grey and vf < 0.9 else 0)))
        if grey and vf < 0.9:
            hh = 0.62  # grey metals get cool blue shadows, which read as steel instead of dust
        return tuple(int(x * 255) for x in colorsys.hsv_to_rgb(hh, ss, max(0.0, min(1.0, v * vf))))

    return [tone(0.26, 1.25, -0.035), tone(0.5, 1.2, -0.025), tone(0.74, 1.1, -0.012), tone(1.0, 1.0, 0.0),
            tone(1.22, 0.72, 0.012), (min(255, int(255 * min(1, v * 1.5))),) * 1 + tuple(int(x * 255) for x in colorsys.hsv_to_rgb(h, s * 0.28, min(1.0, v * 1.5)))[1:]]


def paint(grid, color):
    """Index grid (mode L, CLEAR = transparent) to an RGBA image."""
    cols = ramp(color)
    w, h = grid.size
    src = grid.load()
    img = Image.new("RGBA", (w, h))
    px = img.load()
    for y in range(h):
        for x in range(w):
            i = src[x, y]
            if i != CLEAR:
                px[x, y] = (*cols[i], 255)
    return img


def new_grid(size=32):
    return Image.new("L", (size, size), CLEAR)


def outline(grid):
    """Every drawn pixel touching empty space becomes the dark outline."""
    w, h = grid.size
    src = grid.copy().load()
    px = grid.load()
    for y in range(h):
        for x in range(w):
            if src[x, y] == CLEAR:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if not (0 <= nx < w and 0 <= ny < h) or src[nx, ny] == CLEAR:
                    px[x, y] = OUTLINE
                    break
    return grid


def bevel(grid):
    """A one-pixel lit edge up and left, shaded edge down and right, just inside the outline."""
    w, h = grid.size
    src = grid.copy().load()
    px = grid.load()
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            i = src[x, y]
            if i == CLEAR or i == OUTLINE:
                continue
            if src[x - 1, y] == OUTLINE or src[x, y - 1] == OUTLINE:
                px[x, y] = min(SHINE, i + 1)
            elif src[x + 1, y] == OUTLINE or src[x, y + 1] == OUTLINE:
                px[x, y] = max(SHADOW, i - 1)
    return grid


def polys(*shapes):
    """(index, points) polygons, painted in order, then outlined."""
    g = new_grid()
    d = ImageDraw.Draw(g)
    for idx, pts in shapes:
        if len(pts) == 2:
            d.line(pts, fill=idx)
        else:
            d.polygon(pts, fill=idx)
    return outline(g)


def _scale2x(g):
    """Scale2x on an index grid: doubles the size, keeps diagonals clean, and adds no new colours."""
    w, h = g.size
    src = g.load()
    out = Image.new("L", (w * 2, h * 2), CLEAR)
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


def _layer(path):
    """A Tinkers greyscale layer as a 32x32 index grid with a bevel."""
    if path not in _cache:
        img = Image.open(io.BytesIO(_tcon.read("assets/tconstruct/textures/items/" + path))).convert("RGBA")
        g = Image.new("L", img.size, CLEAR)
        src, px = img.load(), g.load()
        for y in range(img.height):
            for x in range(img.width):
                p = src[x, y]
                if p[3] >= 128:
                    v = sum(p[:3]) / 3
                    px[x, y] = OUTLINE if v < 100 else SHADOW if v < 140 else LOW if v < 180 else BASE if v < 215 else LIGHT if v < 245 else SHINE
        _cache[path] = bevel(_scale2x(g))
    return _cache[path]


def _stack(*images):
    out = Image.new("RGBA", images[0].size)
    for i in images:
        out.alpha_composite(i)
    return out


TOOL_LAYERS = {
    "pickaxe": ("pickaxe/handle.png", "pickaxe/head.png", "pickaxe/binding.png"),
    "axe": ("pickaxe/handle.png", "hatchet/head.png", "hatchet/binding.png"),
    "shovel": ("shovel/handle.png", "shovel/head.png", "shovel/binding.png"),
    "hoe": ("pickaxe/handle.png", "kama/head.png", "kama/binding.png"),
    "sword": ("broadsword/handle.png", "broadsword/blade.png", "broadsword/guard.png"),
}


def tool(kind, color, handle_color):
    h, a, b = TOOL_LAYERS[kind]
    return _stack(paint(_layer(h), handle_color), paint(_layer(a), color), paint(_layer(b), handle_color))


def _shifted(path, dx, dy):
    """A tool layer moved a little, so several heads can share one handle."""
    g = _layer(path)
    out = Image.new("L", g.size, CLEAR)
    out.paste(g, (dx, dy))
    return out


def hammer(color, handle_color):
    """A two-faced sledge on a long haft (Tinkers' hammer layers)."""
    return _stack(paint(_layer("hammer/handle.png"), handle_color), paint(_layer("hammer/back.png"), color), paint(_layer("hammer/front.png"), color), paint(_layer("hammer/head.png"), color))


def excavator(color, handle_color):
    """A broad scoop on a gripped haft (Tinkers' excavator layers)."""
    return _stack(paint(_layer("excavator/handle.png"), handle_color), paint(_layer("excavator/grip.png"), handle_color), paint(_layer("excavator/head.png"), color), paint(_layer("excavator/binding.png"), handle_color))


def ingot(color):
    g = polys(
        (BASE, [(3, 17), (18, 8), (29, 14), (14, 23)]),            # top
        (LOW, [(3, 17), (14, 23), (14, 29), (3, 23)]),              # front left
        (SHADOW, [(14, 23), (29, 14), (29, 20), (14, 29)]),         # front right
        (LIGHT, [(6, 17), (18, 10), (21, 12), (9, 19)]),            # sheen on top
        (SHINE, [(8, 16), (15, 12), (16, 13), (9, 17)]),            # glint
        (SHINE, ((4, 17), (5, 17))),
    )
    return paint(g, color)


def gem(color):
    g = polys(
        (LIGHT, [(9, 6), (23, 6), (29, 13), (3, 13)]),             # crown
        (SHINE, [(9, 6), (15, 6), (11, 13), (3, 13)]),             # lit crown facet
        (BASE, [(15, 6), (23, 6), (21, 13), (11, 13)]),
        (LOW, [(23, 6), (29, 13), (21, 13)]),
        (BASE, [(3, 13), (11, 13), (16, 29)]),                     # pavilion
        (LIGHT, [(11, 13), (21, 13), (16, 29)]),
        (SHADOW, [(21, 13), (29, 13), (16, 29)]),
        (SHINE, [(13, 15), (15, 15), (15, 22)]),
    )
    return paint(g, color)


def crystal(color):
    g = polys(
        (BASE, [(16, 2), (22, 9), (22, 23), (16, 30), (10, 23), (10, 9)]),
        (SHINE, [(16, 2), (16, 9), (10, 9)]),
        (LIGHT, [(10, 9), (16, 9), (16, 23), (10, 23)]),
        (LOW, [(16, 9), (22, 9), (22, 23), (16, 23)]),
        (SHADOW, [(16, 2), (22, 9), (16, 9)]),
        (LOW, [(10, 23), (16, 23), (16, 30)]),
        (SHADOW, [(16, 23), (22, 23), (16, 30)]),
        (SHINE, ((12, 11), (12, 19))),
    )
    return paint(g, color)


def raw(color):
    g = polys(
        (BASE, [(6, 12), (13, 5), (22, 7), (28, 14), (26, 23), (17, 28), (8, 25), (4, 18)]),
        (LIGHT, [(6, 12), (13, 5), (16, 12), (9, 17)]),
        (SHINE, [(9, 11), (13, 8), (14, 11), (10, 14)]),
        (LOW, [(16, 12), (22, 7), (28, 14), (21, 18)]),
        (SHADOW, [(21, 18), (28, 14), (26, 23), (17, 28)]),
        (LOW, [(4, 18), (9, 17), (13, 24), (8, 25)]),
        (LIGHT, [(14, 19), (18, 17), (20, 21), (15, 23)]),
    )
    return paint(g, color)


ARMOR_SHAPES = {
    "helmet": [
        (BASE, [(6, 15), (6, 9), (10, 5), (22, 5), (26, 9), (26, 15), (28, 24), (22, 24), (21, 16), (11, 16), (10, 24), (4, 24)]),
        (LIGHT, [(8, 14), (8, 10), (11, 7), (17, 7), (14, 14)]),
        (SHINE, [(10, 11), (12, 8), (14, 8), (11, 12)]),
        (SHADOW, [(21, 8), (24, 10), (24, 15), (21, 15)]),
        (LOW, [(6, 16), (10, 16), (9, 23), (5, 23)]),
        (SHADOW, [(22, 16), (26, 16), (27, 23), (23, 23)]),
        (SHADOW, ((11, 16), (20, 16))),
    ],
    "chestplate": [
        (BASE, [(2, 7), (10, 4), (12, 8), (20, 8), (22, 4), (30, 7), (29, 15), (24, 15), (24, 29), (8, 29), (8, 15), (3, 15)]),
        (LIGHT, [(4, 8), (10, 6), (10, 13), (5, 13)]),
        (LOW, [(22, 6), (28, 8), (27, 13), (22, 13)]),
        (LIGHT, [(10, 10), (15, 10), (15, 20), (10, 20)]),
        (SHINE, [(11, 11), (13, 11), (13, 16), (11, 16)]),
        (LOW, [(17, 10), (22, 10), (22, 20), (17, 20)]),
        (SHADOW, [(10, 22), (22, 22), (22, 27), (10, 27)]),
        (SHADOW, ((16, 9), (16, 27))),
    ],
    "leggings": [
        (BASE, [(7, 4), (25, 4), (27, 29), (19, 29), (16, 13), (13, 29), (5, 29)]),
        (SHADOW, [(7, 4), (25, 4), (25, 8), (7, 8)]),
        (SHINE, [(14, 5), (18, 5), (18, 7), (14, 7)]),
        (LIGHT, [(9, 10), (13, 10), (11, 27), (7, 27)]),
        (LOW, [(20, 10), (24, 10), (25, 27), (21, 27)]),
        (SHINE, ((9, 12), (8, 23))),
        (SHADOW, [(6, 19), (13, 19), (13, 21), (6, 21)]),
        (SHADOW, [(19, 19), (26, 19), (26, 21), (19, 21)]),
    ],
    "boots": [
        (BASE, [(4, 11), (12, 11), (12, 22), (14, 24), (14, 28), (2, 28), (3, 22)]),
        (BASE, [(18, 11), (26, 11), (26, 22), (30, 24), (30, 28), (17, 28), (18, 22)]),
        (LIGHT, [(6, 13), (9, 13), (9, 21), (6, 21)]),
        (LIGHT, [(20, 13), (23, 13), (23, 21), (20, 21)]),
        (SHINE, ((7, 14), (7, 19))),
        (SHINE, ((21, 14), (21, 19))),
        (SHADOW, [(3, 25), (14, 25), (14, 28), (3, 28)]),
        (SHADOW, [(18, 25), (30, 25), (30, 28), (18, 28)]),
        (SHADOW, [(4, 11), (12, 11), (12, 13), (4, 13)]),
        (SHADOW, [(18, 11), (26, 11), (26, 13), (18, 13)]),
    ],
}


def armor_icon(piece, color):
    return paint(polys(*ARMOR_SHAPES[piece]), color)


# Stone colours: four flat tones and a crack colour. No per-pixel noise.
STONES = {
    "stone": [(140, 140, 140), (128, 128, 128), (116, 116, 116), (104, 104, 104), (84, 84, 84)],
    "deepslate": [(88, 88, 96), (76, 76, 84), (66, 66, 73), (56, 56, 63), (38, 38, 44)],
    "nether": [(134, 54, 54), (112, 42, 44), (92, 34, 38), (76, 28, 34), (48, 16, 22)],
    "end": [(232, 236, 172), (220, 224, 158), (206, 210, 144), (190, 194, 130), (150, 152, 98)],
    "andesite": [(150, 152, 150), (136, 138, 137), (124, 126, 125), (112, 114, 113), (88, 90, 90)],
    "diorite": [(214, 214, 214), (196, 196, 197), (178, 178, 180), (160, 160, 162), (120, 120, 124)],
    "granite": [(176, 122, 100), (158, 108, 88), (142, 94, 78), (124, 82, 68), (92, 58, 48)],
    "bedrock": [(92, 92, 92), (70, 70, 70), (52, 52, 52), (36, 36, 36), (18, 18, 18)],
    "magma": [(214, 96, 30), (176, 62, 26), (132, 40, 26), (94, 28, 24), (52, 14, 16)],
    "meteorite": [(92, 72, 60), (76, 58, 50), (62, 48, 42), (50, 38, 34), (30, 22, 20)],
    "obsidiorite": [(62, 50, 86), (48, 38, 70), (38, 30, 56), (28, 22, 44), (14, 10, 24)],
}
_stone_cache = {}


def stone_base(stone):
    """Hard-edged cells with cracks between them, like a stone block drawn by hand at 32x32."""
    if stone not in _stone_cache:
        rnd = random.Random("stone-" + stone)
        tones = STONES[stone]
        pts = [(rnd.randint(0, 31), rnd.randint(0, 31), rnd.randint(0, 3)) for _ in range(26)]
        img = Image.new("RGBA", (32, 32))
        px = img.load()
        cell = {}
        for y in range(32):
            for x in range(32):
                # tiles: distance wraps round so the block repeats without a seam
                best = min(range(len(pts)), key=lambda i: min(abs(x - pts[i][0]), 32 - abs(x - pts[i][0])) + min(abs(y - pts[i][1]), 32 - abs(y - pts[i][1])))
                cell[x, y] = best
        for y in range(32):
            for x in range(32):
                c = cell[x, y]
                crack = cell[(x + 1) % 32, y] != c or cell[x, (y + 1) % 32] != c
                t = tones[4] if crack and rnd.random() < 0.75 else tones[pts[c][2]]
                px[x, y] = (*t, 255)
        _stone_cache[stone] = img
    return _stone_cache[stone].copy()


def _nugget(g, x, y, w, h):
    """A faceted lump of ore with its own outline."""
    d = ImageDraw.Draw(g)
    d.polygon([(x + w // 3, y), (x + w - 1, y + h // 4), (x + w, y + h * 2 // 3), (x + w * 2 // 3, y + h), (x + 1, y + h - 1), (x, y + h // 3)], fill=BASE)
    d.polygon([(x + w // 3, y + 1), (x + w // 2, y + h // 2), (x + 1, y + h // 2), (x + 1, y + h // 3)], fill=LIGHT)
    d.point([(x + w // 3, y + 2), (x + w // 3 - 1, y + 3)], fill=SHINE)
    d.polygon([(x + w * 2 // 3, y + h // 2), (x + w - 1, y + h * 2 // 3), (x + w * 2 // 3, y + h - 1), (x + w // 2, y + h - 1)], fill=SHADOW)


def _shard(g, x, y, w, h):
    """A sharp gem poking out of the rock."""
    d = ImageDraw.Draw(g)
    cx = x + w // 2
    d.polygon([(cx, y), (x + w, y + h // 3), (cx, y + h), (x, y + h // 3)], fill=BASE)
    d.polygon([(cx, y), (cx, y + h // 3), (x, y + h // 3)], fill=SHINE)
    d.polygon([(cx, y + h // 3), (x + w, y + h // 3), (cx, y + h)], fill=SHADOW)
    d.polygon([(x, y + h // 3), (cx, y + h // 3), (cx, y + h)], fill=LIGHT)


# Spots ore lumps may take; each ore uses its own mix, and the same mix on every stone it appears in.
_ORE_SLOTS = [(2, 3), (19, 2), (10, 11), (22, 13), (3, 20), (15, 22), (25, 24), (9, 1)]


def ore(mid, stone, color, gem_like=False):
    base = stone_base(stone)
    rnd = random.Random("ore-" + mid)
    g = new_grid()
    slots = rnd.sample(_ORE_SLOTS, 4 if gem_like else 5)
    for sx, sy in slots:
        x, y = sx + rnd.randint(0, 1), sy + rnd.randint(0, 1)
        if gem_like:
            _shard(g, x, y, rnd.randint(5, 6), rnd.randint(6, 7))
        else:
            _nugget(g, x, y, rnd.randint(5, 7), rnd.randint(4, 6))
    outline(g)
    base.alpha_composite(paint(g, color))
    return base


def storage(mid, color):
    """A riveted metal block: a raised frame, a sunken panel, a lit corner and four rivets."""
    g = Image.new("L", (32, 32), BASE)
    d = ImageDraw.Draw(g)
    d.rectangle([0, 0, 31, 31], outline=OUTLINE)
    d.line([(1, 1), (30, 1)], fill=SHINE)
    d.line([(1, 1), (1, 30)], fill=LIGHT)
    d.line([(1, 30), (30, 30)], fill=SHADOW)
    d.line([(30, 2), (30, 30)], fill=SHADOW)
    d.rectangle([6, 6, 25, 25], fill=LOW, outline=SHADOW)
    d.line([(7, 25), (25, 25)], fill=LIGHT)
    d.line([(25, 7), (25, 25)], fill=LIGHT)
    d.polygon([(8, 8), (15, 8), (8, 15)], fill=BASE)
    d.line([(8, 8), (13, 8)], fill=LIGHT)
    for cx, cy in ((3, 3), (27, 3), (3, 27), (27, 27)):
        d.rectangle([cx, cy, cx + 1, cy + 1], fill=SHADOW)
        d.point((cx, cy), fill=SHINE)
    return paint(g, color)


def _box(g, x, y, w, h, depth):
    """One limb of the 128x64 humanoid sheet: top, bottom and four sides, each a plate with a bevel and a seam."""
    d = ImageDraw.Draw(g)
    for rx, ry, rw, rh, front in ((x + depth, y, w, depth, False), (x + depth + w, y, w, depth, False), (x, y + depth, depth, h, False),
                                  (x + depth, y + depth, w, h, True), (x + depth + w, y + depth, depth, h, False), (x + depth * 2 + w, y + depth, w, h, False)):
        d.rectangle([rx, ry, rx + rw - 1, ry + rh - 1], fill=BASE if front else LOW, outline=SHADOW)
        d.line([(rx + 1, ry + 1), (rx + rw - 2, ry + 1)], fill=LIGHT if front else BASE)
        d.line([(rx + 1, ry + 1), (rx + 1, ry + rh - 2)], fill=LIGHT if front else BASE)
        if front and rh >= 16:
            for sy in range(ry + 8, ry + rh - 2, 8):
                d.line([(rx + 1, sy), (rx + rw - 2, sy)], fill=LOW)
                d.line([(rx + 1, sy + 1), (rx + rw - 2, sy + 1)], fill=SHINE if rw >= 16 else LIGHT)


def equipment(mid, color, leggings=False):
    g = Image.new("L", (128, 64), CLEAR)
    if leggings:
        _box(g, 0, 32, 8, 24, 8)  # leg
        _box(g, 32, 32, 16, 24, 8)  # waist
    else:
        _box(g, 0, 0, 16, 16, 16)  # head
        d = ImageDraw.Draw(g)
        d.rectangle([18, 22, 29, 25], fill=OUTLINE)  # visor on the helmet's front face
        d.line([(19, 26), (28, 26)], fill=LIGHT)
        d.rectangle([23, 27, 24, 30], fill=SHADOW)  # nose guard
        _box(g, 32, 32, 16, 24, 8)  # body
        _box(g, 80, 32, 8, 24, 8)  # arm
        _box(g, 0, 32, 8, 24, 8)  # boot
    return paint(g, color)


def _aiot_grid():
    """A paxel on one haft: pick spike up-left, axe blade down-right, spade point straight ahead. Hard edges, no blending."""
    g = new_grid()
    d = ImageDraw.Draw(g)
    # Pick spike: a long curved arm from the collar to the upper left.
    d.polygon([(19, 9), (15, 6), (10, 4), (4, 3), (9, 6), (13, 9), (17, 13)], fill=BASE)
    d.line([(5, 3), (10, 4), (15, 6), (19, 9)], fill=LIGHT)
    d.line([(9, 6), (13, 9), (17, 13)], fill=LOW)
    # Axe blade: a broad bearded blade to the lower right, with a bright cutting edge.
    d.polygon([(20, 13), (22, 11), (25, 12), (30, 13), (31, 18), (30, 24), (26, 29), (25, 23), (23, 19), (21, 16)], fill=BASE)
    d.line([(30, 13), (31, 18), (30, 24), (26, 29)], fill=SHINE)
    d.line([(29, 14), (30, 18), (29, 23), (26, 27)], fill=LIGHT)
    d.polygon([(21, 14), (24, 14), (25, 19), (25, 22), (23, 18)], fill=LOW)
    # Spade point: past the collar, along the haft.
    d.polygon([(21, 7), (23, 3), (29, 1), (30, 2), (28, 8), (24, 11)], fill=BASE)
    d.line([(23, 4), (28, 2)], fill=SHINE)
    d.line([(25, 10), (28, 7)], fill=LOW)
    d.line([(24, 6), (27, 4)], fill=LIGHT)
    return g


def _aiot_handle():
    g = new_grid()
    d = ImageDraw.Draw(g)
    d.line([(2, 28), (17, 13)], fill=BASE, width=2)
    d.line([(3, 28), (18, 13)], fill=LOW)
    d.line([(2, 27), (16, 13)], fill=LIGHT)
    # Grip wraps stay inside the haft; a small pommel closes the end.
    for k in range(4):
        g.putpixel((5 + k * 2, 25 - k * 2), SHADOW)
        g.putpixel((6 + k * 2, 25 - k * 2), SHADOW)
    d.polygon([(1, 28), (3, 27), (4, 29), (2, 30)], fill=SHADOW)
    return g


def _aiot_collar():
    g = new_grid()
    d = ImageDraw.Draw(g)
    d.polygon([(17, 10), (20, 8), (24, 11), (22, 14), (19, 15), (16, 13)], fill=BASE)
    d.line([(17, 10), (20, 8)], fill=SHINE)
    d.line([(17, 12), (20, 10), (23, 12)], fill=LIGHT)
    d.line([(16, 13), (19, 15), (22, 14)], fill=SHADOW)
    return g


def aiot(color, handle_color):
    """One outline around the whole tool, so the three heads read as one piece."""
    parts = [(_aiot_handle(), handle_color), (_aiot_grid(), color), (_aiot_collar(), handle_color)]
    mask = new_grid()
    for g, _ in parts:
        mask.paste(g, (0, 0), g.point(lambda v: 0 if v == CLEAR else 255))
    edge = outline(mask.copy())
    out = Image.new("RGBA", (32, 32))
    for g, c in parts:
        out.alpha_composite(paint(g, c))
    dark = paint(edge.point(lambda v: OUTLINE if v == OUTLINE else CLEAR), color)
    out.alpha_composite(dark)
    return out


_DARK, _MID, _LIGHT, _HIGH, _LINE = (58, 38, 22), (92, 62, 36), (128, 90, 54), (160, 118, 74), (34, 22, 14)


def _planks(px, seed=0):
    """Hard-edged planks: dark gaps every 8 rows, a knot or two, no noise."""
    for y in range(32):
        for x in range(32):
            band = (y + seed) // 8
            shift = 11 * band
            row = (y + seed) % 8
            if row == 7 or (x + shift) % 16 == 15:
                px[x, y] = (*_DARK, 255)
            elif row == 0:
                px[x, y] = (*_HIGH, 255)
            elif ((x + shift) * 5 + band * 3) % 7 == 0 and row in (2, 3, 5):
                px[x, y] = (*_MID, 255)
            else:
                px[x, y] = (*_LIGHT, 255)


def table_top():
    """A dark frame round five by five clear cells."""
    img = Image.new("RGBA", (32, 32), (*_LINE, 255))
    px = img.load()
    for r in range(5):
        for c in range(5):
            x0, y0 = 2 + c * 6, 2 + r * 6
            for y in range(y0, y0 + 5):
                for x in range(x0, x0 + 5):
                    edge = x == x0 or y == y0
                    px[x, y] = (*(_HIGH if edge else _LIGHT), 255)
    return img


def table_side():
    """Planks with a hanging saw and a banded top rail."""
    img = Image.new("RGBA", (32, 32))
    px = img.load()
    _planks(px)
    for x in range(32):
        for y in range(5):
            px[x, y] = (*(_LINE if y == 4 else _DARK if y == 0 else _MID), 255)
    steel, shine, dark = (176, 182, 192, 255), (226, 232, 240, 255), (92, 98, 110, 255)
    # A saw: blade, teeth, grip.
    for x in range(7, 25):
        px[x, 13] = shine
        for y in range(14, 18):
            px[x, y] = steel
        if x % 2:
            px[x, 18] = dark
    for y in range(11, 21):
        for x in range(4, 7):
            px[x, y] = (*_LINE, 255) if x == 4 or y in (11, 20) else (*_HIGH, 255)
    # A hammer on the rail below it.
    for x in range(10, 22):
        px[x, 26] = (*_HIGH, 255)
        px[x, 27] = (*_DARK, 255)
    for y in range(23, 30):
        for x in range(21, 26):
            px[x, y] = shine if y == 23 else dark if y == 29 else steel
    return img


def table_bottom():
    img = Image.new("RGBA", (32, 32))
    _planks(img.load(), 4)
    return img
