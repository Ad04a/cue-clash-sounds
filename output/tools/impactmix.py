"""Reference implementation of the impact-sound mechanism (the same rules as
roblox/ImpactAudio.luau), used to render and audition shots offline.

Per event (kind, speed, t):
  1. intensity  k = clamp(speed / vref[kind], 0, 1); below kmin -> silent
  2. gain       g = vmax[kind] * k^curve       (Hertz contact: pressure ~ v^1.2)
  3. layer      soft / medium / hard by k, with a little random 'dither' near the
                edges so there is no audible step between layers
  4. variant    round-robin, never the same file twice in a row
  5. pitch      1 + jitter + small speed term (harder = a touch brighter)

Per frame (events are only heard once per frame in Roblox anyway):
  6. voice budget   at most budget[kind] individual voices per `window` seconds;
                    the loudest events of the frame win
  7. chatter        the energy of the events that did not get a voice is summed
                    (incoherent sources add in energy: g_total = sqrt(sum g^2)) and
                    played as ONE multi-ball 'cluster' sample -> a break keeps all
                    its power without 40 overlapping voices
  8. loudness guard every gain is divided by sqrt(1 + E_recent / E0), where
                    E_recent is the decaying energy of what was just played
"""

import glob
import os

import numpy as np
import soundfile as sf
from scipy import signal

SR = 48000

CONFIG = {
    "frame": 1 / 60,
    "kmin": 0.012,
    "kinds": {
        #            speed for k=1 (studs/s), exponent, max volume, sound folder
        "cue": {"vref": 25.0, "curve": 1.0, "vmax": 1.0, "folder": "cue"},
        "ball": {"vref": 16.0, "curve": 1.2, "vmax": 0.9, "folder": "ball"},
        "cushion": {"vref": 12.0, "curve": 1.3, "vmax": 0.8, "folder": "rail"},
        "bounce": {"vref": 6.0, "curve": 1.3, "vmax": 0.45, "folder": "table"},
    },
    "layer_edges": (0.22, 0.55),
    "layer_dither": 0.06,
    "pitch_jitter": 0.02,
    "volume_jitter": 0.12,  # +-12 % per hit: no two hits exactly alike
    "pitch_by_speed": 0.03,
    "window": 0.08,
    "budget": {"ball": 6, "cushion": 3, "bounce": 2, "cue": 2},
    "chatter_gain": 0.8,
    "chatter_min_interval": 0.03,
    "loudness_E0": 1.6,
    "loudness_tau": 0.06,
}
LAYERS = ("soft", "medium", "hard")


def load_bank(sounds_dir, bank):
    """bank = 'recorded' | 'synth' | 'hybrid' (recorded cue+ball, synth rail). The cloth
    'table' landing sound only exists as synth (no recording of it)."""
    per_kind = {"cue": bank, "ball": bank, "rail": bank, "cluster": bank, "table": "synth"}
    if bank == "hybrid":
        per_kind = {"cue": "recorded", "ball": "recorded", "rail": "synth", "cluster": "recorded", "table": "synth"}
    out = {}
    for folder, b in per_kind.items():
        for layer in LAYERS:
            files = sorted(glob.glob(os.path.join(sounds_dir, b, folder, f"{layer}_*.wav")))
            out[(folder, layer)] = [sf.read(f)[0] for f in files]
    return out


class Mixer:
    def __init__(self, bank, config=CONFIG, seed=0, mechanism=True):
        self.bank = bank
        self.c = config
        self.rng = np.random.default_rng(seed)
        self.mechanism = mechanism
        self.last_variant = {}
        self.voices = []  # (t, kind) of individual voices, for the budget window
        self.E = 0.0
        self.E_t = 0.0
        self.last_chatter = -1.0
        self.played = []  # (t, folder, layer, variant, gain, pitch) - the render list

    # ---- rules 1-5
    def intensity(self, kind, speed):
        return float(np.clip(speed / self.c["kinds"][kind]["vref"], 0, 1))

    def gain(self, kind, k):
        p = self.c["kinds"][kind]
        return p["vmax"] * k ** p["curve"]

    def layer(self, k):
        k = k + self.rng.uniform(-self.c["layer_dither"], self.c["layer_dither"])
        lo, hi = self.c["layer_edges"]
        return "soft" if k < lo else "medium" if k < hi else "hard"

    def variant(self, folder, layer):
        n = len(self.bank[(folder, layer)])
        last = self.last_variant.get((folder, layer))
        v = self.rng.integers(n)
        if n > 1 and v == last:
            v = (v + 1 + self.rng.integers(n - 1)) % n
        self.last_variant[(folder, layer)] = v
        return int(v)

    def pitch(self, k):
        j = np.clip(self.rng.normal(0, self.c["pitch_jitter"]), -0.045, 0.045)
        return 1.0 + j + self.c["pitch_by_speed"] * (k - 0.5)

    # ---- rule 8
    def guard(self, t, g):
        self.E *= np.exp(-(t - self.E_t) / self.c["loudness_tau"])
        self.E_t = t
        g = g / np.sqrt(1 + self.E / self.c["loudness_E0"])
        self.E += g * g
        return g

    def emit(self, t, folder, k, g):
        layer = self.layer(k)
        v = self.variant(folder, layer)
        g *= 1 + self.rng.uniform(-self.c["volume_jitter"], self.c["volume_jitter"])
        g = self.guard(t, g) if self.mechanism else g
        self.played.append((t, folder, layer, v, g, self.pitch(k)))

    # ---- rules 6-7: one frame of events
    def frame(self, t, events):
        if not self.mechanism:
            for e in events:
                k = self.intensity(e["kind"], e["speed"])
                if k >= self.c["kmin"]:
                    self.emit(e["t"], self.c["kinds"][e["kind"]]["folder"], k, self.gain(e["kind"], k))
            return
        w = self.c["window"]
        self.voices = [v for v in self.voices if t - v[0] < w]
        scored = []
        for e in events:
            k = self.intensity(e["kind"], e["speed"])
            if k >= self.c["kmin"]:
                scored.append((self.gain(e["kind"], k), k, e))
        scored.sort(key=lambda s: -s[0])
        pool_E, pool_n = 0.0, 0
        for g, k, e in scored:
            kind = e["kind"]
            used = sum(1 for v in self.voices if v[1] == kind)
            if used < self.c["budget"][kind]:
                self.voices.append((t, kind))
                self.emit(t, self.c["kinds"][kind]["folder"], k, g)
            elif kind == "ball":
                pool_E += g * g
                pool_n += 1
            # dropped cushion/bounce hits are masked by the louder ones: let them go
        if pool_n and t - self.last_chatter >= self.c["chatter_min_interval"]:
            g = self.c["chatter_gain"] * np.sqrt(pool_E)
            mean_k = (np.sqrt(pool_E / pool_n) / self.c["kinds"]["ball"]["vmax"]) ** (1 / 1.2)
            self.last_chatter = t
            self.emit(t, "cluster", mean_k, min(g, 1.0))

    def run(self, events, quantize=True):
        events = sorted(events, key=lambda e: e["t"])
        if not quantize:
            for e in events:
                self.frame(e["t"], [e])
            return self.played
        f = self.c["frame"]
        i = 0
        while i < len(events):
            ft = np.floor(events[i]["t"] / f) * f + f  # heard on the next frame, like the game
            batch = []
            while i < len(events) and events[i]["t"] < ft:
                batch.append(events[i])
                i += 1
            self.frame(ft, batch)
        return self.played

    def render(self, tail=1.0, room=True):
        if not self.played:
            return np.zeros(SR)
        end = max(p[0] for p in self.played) + tail
        out = np.zeros(int(end * SR) + SR)
        for t, folder, layer, v, g, pitch in self.played:
            x = self.bank[(folder, layer)][v]
            if abs(pitch - 1) > 1e-4:  # PlaybackSpeed: pitch and length change together
                up, down = 1000, int(round(1000 * pitch))
                x = signal.resample_poly(x, up, down)
            i = int(t * SR)
            out[i : i + len(x)] += g * x
        if room:  # same idea as ImpactAudio.Config.Room: diffuse tail, no discrete echoes
            n = int(0.9 * SR)
            ir = self.rng.standard_normal(n) * np.exp(-np.arange(n) / (0.6 / 6.9 * SR))
            ir = signal.sosfilt(signal.butter(1, 5000, "lp", fs=SR, output="sos"), ir)
            wet = signal.fftconvolve(out, ir)[: len(out)]
            out = out + wet / (np.sqrt((ir**2).sum()) + 1e-12) * 10 ** (-17 / 20)
        # gentle safety limiter (Roblox mixes in float; this only matters for the WAV)
        peak = np.abs(out).max()
        if peak > 0.98:
            out = np.tanh(out / peak * 1.4) / np.tanh(1.4) * 0.98
        return out[: int(end * SR)]
