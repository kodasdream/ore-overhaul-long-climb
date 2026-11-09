#!/usr/bin/env python3
"""Meteors must not float: every column with meteorite rock in fresh terrain has something under its lowest rock.

usage: meteor_test.py <version folder name> [--radius CHUNKS] [--seed N]
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
SCRATCH = f"{USER_HOME}/AppData/Local/Temp/lcmeteor"
WIN = WIN_HOME + r"\AppData\Local\Temp\lcmeteor"
ROCK = "longclimb:meteorite_rock"
ORE = "longclimb:meteorite_duranite_ore"


def arg(name, default):
    return type(default)(sys.argv[sys.argv.index(name) + 1]) if name in sys.argv else default


RADIUS = arg("--radius", 8)
SEED = arg("--seed", 5)


def ctl(*args, timeout=60):
    r = subprocess.run([f"{VER}/horizon-ctl.exe", "--socket", WIN + r"\ctl.json", "--timeout", str(timeout), *map(str, args)], capture_output=True, text=True, cwd=VER, timeout=timeout + 15)
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
    os.makedirs(f"{SCRATCH}/home")
    pack("longclimb", f"{g}/horizon-mods/longclimb.hmod")
    with open(f"{g}/horizon-mods.txt", "w") as f:
        f.write("mod.longclimb:true\n")
    with open(f"{g}/options.txt", "w") as f:
        f.write(f"renderDistance:{RADIUS + 2}\nsimulationDistance:5\n")
    log = open(f"{SCRATCH}/out.txt", "w")
    game = subprocess.Popen([f"{VER}/horizon-client.exe", "--headless", "--control", "--control-socket", WIN + r"\ctl.json", "--game-dir", WIN + r"\game", "--home", WIN + r"\home", "--world", "M", "--seed", str(SEED), "--creative"],
                            cwd=VER, stdout=log, stderr=subprocess.STDOUT, env=dict(os.environ, HORIZON_NO_AUDIO="1", WSLENV="HORIZON_NO_AUDIO"))
    try:
        t0 = time.time()
        while time.time() - t0 < 400:
            if "error" not in ctl("wait-ready", timeout=30):
                break
            if game.poll() is not None:
                print("game exited", game.returncode)
                return 2
            time.sleep(3)
        p = ctl("state").get("player", {}).get("position", [0, 100, 0])
        cx, cz = int(p[0]) >> 4, int(p[2]) >> 4
        ctl("command", "gamemode spectator")
        ctl("wait", 800, timeout=120)
        rock_chunks = 0
        balls = {}
        floating = []
        scanned = 0
        for x in range(cx - RADIUS, cx + RADIUS + 1):
            for z in range(cz - RADIUS, cz + RADIUS + 1):
                bx, bz = x * 16, z * 16
                found = []
                for y in range(-64, 192, 32):
                    s = ctl("blocks", bx, y, bz, bx + 15, min(y + 31, 191), bz + 15, timeout=30)
                    if "error" in s:
                        continue
                    scanned += 1
                    counts = s.get("counts") or {}
                    if ROCK not in counts and ORE not in counts:
                        continue
                    for b in s.get("blocks", []):
                        if ROCK in b[3] or ORE in b[3]:
                            found.append(b[:3])
                if not found:
                    continue
                rock_chunks += 1
                lows = {}
                for q in found:
                    k = (q[0], q[2])
                    lows[k] = min(lows.get(k, 999), q[1])
                top = max(q[1] for q in found)
                balls[(x, z)] = (len(found), top)
                # The ball's underside as a whole: floating when no column under it touches anything.
                touching = 0
                for (qx, qz), low in lows.items():
                    below = json.dumps(ctl("block", qx, low - 1, qz))
                    if "minecraft:air" not in below and "cave_air" not in below:
                        touching += 1
                if touching == 0:
                    floating.append(((x, z), len(found), top))
        print(f"{(2 * RADIUS + 1) ** 2} chunks, {rock_chunks} with meteor rock: {balls}", flush=True)
        print("floating:", floating, flush=True)
        print("PASS no meteor floats" if not floating else "FAIL some meteors float", flush=True)
        ctl("quit", timeout=30)
        return 0 if not floating else 1
    finally:
        try:
            game.wait(timeout=30)
        except subprocess.TimeoutExpired:
            game.kill()


if __name__ == "__main__":
    sys.exit(main())
