"""The Long Climb manual (native/longclimb/data/manual.json) and the level names Mining Tooltips shows
(native/miningtips/data/levels.json), both from the same tables as the mod itself."""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WIDTH = 21   # characters a book line holds (about 22 measured in game)
LINES = 14   # lines on a page
HEAD, TEXT, LINK, GOOD, NOTE = 0x1F3F7F, 0x000000, 0x0B3D91, 0x1E6B2A, 0x5A5A5A


def wrapped(text):
    n = 0
    for para in text.split("\n"):
        words, line = para.split(" "), 0
        n += 1
        for w in words:
            add = len(w) + (1 if line else 0)
            if line + add > WIDTH and line:
                n += 1
                line = len(w)
            else:
                line += add
    return n


class Book:
    def __init__(self):
        self.pages = [[]]
        self.used = 0
        self.marks = {}

    def new_page(self):
        if self.pages[-1]:
            self.pages.append([])
        self.used = 0

    def mark(self, name):
        self.marks[name] = len(self.pages)

    def add(self, spans):
        """A block of spans that should stay on one page: [(text, colour, bold, link)]."""
        text = "".join(s[0] for s in spans)
        need = wrapped(text.rstrip("\n"))
        if need > LINES and len(spans) == 1:
            # One span longer than a page: cut it at the words, a page's worth at a time.
            t, c, bold, link = spans[0]
            words, chunk = t.rstrip("\n").split(" "), []
            for w in words:
                if chunk and wrapped(" ".join(chunk + [w])) > LINES - 1:
                    self.add([(" ".join(chunk) + "\n", c, bold, link)])
                    chunk = []
                chunk.append(w)
            if chunk:
                self.add([(" ".join(chunk) + "\n", c, bold, link)])
            return
        if need > LINES and len(spans) > 1:
            # Too long for any page: its spans go one by one, the first page taking what fits.
            for sp in spans:
                self.add([sp])
            return
        if self.used + need > LINES:
            self.new_page()
        self.pages[-1].extend({"t": t, "c": c, "b": b, "p": p} for t, c, b, p in spans)
        self.used += need

    def para(self, text, colour=TEXT, bold=False):
        for chunk in text.split("\n\n"):
            self.add([(chunk + "\n", colour, bold, None)])

    def head(self, text):
        self.add([(text + "\n", HEAD, True, None)])


def write(d, vein_text, levels, tool_stats, vanilla_levels, manual_key="B"):
    ladder = d["ladder"]
    sections = [("climb", "How the climb works"), ("table", "The 5x5 table"), ("tools", "Tools, hammers, AIOTs"), ("tiers", "Tiers 0 to 50"), ("ores", "Where the ores are")]

    def build(toc):
        b = Book()
        b.add([("Ore Overhaul\nLong Climb\n", HEAD, True, None)])
        b.add([(f"Press {manual_key} to open this book (Options > Mods to change the key).\n", NOTE, False, None)])
        b.add([("Contents\n", HEAD, True, None)] + [(f"> {title}\n", LINK, False, toc.get(key, 1)) for key, title in sections])
        b.new_page()
        b.mark("climb")
        b.head("How the climb works")
        b.para("Every ore has a mining level. A pickaxe mines anything up to its own level, and each ore needs the pickaxe of the tier before it.")
        b.para("Wood is tier 0 and stone tier 1. Tin needs a stone pickaxe, copper is tier 5, iron 8, diamond 20, netherite 25, and the climb ends at genesium, tier 50.")
        b.para("Hover a tool to see its level. Look at an ore to see the level it needs, and whether what you hold is enough (the Mining Tooltips mod).")
        b.new_page()
        b.mark("table")
        b.head("The 5x5 table")
        b.para("Made on a 3x3 from 4 crafting tables, 4 logs and a stone pickaxe.")
        b.para("Anything made only from early things (wood, stone, coal, sand, plants, mob drops) still crafts on a 3x3. Everything that takes later materials needs the 5x5 table and about 2 to 3 times the material.")
        b.para("A log gives 2 planks, and 2 planks give 2 sticks.")
        b.para("JEI shows every recipe; its + button lays one out in the table. Each shift-click on the result crafts one. Items stay in the table when you close it.")
        b.new_page()
        b.mark("tools")
        b.head("Tools")
        b.para("Every tier has a pickaxe, axe, shovel, hoe, sword and armor. Most take the rarest gem below them, with the tier below as the handle.")
        b.head("Hammer, excavator")
        b.para("Break 3x3. 4x durability; the hammer digs at 40% speed, the excavator 28%. Blocks above the tool's level, or far harder than the one you hit, stay.")
        b.head("AIOT")
        b.para("All 5 tools plus 8 of the material: one tool that does every job, with 5x durability and every tool and weapon enchantment. Right-click makes paths, sneak-right-click tills.")
        b.new_page()
        b.mark("tiers")
        b.head("Tiers 0 to 50")
        for lv, m in enumerate(ladder):
            dur, speed = tool_stats.get(lv, (m["dur"], m["speed"]))
            prev = ladder[lv - 1]["name"] if lv else "your hand"
            also = [c["name"] for c in d.get("companions", {}).get(lv, [])]
            b.add([(f"{lv} {m['name']}\n", GOOD, True, None), (f"mined with {prev}; tools {int(dur)} uses, speed {speed:g}\n", TEXT, False, None)]
                  + ([(f"also: {', '.join(also)}\n", NOTE, False, None)] if also else []))
        b.new_page()
        b.mark("ores")
        b.head("Where the ores are")
        for lv, m in enumerate(ladder):
            for ore in [m] + d.get("companions", {}).get(lv, []):
                veins = ore.get("ore") or []
                if not veins:
                    continue
                b.add([(f"{ore['name']} (level {max(lv - 1, 0)})\n", GOOD, True, None)] + [(vein_text(v) + "\n", TEXT, False, None) for v in veins])
        return b

    first = build({})
    book = build(first.marks)
    out = os.path.join(ROOT, "native", "longclimb", "data")
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "manual.json"), "w") as f:
        json.dump({"pages": book.pages}, f, indent=0)
    tips = os.path.join(ROOT, "native", "miningtips", "data")
    os.makedirs(tips, exist_ok=True)
    with open(os.path.join(tips, "levels.json"), "w") as f:
        json.dump({"names": levels, "vanilla": vanilla_levels}, f, indent=1)
    return len(book.pages)
