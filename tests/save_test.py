#!/usr/bin/env python3
"""Does a world keep its progress after Save and Quit? Runs one Horizon build in a scratch game folder, no mods content.

usage: save_test.py <version folder name> [--player-name NAME]
The player's real worlds are never touched.
"""
import glob
import json
import os
import shutil
import subprocess
import sys
import time

USER_HOME = os.environ.get("WIN_HOME", "/mnt/c/Users/YOUR_WINDOWS_USER")
WIN_HOME = os.environ.get("WIN_HOME_WIN", r"C:\Users\YOUR_WINDOWS_USER")
VER = f"{USER_HOME}/AppData/Roaming/horizon-launcher/versions/" + sys.argv[1]
SCRATCH = f"{USER_HOME}/AppData/Local/Temp/lcsave"
WIN = WIN_HOME + r"\AppData\Local\Temp\lcsave"
WORLD = "SaveTest"


def ctl(*args, timeout=60):
    r = subprocess.run([f"{VER}/horizon-ctl.exe", "--socket", WIN + r"\ctl.json", "--timeout", str(timeout), *map(str, args)], capture_output=True, text=True, cwd=VER, timeout=timeout + 30)
    out = (r.stdout or r.stderr).strip()
    try:
        return json.loads(out.splitlines()[-1])
    except (ValueError, IndexError):
        return {"error": out[:300]}


def boot():
    log = open(f"{SCRATCH}/out.txt", "a")
    env = dict(os.environ, HORIZON_NO_AUDIO="1", WSLENV="HORIZON_NO_AUDIO")
    head = [] if "--window" in sys.argv else ["--headless"]
    return subprocess.Popen([f"{VER}/horizon-client.exe", *head, "--control", "--control-socket", WIN + r"\ctl.json", "--game-dir", WIN + r"\game", "--home", WIN + r"\home",
                             "--world", WORLD, "--seed", "5"], cwd=VER, stdout=log, stderr=subprocess.STDOUT, env=env)


def wait_ready(game):
    t0 = time.time()
    while time.time() - t0 < 300:
        r = ctl("wait-ready", timeout=30)
        if "error" not in r:
            return True
        if game.poll() is not None:
            print("game exited", game.returncode)
            return False
        time.sleep(3)
    return False


def snapshot(mark):
    s = ctl("state")
    p = s.get("player", {})
    inv = ctl("inventory")
    b = ctl("block", 40, 119, 40)
    print(f"[{mark}] pos={p.get('position')} block={b.get('block')} inv={json.dumps(inv.get('counts', inv.get('items', '')))[:120]} xp={p.get('xp') or p.get('experience_level')}", flush=True)
    return p.get("position"), b.get("block"), json.dumps(inv)


def player_files():
    return {os.path.basename(f): (os.path.getsize(f), time.strftime("%H:%M:%S", time.localtime(os.path.getmtime(f)))) for f in glob.glob(f"{SCRATCH}/game/saves/{WORLD}/players/data/*")}


def main():
    if os.path.exists(SCRATCH):
        shutil.rmtree(SCRATCH)
    os.makedirs(f"{SCRATCH}/game")
    os.makedirs(f"{SCRATCH}/home")
    game = boot()
    try:
        if not wait_ready(game):
            return 2
        print("build", json.dumps(ctl("hello"))[:160], flush=True)
        print("start", time.strftime("%H:%M:%S"), player_files(), flush=True)
        ctl("command", "difficulty peaceful")
        ctl("tp", 40, 120, 40)
        ctl("setblock", 40, 119, 40, "minecraft:diamond_block")
        ctl("tp", 40, 120, 40)
        ctl("give", "minecraft:diamond", 7)
        ctl("xp", 5)
        ctl("wait", 40)
        before = snapshot("before quit")

        # The player's way out: the pause menu's Save and Quit to Title.
        ctl("pause")
        time.sleep(0.5)
        scr = ctl("screen")
        labels = [b.get("label") or b.get("text") or b for b in scr.get("buttons", [])]
        print("pause buttons", labels, flush=True)
        exit_label = next((b for b in labels if isinstance(b, str) and "quit" in b.lower()), "Save and Quit to Title")
        q = ctl("click-button", exit_label)
        print("quit button", json.dumps(q)[:160], flush=True)
        time.sleep(6)
        print("after quit", time.strftime("%H:%M:%S"), player_files(), flush=True)
        o = ctl("open", WORLD, timeout=120)
        print("reopen", json.dumps(o)[:160], flush=True)
        wait_ready(game)
        time.sleep(2)
        after = snapshot("reopened, same session")
        same = {"position": bool(before[0] and after[0] and abs(before[0][0] - after[0][0]) < 2 and abs(before[0][2] - after[0][2]) < 2), "placed block": before[1] == after[1], "inventory": "diamond" in after[2]}
        print("KEPT in the same session:", same, flush=True)

        # And across a full restart of the game.
        ctl("quit", timeout=30)
        try:
            game.wait(timeout=40)
        except subprocess.TimeoutExpired:
            game.kill()
        print("after game exit", time.strftime("%H:%M:%S"), player_files(), flush=True)
        game = boot()
        wait_ready(game)
        time.sleep(2)
        after = snapshot("reopened, new game process")
        same = {"position": bool(before[0] and after[0] and abs(before[0][0] - after[0][0]) < 2 and abs(before[0][2] - after[0][2]) < 2), "placed block": before[1] == after[1], "inventory": "diamond" in after[2]}
        print("KEPT after restart:", same, flush=True)
        ctl("quit", timeout=30)
    finally:
        try:
            game.wait(timeout=30)
        except subprocess.TimeoutExpired:
            game.kill()
    return 0


if __name__ == "__main__":
    sys.exit(main())
