"""Offline 8-ball break: a small 2D physics sim with the game's rack, table size and
physics constants (PoolConfig.luau), producing the same event stream the game's
Simulation emits ({t, kind, speed}), then rendered through impactmix.Mixer.

usage: python breaksim.py <output_dir>
writes  <output_dir>/break_renders/*.wav|ogg, events_*.json, break_overview.png
"""

import json
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import soundfile as sf

sys.path.insert(0, os.path.dirname(__file__))
from impactmix import SR, Mixer, load_bank  # noqa: E402

# --- PoolConfig.luau values (studs, studs/s)
MODEL_SCALE = 1 / 0.28
HALF_L = 2.72 * MODEL_SCALE / 2 - 0.06 * MODEL_SCALE  # nose line (outer minus cushion)
HALF_W = 1.32 * MODEL_SCALE / 2 - 0.06 * MODEL_SCALE
R = 0.257 / 2
K = 2.72 * MODEL_SCALE / 18
G = 79 * K
MU_SLIDE, MU_ROLL = 0.2, 0.008
E_BALL, E_CUSHION = 0.95, 0.78
MAX_SHOT = 25.0
POWER_CURVE = 1.35
HEAD_X, FOOT_X = -2.72 * MODEL_SCALE / 4, 2.72 * MODEL_SCALE / 4
POCKETS = [(sx * HALF_L, sy * HALF_W, 0.30) for sx in (-1, 1) for sy in (-1, 1)] + [
    (0, sy * (HALF_W + 0.12), 0.29) for sy in (-1, 1)
]
ROWS = [[1], [9, 2], [10, 8, 3], [11, 7, 14, 4], [5, 13, 15, 6, 12]]


def rack(rng, jitter):
    pos = [(HEAD_X, rng.normal(0, 0.004))]  # cue ball, tiny aim error
    gap = 1.0005
    rs = 2 * R * gap * np.sqrt(3) / 2
    for row, ids in enumerate(ROWS):
        for j, _ in enumerate(ids):
            pos.append((FOOT_X + row * rs, ((j - row / 2) * 2 * R * gap)))
    p = np.array(pos, dtype=float)
    p[1:] += rng.normal(0, jitter * R, p[1:].shape)  # real racks are never perfect
    return p


def simulate(power, seed=0, jitter=0.004, t_max=8.0, dt=1 / 6000):
    rng = np.random.default_rng(seed)
    p = rack(rng, jitter)
    n = len(p)
    v = np.zeros_like(p)
    v0 = MAX_SHOT * power**POWER_CURVE
    aim = np.array([FOOT_X - HEAD_X, -p[0, 1] + rng.normal(0, 0.002)])
    v[0] = v0 * aim / np.linalg.norm(aim)
    roll_speed = np.zeros(n)  # speed at which sliding turns into rolling (5/7 rule)
    roll_speed[0] = v0 * 5 / 7
    alive = np.ones(n, bool)
    events = [{"t": 0.0, "kind": "cue", "a": 0, "speed": v0}]
    t = 0.0
    iu, ju = np.triu_indices(n, 1)
    while t < t_max:
        sp = np.linalg.norm(v, axis=1)
        if not (sp[alive] > 0.02).any():
            break
        # friction
        sliding = sp > roll_speed
        dec = np.where(sliding, MU_SLIDE * G, MU_ROLL * G) * dt
        f = np.where(sp > dec, (sp - dec) / np.maximum(sp, 1e-9), 0)
        v *= f[:, None]
        p += v * dt
        t += dt
        # ball-ball
        d = p[ju] - p[iu]
        dist = np.linalg.norm(d, axis=1)
        hit = np.where((dist < 2 * R) & alive[iu] & alive[ju])[0]
        for h in hit:
            a, b = iu[h], ju[h]
            nrm = d[h] / max(dist[h], 1e-9)
            vn = np.dot(v[a] - v[b], nrm)
            if vn <= 0:
                continue  # already separating
            imp = (1 + E_BALL) / 2 * vn
            v[a] -= imp * nrm
            v[b] += imp * nrm
            ov = 2 * R - dist[h]
            p[a] -= nrm * ov / 2
            p[b] += nrm * ov / 2
            for q in (a, b):
                roll_speed[q] = np.linalg.norm(v[q]) * 5 / 7
            events.append({"t": t, "kind": "ball", "a": int(a), "b": int(b), "speed": float(vn)})
        # cushions
        for q in np.where(alive)[0]:
            for axis, lim in ((0, HALF_L - R), (1, HALF_W - R)):
                if abs(p[q, axis]) > lim and np.sign(v[q, axis]) == np.sign(p[q, axis]):
                    vn = abs(v[q, axis])
                    v[q, axis] *= -E_CUSHION
                    p[q, axis] = np.sign(p[q, axis]) * lim
                    roll_speed[q] = np.linalg.norm(v[q]) * 5 / 7
                    events.append({"t": t, "kind": "cushion", "a": int(q), "speed": float(vn)})
            for px, py, pr in POCKETS:
                if (p[q, 0] - px) ** 2 + (p[q, 1] - py) ** 2 < pr * pr:
                    alive[q] = False
                    events.append({"t": t, "kind": "pocket", "a": int(q), "speed": float(np.linalg.norm(v[q]))})
                    v[q] = 0
                    p[q] = (99 + q, 99)
                    break
    return events, t


def main(out):
    sounds = os.path.join(out, "sounds")
    d = os.path.join(out, "break_renders")
    os.makedirs(d, exist_ok=True)
    banks = {b: load_bank(sounds, b) for b in ("hybrid", "recorded", "synth")}
    summary = {}
    fig, axes = plt.subplots(5, 1, figsize=(14, 13))
    for row, (power, seed) in enumerate(((0.35, 1), (0.55, 2), (0.75, 3), (0.9, 4), (1.0, 5))):
        events, dur = simulate(power, seed)
        with open(os.path.join(d, f"events_power{int(power * 100):03d}.json"), "w") as fh:
            json.dump(events, fh)
        hits = [e for e in events if e["kind"] == "ball"]
        summary[power] = {
            "cue_speed": round(events[0]["speed"], 2),
            "ball_contacts": len(hits),
            "contacts_first_50ms": sum(1 for e in hits if e["t"] < 0.05 + hits[0]["t"]) if hits else 0,
            "cushion_hits": sum(1 for e in events if e["kind"] == "cushion"),
            "pocketed": sum(1 for e in events if e["kind"] == "pocket"),
            "sim_seconds": round(dur, 2),
        }
        for bank_name, bank in banks.items():
            m = Mixer(bank, seed=seed)
            m.run([e for e in events if e["kind"] != "pocket"])
            y = m.render()
            name = f"break_power{int(power * 100):03d}_{bank_name}"
            sf.write(os.path.join(d, name + ".wav"), y.astype(np.float32), SR, subtype="PCM_16")
            sf.write(os.path.join(d, name + ".ogg"), y.astype(np.float32), SR, format="OGG", subtype="VORBIS")
            summary[power][f"voices_{bank_name}"] = len(m.played)
            if bank_name == "hybrid":
                ax = axes[row]
                tt = np.arange(len(y)) / SR
                ax.plot(tt, y, lw=0.3, color="0.3")
                for e in events:
                    if e["kind"] == "ball":
                        ax.plot(e["t"], -1.05, "|", color="tab:orange", ms=6)
                    elif e["kind"] == "cushion":
                        ax.plot(e["t"], -1.15, "|", color="tab:blue", ms=6)
                for pl in m.played:
                    ax.plot(pl[0], 1.05, "|", color="tab:red" if pl[1] == "cluster" else "tab:green", ms=6)
                ax.set_xlim(0, min(dur, 4))
                ax.set_ylim(-1.25, 1.15)
                ax.set_title(
                    f"power {power:.0%}: {len(hits)} ball contacts -> {len(m.played)} voices "
                    "(green=individual, red=cluster; orange=ball events, blue=cushion events)",
                    fontsize=9,
                )
        # naive: every event played, no budget/chatter/guard (to hear the difference)
        if power == 1.0:
            m = Mixer(banks["hybrid"], seed=seed, mechanism=False)
            m.run([e for e in events if e["kind"] != "pocket"])
            y = m.render()
            sf.write(os.path.join(d, "break_power100_NAIVE_every_event.wav"), y.astype(np.float32), SR, subtype="PCM_16")
            summary[power]["voices_naive"] = len(m.played)
        print(power, summary[power])
    plt.tight_layout()
    plt.savefig(os.path.join(d, "break_overview.png"), dpi=65)
    with open(os.path.join(d, "summary.json"), "w") as fh:
        json.dump(summary, fh, indent=1)


if __name__ == "__main__":
    main(sys.argv[1])
