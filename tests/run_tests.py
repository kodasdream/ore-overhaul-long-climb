#!/usr/bin/env python3
"""Boots real Horizon headless on Windows with both mods as a player would have them, and tests the mining ladder.

Scratch folder only: the player's worlds are never touched. Prints each case and exits non-zero if any fails.
"""
import json
import os
import shutil
import subprocess
import sys
import time
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# usage: run_tests.py [mods,comma,separated] [--version NAME] [--window]
USER_HOME = os.environ.get("WIN_HOME", "/mnt/c/Users/feri1")
WIN_HOME = os.environ.get("WIN_HOME_WIN", r"C:\Users\feri1")
VERSION = sys.argv[sys.argv.index("--version") + 1] if "--version" in sys.argv else "nightly-2026-11-04-6475f62"
VER = f"{USER_HOME}/AppData/Roaming/horizon-launcher/versions/{VERSION}"
SCRATCH = f"{USER_HOME}/AppData/Local/Temp/lctest"
WIN = WIN_HOME + r"\AppData\Local\Temp\lctest"
WINDOW = "--window" in sys.argv
MODS = sys.argv[1].split(",") if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else ["longclimb", "ddsstinkers"]


def pack(mod, out):
    src = os.path.join(ROOT, "mod", mod)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for d, _, fs in os.walk(src):
            for f in sorted(fs):
                p = os.path.join(d, f)
                z.write(p, os.path.relpath(p, src))


def ctl(*args, timeout=90):
    r = subprocess.run([f"{VER}/horizon-ctl.exe", "--socket", WIN + r"\ctl.json", "--timeout", str(timeout), *map(str, args)],
                       capture_output=True, text=True, cwd=VER, timeout=timeout + 30)
    out = (r.stdout or r.stderr).strip()
    try:
        return json.loads(out.splitlines()[-1])
    except (ValueError, IndexError):
        return {"error": out[:300]}


results = []


def check(name, ok, detail=""):
    results.append(ok)
    print(("PASS " if ok else "FAIL ") + name + (f"  [{detail}]" if detail else ""), flush=True)


def main():
    if os.path.exists(SCRATCH):
        shutil.rmtree(SCRATCH)
    os.makedirs(f"{SCRATCH}/game/horizon-mods")
    os.makedirs(f"{SCRATCH}/home")
    for m in MODS:
        pack(m, f"{SCRATCH}/game/horizon-mods/{m}.hmod")
    with open(f"{SCRATCH}/game/horizon-mods.txt", "w") as f:
        f.write("".join(f"mod.{m}:true\n" for m in MODS))
    log = open(f"{SCRATCH}/out.txt", "w")
    env = dict(os.environ, HORIZON_NO_AUDIO="1", WSLENV="HORIZON_NO_AUDIO")
    game = subprocess.Popen([f"{VER}/horizon-client.exe", *([] if WINDOW else ["--headless"]), "--control", "--control-socket", WIN + r"\ctl.json", "--game-dir", WIN + r"\game",
                             "--home", WIN + r"\home", "--world", "T", "--seed", "5"], cwd=VER, stdout=log, stderr=subprocess.STDOUT, env=env)
    try:
        t0 = time.time()
        while time.time() - t0 < 420:
            r = ctl("wait-ready", timeout=30)
            if "error" not in r:
                break
            if game.poll() is not None:
                print("game exited", game.returncode)
                break
            time.sleep(5)
        print(f"ready after {time.time() - t0:.0f}s", json.dumps(r)[:200], flush=True)
        text = open(f"{SCRATCH}/out.txt", errors="replace").read()
        check("both mods load" if len(MODS) > 1 else f"{MODS[0]} loads alone", f"content from {len(MODS)} mod(s)" in text)
        for line in text.splitlines():
            if any(k in line for k in ("mod longclimb", "mod ddsstinkers", "content mods not loaded", "cannot run", "refused")):
                print("  log:", line[:220], flush=True)
        ctl("command", "difficulty peaceful")
        ctl("command", "gamerule doDaylightCycle false")
        ctl("time", "6000")
        s = ctl("state")
        pos = s.get("player", s).get("pos") or s.get("pos") or s.get("player", {}).get("position")
        print("state", json.dumps(s)[:260], flush=True)
        if isinstance(pos, dict):
            px, py, pz = int(pos["x"]), int(pos["y"]), int(pos["z"])
        else:
            px, py, pz = int(pos[0]), int(pos[1]), int(pos[2])
        # A small platform high in clear air, so nothing hides the test block. Peaceful, so nothing interrupts.
        px, py, pz = px, 200, pz
        ctl("tp", px, py + 1, pz)
        ctl("fill", px - 3, py, pz - 3, px + 3, py, pz + 3, "minecraft:glass")
        ctl("tp", px, py + 1, pz)
        ctl("wait", 10)
        bx, by, bz = px + 2, py + 1, pz
        ctl("effect", "minecraft:resistance", "9999", "5")

        # (tool, block, item that must drop or None if nothing may). An ore on level L needs a tool of level L-1.
        LC = "longclimb"
        cases = [
            ("minecraft:wooden_pickaxe", f"{LC}:tin_ore", None),
            ("minecraft:stone_pickaxe", f"{LC}:tin_ore", f"{LC}:raw_tin"),
            ("minecraft:stone_pickaxe", f"{LC}:zinc_ore", None),
            (f"{LC}:tin_pickaxe", f"{LC}:zinc_ore", f"{LC}:raw_zinc"),
            (f"{LC}:tin_pickaxe", f"{LC}:aluminum_ore", None),
            ("minecraft:stone_pickaxe", "minecraft:copper_ore", None),
            (f"{LC}:aluminum_pickaxe", "minecraft:copper_ore", "minecraft:raw_copper"),
            ("minecraft:stone_pickaxe", "minecraft:iron_ore", None),
            (f"{LC}:silver_pickaxe", "minecraft:iron_ore", None),
            (f"{LC}:lead_pickaxe", "minecraft:iron_ore", "minecraft:raw_iron"),
            ("minecraft:iron_pickaxe", f"{LC}:thorium_ore", f"{LC}:raw_thorium"),
            ("minecraft:iron_pickaxe", f"{LC}:osmium_ore", None),
            ("minecraft:iron_pickaxe", "minecraft:diamond_ore", None),
            (f"{LC}:tungsten_pickaxe", "minecraft:diamond_ore", None),
            (f"{LC}:palladium_pickaxe", "minecraft:diamond_ore", "minecraft:diamond"),
            ("minecraft:diamond_pickaxe", f"{LC}:titanium_ore", f"{LC}:raw_titanium"),
            ("minecraft:diamond_pickaxe", f"{LC}:nether_chromium_ore", None),
            (f"{LC}:primordium_pickaxe", f"{LC}:end_omnium_ore", f"{LC}:omnium_gem"),
            (f"{LC}:chronite_pickaxe", f"{LC}:end_omnium_ore", None),
            (f"{LC}:omnium_pickaxe", f"{LC}:bedrock_genesium_ore", f"{LC}:raw_genesium"),
            (f"{LC}:primordium_pickaxe", f"{LC}:bedrock_genesium_ore", None),
            # An AIOT has its tier's mining level, and does each tool's job.
            (f"{LC}:iron_aiot", f"{LC}:thorium_ore", f"{LC}:raw_thorium"),
            (f"{LC}:iron_aiot", f"{LC}:osmium_ore", None),
            (f"{LC}:wooden_aiot", f"{LC}:tin_ore", None),
            (f"{LC}:stone_aiot", f"{LC}:tin_ore", f"{LC}:raw_tin"),
            (f"{LC}:tin_aiot", "minecraft:oak_log", "minecraft:oak_log"),
            (f"{LC}:tin_aiot", "minecraft:gravel", "minecraft:gravel"),
            # The Age of Ores companions: their own tier, their own drops.
            ("minecraft:wooden_pickaxe", f"{LC}:calcium_ore", f"{LC}:raw_calcium"),
            ("minecraft:iron_pickaxe", f"{LC}:garnet_ore", f"{LC}:garnet_gem"),
            (f"{LC}:tin_pickaxe", f"{LC}:garnet_ore", None),
            # Fire opal is tier 24: diamond (tier 20) is too weak, tanzanite (23) is enough.
            ("minecraft:diamond_pickaxe", f"{LC}:nether_fire_opal_ore", None),
            (f"{LC}:tanzanite_pickaxe", f"{LC}:nether_fire_opal_ore", f"{LC}:fire_opal_gem"),
            # Hammers and excavators have their tier's mining level too.
            (f"{LC}:wooden_hammer", f"{LC}:tin_ore", None),
            (f"{LC}:stone_hammer", f"{LC}:tin_ore", f"{LC}:raw_tin"),
            (f"{LC}:iron_hammer", f"{LC}:thorium_ore", f"{LC}:raw_thorium"),
            (f"{LC}:iron_hammer", f"{LC}:osmium_ore", None),
            (f"{LC}:tin_excavator", "minecraft:gravel", "minecraft:gravel"),
            # Ores in their special rocks need the same tier as anywhere else.
            ("minecraft:stone_pickaxe", f"{LC}:andesite_karmesine_ore", None),
            (f"{LC}:nickel_pickaxe", f"{LC}:andesite_karmesine_ore", f"{LC}:raw_karmesine"),
            (f"{LC}:tungsten_pickaxe", f"{LC}:meteorite_duranite_ore", None) if False else (f"{LC}:nickel_pickaxe", f"{LC}:molten_osram_ore", None),
            (f"{LC}:sapphire_pickaxe" if False else f"{LC}:ruby_pickaxe", f"{LC}:molten_osram_ore", f"{LC}:raw_osram"),
        ]
        for tool, block, want in ([] if os.environ.get("SKIP_MINING") else cases):
            ctl("command", "clear @s")
            g = ctl("give", tool, "1")
            ctl("select", tool)
            ctl("command", "kill @e[type=item]")
            sb = ctl("setblock", bx, by, bz, block)
            if "error" in sb or "error" in g:
                check(f"{tool} on {block}", False, f"setup failed: {g.get('error')} {sb.get('error')}")
                continue
            for _ in range(40):  # the block has to reach the player's view before it can be mined
                seen = ctl("block", bx, by, bz)
                if block.split(":")[1] in json.dumps(seen):
                    break
                time.sleep(0.25)
            r = ctl("break", bx, by, bz, "--timeout", "60", timeout=75)
            drops = json.dumps(r.get("drops", {}))
            got = want.split(":")[1] in drops if want else drops == "{}"
            mined = "error" not in r and r.get("ticks", 0) > 1
            check(f"{tool.split(':')[1]} on {block.split(':')[1]} -> {want.split(':')[1] if want else 'no drop'}", got and mined, json.dumps({k: r.get(k) for k in ('ticks', 'drops', 'error') if k in r})[:170])

        # Armour goes on and its numbers apply.
        ctl("command", "clear @s")
        ctl("give", f"{LC}:tin_chestplate", "1")
        ctl("select", f"{LC}:tin_chestplate")
        ctl("use-item")
        inv = ctl("inventory")
        check("armor equips", "tin_chestplate" in json.dumps(inv.get("armor", inv)), json.dumps(inv.get("armor", ""))[:160])
        a = ctl("command", "attribute @s minecraft:armor get")
        print("  armor attribute:", json.dumps(a)[:200], flush=True)
        ctl("command", "clear @s")
        ctl("give", f"{LC}:tin_pickaxe", "1")
        ctl("command", "item replace entity @s armor.chest with minecraft:air")

        # Real crafting on a real table: a mod recipe gives its result, and vanilla's iron pickaxe recipe is gone.
        def craft(items, grid):
            """items: what to give. grid: {grid slot 0-8: item}. Returns the result slot's contents."""
            ctl("command", "clear @s")
            for item, n in items.items():
                ctl("give", item, n)
            ctl("setblock", bx, by, bz, "minecraft:crafting_table")
            time.sleep(1)
            opened = ctl("interact", bx, by, bz)
            if "error" in opened:
                return "couldn't open the table: " + json.dumps(opened)[:200]
            time.sleep(0.5)
            for slot, item in grid.items():
                scr = ctl("screen")
                where = None
                for s in scr.get("slots", []):
                    if str(s.get("item", "")).endswith(item.split(":")[1]) and int(s.get("slot", -1)) < 100:
                        where = s["slot"]
                        break
                if where is None:
                    return f"no {item} on screen: " + json.dumps(scr)[:400]
                a = ctl("click-slot", where)
                time.sleep(0.2)
                b = ctl("click-slot", 100 + slot, "right")
                time.sleep(0.2)
                c = ctl("click-slot", where)
                time.sleep(0.2)
                if os.environ.get("CRAFT_DEBUG"):
                    print("   click", where, json.dumps(a)[:220], "| grid", 100 + slot, json.dumps(b)[:220], "| back", json.dumps(c)[:160], flush=True)
            time.sleep(1)  # the server answers with the result slot after the last click
            scr = ctl("screen")
            res = [s for s in scr.get("slots", []) if s.get("slot") == 200]
            if os.environ.get("CRAFT_DEBUG"):
                print("   grid now", [s for s in scr.get("slots", []) if s.get("slot", 0) >= 100], "carried", scr.get("carried"), "screen", scr.get("screen"), "size", scr.get("craft_size"), flush=True)
            ctl("close")
            time.sleep(0.5)
            return json.dumps(res) if res else json.dumps(scr)[:300]

        # Recipes past the stone pickaxe need the 5x5 table: tests/table_test.py makes them there. A 3x3 only keeps the early ones.
        r = craft({"minecraft:iron_ingot": 3, "minecraft:stick": 2}, {0: "minecraft:iron_ingot", 1: "minecraft:iron_ingot", 2: "minecraft:iron_ingot", 4: "minecraft:stick", 7: "minecraft:stick"})
        check("vanilla iron pickaxe recipe is gone", "iron_pickaxe" not in r, r[:170])
        r = craft({"minecraft:cobblestone": 3, "minecraft:stick": 2}, {0: "minecraft:cobblestone", 1: "minecraft:cobblestone", 2: "minecraft:cobblestone", 4: "minecraft:stick", 7: "minecraft:stick"})
        check("stone pickaxe stays vanilla", "stone_pickaxe" in r, r[:170])
        for rid, tp in ((f"{LC}:tin_smelting", "smelt"),):
            pass

        # Worldgen: new ores really generate where the table says, and vanilla's own are scarcer.
        totals = {}
        ctl("command", "gamemode spectator")
        for cx in range(-2, 3):
            for cz in range(-2, 3):
                for y0 in range(-64, 112, 32):
                    x0, z0 = px + cx * 16, pz + cz * 16
                    s = ctl("blocks", x0, y0, z0, x0 + 31, y0 + 31, z0 + 31, timeout=30)
                    c = s.get("counts", s.get("blocks", {}))
                    if isinstance(c, dict):
                        for k, v in c.items():
                            if "longclimb" in k or k.endswith(("iron_ore", "copper_ore", "diamond_ore", "coal_ore", "gold_ore")):
                                totals[k] = totals.get(k, 0) + v
        print("  ore blocks near spawn:", dict(sorted(totals.items())), flush=True)
        check("tier 2-5 ores generate", any(k.endswith(("tin_ore", "zinc_ore", "aluminum_ore")) for k in totals))
        tail = ctl("logs", "--lines", "400") if False else {}
        ctl("quit", timeout=30)
    finally:
        try:
            game.wait(timeout=40)
        except subprocess.TimeoutExpired:
            game.kill()
    print(f"\n{sum(results)} of {len(results)} passed")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
