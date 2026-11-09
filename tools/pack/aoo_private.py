"""A private resource pack: The Age of Ores' own textures (All Rights Reserved, by Lcs128) on Long Climb's companion ores,
their items and blocks, doubled to 32x32 with hard edges. For the player's own game only: never published or committed."""
import io
import json
import os
import sys
import zipfile

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "gen"))
import aoo  # noqa: E402
import design  # noqa: E402

OUT = "/mnt/c/Users/feri1/AppData/Roaming/horizon/resourcepacks/Long Climb - Age of Ores textures (private).zip"
PREFIX = {"overworld": ["", "deepslate_"], "nether": ["nether_"], "end": ["end_"]}


def doubled(z, path):
    img = Image.open(io.BytesIO(z.read(path))).convert("RGBA")
    if img.width < 32:
        img = img.resize((img.width * 2, img.height * 2), Image.NEAREST)
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


def main():
    table = json.load(open(aoo.TABLE))
    z = zipfile.ZipFile(aoo.JAR)
    fmt = 97
    for f in os.listdir(os.path.dirname(OUT)):
        if "32x32" in f and f.endswith(".zip"):
            try:
                fmt = json.loads(zipfile.ZipFile(os.path.join(os.path.dirname(OUT), f)).read("pack.mcmeta"))["pack"]["pack_format"]
            except (KeyError, ValueError, zipfile.BadZipFile):
                pass
    n = 0
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as out:
        out.writestr("pack.mcmeta", json.dumps({"pack": {"pack_format": fmt, "description": "Age of Ores textures on Long Climb's ores (private, by Lcs128)"}}))
        tex = "assets/longclimb/textures"
        for src, sid, _, dim, _, _ in aoo.ORES:
            info = table.get(src)
            if not info:
                continue
            for prefix in PREFIX[dim]:
                path = info.get("deepslate_tex") if prefix == "deepslate_" and info.get("deepslate_tex") else info.get("ore_tex")
                if path:
                    out.writestr(f"{tex}/block/{prefix}{sid}_ore.png", doubled(z, path))
                    n += 1
            if info.get("block_tex"):
                out.writestr(f"{tex}/block/{sid}_block.png", doubled(z, info["block_tex"]))
                n += 1
            if info["metal"]:
                if info.get("raw_tex"):
                    out.writestr(f"{tex}/item/raw_{sid}.png", doubled(z, info["raw_tex"]))
                    n += 1
                ingot = info.get("ingot_tex") or info.get("raw_tex")
                if ingot:
                    out.writestr(f"{tex}/item/{sid}_ingot.png", doubled(z, ingot))
                    n += 1
            elif info.get("gem_tex"):
                out.writestr(f"{tex}/item/{sid}_gem.png", doubled(z, info["gem_tex"]))
                n += 1
    print(n, "textures ->", OUT)


if __name__ == "__main__":
    main()
