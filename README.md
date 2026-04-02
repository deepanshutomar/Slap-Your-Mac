# 👋 slapmactomoan.py

> **Slap your MacBook. It moans back.**
> A Python clone of the viral [SlapMac](https://slapmac.com) app — built in one file, zero paid dependencies.

---

## 🤔 What is this?

Your MacBook has a hidden accelerometer inside its Apple Silicon chip (Bosch BMI286 IMU). Apple uses it for sudden motion detection. We use it to make your laptop scream when you hit it.

Slap detected → sound plays. That's it.

---

## ✨ Features

- 🎯 **Jerk-based slap detection** — detects sudden *change* in acceleration, not raw g-force (no false triggers from gravity)
- 🔊 **Any sound file** — drop in your own `.mp3`, `.wav`, or `.aiff`
- 🎚️ **Volume scaling** — harder slap = louder sound
- ⏱️ **Cooldown** — prevents rapid-fire triggers
- 🔧 **Tunable sensitivity** — `--threshold` flag for light taps or hard smacks
- 🍎 **macOS only** — uses the Apple Silicon SPU HID sensor, no cross-platform nonsense

---

## 📋 Requirements

- MacBook with **Apple Silicon M1 Pro / M2 / M3 / M4** (plain M1 Air may not expose the sensor)
- macOS 13+
- Python 3.10+
- [`macimu`](https://github.com/olvvier/apple-silicon-accelerometer) package

> ⚠️ Requires `sudo` — reading the HID sensor needs root access.

---

## 🚀 Setup

```bash
# 1. Install the sensor library
pip install macimu

# 2. Clone / download slapmac.py

# 3. Drop your sound file in the same folder
#    (moan.mp3, scream.wav, fart.aiff — whatever)

# 4. Run it
sudo python3 slapmac.py
```

---

## 🎛️ Usage

```bash
# Basic — auto-loads any audio file in the same folder
sudo python3 slapmac.py

# Point to a specific folder of sounds
sudo python3 slapmac.py --sounds ~/my_sounds/

# Tune sensitivity (lower = more sensitive)
sudo python3 slapmac.py --threshold 0.03

# Scale volume with slap force
sudo python3 slapmac.py --volume-scale

# Combine everything
sudo python3 slapmac.py --sounds ~/sounds/ --threshold 0.04 --cooldown 0.5 --volume-scale
```

### All flags

| Flag | Default | Description |
|------|---------|-------------|
| `--sounds` | script folder | Path to a `.mp3/.wav/.aiff` file or folder |
| `--threshold` | `0.05` | Min jerk (Δg) to trigger a sound |
| `--cooldown` | `0.75` | Seconds between triggers |
| `--volume-scale` | off | Scale volume with impact force |

---

## 🔍 Check sensor compatibility first

```bash
ioreg -r -c AppleSPUHIDDevice | head -10
```

If you get output → ✅ you're good.
If blank → ❌ your chip doesn't expose the sensor.

---

## 🐛 Troubleshooting

**No sound plays despite `SLAP!` in logs**
```bash
# Test your sound file directly
afplay your_sound.mp3

# If it fails with 'wht?' error — file is corrupted
file your_sound.mp3   # should say MPEG, not HTML/text
```

**Too many / too few triggers**
```bash
# More sensitive (catches light taps)
sudo python3 slapmac.py --threshold 0.02

# Less sensitive (only hard slaps)
sudo python3 slapmac.py --threshold 0.15
```

**Test if your sensor is working at all**
```python
# test_sensor.py
import os, sys, math
if os.geteuid() != 0: sys.exit("Run with sudo")
from macimu import IMU

with IMU() as imu:
    imu.on_accel(lambda s: print(f"amp={math.sqrt(s.x**2+s.y**2+s.z**2):.3f}g"))
    input("Slap your Mac. Watch the numbers.\n")
```
```bash
sudo python3 test_sensor.py
```

---

## 🏗️ How it works

Apple Silicon MacBooks contain an undocumented MEMS IMU managed by the **Sensor Processing Unit (SPU)**. It lives at `AppleSPUHIDDevice` in the IOKit registry under vendor usage page `0xFF00`, usage `0x03`.

The [`macimu`](https://github.com/olvvier/apple-silicon-accelerometer) library opens this device via IOKit HID and streams 22-byte reports at ~100Hz. Each report has x/y/z as `int32` little-endian at byte offsets 6, 10, 14 — divide by 65536 to get acceleration in g.

This script:
1. Registers an `on_accel` callback via `macimu`
2. Computes **jerk** (Δamplitude between samples) each tick
3. When jerk exceeds `--threshold`, triggers `afplay` with a random sound from your folder
4. Enforces a cooldown to prevent machine-gun firing

---

## 🙏 Credits

- [olvvier/apple-silicon-accelerometer](https://github.com/olvvier/apple-silicon-accelerometer) — the Python sensor library that makes all of this possible
- [taigrr/spank](https://github.com/taigrr/spank) — Go implementation that inspired this
- [SlapMac](https://slapmac.com) — the original viral app by Tonino Catapano

---

## ⚠️ Disclaimer

Don't actually slap your MacBook hard enough to break it. This script is not responsible for cracked screens, voided warranties, or confused coworkers.

---

## 📄 License

MIT — do whatever you want with it.
