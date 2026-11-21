"""Shared helpers: clip extraction, modal synthesis of billiard impacts, finishing.

All audio is mono float64 at SR (48 kHz).

Physics behind the synthesis (Hertzian contact of two elastic bodies):
  * contact time   tau ~ v^(-1/5)   -> harder hits are shorter -> brighter
  * peak force     F   ~ v^(6/5)    -> radiated amplitude grows a bit faster than speed
The impact is modelled as a half-sine force pulse of length tau driving a bank of
damped resonant modes (the "ring" of the ball / cue / rail), plus a little noise.
Mode frequencies and decay times come from the analysis of the source recordings
(see output/analysis/analysis.json).
"""

import numpy as np
import soundfile as sf
from scipy import signal

SR = 48000


# ---------------------------------------------------------------- basic dsp
def load(path):
    x, sr = sf.read(path, always_2d=True)
    x = x.mean(axis=1)
    if sr != SR:
        x = signal.resample_poly(x, SR, sr)
    return x.astype(np.float64)


def envelope(x, win=0.002):
    n = max(1, int(win * SR))
    return np.sqrt(np.convolve(x * x, np.ones(n) / n, mode="same"))


def sos(kind, f, order=2):
    return signal.butter(order, f, kind, fs=SR, output="sos")


def filt(x, kind, f, order=2):
    return signal.sosfilt(sos(kind, f, order), x)


def db(x):
    return 20 * np.log10(np.abs(x) + 1e-12)


def finish(x, peak_db=-1.0, floor_db=-62.0, min_len=0.04):
    """DC/rumble cut, trim trailing silence, short fade, normalise peak."""
    x = filt(x, "hp", 35, 2)
    env = envelope(x, 0.004)
    above = np.where(db(env) > db(env.max()) + floor_db)[0]
    end = max(int(min_len * SR), (above[-1] if len(above) else len(x)) + int(0.005 * SR))
    x = x[: min(end, len(x))].copy()
    nf = min(len(x) // 4, int(0.02 * SR))
    x[-nf:] *= np.cos(np.linspace(0, np.pi / 2, nf)) ** 2
    x[: int(0.0003 * SR)] *= np.linspace(0, 1, int(0.0003 * SR))
    return x * (10 ** (peak_db / 20) / (np.abs(x).max() + 1e-12))


def save(path, x, ogg=True):
    sf.write(path, x.astype(np.float32), SR, subtype="PCM_16")
    if ogg:
        sf.write(path[:-4] + ".ogg", x.astype(np.float32), SR, format="OGG", subtype="VORBIS")


# ------------------------------------------------------------ measurements
def features(x):
    """centroid (Hz), low-frequency energy ratio (<450 Hz), t30 (ms)."""
    i = int(np.argmax(np.abs(x[: int(0.02 * SR)])))
    seg = x[max(0, i - 48) : i + int(0.03 * SR)]
    S = np.abs(np.fft.rfft(seg * np.hanning(len(seg)), 8192)) ** 2
    fr = np.fft.rfftfreq(8192, 1 / SR)
    m = fr > 40
    cen = (S[m] * fr[m]).sum() / S[m].sum()
    lf = S[(fr > 40) & (fr < 450)].sum() / S[m].sum()
    env = envelope(x[i:], 0.001)
    below = np.where(db(env) < db(env[: int(0.004 * SR)].max()) - 30)[0]
    t30 = below[0] / SR * 1000 if len(below) else len(x) / SR * 1000
    return {"centroid_hz": round(float(cen)), "lf_ratio": round(float(lf), 2), "t30_ms": round(float(t30), 1)}


# ------------------------------------------------------------- extraction
def gate(y, floor_db=-34.0, win=0.004):
    """Downward expander: attenuate everything that sits close to the noise floor."""
    env = envelope(y, win)
    rel = db(env) - db(env.max())
    g = np.clip((rel - floor_db) / 10.0, 0, 1)  # 10 dB soft knee
    g = np.convolve(g, np.ones(int(0.003 * SR)) / int(0.003 * SR), mode="same")
    return y * g


def extract(x, t_peak, dur, next_onset=None, tail_tau=None, noise_gate=None):
    """Cut one impact out of a recording.

    Starts at the true onset (envelope back below 3% of peak), stops before the
    next impact, and optionally reshapes the tail (tail_tau seconds) to strip
    room reverb / background noise from wetter recordings.
    """
    pad = int(0.02 * SR)  # hits right at the start of a file
    x = np.concatenate([np.zeros(pad), x])
    t_peak += pad / SR
    if next_onset is not None:
        next_onset += pad / SR
    p = int(t_peak * SR)
    w = int(0.006 * SR)
    p = p - w + int(np.argmax(np.abs(x[p - w : p + w])))
    env = envelope(x[p - int(0.008 * SR) : p + 1], 0.0003)
    th = np.where(env < 0.03 * env.max())[0]
    start = p - int(0.008 * SR) + (th[-1] if len(th) else 0) - int(0.0005 * SR)
    end = start + int(dur * SR)
    if next_onset is not None:
        end = min(end, int(next_onset * SR) - int(0.004 * SR))
    y = x[start:end].copy()
    if tail_tau:
        t = np.arange(len(y)) / SR
        knee = (p - start) / SR + 0.004
        y *= np.where(t < knee, 1.0, np.exp(-(t - knee) / tail_tau))
    if noise_gate is not None:
        y = gate(y, noise_gate)
    return y


# ------------------------------------------------------------- synthesis
def half_sine(tau):
    n = max(2, int(tau * SR))
    return np.sin(np.pi * np.arange(n) / n)


def resonators(exc, bands):
    """Drive 2-pole resonators: bands = [(freq, Q, gain)]. The Q sets the material:
    a resonance rings for tau = Q / (pi * f).  Metal Q ~ 500+, resin balls ~ 20-50,
    wood ~ 8-20, rubber / cloth ~ 2-6.  (v1 of this file used Q 60-140 everywhere,
    plus comb-like early echoes: that was the metallic sound.)"""
    y = np.zeros_like(exc)
    for f, q, g in bands:
        b, a = signal.iirpeak(min(f, 0.45 * SR), max(q, 0.7), fs=SR)
        y += g * signal.lfilter(b, a, exc)
    return y


def contact(tau, n, rng, rough=0.35):
    """Contact force: a half-sine of length tau, roughened (no real contact is a
    perfectly smooth pulse, and a smooth one makes the resonances sound like pure tones)."""
    e = np.zeros(n)
    hs = half_sine(tau)
    e[: len(hs)] = hs * (1 + rough * rng.standard_normal(len(hs)))
    return e


def damp(y, tau):
    """Extra overall damping (energy lost to the cloth, the hand, the table)."""
    return y * np.exp(-np.arange(len(y)) / (tau * SR))


def noise_burst(n, rng, lo, hi, tau):
    nb = signal.sosfilt(signal.butter(2, [lo, hi], "bp", fs=SR, output="sos"), rng.standard_normal(n))
    return nb * np.exp(-np.arange(n) / (tau * SR))


def jit(rng, x, amount):
    return x * rng.uniform(1 - amount, 1 + amount)


def norm(y):
    return y / (np.abs(y).max() + 1e-12)


# Phenolic-resin ball (measured on the dry kvv clacks): energy 1.3-3.5 kHz, attack
# 0.5-0.9 ms, -30 dB after ~11 ms, tail ~15 dB under the hit.
BALL_BANDS = [1450, 1800, 2150, 2500, 2900, 3350]


def synth_ball(k, rng):
    """Ball-on-ball clack. k = normalised impact speed 0..1."""
    k = max(k, 0.02)
    n = int(0.15 * SR)
    exc = contact(jit(rng, 0.00018, 0.15) * k**-0.2, n, rng)
    tilt = 1.4 * (k - 0.55)  # quiet clacks measured ~30 % darker
    fs = [jit(rng, f, 0.09) for f in BALL_BANDS] + list(rng.uniform(1200, 4200, 2))
    bands = [(f, rng.uniform(16, 40), rng.uniform(0.4, 1.0) * (f / 2100) ** tilt) for f in fs]
    bands.append((jit(rng, 800, 0.15), rng.uniform(4, 7), rng.uniform(0.15, 0.35)))  # weight of the ball
    y = norm(resonators(exc, bands))
    # the crack: broadband, only as long as the contact
    y += (0.25 + 0.45 * k) * norm(filt(exc, "hp", 3000, 2))
    y = damp(y, jit(rng, 0.010, 0.25))
    m = 0.6 * (1 - k)  # softer contact = darker
    y = (1 - m) * y + m * filt(y, "lp", 2400, 2) * 1.5
    return finish(y)


def synth_cue(k, rng):
    """Leather tip on a wooden cue hitting the resin cue ball: a dull 'tok'.
    Measured: peaks ~400-650 Hz and 1170 / 1430 Hz, -30 dB after ~15 ms."""
    k = max(k, 0.02)
    n = int(0.15 * SR)
    exc = contact(jit(rng, 0.00034, 0.2) * k**-0.15, n, rng, 0.25)  # leather: soft, smooth
    tilt = 0.9 * (k - 0.5)
    bands = [
        (jit(rng, 420, 0.12), rng.uniform(4, 8), 0.45),  # tip / ferrule thock
        (jit(rng, 620, 0.12), rng.uniform(5, 9), 0.4),
        (jit(rng, 1175, 0.05), rng.uniform(12, 24), 1.0 * (1175 / 900) ** tilt),  # cue ball response
        (jit(rng, 1430, 0.05), rng.uniform(12, 24), 0.9 * (1430 / 900) ** tilt),
        (rng.uniform(850, 2300), rng.uniform(6, 12), rng.uniform(0.35, 0.7)),  # wooden shaft
        (rng.uniform(2000, 3400), rng.uniform(8, 16), rng.uniform(0.2, 0.45) * (0.3 + k)),
    ]
    y = norm(resonators(exc, bands))
    # chalk / leather slap
    y += (0.25 + 0.45 * k) * norm(noise_burst(n, rng, 900, 5000, jit(rng, 0.0012, 0.3)))
    return finish(damp(y, jit(rng, 0.011, 0.25)))


def synth_rail(k, rng):
    """Ball into the cloth-covered rubber cushion on a wooden rail: a damped thump,
    a little ball 'tock', cloth noise. Measured: ~60 % of the energy under 450 Hz."""
    k = max(k, 0.02)
    n = int(0.2 * SR)
    exc = contact(jit(rng, 0.0012, 0.2) * k**-0.1, n, rng, 0.4)  # rubber nose under cloth
    bands = [
        (rng.uniform(85, 150), rng.uniform(2, 3.5), 0.3),  # rail body
        (rng.uniform(170, 300), rng.uniform(2.5, 4), 0.45),
        (rng.uniform(340, 600), rng.uniform(3, 5), 0.9),
        (rng.uniform(650, 1100), rng.uniform(4, 7), 0.8),  # wood rail top
    ]
    y = norm(resonators(exc, bands))
    # the ball itself, hit on the cushion nose (short contact, resin resonances)
    ball_exc = contact(0.0005 * k**-0.15, n, rng)
    ball = norm(resonators(ball_exc, [(jit(rng, f, 0.1), rng.uniform(14, 30), 1) for f in BALL_BANDS[:4]]))
    y += (0.5 + 0.4 * k) * damp(ball, 0.006)
    y += 0.15 * norm(filt(noise_burst(n, rng, 200, 3000, 0.003), "lp", 2500))  # cloth
    return finish(damp(y, jit(rng, 0.018, 0.25)))


def synth_table(k, rng):
    """Ball landing on the cloth-covered bed (jump shots, balls dropping back down):
    very damped low thud, almost no ring."""
    k = max(k, 0.02)
    n = int(0.15 * SR)
    exc = contact(jit(rng, 0.0010, 0.25) * k**-0.1, n, rng, 0.4)
    bands = [
        (rng.uniform(65, 120), rng.uniform(1.5, 2.5), 0.55),
        (rng.uniform(150, 260), rng.uniform(2, 3), 0.8),
        (rng.uniform(380, 700), rng.uniform(2.5, 4), 0.6),
    ]
    y = norm(resonators(exc, bands))
    ball = norm(resonators(contact(0.0004, n, rng), [(jit(rng, f, 0.1), rng.uniform(14, 30), 1) for f in BALL_BANDS[:3]]))
    y += (0.12 + 0.18 * k) * damp(ball, 0.004)
    y += 0.2 * norm(noise_burst(n, rng, 150, 1800, 0.002))  # cloth
    return finish(damp(y, jit(rng, 0.012, 0.25)))


# ------------------------------------------------------------- layers / clusters
LAYERS = ("soft", "medium", "hard")
LAYER_K = {"soft": 0.15, "medium": 0.45, "hard": 0.9}  # speed the synthetic layer is rendered at


def soften(x, layer, kind):
    """Derive softer velocity layers from a (hard) recorded hit: lower contact
    brightness = gentle low-pass, as Hertz contact time grows when speed drops."""
    if layer == "hard":
        return finish(x)
    cut = {"ball": (7000, 3800), "cue": (5000, 2600), "rail": (2500, 1200), "table": (2000, 1000)}[kind]
    f = cut[0] if layer == "medium" else cut[1]
    return finish(filt(x, "lp", f, 2) * 0.6 + filt(x, "lp", f * 0.5, 2) * 0.4)


def cluster(hits, rng, n, spread):
    """Several near-simultaneous clacks (the pack 'chatter'), used for the energy the
    voice budget does not play as individual sounds. Each copy is a different hit with
    its own small pitch offset and at least 3 ms apart, so nothing comb-filters."""
    out = np.zeros(int((spread + 0.3) * SR))
    times = np.sort(rng.uniform(0, spread, n - 1))
    t_prev, starts = 0.0, [0.0]
    for t in times:
        t_prev = max(t, t_prev + 0.003)
        starts.append(min(t_prev, spread))
    order = rng.permutation(len(hits))
    for j, t0 in enumerate(starts):
        h = hits[order[j % len(hits)]]
        h = signal.resample_poly(h, 1000, int(1000 * rng.uniform(0.95, 1.05)))
        g = rng.uniform(0.3, 1.0) * (0.88**j)
        i = int(t0 * SR)
        seg = h[: len(out) - i]
        out[i : i + len(seg)] += g * seg
    return finish(out)
