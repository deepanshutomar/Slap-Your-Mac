#!/usr/bin/env python3
"""
slapmac.py — SlapMac clone
Requires: Apple Silicon Mac (M2+), sudo
Install:  pip install macimu
Usage:    sudo python3 slapmac.py --sounds /path/to/folder
"""

import sys
import os
import time
import math
import random
import threading
import subprocess
import argparse
from collections import deque

# ── Check root ────────────────────────────────────────────────────────────────
if os.geteuid() != 0:
    sys.exit("[slapmac] Run with sudo: sudo python3 slapmac.py")

try:
    from macimu import IMU
except ImportError:
    sys.exit(
        "[slapmac] Missing dependency.\n"
        "Run: pip install macimu\n"
        "Then retry with sudo."
    )

# ── Args ──────────────────────────────────────────────────────────────────────
p = argparse.ArgumentParser()
p.add_argument("--threshold",    type=float, default=0.1,
               help="Peak amplitude in g to trigger (default 0.5)")
p.add_argument("--cooldown",     type=float, default=0.75,
               help="Seconds between triggers (default 0.75)")
p.add_argument("--volume-scale", action="store_true",
               help="Scale volume with slap force")
p.add_argument("--sounds",       type=str, default=None,
               help="Folder or single file with .mp3/.wav/.aiff sounds")
args = p.parse_args()

# ── Load sounds ───────────────────────────────────────────────────────────────
def load_sounds(path):
    exts = (".mp3", ".wav", ".aiff", ".aif")
    if path:
        if os.path.isfile(path):
            return [path]
        if os.path.isdir(path):
            files = [os.path.join(path, f) for f in os.listdir(path)
                     if f.lower().endswith(exts)]
            if files:
                return files
        print(f"[slapmac] Warning: '{path}' not found or no audio files. Falling back.")

    # Same folder as script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    local = [os.path.join(script_dir, f) for f in os.listdir(script_dir)
             if f.lower().endswith(exts)]
    if local:
        return local

    # macOS builtins
    builtins = [
        "/System/Library/Sounds/Basso.aiff",
        "/System/Library/Sounds/Funk.aiff",
        "/System/Library/Sounds/Sosumi.aiff",
        "/System/Library/Sounds/Blow.aiff",
        "/System/Library/Sounds/Frog.aiff",
    ]
    return [s for s in builtins if os.path.exists(s)]

sounds = load_sounds(args.sounds)
if not sounds:
    sys.exit("[slapmac] No sounds found.")
print(f"[slapmac] Loaded {len(sounds)} sound(s): {[os.path.basename(s) for s in sounds]}")

# ── Slap detection state ──────────────────────────────────────────────────────
last_trigger = 0.0
lock = threading.Lock()

sta_buf = deque(maxlen=5)   # short-term ~50ms
lta_buf = deque(maxlen=50)  # long-term  ~500ms

def play(amplitude):
    sound = random.choice(sounds)
    vol = min(1.0, max(0.1, amplitude / 3.0)) if args.volume_scale else 1.0
    subprocess.Popen(
        ["afplay", "--volume", str(round(vol, 2)), sound],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    print(f"[slapmac] SLAP! {amplitude:.2f}g → {os.path.basename(sound)}")

# replace the STA/LTA buffer setup and on_sample with this:

last_amp = None

def on_sample(x, y, z):
    global last_trigger, last_amp
    import math
    amp = math.sqrt(x*x + y*y + z*z)
    
    if last_amp is None:
        last_amp = amp
        return
    
    delta = abs(amp - last_amp)  # change from previous sample
    last_amp = amp

    if delta < args.threshold:
        return

    now = time.time()
    with lock:
        if now - last_trigger < args.cooldown:
            return
        last_trigger = now

    threading.Thread(target=play, args=(delta,), daemon=True).start()
# ── Main loop ─────────────────────────────────────────────────────────────────
print(f"[slapmac] Listening... threshold={args.threshold}g cooldown={args.cooldown}s")
print("[slapmac] Ctrl+C to stop.\n")

def _on_sample(s):
    on_sample(s.x, s.y, s.z)

try:
    with IMU() as imu:
        stop = imu.on_accel(_on_sample)  # registers background callback
        while True:
            time.sleep(1)
except KeyboardInterrupt:
    print("\n[slapmac] Stopped.")