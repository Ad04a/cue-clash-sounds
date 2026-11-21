"""Analyse the source billiard recordings.

For every file: detect individual impacts (onsets), and for each impact measure
peak level, spectral centroid, the strongest spectral peaks in the first 25 ms,
and the decay time.  Writes a JSON report plus a spectrogram PNG per file.

usage: python analyze.py <source_dir> <out_dir>
"""

import glob
import json
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import soundfile as sf
from scipy import signal

SR = 48000


def load(path):
    x, sr = sf.read(path, always_2d=True)
    x = x.mean(axis=1)
    if sr != SR:
        x = signal.resample_poly(x, SR, sr)
    return x.astype(np.float64)


def envelope(x, win=0.002):
    n = max(1, int(win * SR))
    return np.sqrt(np.convolve(x * x, np.ones(n) / n, mode="same"))


def onsets(x, min_gap=0.025, thresh_db=-38):
    """Impacts = sharp rises in high-passed energy above a floor."""
    hp = signal.sosfilt(signal.butter(4, 1500, "hp", fs=SR, output="sos"), x)
    env = envelope(hp, 0.0015)
    ref = env.max() + 1e-12
    db = 20 * np.log10(env / ref + 1e-9)
    # flux: rise vs ~6 ms earlier
    lag = int(0.006 * SR)
    rise = db[lag:] - db[:-lag]
    rise = np.concatenate([np.zeros(lag), rise])
    cand = np.where((rise > 9) & (db > thresh_db))[0]
    out = []
    gap = int(min_gap * SR)
    for c in cand:
        if out and c - out[-1] < gap:
            continue
        # snap to local peak within next 4 ms
        seg = env[c : c + int(0.004 * SR)]
        out.append(c + int(np.argmax(seg)))
    return out, db


def impact_features(x, i):
    pre = int(0.001 * SR)
    seg = x[max(0, i - pre) : i + int(0.025 * SR)]
    w = seg * np.hanning(len(seg))
    nfft = 8192
    spec = np.abs(np.fft.rfft(w, nfft))
    freqs = np.fft.rfftfreq(nfft, 1 / SR)
    band = (freqs > 300) & (freqs < 16000)
    centroid = float((spec[band] * freqs[band]).sum() / (spec[band].sum() + 1e-12))
    pk, props = signal.find_peaks(spec[band], prominence=spec[band].max() * 0.08, distance=20)
    order = np.argsort(props["prominences"])[::-1][:6]
    peaks = sorted(round(float(freqs[band][pk[o]])) for o in order)
    # decay: time from peak until envelope falls 30 dB
    env = envelope(x[i : i + int(0.6 * SR)], 0.001)
    p = env[: int(0.004 * SR)].max() + 1e-12
    below = np.where(20 * np.log10(env / p + 1e-12) < -30)[0]
    t30 = float(below[0] / SR) if len(below) else 0.6
    return {
        "t": round(i / SR, 4),
        "peak_db": round(float(20 * np.log10(np.abs(x[i - pre : i + pre + 1]).max() + 1e-12)), 1),
        "centroid_hz": round(centroid),
        "peaks_hz": peaks,
        "t30_ms": round(t30 * 1000, 1),
    }


def main(src, out):
    os.makedirs(out, exist_ok=True)
    report = {}
    for path in sorted(glob.glob(os.path.join(src, "*.*"))):
        name = os.path.basename(path)
        if name.startswith("4.1"):  # 3 min ambience: summarise only
            x = load(path)[: 30 * SR]
        else:
            x = load(path)
        on, db = onsets(x)
        feats = [impact_features(x, i) for i in on if i > int(0.002 * SR)]
        report[name] = {
            "duration_s": round(len(x) / SR, 2),
            "rms_db": round(float(20 * np.log10(np.sqrt(np.mean(x * x)) + 1e-12)), 1),
            "n_impacts": len(feats),
            "impacts": feats,
        }
        fig, ax = plt.subplots(2, 1, figsize=(14, 6), sharex=True)
        t = np.arange(len(x)) / SR
        ax[0].plot(t, x, lw=0.4)
        for f in feats:
            ax[0].axvline(f["t"], color="r", lw=0.5, alpha=0.6)
        ax[0].set_title(f"{name}  ({len(feats)} impacts)")
        ax[1].specgram(x, NFFT=1024, Fs=SR, noverlap=768, cmap="magma", vmin=-130)
        ax[1].set_ylim(0, 16000)
        plt.tight_layout()
        plt.savefig(os.path.join(out, name.rsplit(".", 1)[0][:40] + ".png"), dpi=70)
        plt.close(fig)
        print(f"{name[:50]:50s} impacts={len(feats):3d}")
    with open(os.path.join(out, "analysis.json"), "w") as fh:
        json.dump(report, fh, indent=1)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
