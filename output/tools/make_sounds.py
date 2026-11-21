"""Build the impact sound banks.

  recorded/  : the cleanest real hits cut from the source recordings, with derived
               soft / medium / hard velocity layers
  synth/     : procedural (modal synthesis) hits calibrated to the same measurements,
               free of any third-party licence
  both banks : cue/, ball/, rail/, cluster/ with identical file names, so the game
               can switch bank by changing ids only.

usage: python make_sounds.py <source_dir> <out_dir>
"""

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from impactlib import (  # noqa: E402
    LAYER_K,
    LAYERS,
    SR,
    cluster,
    db,
    envelope,
    extract,
    features,
    finish,
    load,
    save,
    soften,
    synth_ball,
    synth_cue,
    synth_rail,
    synth_table,
)
from ring_metrics import metrics  # noqa: E402

# Hand-labelled from analysis.json (peak time in seconds). Labels were chosen from
# the measured signature of each class:
#   cue : first hit of a shot, 1.1-1.5 ms attack, peaks ~400-650 Hz + 1170/1430 Hz
#   ball: 0.5-0.9 ms attack, energy 1.3-3.5 kHz, almost no energy below 450 Hz
#   rail: low centroid (~1.1 kHz) with >50 % of the energy below 450 Hz
F23 = "2.3_830221__kvv_audio__sprtindor_billiard-cue-ball-strike-01_kvv-audio_free.wav"
F22 = "2.2_62331__bsumusictech__pool-balls.wav"
F21 = "2.1_350918__csaszi__billiard-pool-shots-csg.wav"
F31 = "3.1_539854__za-games__billiard-ball-clack.wav"
F33 = "3.3_432592__coral_island_studios__billiards3.wav"
F34 = "3.4_204187__reg7783__pool_break.wav"
F11 = "1.1_235687__jsburgh__pool-break.aiff"

CANDIDATES = {
    "cue": [
        (F23, 0.039), (F23, 2.410), (F23, 4.365), (F23, 6.782),
        (F21, 9.8085), (F21, 13.3484), (F21, 7.0978), (F33, 0.2264), (F34, 0.5368), (F11, 0.395),
    ],
    "ball": [
        (F23, 0.408), (F23, 2.526), (F23, 4.424), (F23, 4.720), (F23, 5.239), (F23, 6.900),
        (F23, 7.920), (F23, 9.489), (F23, 9.871), (F31, 0.006), (F22, 2.3141), (F22, 7.2734),
        (F22, 13.5207), (F22, 21.4048), (F33, 0.4071), (F21, 10.0501), (F21, 13.4279),
    ],
    "rail": [(F23, 7.085), (F23, 9.730), (F23, 0.800)],
}
DUR = {"cue": 0.22, "ball": 0.32, "rail": 0.3}
# Every recorded hit gets its tail damped from 4 ms after the peak: this removes room
# reverb and the long tonal ring some clips have (za-games / bsumusictech rang for
# ~37 ms with Q ~230, which reads as metal). Resin, wood and cloth die fast.
TAIL = {"cue": 0.009, "ball": 0.007, "rail": 0.010}
KEEP = {"cue": 7, "ball": 10, "rail": 3}
N_SYNTH = 8
MAX_TAIL_DB = -12  # reject clips whose 15-60 ms tail is still louder than this (ringing)


def snr(x, src, t):
    """peak vs the source's noise floor 80..15 ms before the hit (digital silence -> 1e-5)."""
    a, b = max(0, int((t - 0.08) * SR)), max(0, int((t - 0.015) * SR))
    pre = src[a:b]
    noise = max(np.sqrt(np.mean(pre**2)) if len(pre) > 20 else 0, 1e-5)
    return float(db(np.abs(x).max()) - db(noise))


def build_recorded(src, out, report):
    analysis = json.load(open(os.path.join(out, "analysis", "analysis.json")))
    cache = {}
    picked = {}
    for kind, cands in CANDIDATES.items():
        clips = []
        for fname, t in cands:
            if fname not in cache:
                cache[fname] = load(os.path.join(src, fname))
            x = cache[fname]
            imp = analysis[fname]["impacts"]
            peak = max((i["peak_db"] for i in imp if abs(i["t"] - t) < 0.01), default=0)
            nxt = [i["t"] for i in imp if t + 0.012 < i["t"] and i["peak_db"] > peak - 30]
            # take a little pre-roll so the onset is not clipped
            y = extract(x, t, DUR[kind] + 0.02, nxt[0] if nxt else None, TAIL[kind], -30 if kind == "rail" else None)
            if len(y) < 0.045 * SR:
                continue
            ring = metrics(finish(y))
            if ring["tail_db"] > MAX_TAIL_DB:
                print("  reject (rings)", kind, fname[:12], t, ring)
                continue
            clips.append({"src": fname, "t": t, "x": y, "snr": snr(y, x, t), "len_ms": len(y) / SR * 1000})
        # rank: dry, long enough, best signal-to-noise
        clips.sort(key=lambda c: (-c["snr"] - 0.02 * min(c["len_ms"], 200)))
        picked[kind] = clips[: KEEP[kind]]
        d = os.path.join(out, "sounds", "recorded", kind)
        os.makedirs(d, exist_ok=True)
        for n, c in enumerate(picked[kind], 1):
            for layer in LAYERS:
                y = soften(c["x"], layer, kind)
                save(os.path.join(d, f"{layer}_{n:02d}.wav"), y)
            report["recorded"].setdefault(kind, []).append(
                {"file": f"{kind}/*_{n:02d}", "source": c["src"], "t": c["t"], "snr_db": round(c["snr"], 1),
                 **features(finish(c["x"])), **metrics(finish(c["x"]))}
            )
    return picked


def build_synth(out, report):
    rng = np.random.default_rng(1234)
    fn = {"cue": synth_cue, "ball": synth_ball, "rail": synth_rail, "table": synth_table}
    hits = {}
    for kind, f in fn.items():
        d = os.path.join(out, "sounds", "synth", kind)
        os.makedirs(d, exist_ok=True)
        for layer in LAYERS:
            for n in range(1, N_SYNTH + 1):
                # every variant at a slightly different speed too: more variety per layer
                y = f(float(np.clip(LAYER_K[layer] * rng.uniform(0.75, 1.25), 0.03, 1)), rng)
                save(os.path.join(d, f"{layer}_{n:02d}.wav"), y)
                hits.setdefault((kind, layer), []).append(y)
                if n == 1:
                    report["synth"].setdefault(kind, []).append({"layer": layer, **features(y), **metrics(y)})
    return hits


def build_clusters(bank_hits, out, bank, seed):
    """3 intensities x 3 variants of multi-ball chatter."""
    rng = np.random.default_rng(seed)
    d = os.path.join(out, "sounds", bank, "cluster")
    os.makedirs(d, exist_ok=True)
    spec = {"soft": (5, 0.045, "soft"), "medium": (8, 0.040, "medium"), "hard": (12, 0.035, "hard")}
    for layer, (n, spread, src_layer) in spec.items():
        for v in range(1, 5):
            y = cluster(bank_hits[src_layer], rng, n + rng.integers(-1, 3), spread)
            save(os.path.join(d, f"{layer}_{v:02d}.wav"), y)


def main(src, out):
    import shutil

    for bank in ("recorded", "synth"):  # start clean: variant counts may change
        shutil.rmtree(os.path.join(out, "sounds", bank), ignore_errors=True)
    report = {"recorded": {}, "synth": {}, "reference_real_means": {}}
    picked = build_recorded(src, out, report)
    for kind, clips in picked.items():
        fs = [features(finish(c["x"])) for c in clips]
        report["reference_real_means"][kind] = {k: round(float(np.mean([f[k] for f in fs])), 2) for k in fs[0]}
    rec_hits = {layer: [soften(c["x"], layer, "ball") for c in picked["ball"]] for layer in LAYERS}
    build_clusters(rec_hits, out, "recorded", 7)
    syn = build_synth(out, report)
    build_clusters({layer: syn[("ball", layer)] for layer in LAYERS}, out, "synth", 8)
    with open(os.path.join(out, "sounds", "bank_report.json"), "w") as fh:
        json.dump(report, fh, indent=1)
    print(json.dumps(report["reference_real_means"], indent=1))
    for kind, rows in report["synth"].items():
        print("synth", kind, rows)
    for kind, rows in report["recorded"].items():
        for r in rows:
            print("rec", kind, r)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
