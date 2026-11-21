"""Render the v3 bank so it can be compared with the v2 renders in real-shit/:
  * the same simulated breaks (same event logs, same mixer, same seeds)
  * per kind, a "soft to hard" showcase: 10 hits from a gentle tap to full force
  * numbers: loudness, brightness and voices, v3 next to the v2 hybrid renders

usage (from ball-hit-sounds/):  python v3/tools/render_v3.py
"""

import json
import os
import sys

import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "output", "tools"))
from impactmix import SR, Mixer, load_bank  # noqa: E402

OUT = os.path.join(ROOT, "v3")
POWERS = ((0.35, 1), (0.55, 2), (0.75, 3), (0.9, 4), (1.0, 5))  # same seeds as v2 breaksim.py
SHOWCASE = {"cue": 25.0, "ball": 16.0, "cushion": 12.0}  # the mixer's full-force speed per kind


def write(path, y):
    sf.write(path + ".wav", y.astype(np.float32), SR, subtype="PCM_16")
    sf.write(path + ".ogg", y.astype(np.float32), SR, format="OGG", subtype="VORBIS")


def measure(y):
    y = y.astype(np.float64)
    rms = np.sqrt(np.mean(y[np.abs(y) > 1e-4] ** 2)) if np.any(np.abs(y) > 1e-4) else 0
    spec = np.abs(np.fft.rfft(y)) ** 2
    f = np.fft.rfftfreq(len(y), 1 / SR)
    m = f > 40
    return {
        "peak_db": round(float(20 * np.log10(np.abs(y).max() + 1e-12)), 1),
        "rms_db": round(float(20 * np.log10(rms + 1e-12)), 1),
        "centroid_hz": round(float((spec[m] * f[m]).sum() / spec[m].sum())),
        "low_share": round(float(spec[(f > 40) & (f < 450)].sum() / spec[m].sum()), 2),
    }


def main():
    bank = load_bank(os.path.join(OUT, "sounds"), "v3")
    old = load_bank(os.path.join(ROOT, "output", "sounds"), "hybrid")
    d = os.path.join(OUT, "break_renders")
    os.makedirs(d, exist_ok=True)
    compare = {}
    for power, seed in POWERS:
        tag = f"power{int(power * 100):03d}"
        with open(os.path.join(ROOT, "output", "break_renders", f"events_{tag}.json")) as fh:
            events = [e for e in json.load(fh) if e["kind"] != "pocket"]
        m = Mixer(bank, seed=seed)
        m.run(events)
        y = m.render()
        write(os.path.join(d, f"break_{tag}_v3"), y)
        ref_path = os.path.join(ROOT, "real-shit", f"break_{tag}_hybrid.wav")
        ref, _ = sf.read(ref_path)
        compare[tag] = {"v3": {**measure(y), "voices": len(m.played)}, "v2_hybrid (real-shit)": measure(ref)}
    # soft -> hard showcases, v3 and v2 hybrid
    sd = os.path.join(OUT, "showcase")
    os.makedirs(sd, exist_ok=True)
    for kind, vmax in SHOWCASE.items():
        for name, b in (("v3", bank), ("v2_hybrid", old)):
            speeds = np.geomspace(0.06, 1.0, 10) * vmax
            events = [{"t": 0.25 + 0.55 * j, "kind": kind, "speed": float(s)} for j, s in enumerate(speeds)]
            m = Mixer(b, seed=11)
            m.run(events)
            y = m.render(room=True)
            write(os.path.join(sd, f"{kind}_soft_to_hard_{name}"), y)
    with open(os.path.join(d, "compare.json"), "w") as fh:
        json.dump(compare, fh, indent=1)
    for tag, row in compare.items():
        a, b = row["v3"], row["v2_hybrid (real-shit)"]
        print(f"{tag}: v3 peak {a['peak_db']:5.1f} rms {a['rms_db']:5.1f} centroid {a['centroid_hz']:5d} low {a['low_share']:.2f} voices {a['voices']:2d}"
              f"   |  v2 peak {b['peak_db']:5.1f} rms {b['rms_db']:5.1f} centroid {b['centroid_hz']:5d} low {b['low_share']:.2f}")


if __name__ == "__main__":
    main()
