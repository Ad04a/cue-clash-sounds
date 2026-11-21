"""Build the v3 impact bank: cue strikes, ball-on-ball hits and cushion (rail) hits,
each in soft / medium / hard force layers with several variants per layer.

v3 adds new recordings to the v2 bank in ../../output:
  * craigsmith, Freesound 675330 (CC0): ~2 minutes of close-miked cue strikes
  * papapleygames "Pool And Billiards SFX" on itch.io (CC0): ball, "shoot" and wall hits
  * 13FPanska_Marval_Lukas, Freesound 379327 (CC0): ball hits
and keeps the v2 sources that worked (KVV_Audio, csaszi, coral_island_studios, ...).

Force layers:
  hard   = the brightest real hits, unfiltered
  medium = real hits of medium brightness, plus the bright ones softened
  soft   = naturally dark (soft) real hits, plus the bright ones softened more
Softening follows the Hertz contact law the v2 tools use: a slower hit has a longer
contact time, so less treble (impactlib.soften).

usage (from ball-hit-sounds/):  python v3/tools/make_v3.py
"""

import json
import os
import shutil
import sys

import numpy as np
from scipy import signal

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))  # ball-hit-sounds/
V2_TOOLS = os.path.join(ROOT, "output", "tools")
sys.path.insert(0, V2_TOOLS)
from analyze import onsets  # noqa: E402
from impactlib import LAYER_K, LAYERS, SR, cluster, db, extract, features, finish, load, save, soften, synth_rail  # noqa: E402
from ring_metrics import metrics  # noqa: E402

OUT = os.path.join(ROOT, "v3")
BANK = "v3"

ITCH = os.path.join(ROOT, "downloads", "itch", "Pool_And_Billiards _SFX", "Sounds")
CRAIG = os.path.join(ROOT, "downloads", "freesound", "675330__craigsmith__s02-22-billiards-cue-stick-hits-ball.wav")
PANSKA = os.path.join(ROOT, "real-shit", "379327__13fpanska_marval_lukas__billiards.wav")
F23 = os.path.join(ROOT, "2.3_830221__kvv_audio__sprtindor_billiard-cue-ball-strike-01_kvv-audio_free.wav")
F22 = os.path.join(ROOT, "2.2_62331__bsumusictech__pool-balls.wav")
F21 = os.path.join(ROOT, "2.1_350918__csaszi__billiard-pool-shots-csg.wav")
F31 = os.path.join(ROOT, "3.1_539854__za-games__billiard-ball-clack.wav")
F33 = os.path.join(ROOT, "3.3_432592__coral_island_studios__billiards3.wav")

LICENCE = {
    CRAIG: "CC0 (Freesound 675330, craigsmith)",
    PANSKA: "CC0 (Freesound 379327, 13FPanska_Marval_Lukas)",
    F23: "CC-BY 4.0 (Freesound 830221, KVV_Audio) - credit needed",
    F22: "CC0 (Freesound 62331, bsumusictech)",
    F21: "CC0 (Freesound 350918, csaszi)",
    F31: "CC0 (Freesound 539854, Za-Games)",
    F33: "CC-BY 4.0 (Freesound 432592, coral_island_studios) - credit needed",
}
ITCH_LICENCE = "CC0 (itch.io papapleygames, Pool And Billiards SFX by SURAJ KISPOTTA)"

# clean first strikes found in the craigsmith recording (see v3/analysis/craig_picks.json)
CRAIG_T = [3.818, 7.223, 9.654, 11.938, 12.677, 15.075, 25.209, 30.808, 33.537, 37.215, 41.463, 41.936,
           44.740, 45.336, 48.439, 51.654, 62.428, 63.002, 65.047, 68.097, 68.912, 70.355, 72.549, 73.150,
           76.053, 85.604, 90.395, 113.861]

# (file, peak time or None for "the loudest point of a one-shot file", cut length in s)
CANDIDATES = {
    "cue": [(CRAIG, t, 0.22) for t in CRAIG_T]
    + [(F23, 0.039, 0.22), (F23, 2.410, 0.22), (F23, 4.365, 0.22), (F23, 6.782, 0.22),
       (F21, 9.8085, 0.22), (F21, 13.3484, 0.22), (F21, 7.0978, 0.22), (F33, 0.2264, 0.22)],
    "ball": [(os.path.join(ITCH, f"ball_collide_ball_{n}.wav"), None, 0.08) for n in range(1, 7)]
    # itch's "ball_shoot" files are ball clicks too (no cue character), so they count as ball hits
    + [(os.path.join(ITCH, f"ball_shoot_{n}.wav"), None, 0.08) for n in range(1, 5)]
    + [(F23, t, 0.32) for t in (0.408, 2.526, 4.424, 4.720, 5.239, 6.900, 7.920, 9.489, 9.871)]
    + [(F31, 0.006, 0.32), (F22, 2.3141, 0.32), (F22, 7.2734, 0.32), (F22, 13.5207, 0.32),
       (F33, 0.4071, 0.32), (F21, 10.0501, 0.32), (F21, 13.4279, 0.32)],
    # wall_3 is left out: a regular sine-like burst that sounds synthetic, not a cushion
    "rail": [(os.path.join(ITCH, f"ball_collide_wall_{n}.wav"), None, 0.3) for n in (1, 2)]
    + [(F23, 7.085, 0.3), (F23, 9.730, 0.3), (F23, 0.800, 0.3)],
}
# tail damping from 4 ms after the peak: strips room reverb (craigsmith's film studio rings for
# 70-165 ms). Cushions keep a longer tail: the rubber thump is the sound (~25-60 ms real decay).
TAIL = {"cue": 0.009, "ball": 0.007, "rail": 0.025}
# cushions: the long tail is a low (~200 Hz) rubber thump, not the high metallic ring the check is for
MAX_TAIL_DB = {"cue": -12, "ball": -12, "rail": -2.5}
MIN_SNR = 28
KEEP = {"cue": 15, "ball": 15, "rail": 6}
# not the hit we want: craigsmith's darkest "strikes" have no cue-ball click at all (thuds from the
# film recording), and one itch ball file is a low thump
MIN_CENTROID = {"cue": 700, "ball": 900, "rail": 0}
RAIL_VARIANTS = 2  # extra pitch-shifted copies per recorded cushion hit (few clean recordings exist)
SYNTH_RAILS = 5  # per layer: the v2 synth rail model at the layer's speed (as in the hybrid renders)


def peak_noise_snr(y, src, i):
    a, b = max(0, i - int(0.08 * SR)), max(0, i - int(0.015 * SR))
    pre = src[a:b]
    noise = max(np.sqrt(np.mean(pre**2)) if len(pre) > 20 else 0.0, 1e-5)
    return float(db(np.abs(y).max()) - db(noise))


def candidate_clips(kind):
    cache, ons = {}, {}
    clips = []
    for path, t, dur in CANDIDATES[kind]:
        if path not in cache:
            cache[path] = load(path)
            ons[path] = [o / SR for o in onsets(cache[path])[0]]
        x = cache[path]
        one_shot = t is None  # a file holding one hit: nothing after it is a "next hit"
        times = [t]
        if t is None:
            times = [float(np.argmax(np.abs(x)) / SR)]
        elif t == "auto":  # every strong, separated hit in the file
            env = np.abs(x)
            times = [o for o in ons[path] if db(env[int(o * SR)]) > db(env.max()) - 18]
        for tp in times:
            nxt = [] if one_shot else [o for o in ons[path] if tp + 0.012 < o]
            y = extract(x, tp, dur + 0.02, nxt[0] if nxt else None, TAIL[kind], -30 if kind == "rail" and path == F23 else None)
            if len(y) < 0.04 * SR:
                continue
            snr = peak_noise_snr(y, x, int(tp * SR))
            ring = metrics(finish(y))
            if snr < MIN_SNR or ring["tail_db"] > MAX_TAIL_DB[kind]:
                continue
            feat = features(finish(y))
            if feat["centroid_hz"] < MIN_CENTROID[kind]:
                continue
            clips.append({"src": path, "t": round(tp, 4), "x": y, "snr": snr, **feat, "tail_db": ring["tail_db"]})
    # best first: clean, then long enough; at most 5 per source file so no single recording dominates
    clips.sort(key=lambda c: -c["snr"] - 0.02 * min(len(c["x"]) / SR * 1000, 200))
    per_src, keep = {}, []
    for c in clips:
        if per_src.get(c["src"], 0) >= (8 if kind == "cue" and c["src"] == CRAIG else 5):
            continue
        per_src[c["src"]] = per_src.get(c["src"], 0) + 1
        keep.append(c)
    return keep[: KEEP[kind]]


def natural_layers(clips):
    """A hit's natural force from its brightness (Hertz: harder = shorter contact = brighter).
    Sources differ in mic and room, so rank instead of fixed limits: darkest third soft,
    middle third medium, brightest third hard."""
    order = sorted(range(len(clips)), key=lambda j: clips[j]["centroid_hz"])
    out = {}
    for rank, j in enumerate(order):
        out[j] = LAYERS[min(2, rank * 3 // max(1, len(clips)))]
    return out


def pitch(y, ratio):
    return signal.resample_poly(y, 1000, int(round(1000 * ratio)))


# ------------------------------------------------- tonal balance toward the v2 bank
# The v2 renders (real-shit/) are the reference that sounded right. New recordings bring new
# attacks and textures, but some are much brighter: craigsmith's 1930s-60s film strikes are
# mostly the tip-on-ball crack, without the low cue-shaft "thock" (~400-650 Hz). So every new
# clip is EQ'd part of the way toward the v2 bank's average spectrum for the same kind and layer.
EDGES = np.geomspace(80, 16000, 25)
CENTRES = np.sqrt(EDGES[:-1] * EDGES[1:])
MATCH = {"cue": 0.9, "ball": 0.6, "rail": 0.0}  # share of the difference to correct
MAX_EQ_DB = 8.0
V2_BANK = {"cue": "recorded/cue", "ball": "recorded/ball", "rail": "synth/rail"}


def band_db(y):
    i = int(np.argmax(np.abs(y[: int(0.02 * SR)])))
    seg = y[max(0, i - 48): i + int(0.04 * SR)]
    spec = np.abs(np.fft.rfft(seg * np.hanning(len(seg)), 16384)) ** 2
    f = np.fft.rfftfreq(16384, 1 / SR)
    e = np.array([spec[(f >= a) & (f < b)].mean() for a, b in zip(EDGES[:-1], EDGES[1:])]) + 1e-20
    v = 10 * np.log10(e)
    return v - v.max()


def v2_targets(kind):
    import glob

    out = {}
    for layer in LAYERS:
        files = sorted(glob.glob(os.path.join(ROOT, "output", "sounds", V2_BANK[kind], f"{layer}_*.wav")))
        out[layer] = np.mean([band_db(load(p)) for p in files], axis=0)
    return out


def match_eq(y, target, amount):
    """Linear-phase EQ that moves the clip's band balance `amount` of the way to `target`."""
    if amount <= 0:
        return y
    diff = np.clip(amount * (target - band_db(y)), -MAX_EQ_DB, MAX_EQ_DB)
    diff = np.convolve(diff, [0.25, 0.5, 0.25], mode="same")  # no narrow bumps
    diff -= diff.max()  # only cut: never boost noise
    freqs = np.concatenate([[0], CENTRES, [SR / 2]]) / (SR / 2)
    gains = 10 ** (np.concatenate([[diff[0]], diff, [diff[-1]]]) / 20)
    fir = signal.firwin2(1025, freqs, gains)
    out = signal.fftconvolve(y, fir, mode="full")[512: 512 + len(y)]
    return out


def build_layers(kind, clips, rng):
    """Every clip lands in its natural layer as recorded, and is softened into the layers
    below it. Dark (soft) recordings are never brightened into 'hard'."""
    layers = {layer: [] for layer in LAYERS}
    order = {"soft": 0, "medium": 1, "hard": 2}
    targets = v2_targets(kind) if MATCH[kind] > 0 else None
    nat_of = natural_layers(clips)
    for j, c in enumerate(clips):
        nat = nat_of[j]
        srcs = [c["x"]]
        if kind == "rail":
            srcs += [pitch(c["x"], r) for r in rng.uniform(0.9, 1.1, RAIL_VARIANTS)]
        for y in srcs:
            for layer in LAYERS:
                if order[layer] > order[nat]:
                    continue
                out = finish(y) if layer == nat else soften(y, layer, kind)
                if targets is not None:
                    out = finish(match_eq(out, targets[layer], MATCH[kind]))
                layers[layer].append((out, c, layer == nat))
    if kind == "rail":
        synth = {"src": "synth rail (v2 model, impactlib.synth_rail)", "t": None, "snr": 99.0}
        for layer in LAYERS:
            for _ in range(SYNTH_RAILS):
                k = float(np.clip(LAYER_K[layer] * rng.uniform(0.75, 1.25), 0.03, 1))
                layers[layer].append((synth_rail(k, rng), synth, True))
    return layers


def main():
    rng = np.random.default_rng(303)
    sounds = os.path.join(OUT, "sounds")
    shutil.rmtree(os.path.join(sounds, BANK), ignore_errors=True)
    report = {"bank": BANK, "kinds": {}}
    ball_hits = {}
    for kind in ("cue", "ball", "rail"):
        clips = candidate_clips(kind)
        layers = build_layers(kind, clips, rng)
        d = os.path.join(sounds, BANK, kind)
        os.makedirs(d, exist_ok=True)
        rows = []
        for layer, items in layers.items():
            for n, (y, c, natural) in enumerate(items, 1):
                save(os.path.join(d, f"{layer}_{n:02d}.wav"), y)
                src = c["src"]
                rows.append({
                    "file": f"{kind}/{layer}_{n:02d}",
                    "source": os.path.basename(src),
                    "licence": "no third-party audio" if src.startswith("synth") else LICENCE.get(src, ITCH_LICENCE),
                    "t": c["t"], "natural_force": natural, "snr_db": round(c["snr"], 1),
                    **features(y),
                })
            if kind == "ball":
                ball_hits[layer] = [y for y, _, _ in items]
        report["kinds"][kind] = {
            "clips_used": len(clips),
            "per_layer": {layer: len(items) for layer, items in layers.items()},
            "files": rows,
        }
        print(kind, "clips", len(clips), {layer: len(v) for layer, v in layers.items()})
    # multi-ball chatter for breaks, built from the v3 ball hits
    d = os.path.join(sounds, BANK, "cluster")
    os.makedirs(d, exist_ok=True)
    spec = {"soft": (5, 0.045), "medium": (8, 0.040), "hard": (12, 0.035)}
    for layer, (n, spread) in spec.items():
        for v in range(1, 5):
            save(os.path.join(d, f"{layer}_{v:02d}.wav"), cluster(ball_hits[layer], rng, n + int(rng.integers(-1, 3)), spread))
    # the cloth landing sound has no recording: reuse the v2 synth one so breaks render the same way
    shutil.rmtree(os.path.join(sounds, "synth", "table"), ignore_errors=True)
    shutil.copytree(os.path.join(ROOT, "output", "sounds", "synth", "table"), os.path.join(sounds, "synth", "table"))
    with open(os.path.join(sounds, "bank_report.json"), "w") as fh:
        json.dump(report, fh, indent=1)


if __name__ == "__main__":
    main()
