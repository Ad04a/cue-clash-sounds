"""Median measurements per bank/kind/layer (quick calibration table)."""
import glob, sys, os
import numpy as np, soundfile as sf
sys.path.insert(0, os.path.dirname(__file__))
from impactlib import features
from ring_metrics import metrics
for kind in ("cue", "ball", "rail", "table", "cluster"):
    for bank in ("recorded", "synth"):
        for layer in ("soft", "hard"):
            fs = glob.glob(f"sounds/{bank}/{kind}/{layer}_*.wav")
            if not fs: continue
            r = [{**features(sf.read(f)[0]), **metrics(sf.read(f)[0])} for f in fs]
            med = {k: float(np.median([x[k] for x in r])) for k in ("centroid_hz", "lf_ratio", "t30_ms", "tail_db", "q_est")}
            print(f"{bank:8s} {kind:7s} {layer:5s} n={len(fs):2d} " + "  ".join(f"{k.split('_')[0]} {v:7.1f}" for k, v in med.items()))
