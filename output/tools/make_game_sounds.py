"""Build output/ambient-sounds/: match flow, scoring, results, economy, the ball machine's
winning-ball reveals (one per rarity) and ambience loops.

All one-shots are synthesized from billiards materials (uisynth.py). The pool-hall loops
are cut from the CC0 recording 4.1_68218 (damien bazin, Freesound) in ball-hit-sounds/.

usage: python make_game_sounds.py <output_dir> <ball-hit-sounds dir>
"""

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import uisynth as U  # noqa: E402
from make_ui_sounds import render  # noqa: E402

SPECS = []
FOLDER = "ambient-sounds"


def sound(group, name, variants=1, target=-16.0, desc="", loop=None):
    def deco(fn):
        SPECS.append(dict(group=group, name=name, variants=variants, target=target, desc=desc, loop=loop, fn=fn,
                          stereo=True))
        return fn

    return deco


def arp(m, notes, t0, step, rng, vel=(0.6, 0.8), gain=0.75, spread=0.5, decay=None):
    n = len(notes)
    for i, note in enumerate(notes):
        u = i / max(n - 1, 1)
        m.add(U.clack_tone(note, rng, vel[0] + (vel[1] - vel[0]) * u, decay=decay), t0 + step * i, gain,
              -spread + 2 * spread * u)


# ================================================================== match flow
@sound("match", "match_found", 1, -15, "Opponent found: whoosh in, rising arpeggio, a ball clack accent.")
def match_found(rng, v):
    m = U.Mix(stereo=True)
    m.add(U.whoosh(0.35, rng, 400, 3000, 0.8), 0, 0.4)
    arp(m, ["C5", "E5", "G5", "C6"], 0.3, 0.06, rng)
    m.add(U.clack(0.7, rng), 0.3, 0.5)
    m.add(U.bell("C7", rng, 0.9, 0.4), 0.48, 0.18, 0.3)
    return U.reverb(m.y, rng, 1.0, 0.18)


@sound("match", "countdown_tick", 1, -17, "3... 2... 1...: a cue-butt knock with a short tone.")
def countdown_tick(rng, v):
    m = U.Mix(stereo=True)
    m.add(U.wood_knock(900, rng, q=12, decay=0.03, k=0.8), 0, 0.8)
    m.add(U.clack_tone("G5", rng, 0.6, decay=0.12, click=0.3), 0.002, 0.6)
    return U.reverb(m.y, rng, 0.6, 0.1)


@sound("match", "countdown_go", 1, -13, "GO!: the break (cue strike into the pack), a bright chord and a low thump.")
def countdown_go(rng, v):
    m = U.Mix(stereo=True)
    m.add(U.crash(rng, 10, 0.05, 0.9, cue=True), 0, 1.0)
    for note, p in (("C5", -0.3), ("E5", 0.0), ("G5", 0.3), ("C6", 0.1)):
        m.add(U.clack_tone(note, rng, 0.75, decay=0.3), 0.012, 0.5, p)
    m.add(U.brass(["C4", "G4", "C5", "E5"], 0.55, rng, release=0.3), 0.012, 0.45)
    m.add(U.sub_boom(rng, 0.6, 80, 42, 0.06, 0.2), 0.012, 0.4)
    return U.reverb(m.y, rng, 1.2, 0.16)


@sound("match", "round_start", 1, -13, "Round starts: chalking up, a rising whoosh, then the break with a short brass stab.")
def round_start(rng, v):
    m = U.Mix(stereo=True)
    m.add(U.chalk_twist(0.18, rng), 0, 0.3)
    m.add(U.whoosh(0.45, rng, 300, 4000, 0.95), 0.15, 0.45)
    t0 = 0.6
    m.add(U.crash(rng, 12, 0.06, 0.92, cue=True), t0, 1.0)
    m.add(U.sub_boom(rng, 0.7, 80, 40), t0, 0.5)
    m.add(U.brass(["C4", "G4", "C5", "E5"], 0.7, rng, release=0.4), t0 + 0.02, 0.45)
    arp(m, ["C6", "E6", "G6"], t0 + 0.03, 0.04, rng, gain=0.5, decay=0.25)
    return U.reverb(m.y, rng, 1.3, 0.18)


@sound("match", "round_end", 1, -16, "Round over: a ball rolls to a stop and drops; falling tones over a soft chord.")
def round_end(rng, v):
    m = U.Mix(stereo=True)
    m.add(U.fade(U.roll(1.0, rng, 0.8, 0.15, surface=(250, 900), rumble=(60, 200), ticks=0.1), 0.05, 0.1), 0, 0.3)
    m.add(U.pocket_drop(rng, 0.6), 0.85, 0.8)
    for i, note in enumerate(["G5", "E5", "C5"]):
        m.add(U.clack_tone(note, rng, 0.65, decay=0.3), 0.9 + 0.15 * i, 0.7, 0.3 - 0.3 * i)
    m.add(U.pad(["C4", "E4", "G4"], 1.6, rng, attack=0.1, release=0.9, cut=(500, 1800)), 0.9, 0.35)
    return U.reverb(m.y, rng, 1.4, 0.2)


@sound("match", "turn_yours", 1, -17, "It's your shot: two bright rising clack tones and a chalk accent.")
def turn_yours(rng, v):
    m = U.Mix(stereo=True)
    m.add(U.chalk_twist(0.06, rng), 0, 0.2)
    m.add(U.clack_tone("G5", rng, 0.7, decay=0.2), 0.04, 0.8, -0.2)
    m.add(U.clack_tone("D6", rng, 0.8, decay=0.25), 0.12, 0.9, 0.2)
    m.add(U.bell("D7", rng, 0.7, 0.4), 0.12, 0.1, 0.4)
    return U.reverb(m.y, rng, 0.8, 0.12)


@sound("match", "turn_opponent", 1, -21, "Opponent's shot: softer, falling clack tones.")
def turn_opponent(rng, v):
    m = U.Mix(stereo=True)
    m.add(U.lp(U.clack_tone("E5", rng, 0.55, decay=0.2), 4000), 0, 0.8, 0.15)
    m.add(U.lp(U.clack_tone("B4", rng, 0.5, decay=0.25), 4000), 0.09, 0.75, -0.15)
    m.add(U.felt(0.3, rng), 0.09, 0.25)
    return U.reverb(m.y, rng, 0.8, 0.12)


@sound("match", "shot_clock_tick", 2, -22, "Shot clock tick / tock (cue butt on the floor).")
def shot_clock_tick(rng, v):
    return U.to_stereo(U.wood_knock([1100, 900][v], rng, q=14, decay=0.015, k=0.6))


@sound("match", "shot_clock_warning", 1, -18, "Last seconds on the shot clock: quick double knock and a high tone.")
def shot_clock_warning(rng, v):
    m = U.Mix(stereo=True)
    m.add(U.wood_knock(1400, rng, q=14, decay=0.015, k=0.8), 0, 0.8)
    m.add(U.wood_knock(1400, rng, q=14, decay=0.015, k=0.7), 0.07, 0.7)
    m.add(U.clack_tone("E6", rng, 0.6, decay=0.1, click=0.2), 0.07, 0.5)
    return m.y


@sound("match", "shot_clock_expired", 1, -15, "Time's up: a miscue, a low clashing pair of tones, a dull thud.")
def shot_clock_expired(rng, v):
    m = U.Mix(stereo=True)
    m.add(U.miscue(rng), 0, 0.7)
    m.add(U.clack_tone("C4", rng, 0.7, decay=0.25, click=0.3), 0.05, 0.6, -0.2)
    m.add(U.clack_tone("Db4", rng, 0.7, decay=0.25, click=0.3), 0.05, 0.55, 0.2)
    m.add(U.wood_knock(160, rng, q=6, decay=0.06, k=0.8), 0.05, 0.6)
    m.add(U.felt(0.7, rng), 0.05, 0.5)
    return U.reverb(m.y, rng, 0.9, 0.12)


# ================================================================== scoring
@sound("scoring", "score_pot", 3, -16, "A ball is potted: drops into the leather pocket, a bright tone and a little shine.")
def score_pot(rng, v):
    m = U.Mix(stereo=True)
    m.add(U.pocket_drop(rng, 0.8), 0, 0.9)
    m.add(U.clack_tone(["E6", "D6", "G6"][v], rng, 0.7, decay=0.3), 0.02, 0.7, 0.1)
    m.add(U.bell(["E7", "D7", "G7"][v], rng, 0.9, 0.4), 0.02, 0.15, 0.35)
    m.add(U.glitter(0.35, rng, 40), 0.03, 0.08)
    return U.reverb(m.y, rng, 0.9, 0.15)


COMBO = ["C6", "D6", "E6", "G6", "C7"]
for _n in range(1, 6):

    def _combo(rng, v, n=_n):
        m = U.Mix(stereo=True)
        m.add(U.pocket_drop(rng, 0.8), 0, 0.9)
        m.add(U.clack_tone(COMBO[n - 1], rng, 0.75, decay=0.32), 0.02, 0.75)
        if n >= 3:
            for note, p in (("C5", -0.4), ("E5", 0.0), ("G5", 0.4)):
                m.add(U.clack_tone(note, rng, 0.55, decay=0.3), 0.02, 0.35, p)
        if n >= 4:
            m.add(U.brass(["C4", "G4", "C5", "E5"], 0.5, rng, release=0.3), 0.02, 0.35)
        if n >= 5:
            m.add(U.sparkle(rng, 0.9, ["C7", "E7", "G7"], 8, bright=0.55), 0.05, 0.3)
            m.add(U.sub_boom(rng, 0.5, 75, 42, 0.06, 0.15), 0.0, 0.3)
        m.add(U.bell(COMBO[n - 1][:-1] + str(int(COMBO[n - 1][-1]) + 1), rng, 0.9, 0.4), 0.02, 0.12, 0.3)
        return U.reverb(m.y, rng, 1.0 + 0.1 * n, 0.15 + 0.01 * n)

    sound("scoring", f"score_combo_{_n}", 1, -16 + 0.5 * _n,
          f"Pot number {_n} in a row: the tone climbs ({COMBO[_n - 1]}); from 3 a chord, 4 brass, 5 sparkle.")(_combo)


@sound("scoring", "score_eight_ball", 1, -13, "The 8-ball goes down: deep thump, minor chord resolving to major, rising arpeggio.")
def score_eight_ball(rng, v):
    m = U.Mix(stereo=True)
    m.add(U.pocket_drop(rng, 0.95), 0, 1.0)
    m.add(U.sub_boom(rng, 1.0, 85, 36), 0, 0.55)
    m.add(U.pad(["A3", "C4", "E4"], 0.5, rng, attack=0.02, release=0.2, cut=(600, 2400)), 0.0, 0.35)
    m.add(U.brass(["C4", "E4", "G4", "C5"], 1.4, rng, release=0.9, decay=0.5), 0.45, 0.5)
    arp(m, ["C6", "E6", "G6"], 0.47, 0.06, rng, gain=0.6)
    m.add(U.sparkle(rng, 1.0, ["C7", "E7", "G7"], 7), 0.5, 0.25)
    return U.reverb(m.y, rng, 1.6, 0.22)


@sound("scoring", "foul", 1, -16, "Foul / scratch: the cue ball drops, falling tones end in a low 'womp', dull knocks.")
def foul(rng, v):
    m = U.Mix(stereo=True)
    m.add(U.pocket_drop(rng, 0.6), 0, 0.7)
    m.add(U.clack_tone("Bb4", rng, 0.6, decay=0.15), 0.05, 0.6, 0.2)
    m.add(U.clack_tone("A4", rng, 0.6, decay=0.15), 0.2, 0.6, 0.0)
    m.add(U.clack_tone("E3", rng, 0.75, decay=0.35, click=0.2), 0.4, 0.8, -0.2)
    m.add(U.wood_knock(160, rng, q=6, decay=0.05, k=0.7), 0.2, 0.5)
    m.add(U.wood_knock(140, rng, q=6, decay=0.05, k=0.7), 0.4, 0.5)
    return U.reverb(m.y, rng, 0.9, 0.12)


@sound("scoring", "trick_shot", 1, -15, "Bank / trick shot bonus: cushion, clack, a fast rising run and some shine.")
def trick_shot(rng, v):
    m = U.Mix(stereo=True)
    m.add(U.cushion(0.8, rng), 0, 0.7, -0.4)
    m.add(U.clack(0.8, rng), 0.08, 0.8, 0.2)
    arp(m, ["G5", "B5", "D6", "G6"], 0.1, 0.045, rng, gain=0.65)
    m.add(U.glitter(0.6, rng, 70), 0.25, 0.15)
    return U.reverb(m.y, rng, 1.1, 0.16)


# ================================================================== results
@sound("results", "win", 1, -13, "Match won (about 3 s): break, I-IV-V-I brass fanfare, melody, sparkle and a choir pad.")
def win(rng, v):
    m = U.Mix(stereo=True)
    m.add(U.crash(rng, 6, 0.04, 0.8, cue=True), 0, 0.8)
    chords = [(0.05, ["C4", "E4", "G4", "C5"], 0.35), (0.45, ["F4", "A4", "C5", "F5"], 0.35),
              (0.85, ["G4", "B4", "D5", "G5"], 0.3), (1.2, ["C4", "E4", "G4", "C5", "E5"], 1.8)]
    for t0, ch, d in chords:
        m.add(U.brass(ch, d, rng, release=min(1.2, d * 0.6), decay=0.3 if d < 1 else 0.7), t0, 0.5)
    for t0, note in ((0.05, "C5"), (0.25, "E5"), (0.45, "G5"), (0.65, "A5"), (0.85, "G5"), (1.2, "C6")):
        m.add(U.clack_tone(note, rng, 0.75, decay=0.45 if note == "C6" else 0.22), t0, 0.75, 0.1)
    m.add(U.sub_boom(rng, 0.8, 80, 40), 1.2, 0.45)
    m.add(U.sparkle(rng, 1.4, ["C6", "E6", "G6", "C7"], 10), 1.25, 0.35)
    m.add(U.pad(["C4", "G4", "C5", "E5"], 1.8, rng, attack=0.15, release=1.1, cut=(600, 2600), choir=True), 1.2, 0.3)
    return U.reverb(m.y, rng, 1.8, 0.22)


@sound("results", "lose", 1, -16, "Match lost (about 2.5 s): a ball rattles in the jaws and stays out; falling tones over D minor.")
def lose(rng, v):
    m = U.Mix(stereo=True)
    m.add(U.clack(0.5, rng), 0, 0.6, 0.3)
    m.add(U.cushion(0.5, rng), 0.08, 0.6, 0.4)
    m.add(U.clack(0.3, rng), 0.16, 0.45, 0.35)
    m.add(U.fade(U.roll(0.35, rng, 0.4, 0.05, surface=(250, 900), ticks=0.1), 0.02, 0.15), 0.18, 0.25, 0.3)
    for t0, note in ((0.45, "A4"), (0.75, "F4"), (1.05, "D4")):
        m.add(U.clack_tone(note, rng, 0.65, decay=0.3), t0, 0.7)
    m.add(U.clack_tone("A3", rng, 0.7, decay=0.5, click=0.25), 1.4, 0.75)
    m.add(U.pad(["D3", "F3", "A3"], 1.9, rng, attack=0.2, release=1.0, cut=(400, 1200)), 0.45, 0.35)
    m.add(U.felt(0.5, rng), 1.4, 0.4)
    return U.reverb(m.y, rng, 1.5, 0.2)


@sound("results", "win_short", 1, -14, "Round won / short victory (about 1.2 s).")
def win_short(rng, v):
    m = U.Mix(stereo=True)
    arp(m, ["C5", "E5", "G5", "C6"], 0, 0.07, rng, gain=0.75)
    m.add(U.brass(["C4", "E4", "G4", "C5"], 0.7, rng, release=0.4), 0.21, 0.45)
    m.add(U.sparkle(rng, 0.7, ["C7", "E7", "G7"], 4), 0.22, 0.25)
    return U.reverb(m.y, rng, 1.2, 0.18)


@sound("results", "lose_short", 1, -17, "Round lost / short defeat (about 1 s).")
def lose_short(rng, v):
    m = U.Mix(stereo=True)
    for i, note in enumerate(["E4", "C4", "A3"]):
        m.add(U.clack_tone(note, rng, 0.6, decay=0.25), 0.12 * i, 0.7)
    m.add(U.pad(["A3", "C4", "E4"], 0.9, rng, attack=0.05, release=0.5, cut=(400, 1100)), 0.0, 0.3)
    m.add(U.felt(0.4, rng), 0.24, 0.35)
    return U.reverb(m.y, rng, 1.0, 0.15)


@sound("results", "draw", 1, -17, "Draw: an open fifth knocked twice, neither up nor down.")
def draw(rng, v):
    m = U.Mix(stereo=True)
    for t0 in (0.0, 0.18):
        m.add(U.clack_tone("C5", rng, 0.6, decay=0.3), t0, 0.6, -0.2)
        m.add(U.clack_tone("G5", rng, 0.6, decay=0.3), t0, 0.55, 0.2)
    m.add(U.pad(["C4", "G4", "D5"], 1.0, rng, attack=0.05, release=0.6, cut=(500, 1600)), 0.18, 0.25)
    return U.reverb(m.y, rng, 1.0, 0.15)


# ================================================================== economy
@sound("economy", "buy", 2, -15, "Purchase made: tokens clink, drop into a pocket, two bright tones and a glint.")
def buy(rng, v):
    m = U.Mix(stereo=True)
    m.add(U.token_clink(rng, 3000, 0.7, 0.08), 0, 0.5, -0.2)
    m.add(U.token_clink(rng, 2500, 0.6, 0.08), 0.04, 0.4, 0.2)
    m.add(U.pocket_drop(rng, 0.6), 0.08, 0.7)
    m.add(U.clack_tone(["G5", "E5"][v], rng, 0.7, decay=0.2), 0.1, 0.7)
    m.add(U.clack_tone(["C6", "A5"][v], rng, 0.8, decay=0.3), 0.18, 0.8)
    m.add(U.bell("C7", rng, 0.8, 0.4), 0.18, 0.15, 0.3)
    m.add(U.glitter(0.4, rng, 50), 0.18, 0.12)
    return U.reverb(m.y, rng, 0.9, 0.14)


@sound("economy", "buy_fail", 1, -18, "Can't afford it: two dull knocks and a muted falling semitone.")
def buy_fail(rng, v):
    m = U.Mix(stereo=True)
    m.add(U.wood_knock(200, rng, q=6, decay=0.05, k=0.7), 0, 0.7)
    m.add(U.wood_knock(185, rng, q=6, decay=0.05, k=0.6), 0.1, 0.6)
    m.add(U.lp(U.clack_tone("C5", rng, 0.55, decay=0.12), 3000), 0, 0.6)
    m.add(U.lp(U.clack_tone("B4", rng, 0.55, decay=0.15), 3000), 0.1, 0.6)
    return m.y


@sound("economy", "coins_gain", 1, -15, "Reward / coins collected: a shower of tokens and a fast rising run.")
def coins_gain(rng, v):
    m = U.Mix(stereo=True)
    for i in range(9):
        t0 = 0.5 * (i / 9) ** 1.3 + rng.uniform(0, 0.02)
        m.add(U.token_clink(rng, rng.uniform(2600, 3600), 0.7, 0.07), t0, 0.35 * (0.92**i), rng.uniform(-0.6, 0.6))
    arp(m, ["C5", "D5", "E5", "G5", "A5", "C6"], 0.05, 0.06, rng, gain=0.6, decay=0.2)
    m.add(U.glitter(0.8, rng, 70), 0.1, 0.15)
    return U.reverb(m.y, rng, 1.0, 0.15)


@sound("economy", "coins_count_loop", 1, -22, "Seamless 0.6 s loop of coin ticks for a counter animation.", loop=0.6)
def coins_count_loop(rng, v):
    m = U.Mix(stereo=True)
    for i in range(12):
        m.add(U.token_clink(rng, rng.uniform(3200, 3900), 0.5, 0.03), i * 0.05, rng.uniform(0.6, 1.0), rng.uniform(-0.3, 0.3))
    return U.loop_fold(m.y, 0.6)


@sound("economy", "level_up", 1, -13, "Level up (about 2 s): riser into a break hit, brass chord, two-octave arpeggio, sparkle.")
def level_up(rng, v):
    m = U.Mix(stereo=True)
    m.add(U.riser(0.8, rng, "C4", "C5"), 0, 0.45)
    t0 = 0.8
    m.add(U.crash(rng, 8, 0.04, 0.85), t0, 0.8)
    m.add(U.sub_boom(rng, 0.8, 85, 38), t0, 0.45)
    m.add(U.brass(["C4", "E4", "G4", "C5", "E5"], 1.3, rng, release=0.9, decay=0.6), t0 + 0.01, 0.5)
    arp(m, ["C5", "E5", "G5", "C6", "E6", "G6", "C7"], t0 + 0.02, 0.04, rng, gain=0.55, spread=0.7)
    m.add(U.sparkle(rng, 1.2, ["C7", "E7", "G7"], 9), t0 + 0.2, 0.3)
    m.add(U.glitter(1.0, rng, 70), t0 + 0.1, 0.12)
    return U.reverb(m.y, rng, 1.8, 0.22)


@sound("economy", "achievement_unlock", 1, -14, "Achievement / unlock: rising clack tones, bells and a soft add9 pad.")
def achievement_unlock(rng, v):
    m = U.Mix(stereo=True)
    for t0, note in ((0.0, "G5"), (0.1, "C6"), (0.2, "E6")):
        m.add(U.clack_tone(note, rng, 0.75, decay=0.3), t0, 0.7, -0.2 + t0 * 2)
    m.add(U.bell("G6", rng, 1.2, 0.5), 0.2, 0.2, -0.3)
    m.add(U.bell("E7", rng, 1.2, 0.5), 0.2, 0.15, 0.3)
    m.add(U.pad(["C4", "G4", "D5", "E5"], 1.4, rng, attack=0.08, release=0.9, cut=(600, 2800)), 0.2, 0.3)
    m.add(U.sparkle(rng, 0.9, ["C7", "E7", "G7", "D7"], 6), 0.25, 0.25)
    return U.reverb(m.y, rng, 1.5, 0.2)


# ================================================================== machine reveal (the winning ball)
@sound("machine_reveal", "reveal_anticipation", 1, -21, "Build-up before the ball is shown (1.4 s, ends at its peak).")
def reveal_anticipation(rng, v):
    dur = 1.4
    m = U.Mix(stereo=True)
    m.add(U.riser(dur, rng, "G3", "G5"), 0, 0.6)
    t, gap = 0.0, 0.17
    while t < dur - 0.03:  # clacks speeding up, like balls jostling in the globe
        m.add(U.tick(0.2 + 0.4 * t / dur, rng, 1200), t, 0.25 + 0.3 * t / dur, rng.uniform(-0.5, 0.5))
        t += gap
        gap = max(gap * 0.85, 0.03)
    m.add(U.reverse_swell(0.6, rng), dur - 0.6, 0.3)
    return m.y


@sound("machine_reveal", "reveal_common", 1, -16, "Common ball: a plain clack and an open fifth.")
def reveal_common(rng, v):
    m = U.Mix(stereo=True)
    m.add(U.clack(0.5, rng), 0, 0.6)
    m.add(U.felt(0.4, rng), 0, 0.4)
    m.add(U.clack_tone("C5", rng, 0.6, decay=0.3), 0.015, 0.7, -0.15)
    m.add(U.clack_tone("G5", rng, 0.5, decay=0.25), 0.015, 0.55, 0.15)
    return U.reverb(m.y, rng, 0.8, 0.12)


@sound("machine_reveal", "reveal_uncommon", 1, -15.5, "Uncommon ball: a rising three-note arpeggio with a faint bell.")
def reveal_uncommon(rng, v):
    m = U.Mix(stereo=True)
    m.add(U.clack(0.6, rng), 0, 0.6)
    m.add(U.felt(0.45, rng), 0, 0.4)
    arp(m, ["E5", "G5", "C6"], 0.015, 0.08, rng, gain=0.75, spread=0.2, decay=0.3)
    m.add(U.bell("C7", rng, 1.0, 0.4), 0.18, 0.12, 0.3)
    return U.reverb(m.y, rng, 1.0, 0.15)


@sound("machine_reveal", "reveal_rare", 1, -15, "Rare ball: whoosh in, pocket thump, a Cmaj9 arpeggio over a soft pad, a few sparkles.")
def reveal_rare(rng, v):
    m = U.Mix(stereo=True)
    m.add(U.whoosh(0.25, rng, 600, 3500, 0.85), 0, 0.35)
    t0 = 0.22
    m.add(U.clack(0.75, rng), t0, 0.8)
    m.add(U.pocket_drop(rng, 0.7, rattle=False), t0, 0.5)
    m.add(U.sub_boom(rng, 0.5, 70, 45, 0.06, 0.15), t0, 0.25)
    arp(m, ["C5", "E5", "G5", "B5", "D6"], t0 + 0.015, 0.06, rng, gain=0.7, spread=0.4, decay=0.35)
    m.add(U.pad(["C4", "E4", "G4", "B4"], 1.6, rng, attack=0.08, release=1.0, cut=(500, 2400)), t0, 0.3)
    m.add(U.sparkle(rng, 0.8, ["E6", "B6", "G6", "D7"], 5, bright=0.5), t0 + 0.25, 0.25)
    return U.reverb(m.y, rng, 1.4, 0.2)


@sound("machine_reveal", "reveal_epic", 1, -14, "Epic ball: riser, a break hit, Ab-to-C brass, a fast nine-note run, choir and sparkles.")
def reveal_epic(rng, v):
    m = U.Mix(stereo=True)
    m.add(U.riser(0.4, rng, "G3", "G4"), 0, 0.35)
    t0 = 0.38
    m.add(U.crash(rng, 8, 0.04, 0.85), t0, 0.8)
    m.add(U.sub_boom(rng, 0.8, 85, 38), t0, 0.5)
    m.add(U.brass(["Ab3", "C4", "Eb4", "Ab4"], 0.45, rng, release=0.15), t0, 0.45)
    m.add(U.brass(["C4", "E4", "G4", "C5", "E5"], 1.8, rng, release=1.2, decay=0.6), t0 + 0.42, 0.5)
    arp(m, ["C5", "D5", "E5", "G5", "A5", "C6", "D6", "E6", "G6"], t0 + 0.02, 0.035, rng, gain=0.6, spread=0.6, decay=0.25)
    m.add(U.sparkle(rng, 1.2, ["C7", "E7", "G7", "D7"], 8, bright=0.55), t0 + 0.4, 0.3)
    m.add(U.pad(["C4", "G4", "E5"], 2.0, rng, attack=0.2, release=1.2, cut=(600, 3000), choir=True), t0 + 0.4, 0.25)
    return U.reverb(m.y, rng, 1.8, 0.24)


@sound("machine_reveal", "reveal_legendary", 1, -13, "Legendary ball: clacks speeding up into a big break, 'da-da-DAA' brass fanfare, choir, gold shimmer.")
def reveal_legendary(rng, v):
    m = U.Mix(stereo=True)
    pre = 0.6
    m.add(U.riser(pre, rng, "C4", "C5"), 0, 0.4)
    m.add(U.reverse_swell(pre, rng), 0, 0.35)
    tt, gap = 0.0, 0.16
    while tt < pre - 0.04:
        m.add(U.clack(0.3 + 0.5 * tt / pre, rng), tt, 0.35, rng.uniform(-0.4, 0.4))
        tt += gap
        gap *= 0.72
    t0 = pre
    m.add(U.crash(rng, 12, 0.05, 0.95, cue=True), t0, 0.9)
    m.add(U.sub_boom(rng, 1.2, 90, 34, 0.1, 0.45), t0, 0.6)
    m.add(U.bell("C7", rng, 1.6, 0.6), t0, 0.25, 0.2)
    m.add(U.brass(["C4", "E4", "G4", "C5"], 0.22, rng, release=0.08), t0 + 0.02, 0.5)
    m.add(U.brass(["D4", "G4", "B4", "D5"], 0.22, rng, release=0.08), t0 + 0.26, 0.5)
    m.add(U.brass(["C4", "E4", "G4", "C5", "E5", "G5"], 2.4, rng, release=1.5, decay=0.8), t0 + 0.5, 0.55)
    m.add(U.pad(["C3", "G3", "C4", "E4", "G4"], 2.6, rng, attack=0.3, release=1.4, cut=(500, 2600), choir=True), t0 + 0.45, 0.35)
    for t1, note in ((0.02, "G5"), (0.26, "B5"), (0.5, "C6"), (0.62, "E6"), (0.74, "G6"), (0.86, "C7")):
        m.add(U.clack_tone(note, rng, 0.75, decay=0.35), t0 + t1, 0.6, -0.3 + 0.6 * t1)
    m.add(U.sparkle(rng, 1.8, ["C7", "E7", "G7", "C8"], 12, bright=0.6), t0 + 0.5, 0.35)
    m.add(U.glitter(1.8, rng, 80), t0 + 0.5, 0.15)
    return U.reverb(m.y, rng, 2.2, 0.26)


@sound("machine_reveal", "reveal_mythic", 1, -12.5, "Mythic ball: heartbeat clacks, a huge break, an otherworldly Lydian chord opening to a wide C major, all 15 rack balls ringing up and down.")
def reveal_mythic(rng, v):
    m = U.Mix(stereo=True)
    pre = 1.0
    m.add(U.reverse_swell(pre, rng), 0, 0.45)
    m.add(U.riser(pre, rng, "F#3", "F#5"), 0, 0.35)
    tt, gap = 0.0, 0.3
    while tt < pre - 0.05:  # two balls kissing like a heartbeat, faster and faster
        k = 0.25 + 0.5 * tt / pre
        m.add(U.clack(k, rng), tt, 0.4, -0.3)
        m.add(U.clack(k * 0.7, rng), tt + 0.05, 0.3, 0.3)
        m.add(U.sub_boom(rng, 0.25, 70, 45, 0.04, 0.06), tt, 0.25)
        tt += gap
        gap *= 0.7
    t0 = pre
    m.add(U.crash(rng, 16, 0.06, 1.0, cue=True), t0, 1.0)
    m.add(U.sub_boom(rng, 1.8, 75, 28, 0.12, 0.7), t0, 0.75)
    t = U.taxis(2.0)
    m.add(U.norm(U.hp(U.white(2.0, rng, 2), 4000) * np.exp(-t / 0.5)[:, None]), t0, 0.22)
    m.add(U.pad(["C3", "G3", "E4", "F#4", "B4"], 1.2, rng, attack=0.04, release=0.5, cut=(600, 3500), choir=True), t0, 0.4)
    m.add(U.brass(["C3", "C4", "E4", "G4", "C5", "E5", "G5"], 3.0, rng, release=2.0, decay=1.0, cut=(500, 5000)), t0 + 0.9, 0.5)
    m.add(U.pad(["C4", "E4", "G4", "B4", "D5"], 3.4, rng, attack=0.5, release=2.0, cut=(700, 3800), voices=7, detune=18), t0 + 0.6, 0.35)
    rack = ["C5", "D5", "E5", "G5", "A5", "C6", "D6", "E6", "G6", "A6", "C7", "D7", "E7", "G7", "A7"]  # 15 balls
    arp(m, rack, t0 + 0.03, 0.03, rng, vel=(0.5, 0.92), gain=0.5, spread=0.8, decay=0.3)
    arp(m, list(reversed(rack[:10])), t0 + 0.6, 0.035, rng, vel=(0.55, 0.5), gain=0.35, spread=-0.8, decay=0.25)
    m.add(U.sparkle(rng, 2.5, ["C7", "E7", "G7", "B7", "D7", "F#7"], 20, bright=0.6), t0 + 0.3, 0.35)
    m.add(U.glitter(2.6, rng, 90), t0 + 0.3, 0.18)
    m.add(U.bell("C6", rng, 3.0, 0.5), t0 + 0.9, 0.2)
    return U.reverb(m.y, rng, 3.0, 0.3)


@sound("machine_reveal", "ball_won", 1, -15, "Short generic 'you got a ball' (for lists, repeats, or when the reveal is skipped).")
def ball_won(rng, v):
    m = U.Mix(stereo=True)
    m.add(U.pocket_drop(rng, 0.7), 0, 0.7)
    for note, p in (("C5", -0.3), ("E5", 0.0), ("G5", 0.3)):
        m.add(U.clack_tone(note, rng, 0.65, decay=0.3), 0.02, 0.5, p)
    m.add(U.clack_tone("C6", rng, 0.8, decay=0.35), 0.14, 0.75)
    m.add(U.sparkle(rng, 0.6, ["C7", "E7", "G7"], 4), 0.15, 0.2)
    return U.reverb(m.y, rng, 1.0, 0.15)


# ================================================================== ambience loops
@sound("loops", "lobby_room_tone_loop", 1, -36, "Seamless 40 s synthetic room tone with distant, reverberant ball clacks (licence-free).", loop=40.0)
def lobby_room_tone_loop(rng, v):
    L = 40.0
    bed = U.lp(U.pink(L + 1.0, rng, 2), 700) * 0.25
    bed = U.loop_xfade(bed, L, 1.0)
    ev = U.Mix(stereo=True)
    t = rng.uniform(0.3, 1.5)
    while t < L:
        k = rng.uniform(0.2, 0.8)
        hit = U.crash(rng, int(rng.integers(2, 5)), 0.08, k) if rng.uniform() < 0.2 else U.clack(k, rng)
        ev.add(U.lp(hit, 3000), t, 0.5 * k, rng.uniform(-0.7, 0.7))
        t += rng.uniform(0.6, 3.0)
    room = U.reverb(ev.y, rng, 1.6, 1.0, predelay=0.03, bright=3500)  # dry + equal wet: far away
    return bed + U.loop_fold(0.3 * room, L)


HALL = "4.1_68218__damien-bazin__lyon-ambience-salle-de-billard.mp3"


def hall_loops(src_dir, out_dir, length=60.0, xf=2.0):
    """Cut the steadiest stretch of the CC0 pool-hall recording into seamless loops."""
    import soundfile as sf
    from scipy import signal

    x, sr = sf.read(os.path.join(src_dir, HALL), always_2d=True)
    x = signal.resample_poly(x, U.SR, sr, axis=0) if sr != U.SR else x
    k = U.k_weight(x)
    p = (k**2).sum(axis=1)
    sec = U.SR
    frames = np.array([10 * np.log10(p[i : i + sec // 4].mean() + 1e-12) for i in range(0, len(p) - sec // 4, sec // 4)])
    need = int((length + xf) * 4)
    best, best_score = 0, 1e9
    for s in range(0, len(frames) - need, 4):
        f = frames[s : s + need]
        score = f.std() + 0.5 * max(0, f.max() - np.median(f) - 8)  # steady, no big bursts
        if score < best_score:
            best, best_score = s, score
    start = best * sec // 4
    seg = x[start : start + U.ns(length + xf)]
    loop = U.loop_xfade(seg, length, xf)
    near = U.master_loop_level(loop, -26.0, win=3.0)
    far = U.master_loop_level(U.lp(U.lp(loop, 1500), 1500), -32.0, win=3.0)
    entries = []
    for name, y, desc in (("pool_hall_ambience_loop", near, "Seamless 60 s pool-hall ambience (CC0 recording, Lyon)."),
                          ("pool_hall_ambience_distant_loop", far, "The same hall, muffled and quieter: for menus and the lobby.")):
        rel = f"loops/{name}"
        U.save(os.path.join(out_dir, FOLDER, rel), y)
        q = U.qa(y)
        q["limited_db"] = 0.0
        entries.append({"name": name, "group": "loops", "variants": 1, "loop": True, "channels": 2, "target": None,
                        "description": desc, "source": f"{HALL} (CC0, damien bazin, Freesound 68218), "
                        f"{start / U.SR:.1f}-{start / U.SR + length:.1f} s", "files": [{"file": rel, **q}]})
        print(f"loops        {name:32s} {q['dur_s']:6.2f}s  loud {q['loud']:6.1f}  from {start / U.SR:.1f} s (steadiness {best_score:.2f})")
    return entries


def main(out, src):
    import shutil

    shutil.rmtree(os.path.join(out, FOLDER), ignore_errors=True)
    manifest = render(SPECS, out, FOLDER)
    manifest += hall_loops(src, out)
    with open(os.path.join(out, FOLDER, "manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=1)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
