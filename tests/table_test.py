#!/usr/bin/env python3
"""The 5x5 table in a real window with real clicks: what still fits a small grid, what needs the table, shift-crafting, remainders.

usage: table_test.py <version folder name>
"""
import json
import os
import shutil
import subprocess
import sys
import time
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USER_HOME = "/mnt/c/Users/feri1"
WIN_HOME = r"C:\Users\feri1"
VER = f"{USER_HOME}/AppData/Roaming/horizon-launcher/versions/" + sys.argv[1]
SCRATCH = f"{USER_HOME}/AppData/Local/Temp/lctable"
WIN = WIN_HOME + r"\AppData\Local\Temp\lctable"
SHOTS = f"{USER_HOME}/AppData/Local/Temp/lctable_shots"
LC = "longclimb"
TABLE = f"{LC}:crafting_table_5x5"
results = []


def ctl(*args, timeout=60):
    r = subprocess.run([f"{VER}/horizon-ctl.exe", "--socket", WIN + r"\ctl.json", "--timeout", str(timeout), *map(str, args)], capture_output=True, text=True, cwd=VER, timeout=timeout + 15)
    out = (r.stdout or r.stderr).strip()
    try:
        return json.loads(out.splitlines()[-1])
    except (ValueError, IndexError):
        return {"error": out[:300]}


def check(name, ok, detail=""):
    results.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + name + (f"  [{str(detail)[:200]}]" if detail else ""), flush=True)


def pack(mod, out):
    src = os.path.join(ROOT, "mod", mod)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for d, _, fs in os.walk(src):
            for f in sorted(fs):
                p = os.path.join(d, f)
                z.write(p, os.path.relpath(p, src))


def main():
    running = subprocess.run(["powershell.exe", "-NoProfile", "-Command", "Get-CimInstance Win32_Process -Filter \"Name='horizon-client.exe'\" | ForEach-Object { $_.CommandLine }"], capture_output=True, text=True).stdout
    if any(line.strip() and "--headless" not in line for line in running.splitlines()):
        print("a game is already running: not opening a second window")
        return 3
    if os.path.exists(SCRATCH):
        shutil.rmtree(SCRATCH)
    g = f"{SCRATCH}/game"
    os.makedirs(f"{g}/horizon-mods")
    os.makedirs(f"{SCRATCH}/home")
    os.makedirs(SHOTS, exist_ok=True)
    for m in ("longclimb", "ddsstinkers"):
        pack(m, f"{g}/horizon-mods/{m}.hmod")
    with open(f"{g}/horizon-mods.txt", "w") as f:
        f.write("mod.longclimb:true\nmod.ddsstinkers:true\nmod.jei:true\nmod.miningtips:true\nmod.minimap:true\n")
    with open(f"{g}/options.txt", "w") as f:
        f.write("renderDistance:6\nsimulationDistance:5\nguiScale:3\n")
    log = open(f"{SCRATCH}/out.txt", "w")
    game = subprocess.Popen([f"{VER}/horizon-client.exe", "--control", "--control-socket", WIN + r"\ctl.json", "--game-dir", WIN + r"\game", "--home", WIN + r"\home", "--world", "T", "--seed", "5"],
                            cwd=VER, stdout=log, stderr=subprocess.STDOUT, env=dict(os.environ, HORIZON_NO_AUDIO="1", LONGCLIMB_DEBUG="1", MININGTIPS_DEBUG="1", WSLENV="HORIZON_NO_AUDIO:LONGCLIMB_DEBUG:MININGTIPS_DEBUG"))
    try:
        t0 = time.time()
        while time.time() - t0 < 400:
            if "error" not in ctl("wait-ready", timeout=30):
                break
            if game.poll() is not None:
                print("game exited", game.returncode)
                return 2
            time.sleep(3)
        print(f"ready after {time.time() - t0:.0f}s", flush=True)
        ctl("command", "difficulty peaceful")
        ctl("command", "gamerule doDaylightCycle false")
        ctl("command", "time set 6000")
        p = ctl("state").get("player", {}).get("position", [0, 100, 0])
        x, y, z = int(p[0]), 140, int(p[2])
        ctl("fill", x - 8, y - 2, z - 8, x + 8, y - 2, z + 8, "minecraft:smooth_stone")
        ctl("command", f"tp @s {x + 0.5} {y - 1} {z + 0.5}")
        ctl("wait", 40)
        small = (x + 1, y - 1, z + 2)
        big = (x - 1, y - 1, z + 2)
        ctl("setblock", *small, "minecraft:crafting_table")
        ctl("setblock", *big, TABLE)
        ctl("wait", 5)

        def lay(table_pos, base, items, grid):
            """Fills a grid with real clicks. grid: {cell: item}. Returns the screen."""
            ctl("close")
            ctl("command", "clear @s")
            for item, n in items.items():
                ctl("give", item, n)
            time.sleep(0.4)
            opened = ctl("interact", *table_pos)
            if "error" in opened:
                print("   couldn't open", opened, flush=True)
            time.sleep(0.5)
            for cell, item in grid.items():
                scr = ctl("screen")
                short = item.split(":")[1]
                where = next((s["slot"] for s in scr.get("slots", []) if str(s.get("item", "")).endswith(short) and int(s.get("slot", 999)) < 100), None)
                if where is None:
                    print("   no", item, "on screen", json.dumps(scr)[:200], flush=True)
                    return scr
                ctl("click-slot", where)
                ctl("click-slot", base + cell, "right")
                ctl("click-slot", where)
                time.sleep(0.05)
            # The result follows within a tick or two; give the screen a moment before reading it.
            for _ in range(8):
                time.sleep(0.25)
                scr = ctl("screen")
                if any(s.get("slot") in (200, 325) and s.get("item") for s in scr.get("slots", [])):
                    break
            return scr

        def result(scr, slot):
            got = next((s.get("item") for s in scr.get("slots", []) if s.get("slot") == slot), None)
            if got is None and slot == 325:
                cells = {int(s["slot"]) - 300: (s.get("item", "").split(":")[-1], s.get("count")) for s in scr.get("slots", []) if 300 <= int(s.get("slot", 0)) < 325 and s.get("item")}
                print("   grid when empty:", cells, "| server says:", [l[:160] for l in open(f"{SCRATCH}/out.txt", errors="replace").read().splitlines() if "[longclimb] tick" in l][-2:], flush=True)
            return got

        def clear_table():
            ctl("close")
            ctl("fill", big[0], big[1], big[2], big[0], big[1], big[2], "minecraft:air")
            ctl("wait", 4)
            ctl("setblock", *big, TABLE)
            ctl("wait", 4)

        if os.environ.get("SNIP"):
            exec(open(os.environ["SNIP"]).read(), dict(globals(), **locals()))
            ctl("quit", timeout=30)
            return 0

        # The ladder into the table: all of this still works on vanilla's 3x3.
        scr = lay(small, 100, {"minecraft:oak_log": 1}, {4: "minecraft:oak_log"})
        got = [x for x in scr.get("slots", []) if x.get("slot") == 200]
        check("a log makes 2 planks on a 3x3", got and "oak_planks" in str(got[0].get("item")) and got[0].get("count") == 2, got)
        scr = lay(small, 100, {"minecraft:coal": 1, "minecraft:stick": 1}, {1: "minecraft:coal", 4: "minecraft:stick"})
        check("a torch still crafts on a 3x3", "torch" in str(result(scr, 200)), result(scr, 200))
        scr = lay(small, 100, {"minecraft:cobblestone": 8}, {i: "minecraft:cobblestone" for i in (0, 1, 2, 3, 5, 6, 7, 8)})
        check("a furnace still crafts on a 3x3", "furnace" in str(result(scr, 200)), result(scr, 200))
        scr = lay(small, 100, {"minecraft:iron_ingot": 3}, {0: "minecraft:iron_ingot", 2: "minecraft:iron_ingot", 4: "minecraft:iron_ingot"})
        check("a bucket needs the 5x5 table", result(scr, 200) is None, result(scr, 200))
        scr = lay(small, 100, {"minecraft:oak_planks": 2}, {1: "minecraft:oak_planks", 4: "minecraft:oak_planks"})
        got = [x for x in scr.get("slots", []) if x.get("slot") == 200]
        check("2 planks make 2 sticks on a 3x3", got and "stick" in str(got[0].get("item")) and got[0].get("count") == 2, got)
        scr = lay(small, 100, {"minecraft:cobblestone": 3, "minecraft:stick": 2}, {0: "minecraft:cobblestone", 1: "minecraft:cobblestone", 2: "minecraft:cobblestone", 4: "minecraft:stick", 7: "minecraft:stick"})
        check("a stone pickaxe still works on a 3x3", "stone_pickaxe" in str(result(scr, 200)), result(scr, 200))
        scr = lay(small, 100, {"minecraft:crafting_table": 4, "minecraft:oak_log": 4, "minecraft:stone_pickaxe": 1},
                  {0: "minecraft:crafting_table", 2: "minecraft:crafting_table", 6: "minecraft:crafting_table", 8: "minecraft:crafting_table", 1: "minecraft:oak_log", 3: "minecraft:oak_log", 5: "minecraft:oak_log", 7: "minecraft:oak_log", 4: "minecraft:stone_pickaxe"})
        check("4 tables, 4 logs and a stone pickaxe make the 5x5 table on a 3x3", "crafting_table_5x5" in str(result(scr, 200)), result(scr, 200))
        # What is past the gate no longer fits a 3x3.
        # Conversions stay: nine ingots to a block.
        scr = lay(small, 100, {"minecraft:iron_ingot": 9}, {i: "minecraft:iron_ingot" for i in range(9)})
        check("nine ingots still make a block on a 3x3", "iron_block" in str(result(scr, 200)), result(scr, 200))
        ctl("close")

        # The table itself.
        opened = ctl("interact", *big)
        time.sleep(0.6)
        scr = ctl("screen")
        ids = [s.get("slot") for s in scr.get("slots", [])]
        check("the table opens with 25 cells and a result", all(300 + i in ids for i in range(26)), json.dumps(opened)[:120])
        ctl("screenshot", WIN + r"\shot_table_empty.png", timeout=30)
        chest = {c: "minecraft:oak_planks" for c in range(25) if c != 12}
        # A chest is early game now, so the 5x5 checks use a bucket: a V of 5 iron.
        bucket = {c: "minecraft:iron_ingot" for c in (0, 4, 6, 8, 12)}
        scr = lay(big, 300, {"minecraft:iron_ingot": 10}, bucket)
        check("a bucket is a V of 5 iron on the 5x5", "bucket" in str(result(scr, 325)), result(scr, 325))
        ctl("screenshot", WIN + r"\shot_table_chest.png", timeout=30)
        ctl("click-slot", 325)
        time.sleep(0.4)
        menu = ctl("menu")
        check("taking the result puts it on the cursor", "bucket" in json.dumps(menu.get("carried", "")), json.dumps(menu.get("carried"))[:100])
        scr = ctl("screen")
        cells = [s for s in scr.get("slots", []) if 300 <= int(s.get("slot", 0)) < 325 and s.get("item")]
        check("taking it uses up the iron", not cells, len(cells))
        ctl("click-slot", 0) if False else None
        clear_table()
        # Shift crafts as many as the grid allows: three layers of planks, three chests.
        ctl("command", "clear @s")
        ctl("give", "minecraft:iron_ingot", 15)
        time.sleep(0.3)
        ctl("interact", *big)
        time.sleep(0.5)
        for layer in range(3):
            for c in bucket:
                scr = ctl("screen")
                where = next((s["slot"] for s in scr.get("slots", []) if "iron_ingot" in str(s.get("item", "")) and int(s.get("slot", 999)) < 100), None)
                ctl("click-slot", where)
                ctl("click-slot", 300 + c, "right")
                ctl("click-slot", where)
                time.sleep(0.05)
        time.sleep(0.4)
        ctl("click-slot", 325, "shift")
        time.sleep(0.5)
        inv = json.dumps(ctl("inventory"))
        made = ctl("screen")
        count = sum(int(s.get("count", 0)) for s in made.get("slots", []) if str(s.get("item", "")).endswith("bucket") and int(s.get("slot", 999)) < 100)
        scr = ctl("screen")
        left = sum(int(s.get("count", 0)) for s in scr.get("slots", []) if 300 <= int(s.get("slot", 0)) < 325)
        check("a shift-click puts one bucket in the inventory and uses one layer", count == 1 and left == 10, (count, left))
        ctl("click-slot", 325, "shift")
        time.sleep(0.5)
        ctl("click-slot", 325, "shift")
        time.sleep(0.5)
        made = ctl("screen")
        count = sum(int(s.get("count", 0)) for s in made.get("slots", []) if str(s.get("item", "")).endswith("bucket") and int(s.get("slot", 999)) < 100)
        check("three shift-clicks make all three buckets", count == 3, count)
        clear_table()
        # Shapeless past nine: a fire charge's gunpowder, blaze powder and coal, four of each.
        charge = {i: "minecraft:gunpowder" for i in range(4)}
        charge.update({i: "minecraft:blaze_powder" for i in range(4, 8)})
        charge.update({i: "minecraft:coal" for i in range(8, 12)})
        scr = lay(big, 300, {"minecraft:gunpowder": 4, "minecraft:blaze_powder": 4, "minecraft:coal": 4}, charge)
        check("a fire charge takes 4 each of its three", "fire_charge" in str(result(scr, 325)), result(scr, 325))
        clear_table()
        # Two ingredients become a column of four: flint and steel.
        scr = lay(big, 300, {"minecraft:iron_ingot": 2, "minecraft:flint": 2}, {2: "minecraft:iron_ingot", 7: "minecraft:iron_ingot", 12: "minecraft:flint", 17: "minecraft:flint"})
        check("flint and steel takes a column of 2 iron and 2 flint", "flint_and_steel" in str(result(scr, 325)), result(scr, 325))
        clear_table()
        # Long Climb's own shapes.
        scr = lay(big, 300, {"minecraft:iron_ingot": 12, f"{LC}:lead_ingot": 8},
                  {0: "minecraft:iron_ingot", 1: "minecraft:iron_ingot", 2: "minecraft:iron_ingot", 3: "minecraft:iron_ingot", 4: "minecraft:iron_ingot", 5: "minecraft:iron_ingot", 9: "minecraft:iron_ingot",
                   7: f"{LC}:lead_ingot", 12: f"{LC}:lead_ingot", 17: f"{LC}:lead_ingot", 22: f"{LC}:lead_ingot"})
        check("an iron pickaxe has its 5x5 shape", "iron_pickaxe" in str(result(scr, 325)), result(scr, 325))
        clear_table()
        tools = ["minecraft:iron_pickaxe", "minecraft:iron_axe", "minecraft:iron_shovel", "minecraft:iron_hoe", "minecraft:iron_sword"]
        grid = {0: tools[0], 4: tools[1], 12: tools[2], 20: tools[3], 24: tools[4]}
        grid.update({c: "minecraft:iron_ingot" for c in (6, 7, 8, 11, 13, 16, 17, 18)})
        scr = lay(big, 300, {**{t: 1 for t in tools}, "minecraft:iron_ingot": 16}, grid)
        check("five tools and eight ingots make an iron AIOT", "iron_aiot" in str(result(scr, 325)), result(scr, 325))
        clear_table()
        grid = {c: "minecraft:iron_block" for c in (0, 1, 2, 3, 4, 6, 8)}
        grid.update({5: "minecraft:iron_block", 9: "minecraft:iron_block", 7: "minecraft:iron_pickaxe", 12: f"{LC}:lead_block", 17: f"{LC}:lead_block"})
        scr = lay(big, 300, {"minecraft:iron_block": 18, "minecraft:iron_pickaxe": 1, f"{LC}:lead_block": 4}, grid)
        check("an iron hammer has its 5x5 shape", "iron_hammer" in str(result(scr, 325)), result(scr, 325))
        clear_table()
        # A remainder comes back: a cake's milk buckets.
        cake_top = {0: "minecraft:milk_bucket", 1: "minecraft:milk_bucket", 2: "minecraft:milk_bucket", 3: "minecraft:milk_bucket", 4: "minecraft:milk_bucket",
                    5: "minecraft:milk_bucket", 6: "minecraft:milk_bucket", 7: "minecraft:milk_bucket", 8: "minecraft:milk_bucket", 9: "minecraft:milk_bucket",
                    10: "minecraft:sugar", 11: "minecraft:sugar", 12: "minecraft:egg", 13: "minecraft:sugar", 14: "minecraft:sugar",
                    15: "minecraft:wheat", 16: "minecraft:wheat", 17: "minecraft:wheat", 18: "minecraft:wheat", 19: "minecraft:wheat",
                    20: "minecraft:wheat", 21: "minecraft:wheat", 22: "minecraft:wheat", 23: "minecraft:wheat", 24: "minecraft:wheat"}
        scr = lay(big, 300, {"minecraft:milk_bucket": 10, "minecraft:sugar": 4, "minecraft:egg": 1, "minecraft:wheat": 10}, cake_top)
        check("a cake's recipe is there", "cake" in str(result(scr, 325)), result(scr, 325))
        ctl("click-slot", 325)
        time.sleep(0.4)
        scr = ctl("screen")
        back = sum(1 for s in scr.get("slots", []) if 300 <= int(s.get("slot", 0)) < 325 and "bucket" in str(s.get("item", "")))
        check("its empty buckets come back to the grid", back == 10, back)
        ctl("close")
        clear_table()
        # Breaking the table returns what's in the grid, not the preview as well.
        scr = lay(big, 300, {"minecraft:iron_ingot": 5}, bucket)
        ctl("close")
        ctl("command", "kill @e[type=item]")
        ctl("command", f"setblock {big[0]} {big[1]} {big[2]} minecraft:air destroy")
        ctl("wait", 10)
        drops = ctl("command", "execute if entity @e[type=item,nbt={Item:{id:\"minecraft:bucket\"}}]")
        check("breaking the table spills its grid but not the preview", "passed" not in json.dumps(drops).lower(), json.dumps(drops)[:120])
        # The recipe book must not choke on a 5x5 recipe in a 3x3 table.
        ctl("close")
        ctl("command", "recipe give @s *")
        ctl("wait", 4)
        ctl("interact", *small)
        time.sleep(0.6)
        check("the game survives a 3x3 table with every recipe known", game.poll() is None)
        ctl("screenshot", WIN + r"\shot_small_table.png", timeout=30)
        ctl("close")
        log_lines = open(f"{SCRATCH}/home/logs/latest.log", errors="replace").read().splitlines()
        errors = [l[:200] for l in log_lines if "ERROR" in l or "panic" in l.lower()]
        print("log errors:", errors[:6], flush=True)
        ctl("quit", timeout=30)
    finally:
        try:
            game.wait(timeout=30)
        except subprocess.TimeoutExpired:
            game.kill()
    for f in os.listdir(SCRATCH):
        if f.startswith("shot_"):
            shutil.copy(f"{SCRATCH}/{f}", f"{SHOTS}/{f}")
    print(f"{sum(results)}/{len(results)} passed", flush=True)
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
