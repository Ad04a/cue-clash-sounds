"""Synthesis toolkit for Cue Clash UI and game-event sounds (billiards flavoured).

Materials, built on the measured impact models in impactlib.py:
  resin ball clacks, wooden cue and rack, felt cloth, leather pockets, chalk,
  machine parts (metal token, plastic ratchet, glass globe, plastic chute),
  and musical layers: "clack tones" (tuned ball clacks), soft bells, pads, risers.
Everything is synthesized: no third-party audio.

Arrays are mono (n,) or stereo (n, 2), float64, at SR.
"""

import os

import numpy as np
import soundfile as sf
from scipy import signal
from scipy.ndimage import maximum_filter1d, uniform_filter1d

import impactlib as il

SR = il.SR
_NOTE = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6, "Gb": 6,
         "G": 7, "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11}


# ------------------------------------------------------------------ basics
def hz(note):
    """'C5', 'F#4', 'Bb3' or a number in Hz."""
    if isinstance(note, (int, float, np.floating)):
        return float(note)
    midi = 12 * (int(note[-1]) + 1) + _NOTE[note[:-1]]
    return 440.0 * 2 ** ((midi - 69) / 12)


def ns(dur):
    return int(round(dur * SR))


def taxis(dur):
    return np.arange(ns(dur)) / SR


def norm(x, peak=1.0):
    m = np.abs(x).max()
    return x * (peak / m) if m > 0 else x


def _sos(kind, f, order=2):
    if kind == "bp":
        lo, hi = max(f[0], 10.0), min(f[1], 0.45 * SR)
        return signal.butter(order, [lo, max(hi, lo * 1.05)], "bp", fs=SR, output="sos")
    return signal.butter(order, min(max(f, 10.0), 0.45 * SR), kind, fs=SR, output="sos")


def lp(x, f, order=2):
    return signal.sosfilt(_sos("lowpass", f, order), x, axis=0)


def hp(x, f, order=2):
    return signal.sosfilt(_sos("highpass", f, order), x, axis=0)


def bp(x, lo, hi, order=2):
    return signal.sosfilt(_sos("bp", (lo, hi), order), x, axis=0)


def sweep(x, f_t, kind="lp", k=18, bw=1.0):
    """Time-varying filter: crossfade between k fixed filters spaced on a log scale.
    f_t: cutoff (lp/hp) or centre (bp, bw octaves wide) per sample."""
    f_t = np.broadcast_to(np.asarray(f_t, float), (len(x),))
    lo, hi = float(f_t.min()), float(f_t.max())
    if hi / lo < 1.02:
        k = 1
    cuts = np.geomspace(lo, hi, k) if k > 1 else np.array([lo])
    out = np.zeros_like(x)
    pos = np.interp(np.log(f_t), np.log(cuts), np.arange(k)) if k > 1 else np.zeros(len(x))
    i0 = np.clip(np.floor(pos).astype(int), 0, max(k - 2, 0))
    w = pos - i0
    for j, c in enumerate(cuts):
        if kind == "bp":
            y = bp(x, c / 2 ** (bw / 2), c * 2 ** (bw / 2))
        elif kind == "lp":
            y = lp(x, c)
        else:
            y = hp(x, c)
        if k == 1:
            return y
        wj = np.where(i0 == j, 1 - w, 0.0) + np.where(i0 + 1 == j, w, 0.0)
        out += y * (wj[:, None] if x.ndim == 2 else wj)
    return out


# ------------------------------------------------------------------ envelopes
def env_ad(dur, attack, tau):
    t = taxis(dur)
    a = max(attack, 1e-4)
    return np.where(t < a, t / a, np.exp(-(t - a) / tau))


def env_adsr(dur, a, d, s, r):
    """Attack / decay to sustain level s / release over the last r seconds."""
    t = taxis(dur)
    e = np.where(t < a, t / max(a, 1e-4), s + (1 - s) * np.exp(-(t - a) / max(d, 1e-4)))
    rel_start = dur - r
    return e * np.where(t > rel_start, np.clip((dur - t) / max(r, 1e-4), 0, 1) ** 1.5, 1.0)


def hump(dur, peak_at=0.5, sharp=4.0):
    """Smooth swell-and-fade, maximum at peak_at (0..1) of the duration."""
    u = np.clip(taxis(dur) / dur, 1e-6, 1 - 1e-6)
    a, b = peak_at * sharp, (1 - peak_at) * sharp
    e = u**a * (1 - u) ** b
    return e / e.max()


def fade(x, fin=0.0005, fout=0.01):
    x = x.copy()
    a, b = ns(fin), min(ns(fout), len(x) // 2)
    if a:
        g = np.linspace(0, 1, a)
        x[:a] *= g[:, None] if x.ndim == 2 else g
    if b:
        g = np.cos(np.linspace(0, np.pi / 2, b)) ** 2
        x[-b:] *= g[:, None] if x.ndim == 2 else g
    return x


# ------------------------------------------------------------------ stereo + mixing
def pan(x, p):
    """Mono -> stereo, equal-power pan p in [-1, 1] (p may be an array per sample)."""
    a = (np.clip(p, -1, 1) + 1) * np.pi / 4
    return np.stack([x * np.cos(a), x * np.sin(a)], axis=1)


class Mix:
    """Growable mono or stereo buffer: add(x, t, gain, pan)."""

    def __init__(self, stereo=False, dur=0.0):
        self.stereo = stereo
        self.y = np.zeros((ns(dur), 2)) if stereo else np.zeros(ns(dur))

    def add(self, x, t=0.0, gain=1.0, p=0.0):
        if self.stereo and x.ndim == 1:
            x = pan(x, p)
        elif not self.stereo and x.ndim == 2:
            x = x.mean(axis=1)
        i = max(ns(t), 0)
        need = i + len(x)
        if need > len(self.y):
            pad = np.zeros((need - len(self.y), 2)) if self.stereo else np.zeros(need - len(self.y))
            self.y = np.concatenate([self.y, pad])
        self.y[i:need] += gain * x
        return self


def to_stereo(x):
    return pan(x, 0.0) * np.sqrt(2) if x.ndim == 1 else x


# ------------------------------------------------------------------ noise
def white(dur, rng, ch=1):
    return rng.standard_normal((ns(dur), 2) if ch == 2 else ns(dur))


def pink(dur, rng, ch=1):
    n = ns(dur)

    def one():
        spec = np.fft.rfft(rng.standard_normal(n))
        f = np.fft.rfftfreq(n, 1 / SR)
        spec[1:] /= np.sqrt(f[1:])
        spec[0] = 0
        return norm(np.fft.irfft(spec, n))

    return np.stack([one(), one()], axis=1) if ch == 2 else one()


# ------------------------------------------------------------------ billiards materials
def clack(k, rng):
    """Resin ball on ball (impactlib v2 model). Mono, peak 1."""
    return norm(il.synth_ball(k, rng))


def tick(k, rng, hp_f=1800):
    """A small, light clack: a ball just touching another."""
    return norm(hp(il.synth_ball(k, rng), hp_f))


def felt(k, rng):
    """Ball landing on the cloth: soft, dead thud."""
    return norm(il.synth_table(k, rng))


def cushion(k, rng):
    return norm(il.synth_rail(k, rng))


def cue_tap(k, rng):
    """Leather cue tip on the cue ball."""
    return norm(il.synth_cue(k, rng))


def wood_knock(f0, rng, q=12, decay=0.04, k=0.7):
    """Wooden rack / cue butt knock (low-Q wood resonances)."""
    j = lambda: rng.uniform(0.95, 1.05)  # noqa: E731
    bands = [(f0 * j(), q, 1.0), (f0 * 2.42 * j(), q * 1.1, 0.5), (f0 * 4.1 * j(), q * 1.3, 0.22)]
    exc = il.contact(0.00045 * (1.4 - k), ns(0.3), rng, 0.3)
    y = norm(il.resonators(exc, bands))
    y = il.damp(y, decay)
    y += (0.1 + 0.2 * k) * norm(hp(exc, 2500))
    return norm(y[: ns(min(0.3, decay * 7 + 0.02))])


def pocket_drop(rng, k=0.7, rattle=True):
    """Ball dropping into a leather pocket: low thud, leather slap, balls nudging inside."""
    m = Mix()
    m.add(felt(k, rng), 0, 1.0)
    slap = lp(rng.standard_normal(ns(0.03)), 1500) * np.exp(-taxis(0.03) / 0.005)
    m.add(norm(slap), 0.001, 0.35 * k)
    if rattle:
        for t0, kk in ((rng.uniform(0.05, 0.08), 0.25), (rng.uniform(0.11, 0.16), 0.12)):
            m.add(lp(clack(kk * (0.5 + k), rng), 3200), t0, 0.35 * k)
    return norm(m.y)


def crash(rng, n=10, spread=0.05, k=0.85, cue=False):
    """The pack being hit: n clacks over `spread` seconds, at least 3 ms apart (no comb)."""
    m = Mix()
    t = 0.0
    if cue:
        m.add(cue_tap(k, rng), 0, 0.8)
        t = 0.012
    times = np.sort(rng.uniform(0, spread, n))
    last = -1.0
    for i, ti in enumerate(times):
        ti = max(ti, last + 0.003)
        last = ti
        kk = float(np.clip(k * rng.uniform(0.4, 1.0) * (0.92**i), 0.05, 1))
        m.add(clack(kk, rng), t + ti, kk)
    m.add(felt(k, rng), t, 0.3)
    return norm(m.y)


def chalk_twist(dur, rng, rate=(160, 420), bright=(1800, 6000)):
    """Chalk cube twisted on the cue tip: stick-slip squeak = a train of tiny clicks."""
    t = taxis(dur)
    f = rate[0] + (rate[1] - rate[0]) * (0.5 + 0.5 * np.sin(2 * np.pi * rng.uniform(1.5, 3.5) * t + rng.uniform(0, 6)))
    ph = np.cumsum(f / SR)
    idx = np.where(np.diff(np.floor(ph)) > 0)[0]
    x = np.zeros(len(t))
    x[idx] = rng.uniform(0.4, 1.0, len(idx)) * rng.choice([-1, 1], len(idx))
    y = sum(bp(x, f0 * 0.85, f0 * 1.15) * g for f0, g in ((bright[0] * 1.4, 1.0), (bright[1] * 0.6, 0.6), (2 * bright[0] * 1.4, 0.3)))
    y += 0.15 * bp(rng.standard_normal(len(t)), bright[0], bright[1])
    return norm(y * hump(dur, 0.35, 3.0))


def miscue(rng):
    """Cue tip slipping off the ball: tick, skid, weak glancing clack. A billiards 'error'."""
    m = Mix()
    m.add(hp(cue_tap(0.35, rng), 900), 0, 0.7)
    m.add(chalk_twist(0.045, rng, rate=(900, 1500), bright=(2500, 7000)), 0.004, 0.6)
    m.add(clack(0.18, rng), 0.045, 0.45)
    return norm(m.y)


def felt_swish(dur, rng, f0=700, f1=2600, peak_at=0.4, ch=1):
    """Brush / cue stroke through the air and over the cloth."""
    x = pink(dur, rng, ch)
    t = taxis(dur)
    fc = f0 * (f1 / f0) ** (t / dur)
    y = sweep(x, fc, "bp", bw=1.4)
    e = hump(dur, peak_at, 3.5)
    return norm(y * (e[:, None] if ch == 2 else e))


# ------------------------------------------------------------------ machine parts
DISC = [1.0, 1.594, 2.136, 2.296, 2.653, 2.918, 3.156, 3.501]  # free circular plate modes


def token_clink(rng, f0=2900, k=0.8, decay=0.12):
    """Metal token / coin: inharmonic disc modes (metal is meant to ring here)."""
    t = taxis(decay * 6)
    ir = np.zeros(len(t))
    for i, r in enumerate(DISC):
        f = f0 * r * rng.uniform(0.985, 1.015)
        if f > 0.45 * SR:
            continue
        ir += rng.uniform(0.3, 1.0) / (1 + 0.4 * i) * np.exp(-t / (decay / (1 + 0.35 * i))) * np.sin(2 * np.pi * f * t + rng.uniform(0, 6))
    exc = il.contact(0.00006, len(t), rng, 0.3)
    y = norm(signal.fftconvolve(exc, ir)[: len(t)])
    y[: ns(0.002)] += 0.4 * k * norm(hp(rng.standard_normal(ns(0.002)), 4000))
    return norm(y)


def scrape(dur, rng, lo=2000, hi=7000, rate=(60, 140)):
    """Metal sliding on metal: band noise with stick-slip roughness."""
    t = taxis(dur)
    x = bp(rng.standard_normal(len(t)), lo, hi)
    am = 0.55 + 0.45 * np.sign(np.sin(2 * np.pi * np.cumsum(rng.uniform(*rate, len(t)) / SR)))
    return norm(lp(am, 900) * x * hump(dur, 0.3, 2.5))


def ratchet_click(rng, k=0.7, pitch=1.0):
    """Plastic pawl over a gear tooth, with a bit of machine housing."""
    p = pitch * rng.uniform(0.96, 1.04)
    bands = [(3300 * p, 16, 1.0), (5100 * p, 20, 0.6), (1650 * p, 10, 0.5), (760, 6, 0.35)]
    exc = il.contact(0.00009, ns(0.06), rng, 0.4)
    y = il.damp(norm(il.resonators(exc, bands)), 0.009)
    y += 0.25 * k * norm(hp(exc, 3000))
    return norm(y)


def mech_clunk(rng, k=0.9):
    """Heavy mechanism (gate / crank lock): low wooden-metal thunk."""
    m = Mix()
    m.add(wood_knock(rng.uniform(140, 190), rng, q=7, decay=0.06, k=k), 0, 1.0)
    m.add(ratchet_click(rng, k, 0.6), 0.002, 0.45)
    m.add(felt(k, rng), 0, 0.5)
    return norm(m.y)


def glass_tink(rng, k=0.6):
    """Ball knocking the glass globe."""
    fs = rng.choice([1850, 2600, 3900, 5200, 6900], 3, replace=False) * rng.uniform(0.95, 1.05, 3)
    bands = [(f, rng.uniform(90, 160), rng.uniform(0.4, 1.0)) for f in fs]
    exc = il.contact(0.00012, ns(0.12), rng, 0.3)
    m = Mix()
    m.add(il.damp(norm(il.resonators(exc, bands)), rng.uniform(0.03, 0.06)), 0, 1.0)
    m.add(tick(0.4 * k, rng), 0, 0.3)
    return norm(m.y)


def plastic_hit(rng, k=0.7, f0=820):
    """Ball landing on the plastic tray / chute."""
    bands = [(f0 * rng.uniform(0.92, 1.08), 9, 1.0), (f0 * 2.7 * rng.uniform(0.95, 1.05), 12, 0.45), (f0 * 5.2, 14, 0.2)]
    exc = il.contact(0.0003 * (1.4 - k), ns(0.15), rng, 0.3)
    y = il.damp(norm(il.resonators(exc, bands)), 0.025)
    m = Mix()
    m.add(y, 0, 1.0)
    m.add(clack(0.5 * k, rng), 0, 0.45)
    return norm(m.y)


def roll(dur, rng, v0=1.0, v1=1.0, surface=(380, 1300), rumble=(70, 230), bumps=0.6, ticks=0.25):
    """Rolling ball: rotation-rate amplitude ripple on surface noise, a low rumble and
    tiny contact ticks; loudness follows speed (m/s)."""
    t = taxis(dur)
    v = v0 + (v1 - v0) * t / dur
    f_rot = v / (2 * np.pi * 0.0286)
    ph = 2 * np.pi * np.cumsum(f_rot) / SR
    am = 1 + bumps * (0.5 * np.sin(ph) + 0.3 * np.sin(2 * ph + 1.3) + 0.2 * np.sin(3 * ph + 0.4))
    tex = bp(pink(dur, rng), *surface) * am
    rum = bp(pink(dur, rng), *rumble) * (0.85 + 0.15 * np.sin(ph))
    y = 0.6 * norm(tex) + 0.9 * norm(rum)
    if ticks:
        rate = 25 * v
        k = np.where(rng.uniform(0, 1, len(t)) < rate / SR)[0]
        x = np.zeros(len(t))
        x[k] = rng.uniform(-1, 1, len(k))
        y += ticks * norm(hp(x, 2500)) if len(k) else 0
    return norm(y * (v / max(v.max(), 1e-6)) ** 1.2)


def bounces(rng, hit, n=5, first_dt=0.09, e=0.55, k0=0.8):
    """Impacts of a bouncing ball: intervals and strengths shrink by the restitution e."""
    m = Mix()
    t, dt, k = 0.0, first_dt, k0
    for _ in range(n):
        m.add(hit(rng, k), t, k)
        t += dt
        dt *= e
        k *= e**0.8
    return norm(m.y)


# ------------------------------------------------------------------ musical layers
def clack_tone(note, rng, vel=0.7, decay=None, bright=0.5, click=0.45):
    """A ball clack tuned to a note (a 'ball marimba'): the resin click on top of a
    woody bar tone (partials 1 : 3.98 : 9.1, upper ones die fast)."""
    f0 = hz(note)
    tau = decay or float(np.clip(0.26 * (261.6 / f0) ** 0.5, 0.06, 0.4))  # wood: C5 ~0.18 s
    t = taxis(min(tau * 5 + 0.03, 3.0))
    parts = [(1.0, 1.0, tau), (3.98, 0.15 + 0.25 * bright, tau * 0.25), (9.1, 0.04 + 0.1 * bright, tau * 0.09)]
    ir = sum(a * np.exp(-t / tt) * np.sin(2 * np.pi * f0 * r * t) for r, a, tt in parts if f0 * r < 0.45 * SR)
    exc = il.contact(0.00022 * (1.3 - vel), len(t), rng, 0.2)
    y = norm(signal.fftconvolve(exc, ir)[: len(t)])
    c = clack(float(np.clip(vel, 0.05, 1)), rng)
    y[: min(len(c), len(y))] += click * vel * c[: len(y)]
    return norm(y) * vel


BELL = [(0.5, 0.25, 1.0), (1.0, 1.0, 0.75), (1.19, 0.5, 0.55), (1.56, 0.35, 0.45), (2.0, 0.4, 0.4),
        (2.51, 0.22, 0.3), (2.66, 0.2, 0.25), (3.01, 0.15, 0.2), (4.07, 0.08, 0.12)]


def bell(note, rng, dur=1.2, bright=0.5):
    """Soft bell (sparkle layer only, used sparingly)."""
    f0 = hz(note)
    t = taxis(dur)
    y = np.zeros(len(t))
    for i, (r, a, d) in enumerate(BELL):
        f = f0 * r
        if f < 0.45 * SR:
            y += a * bright ** (i * 0.25) * np.exp(-t / (d * dur * 0.5)) * np.sin(2 * np.pi * f * t + rng.uniform(0, 6))
    y[: ns(0.002)] *= np.linspace(0, 1, ns(0.002))
    return norm(y)


def saw(freq, dur, rng):
    """Band-limited (polyBLEP) sawtooth; freq may vary per sample."""
    n = ns(dur)
    f = np.broadcast_to(np.asarray(freq, float), (n,))
    dt = f / SR
    ph = (np.cumsum(dt) + rng.uniform()) % 1.0
    y = 2 * ph - 1
    m = ph < dt
    tt = ph[m] / dt[m]
    y[m] -= tt + tt - tt * tt - 1
    m = ph > 1 - dt
    tt = (ph[m] - 1) / dt[m]
    y[m] -= tt * tt + tt + tt + 1
    return y


def supersaw(notes, dur, rng, voices=5, detune=12, vib=0.003, spread=0.7):
    out = np.zeros((ns(dur), 2))
    t = taxis(dur)
    for note in notes:
        f0 = hz(note)
        for v in range(voices):
            u = (2 * v / (voices - 1) - 1) if voices > 1 else 0.0
            f = f0 * 2 ** (detune * u / 1200) * (1 + vib * np.sin(2 * np.pi * rng.uniform(4.5, 6) * t + rng.uniform(0, 6)))
            out += pan(saw(f, dur, rng), spread * u) / voices
    return out / max(len(notes), 1)


VOWEL_AH = ((800, 80, 1.0), (1150, 90, 0.55), (2900, 120, 0.25), (3900, 130, 0.1))


def formant(x, formants=VOWEL_AH):
    return sum(g * bp(x, f - b, f + b) for f, b, g in formants)


def pad(notes, dur, rng, attack=0.3, release=0.8, cut=(700, 3200), voices=5, detune=12, choir=False, vib=0.003):
    """Soft synth pad, filter opening with the swell. Stereo."""
    x = supersaw(notes, dur, rng, voices, detune, vib)
    env = env_adsr(dur, attack, 0.4, 0.8, release)
    y = sweep(x, cut[0] * (cut[1] / cut[0]) ** env, "lp")
    if choir:
        y = 0.65 * formant(y) + 0.35 * lp(y, 1800)
    return norm(y * env[:, None])


def brass(notes, dur, rng, attack=0.025, release=0.5, cut=(450, 4200), decay=0.35):
    """Brass-like stab: few detuned saws with a fast filter envelope. Stereo."""
    x = supersaw(notes, dur, rng, voices=3, detune=7, vib=0.004, spread=0.4)
    t = taxis(dur)
    fenv = np.where(t < attack, t / attack, np.exp(-(t - attack) / decay))
    y = sweep(x, cut[0] * (cut[1] / cut[0]) ** fenv, "lp")
    return norm(y * env_adsr(dur, attack, 0.15, 0.7, release)[:, None])


def sub_boom(rng, dur=1.0, f_hi=85, f_lo=36, tau_f=0.09, tau_a=0.35):
    """Deep impact under big moments (a pitch-dropping sine + felt thud)."""
    t = taxis(dur)
    f = f_lo + (f_hi - f_lo) * np.exp(-t / tau_f)
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / tau_a)
    y[: ns(0.004)] *= np.linspace(0, 1, ns(0.004))
    th = felt(0.9, rng)
    y[: len(th)] += 0.3 * th[: len(y)]
    return norm(y)


def whoosh(dur, rng, f0=500, f1=5000, peak_at=0.7, bw=1.2, ch=2, pan_from=0.0, pan_to=0.0):
    """Air/cloth whoosh with a moving band; optionally moving across the stereo field."""
    t = taxis(dur)
    x = pink(dur, rng, 1)
    y = sweep(x, f0 * (f1 / f0) ** (t / dur), "bp", bw=bw) * hump(dur, peak_at, 3.5)
    y = norm(y)
    if ch == 1:
        return y
    if pan_from != pan_to:
        return pan(y, pan_from + (pan_to - pan_from) * t / dur)
    if pan_from != 0:
        return pan(y, pan_from)
    # centred but wide: a second, independent noise band in the right channel
    x2 = norm(sweep(pink(dur, rng, 1), f0 * (f1 / f0) ** (t / dur), "bp", bw=bw) * hump(dur, peak_at, 3.5))
    return np.stack([y, 0.55 * y + 0.45 * x2], axis=1)


def riser(dur, rng, note_from="G3", note_to="G5"):
    """Build-up: rising filtered tone with speeding tremolo, plus a rising whoosh. Stereo."""
    t = taxis(dur)
    f = hz(note_from) * (hz(note_to) / hz(note_from)) ** ((t / dur) ** 1.4)
    tone = 0.5 * saw(f, dur, rng) + 0.5 * saw(f * 1.004, dur, rng)
    tone = sweep(tone, 400 + 3500 * (t / dur) ** 2, "lp")
    trem = 0.6 + 0.4 * np.sin(2 * np.pi * np.cumsum(4 + 14 * (t / dur) ** 2) / SR)
    cresc = (t / dur) ** 2.2
    m = Mix(stereo=True)
    m.add(norm(tone * trem * cresc), 0, 0.5)
    m.add(whoosh(dur, rng, 300, 7000, peak_at=0.97, bw=1.5), 0, 0.8)
    return norm(m.y)


def reverse_swell(dur, rng):
    """Reversed cymbal-like noise + bell: a swell that ends exactly at dur."""
    t = taxis(dur)
    n_ = hp(white(dur, rng, 2), 3500) * np.exp(-t / (dur / 3))[:, None]
    b = to_stereo(bell("C7", rng, dur, 0.6))[: len(t)]
    y = 0.7 * norm(n_) + 0.4 * b
    return norm(y[::-1])


def sparkle(rng, dur, notes, count, spread=0.85, bright=0.6):
    """Bell pings scattered over the stereo field, denser at the start."""
    m = Mix(stereo=True, dur=dur)
    for i in range(count):
        t0 = dur * 0.75 * rng.uniform() ** 1.6
        m.add(bell(notes[rng.integers(len(notes))], rng, rng.uniform(0.5, 1.1), bright), t0,
              rng.uniform(0.2, 0.6), rng.uniform(-spread, spread))
    return norm(m.y)


def glitter(dur, rng, density=60):
    """Very short high ticks, thinning out: 'shine'."""
    t = taxis(dur)
    rate = density * np.exp(-t / (dur / 2.5))
    k = np.where(rng.uniform(0, 1, len(t)) < rate / SR)[0]
    x = np.zeros((len(t), 2))
    x[k, rng.integers(0, 2, len(k))] = rng.uniform(-1, 1, len(k))
    return norm(hp(lp(x, 14000), 6500))


def reverb(x, rng, decay=1.2, wet=0.2, predelay=0.012, bright=7000):
    """Diffuse stereo reverb (decorrelated decaying noise; no discrete echoes)."""
    x = to_stereo(x)
    m = ns(decay * 1.2)
    t = np.arange(m) / SR
    out = np.zeros((len(x) + m + ns(predelay), 2))
    out[: len(x)] += x
    for c in range(2):
        ir = lp(rng.standard_normal(m) * np.exp(-t / (decay / 6.91)), bright)
        ir[: ns(0.008)] *= np.linspace(0, 1, ns(0.008))
        ir /= np.sqrt((ir**2).sum())
        w = signal.fftconvolve(x[:, c], ir)
        d = ns(predelay)
        out[d : d + len(w), c] += wet * w
    return out


# ------------------------------------------------------------------ mastering
def k_weight(x):
    """ITU-R BS.1770 K-weighting (as in loudness meters)."""
    G, Q, fc = 3.99984385397, 0.7071752369554193, 1681.9744509555319
    K = np.tan(np.pi * fc / SR)
    Vh = 10 ** (G / 20)
    Vb = Vh**0.4996667741545416
    a0 = 1 + K / Q + K * K
    b1 = np.array([(Vh + Vb * K / Q + K * K), 2 * (K * K - Vh), (Vh - Vb * K / Q + K * K)]) / a0
    a1 = np.array([1, 2 * (K * K - 1) / a0, (1 - K / Q + K * K) / a0])
    fc2, Q2 = 38.13547087613982, 0.5003270373253953
    K = np.tan(np.pi * fc2 / SR)
    a0 = 1 + K / Q2 + K * K
    b2 = np.array([1.0, -2.0, 1.0])
    a2 = np.array([1, 2 * (K * K - 1) / a0, (1 - K / Q2 + K * K) / a0])
    return signal.lfilter(b2, a2, signal.lfilter(b1, a1, x, axis=0), axis=0)


def loudness(x, win=0.1):
    """Maximum momentary loudness over `win` seconds (LUFS-like units)."""
    y = k_weight(x)
    p = (y**2).sum(axis=1) if y.ndim == 2 else y**2
    w = max(ns(win), 1)
    if len(p) <= w:
        return float(-0.691 + 10 * np.log10(p.sum() / w + 1e-12))
    c = np.concatenate([[0.0], np.cumsum(p)])  # running sum: O(n) for any window length
    return float(-0.691 + 10 * np.log10(((c[w:] - c[:-w]) / w).max() + 1e-12))


def limiter(x, ceiling_db=-1.0, release=0.05, look=0.0015):
    """Lookahead peak limiter (instant attack via lookahead window, exponential release)."""
    c = 10 ** (ceiling_db / 20)
    a = np.abs(x).max(axis=1) if x.ndim == 2 else np.abs(x)
    L = max(ns(look), 1)
    pk = maximum_filter1d(a, size=2 * L + 1, mode="constant")
    req = np.minimum(1.0, c / np.maximum(pk, 1e-12))
    g = np.empty_like(req)
    r = np.exp(-1 / (release * SR))
    cur = 1.0
    for i in range(len(req)):
        cur = req[i] if req[i] < cur else req[i] + (cur - req[i]) * r
        g[i] = cur
    g = uniform_filter1d(g, L, mode="nearest")  # smooth without dragging the edges toward 0
    g = np.minimum(g, req)
    return x * (g[:, None] if x.ndim == 2 else g)


def master(x, target, ceiling_db=-1.0, tail_db=-66.0, fout=0.012, max_limit=2.0):
    """DC cut, loudness to target, peak-limit to the ceiling, trim the silent tail.
    Limiting is capped at max_limit dB: a short click that can't reach the target
    without being squashed is left a little quieter instead (transients stay sharp)."""
    x = hp(np.asarray(x, float), 18)
    x = x * 10 ** ((target - loudness(x)) / 20)
    over = 20 * np.log10(np.abs(x).max() + 1e-12) - ceiling_db
    if over > max_limit:
        x = x * 10 ** (-(over - max_limit) / 20)
    reduction = 0.0
    if np.abs(x).max() > 10 ** (ceiling_db / 20):
        before = np.abs(x).max()
        x = limiter(x, ceiling_db)
        reduction = float(20 * np.log10(before / max(np.abs(x).max(), 1e-12)))
    a = np.abs(x).max(axis=1) if x.ndim == 2 else np.abs(x)
    above = np.where(a > 10 ** (tail_db / 20))[0]
    end = min(len(x), (above[-1] if len(above) else len(x)) + ns(0.01))
    # no fade-in: the sounds start from silence and the first transient is the attack
    x = fade(x[:end], 0.0, fout)
    return x, reduction


def loop_fold(y, length):
    """Exact loop for summed events: whatever rings past the end is added to the start."""
    L = ns(length)
    out = np.zeros((L, 2) if y.ndim == 2 else L)
    out[: min(L, len(y))] = y[:L]
    tail = y[L:]
    while len(tail):
        k = min(len(tail), L)
        out[:k] += tail[:k]
        tail = tail[k:]
    return out


def loop_xfade(y, length, xf=0.3):
    """Loop for noise beds: equal-power crossfade of the extra tail into the start
    (y must be at least length + xf long)."""
    L, X = ns(length), ns(xf)
    out = y[:L].copy()
    g = np.sin(np.linspace(0, np.pi / 2, X))
    g = g[:, None] if y.ndim == 2 else g
    out[:X] = y[:X] * g + y[L : L + X] * np.cos(np.arcsin(np.clip(g, 0, 1)))
    return out


def master_loop_level(x, target, win=0.4):
    """Set a loop's loudness (no fades, no trimming: the ends must stay joined)."""
    x = x * 10 ** ((target - loudness(x, win)) / 20)
    pk = np.abs(x).max()
    return x * (10 ** (-1 / 20) / pk) if pk > 10 ** (-1 / 20) else x


def save(path, x):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    x = np.clip(x, -1, 1).astype(np.float32)
    sf.write(path + ".wav", x, SR, subtype="PCM_16")
    ch = 2 if x.ndim == 2 else 1
    with sf.SoundFile(path + ".ogg", "w", SR, ch, format="OGG", subtype="VORBIS") as fh:
        for i in range(0, len(x), 8192):  # blocks: libsndfile's Vorbis encoder dislikes huge writes
            fh.write(x[i : i + 8192])


def qa(x):
    """Numbers to check a finished sound without listening."""
    a = np.abs(x).max(axis=1) if x.ndim == 2 else np.abs(x)
    out = {
        "dur_s": round(len(x) / SR, 3),
        "peak_db": round(float(20 * np.log10(a.max() + 1e-12)), 1),
        "loud": round(loudness(x), 1),
        "dc": round(float(np.abs(x.mean(axis=0)).max()), 5),
        "clipped": int((a >= 0.999).sum()),
        "tail_db": round(float(20 * np.log10(a[-ns(0.005):].max() + 1e-12)), 1),
        "start_db": round(float(20 * np.log10(a[: ns(0.0005)].max() + 1e-12)), 1),
    }
    if x.ndim == 2:
        out["lr_corr"] = round(float(np.corrcoef(x[:, 0], x[:, 1])[0, 1]), 2)
    return out
