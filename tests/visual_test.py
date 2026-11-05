#!/usr/bin/env python3
"""Opens a real window in a scratch game folder with the mods, the resource pack and the shader on, lays out ores and
gear, and saves screenshots. Prints what the log says about the pack and the shader.

usage: visual_test.py <version folder name> [--no-shader] [--no-pack] [--tag NAME]
"""
import json
import os
import shutil
import subprocess
import sys
import time
import zipfile

USER_HOME = os.environ.get("WIN_HOME", "/mnt/c/Users/YOUR_WINDOWS_USER")
WIN_HOME = os.environ.get("WIN_HOME_WIN", r"C:\Users\YOUR_WINDOWS_USER")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VER = f"{USER_HOME}/AppData/Roaming/horizon-launcher/versions/" + sys.argv[1]
REAL = f"{USER_HOME}/AppData/Roaming/horizon"
SCRATCH = f"{USER_HOME}/AppData/Local/Temp/lcview"
WIN = WIN_HOME + r"\AppData\Local\Temp\lcview"
PACK = "Default 32x32 (Horizon).zip"
SHADER = "wisdom_horizon-1.1.0.hshader"
TAG = sys.argv[sys.argv.index("--tag") + 1] if "--tag" in sys.argv else "all"


def ctl(*args, timeout=60):
    r = subprocess.run([f"{VER}/horizon-ctl.exe", "--socket", WIN + r"\ctl.json", "--timeout", str(timeout), *map(str, args)], capture_output=True, text=True, cwd=VER, timeout=timeout + 30)
    out = (r.stdout or r.stderr).strip()
    try:
        return json.loads(out.splitlines()[-1])
    except (ValueError, IndexError):
        return {"error": out[:300]}


def pack(mod, out):
    src = os.path.join(ROOT, "mod", mod)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for d, _, fs in os.walk(src):
            for f in sorted(fs):
                p = os.path.join(d, f)
                z.write(p, os.path.relpath(p, src))


def main():
    if os.path.exists(SCRATCH):
        shutil.rmtree(SCRATCH)
    g = f"{SCRATCH}/game"
    os.makedirs(f"{g}/horizon-mods")
    os.makedirs(f"{g}/resourcepacks")
    os.makedirs(f"{g}/shaderpacks")
    os.makedirs(f"{SCRATCH}/home")
    os.makedirs(f"{SCRATCH}/shots")
    for m in ("longclimb", "ddsstinkers"):
        pack(m, f"{g}/horizon-mods/{m}.hmod")
    with open(f"{g}/horizon-mods.txt", "w") as f:
        f.write("mod.longclimb:true\nmod.ddsstinkers:true\n")
    opts = []
    if "--no-pack" not in sys.argv:
        shutil.copy(f"{REAL}/resourcepacks/{PACK}", f"{g}/resourcepacks/{PACK}")
        opts.append('resourcePacks:["vanilla","file/' + PACK + '"]')
    if "--no-shader" not in sys.argv:
        shutil.copy(f"{REAL}/shaderpacks/{SHADER}", f"{g}/shaderpacks/{SHADER}")
        for line in open(f"{REAL}/horizon-graphics.txt", errors="replace"):
            if "shader" in line.lower():
                with open(f"{g}/horizon-graphics.txt", "a") as f:
                    f.write(line)
    if opts:
        with open(f"{g}/options.txt", "w") as f:
            f.write("\n".join(opts) + "\n")
    log = open(f"{SCRATCH}/out.txt", "w")
    game = subprocess.Popen([f"{VER}/horizon-client.exe", "--control", "--control-socket", WIN + r"\ctl.json", "--game-dir", WIN + r"\game", "--home", WIN + r"\home", "--world", "V", "--seed", "5", "--creative"],
                            cwd=VER, stdout=log, stderr=subprocess.STDOUT, env=dict(os.environ, HORIZON_NO_AUDIO="1", WSLENV="HORIZON_NO_AUDIO"))
    try:
        t0 = time.time()
        while time.time() - t0 < 300:
            r = ctl("wait-ready", timeout=30)
            if "error" not in r:
                break
            if game.poll() is not None:
                print("game exited", game.returncode)
                return 2
            time.sleep(3)
        print(f"ready after {time.time() - t0:.0f}s", flush=True)
        ctl("command", "difficulty peaceful")
        ctl("time", "6000")
        ctl("command", "gamerule doDaylightCycle false")
        ctl("command", "weather clear")
        s = ctl("state")
        p = s.get("player", {}).get("position", [0, 100, 0])
        x, z = int(p[0]), int(p[2])
        y = 150
        ctl("fill", x - 12, y - 1, z - 2, x + 12, y - 1, z + 12, "minecraft:smooth_stone")
        ctl("tp", x, y, z)
        ctl("wait", 20)
        L = "longclimb"
        rows = [
            [f"{L}:tin_ore", f"{L}:deepslate_tin_ore", f"{L}:silver_ore", f"{L}:lead_ore", f"{L}:ruby_ore", f"{L}:sapphire_ore", "minecraft:iron_ore", "minecraft:diamond_ore"],
            [f"{L}:nether_ardite_ore", f"{L}:nether_cobalt_ore", f"{L}:end_draconium_ore", f"{L}:end_omnium_ore", f"{L}:nether_genesium_ore", f"{L}:tin_block", f"{L}:draconium_block", f"{L}:genesium_block"],
        ]
        for j, row in enumerate(rows):
            for i, b in enumerate(row):
                print(" set", b, json.dumps(ctl("setblock", x - 7 + i * 2, y + j * 2, z + 6, b))[:80], flush=True) if "error" in ctl("setblock", x - 7 + i * 2, y + j * 2, z + 6, b) else None
        ctl("command", "gamerule sendCommandFeedback false")
        ctl("command", "gamerule announceAdvancements false")
        for tag, mat, sx in (("a", "draconium", 2), ("b", "ruby", 0), ("c", "tin", -2), ("d", "omnium", -4), ("e", "cobalt", 4)):
            ctl("command", f'summon minecraft:armor_stand {x + sx} {y} {z + 3} {{Tags:["{tag}"],ShowArms:1b,Rotation:[180f,0f]}}')
            for piece, slot in (("helmet", "head"), ("chestplate", "chest"), ("leggings", "legs"), ("boots", "feet")):
                ctl("command", f"item replace entity @e[tag={tag},limit=1] armor.{slot} with {L}:{mat}_{piece}")
        ctl("give", f"{L}:draconium_pickaxe", 1)
        ctl("give", f"{L}:ruby_sword", 1)
        ctl("give", f"{L}:tin_ingot", 16)
        ctl("give", f"{L}:ruby_gem", 16)
        ctl("give", "minecraft:iron_pickaxe", 1)
        ctl("give", "minecraft:diamond", 16)
        ctl("give", f"{L}:draconium_helmet", 1)
        ctl("give", f"{L}:kyronite_crystal" if False else f"{L}:raw_tin", 16)
        ctl("select", f"{L}:draconium_pickaxe")
        ctl("look-at", x, y + 1, z + 6)
        ctl("wait", 60)
        win_shot = WIN + rf"\shots\{TAG}_world.png"
        print("shot", json.dumps(ctl("screenshot", win_shot, timeout=30))[:200], flush=True)
        ctl("tp", x, y, z - 1)
        ctl("look-at", x, y + 1, z + 3)
        ctl("wait", 240)  # chat and toasts fade
        print("shot", json.dumps(ctl("screenshot", WIN + rf"\shots\{TAG}_armor.png", timeout=30))[:200], flush=True)
        ctl("open-inventory")
        time.sleep(1.5)
        print("shot", json.dumps(ctl("screenshot", WIN + rf"\shots\{TAG}_inventory.png", timeout=30))[:200], flush=True)
        ctl("close")
        fps = ctl("stats")
        print("frames", json.dumps(fps)[:260], flush=True)
        ctl("quit", timeout=30)
    finally:
        try:
            game.wait(timeout=30)
        except subprocess.TimeoutExpired:
            game.kill()
    print("shots:", os.listdir(f"{SCRATCH}/shots"))
    txt = open(f"{SCRATCH}/home/logs/latest.log", errors="replace").read()
    print("448 lines:", txt.count("os error 448"))
    for line in txt.splitlines():
        if any(k in line.lower() for k in ("refused", "unbound", "failed to load", "not loaded", "caught error", "shader pack", "panic", "unknown field")) and "os error 448" not in line:
            print("  log:", line[:220])
    return 0


if __name__ == "__main__":
    sys.exit(main())
