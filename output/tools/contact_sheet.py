"""Spectrogram grid of the banks (real vs synth, per kind and layer) for a visual check."""
import sys, os, glob
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np, soundfile as sf
out = sys.argv[1]
rows = [(b, k) for k in ("cue", "ball", "rail", "table", "cluster") for b in ("recorded", "synth") if os.path.isdir(os.path.join(sys.argv[1], "sounds", b, k))]
cols = ["soft_01", "medium_01", "hard_01", "hard_02"]
fig, ax = plt.subplots(len(rows), len(cols), figsize=(16, 2.1 * len(rows)))
for r, (b, k) in enumerate(rows):
    for c, n in enumerate(cols):
        x, sr = sf.read(os.path.join(out, "sounds", b, k, n + ".wav"))
        a = ax[r, c]
        a.specgram(x, NFFT=256, Fs=sr, noverlap=224, cmap="magma", vmin=-120)
        a.set_ylim(0, 12000); a.set_xlim(0, 0.3)
        a.set_title(f"{b}/{k}/{n}  {len(x)/sr*1000:.0f}ms", fontsize=8)
        a.tick_params(labelsize=6)
plt.tight_layout(); plt.savefig(os.path.join(out, "analysis", "bank_contact_sheet.png"), dpi=60)
