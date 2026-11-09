"""Reads The Age of Ores (Crystalcraft Unlimited Java) jar: each ore's name, its block, raw item or gem, and textures.
Writes extract/aoo.json. The jar's art is All Rights Reserved: it goes only into a private resource pack, never the mod."""
import json
import re
import sys
import zipfile

NS = "crystalcraft_unlimited_java"


def main(jar, out):
    z = zipfile.ZipFile(jar)
    names = set(z.namelist())
    lang = json.loads(z.read(f"assets/{NS}/lang/en_us.json"))

    def texture_of(kind, ident):
        """The first texture an item or block model of this id uses."""
        for path in (f"assets/{NS}/models/{kind}/{ident}.json",):
            if path not in names:
                continue
            m = json.loads(z.read(path))
            tex = m.get("textures", {})
            for key in ("all", "layer0", "side", "particle", "top", "end"):
                if key in tex:
                    t = tex[key].split(":")[-1]
                    p = f"assets/{NS}/textures/{t}.png"
                    if p in names:
                        return p
            if m.get("parent", "").startswith(f"{NS}:"):
                return texture_of(kind, m["parent"].split("/")[-1])
        return None

    def block_texture(ident):
        bs = f"assets/{NS}/blockstates/{ident}.json"
        if bs in names:
            v = json.loads(z.read(bs))
            variants = v.get("variants") or {}
            model = None
            if variants:
                first = next(iter(variants.values()))
                model = (first[0] if isinstance(first, list) else first).get("model")
            elif v.get("multipart"):
                a = v["multipart"][0]["apply"]
                model = (a[0] if isinstance(a, list) else a).get("model")
            if model:
                return texture_of("block", model.split("/")[-1])
        return texture_of("block", ident)

    blocks = {k.split(".")[-1]: v for k, v in lang.items() if k.startswith(f"block.{NS}.")}
    items = {k.split(".")[-1]: v for k, v in lang.items() if k.startswith(f"item.{NS}.")}
    ores = {}
    for bid, name in sorted(blocks.items()):
        if not bid.endswith("_ore") or "raw" in bid:
            continue
        if bid.startswith("deepslate_"):
            # Some metals exist only as deepslate ores.
            if bid[len("deepslate_"):] in blocks:
                continue
            base = bid[len("deepslate_"): -len("_ore")]
            name = re.sub(r"^Deepslate\s+", "", name)
        else:
            base = bid[: -len("_ore")]
        ores[base] = {"block": bid, "name": re.sub(r"\s*Ore$", "", name).strip(), "ore_tex": block_texture(bid),
                      "deepslate_tex": block_texture(f"deepslate_{bid}") if f"deepslate_{bid}" in blocks else None}
    for base, o in ores.items():
        raw = next((i for i in (f"raw_{base}", f"{base}_raw") if i in items), None)
        gem = next((i for i in (base, f"{base}_gem", f"{base}_crystal", f"{base}_shard") if i in items), None)
        ingot = next((i for i in (f"{base}_ingot",) if i in items), None)
        o["metal"] = bool(raw or ingot)
        o["raw_tex"] = texture_of("item", raw) if raw else None
        o["ingot_tex"] = texture_of("item", ingot) if ingot else None
        o["gem_tex"] = texture_of("item", gem) if gem and not o["metal"] else None
        store = f"{base}_block"
        o["block_tex"] = block_texture(store) if store in blocks else None
    json.dump(ores, open(out, "w"), indent=1, sort_keys=True)
    print(len(ores), "ores;", sum(1 for o in ores.values() if o["metal"]), "metals;", sum(1 for o in ores.values() if o["ore_tex"]), "with ore textures")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
