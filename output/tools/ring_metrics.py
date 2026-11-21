"""'Metallic-ness' metrics for impact clips.

Metal rings: a few narrow spectral peaks that keep sounding long after the hit.
Resin / wood / cloth: broad spectrum that dies in a few ms.

  t30_ms      time for the envelope to fall 30 dB below the peak
  ring_db     in the tail (15-60 ms after the peak): how far the strongest narrow
              peak sticks out above the median spectrum, 500-8000 Hz (high = tonal ring)
  tail_db     tail energy (15-60 ms) relative to the first 5 ms (high = long ring)
  q_est       quality factor of the strongest tail peak, Q = pi * f * tau
              (metal ~ 500+, ceramic/resin ~ 30-80, wood ~ 10-30, cloth ~ < 10)

usage: python ring_metrics.py <wav or dir> [...]
"""

import glob
import os
import sys

import numpy as np
import soundfile as sf
from scipy import signal

SR = 48000


def metrics(x, sr=SR):
    if sr != SR:
        x = signal.resample_poly(x, SR, sr)
    p = int(np.argmax(np.abs(x[: int(0.03 * SR)])))
    env = np.sqrt(np.convolve(x * x, np.ones(48) / 48, mode="same"))
    pk = env[p : p + 240].max()
    below = np.where(env[p:] < pk * 10 ** (-30 / 20))[0]
    t30 = below[0] / SR * 1000 if len(below) else (len(x) - p) / SR * 1000
    head = x[p : p + int(0.005 * SR)]
    tail = x[p + int(0.015 * SR) : p + int(0.060 * SR)]
    tail_db = 10 * np.log10((tail**2).sum() / max((head**2).sum(), 1e-12) + 1e-12)
    ring_db, q = 0.0, 0.0
    if len(tail) > 512:
        S = np.abs(np.fft.rfft(tail * np.hanning(len(tail)), 16384))
        fr = np.fft.rfftfreq(16384, 1 / SR)
        m = (fr > 500) & (fr < 8000)
        Sd = 20 * np.log10(S[m] + 1e-12)
        ring_db = float(Sd.max() - np.median(Sd))
        f0 = fr[m][np.argmax(Sd)]
        # decay of that frequency: narrow band envelope
        b = signal.butter(2, [f0 * 0.97, f0 * 1.03], "bp", fs=SR, output="sos")
        e = np.abs(signal.hilbert(signal.sosfilt(b, x[p:])))
        e = np.convolve(e, np.ones(96) / 96, mode="same")
        a, z = int(0.005 * SR), int(0.05 * SR)
        seg = np.log(e[a:z] + 1e-9)
        if len(seg) > 10:
            slope = np.polyfit(np.arange(len(seg)) / SR, seg, 1)[0]
            tau = -1 / slope if slope < 0 else 1.0
            q = float(np.pi * f0 * tau)
    return {"t30_ms": round(t30, 1), "ring_db": round(ring_db, 1), "tail_db": round(float(tail_db), 1), "q_est": round(q)}


def files(args):
    for a in args:
        if os.path.isdir(a):
            yield from sorted(glob.glob(os.path.join(a, "**", "*.wav"), recursive=True))
        else:
            yield a


if __name__ == "__main__":
    for f in files(sys.argv[1:]):
        x, sr = sf.read(f, always_2d=True)
        print(f"{f[-42:]:42s}", metrics(x.mean(axis=1), sr))
