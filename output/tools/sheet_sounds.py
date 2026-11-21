"""Spectrogram sheet of every sound in a manifest (first variant each), for a visual check.
usage: python sheet_sounds.py <folder with manifest.json> <out.png> [max_seconds]"""

import json
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import soundfile as sf

folder, out = sys.argv[1], sys.argv[2]
tmax = float(sys.argv[3]) if len(sys.argv) > 3 else None
man = json.load(open(os.path.join(folder, "manifest.json"), encoding="utf-8"))
cols = 6
rows = (len(man) + cols - 1) // cols
fig, axes = plt.subplots(rows, cols, figsize=(cols * 3.2, rows * 1.9))
for ax in axes.flat:
    ax.axis("off")
for ax, e in zip(axes.flat, man):
    x, sr = sf.read(os.path.join(folder, e["files"][0]["file"] + ".wav"))
    x = x.mean(axis=1) if x.ndim == 2 else x
    ax.axis("on")
    nfft = 512 if len(x) > 4096 else 128
    ax.specgram(x + 1e-9, NFFT=nfft, Fs=sr, noverlap=nfft * 3 // 4, cmap="magma", vmin=-120)
    ax.set_ylim(0, 12000)
    ax.set_xlim(0, min(len(x) / sr, tmax or 1e9))
    ax.set_title(f"{e['name']}  {len(x) / sr:.2f}s", fontsize=7)
    ax.tick_params(labelsize=5)
plt.tight_layout()
plt.savefig(out, dpi=55)
