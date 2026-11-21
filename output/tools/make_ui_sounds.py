"""Build output/ui-sounds/: buttons, navigation, the loadout rack and the ball machine.
Every sound is synthesized from billiards materials (uisynth.py); no third-party audio.

usage: python make_ui_sounds.py <output_dir>
writes <output_dir>/ui-sounds/<group>/<name>[_NN].wav|ogg and ui-sounds/manifest.json
"""

import json
import os
import sys
import zlib

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import uisynth as U  # noqa: E402

SPECS = []


def sound(group, name, variants=1, target=-20.0, desc="", loop=None, stereo=False):
    """Register a recipe. target = loudness (max momentary, LUFS-like); loop = seconds."""

    def deco(fn):
        SPECS.append(dict(group=group, name=name, variants=variants, target=target, desc=desc, loop=loop, fn=fn,
                          stereo=stereo))
        return fn

    return deco


PENTA = ["C5", "D5", "E5", "G5", "A5", "C6", "D6", "E6"]


# ================================================================== buttons
@sound("buttons", "button_hover", 3, -31, "Pointer enters a button: two balls barely touching.")
def button_hover(rng, v):
    return U.tick(rng.uniform(0.05, 0.1), rng, 2200)


@sound("buttons", "button_click", 4, -22, "Generic button press: a crisp ball clack with a little wood.")
def button_click(rng, v):
    m = U.Mix()
    m.add(U.clack(rng.uniform(0.45, 0.65), rng), 0, 1.0)
    m.add(U.wood_knock(rng.uniform(850, 1050), rng, q=10, decay=0.02, k=0.5), 0.0005, 0.25)
    return m.y


@sound("buttons", "button_confirm", 2, -19, "Confirm / OK / Play: cue tip taps the ball, two rising clack tones.")
def button_confirm(rng, v):
    m = U.Mix()
    m.add(U.cue_tap(0.45, rng), 0, 0.5)
    m.add(U.clack_tone(["G5", "A5"][v], rng, 0.6, click=0.5), 0.006, 0.8)
    m.add(U.clack_tone(["C6", "D6"][v], rng, 0.75, click=0.5), 0.07, 1.0)
    return m.y


@sound("buttons", "button_back", 2, -21, "Back / cancel / close: two falling clack tones onto the cloth.")
def button_back(rng, v):
    m = U.Mix()
    m.add(U.clack_tone(["E5", "D5"][v], rng, 0.6, click=0.5), 0, 0.9)
    m.add(U.clack_tone(["B4", "A4"][v], rng, 0.5, click=0.4), 0.06, 0.75)
    m.add(U.felt(0.3, rng), 0.06, 0.3)
    return m.y


@sound("buttons", "button_error", 2, -19, "Error / not allowed: a miscue (tip skids off the ball) and two dull knocks.")
def button_error(rng, v):
    m = U.Mix()
    m.add(U.miscue(rng), 0, 0.8)
    m.add(U.wood_knock(rng.uniform(170, 200), rng, q=6, decay=0.05, k=0.7), 0.06, 0.7)
    m.add(U.wood_knock(rng.uniform(150, 175), rng, q=6, decay=0.05, k=0.6), 0.17, 0.6)
    m.add(U.clack_tone("Bb3", rng, 0.5, decay=0.12, click=0.2), 0.06, 0.45)
    m.add(U.clack_tone("A3", rng, 0.5, decay=0.12, click=0.2), 0.17, 0.4)
    return m.y


@sound("buttons", "button_disabled", 1, -29, "Pressing a disabled button: a muted felt thud.")
def button_disabled(rng, v):
    return U.lp(U.felt(0.25, rng), 700)


@sound("buttons", "toggle_on", 1, -21, "Switch / checkbox on: short roll, ball clicks into place, small up-tone.")
def toggle_on(rng, v):
    m = U.Mix()
    m.add(U.roll(0.07, rng, 0.6, 0.9, surface=(500, 1600), ticks=0.1), 0, 0.25)
    m.add(U.clack(0.5, rng), 0.06, 1.0)
    m.add(U.clack_tone("G5", rng, 0.5, decay=0.08, click=0.3), 0.065, 0.5)
    return m.y


@sound("buttons", "toggle_off", 1, -22, "Switch / checkbox off: click, small down-tone, short roll away.")
def toggle_off(rng, v):
    m = U.Mix()
    m.add(U.clack(0.35, rng), 0, 0.9)
    m.add(U.clack_tone("D5", rng, 0.45, decay=0.08, click=0.3), 0.005, 0.45)
    m.add(U.roll(0.06, rng, 0.8, 0.4, surface=(400, 1300), ticks=0.1), 0.01, 0.2)
    return m.y


@sound("buttons", "select", 2, -21, "Select an item in a list or grid: clack plus a short tone.")
def select(rng, v):
    m = U.Mix()
    m.add(U.clack(0.5, rng), 0, 0.8)
    m.add(U.clack_tone(["G5", "A5"][v], rng, 0.55, decay=0.1, click=0.3), 0.003, 0.7)
    return m.y


for _i, _note in enumerate(PENTA):

    def _sel(rng, v, note=_note):
        return U.clack_tone(note, rng, 0.6, click=0.5)

    sound("buttons", f"select_note_{_i + 1}", 1, -21,
          f"Pitched select ({_note}); play 1..8 in order for steps, combos or a count-up.")(_sel)


@sound("buttons", "equip", 1, -20, "Equip a ball / cue: chalk twist on the tip, then a firm clack.")
def equip(rng, v):
    m = U.Mix()
    m.add(U.chalk_twist(0.12, rng), 0, 0.45)
    m.add(U.clack(0.55, rng), 0.11, 1.0)
    m.add(U.clack_tone("G5", rng, 0.5, decay=0.12, click=0.3), 0.115, 0.5)
    return m.y


@sound("buttons", "unequip", 1, -22, "Unequip: lighter clack, falling tone, brush away.")
def unequip(rng, v):
    m = U.Mix()
    m.add(U.clack(0.35, rng), 0, 0.8)
    m.add(U.clack_tone("D5", rng, 0.4, decay=0.1, click=0.3), 0.005, 0.4)
    m.add(U.felt_swish(0.1, rng, 2000, 700, 0.3), 0.01, 0.35)
    return m.y


@sound("buttons", "coin_tick", 3, -25, "One coin in a currency count-up (play rapidly, pitch up slightly).")
def coin_tick(rng, v):
    return U.token_clink(rng, f0=rng.uniform(3300, 3800), k=0.6, decay=0.035)


# ================================================================== navigation
@sound("navigation", "tab_switch", 3, -23, "Switch tab / page: quick brush and a light clack.")
def tab_switch(rng, v):
    m = U.Mix()
    m.add(U.felt_swish(0.05, rng, 1500, 4000, 0.3), 0, 0.35)
    m.add(U.tick(rng.uniform(0.25, 0.4), rng, 1200), 0.025, 1.0)
    return m.y


@sound("navigation", "menu_open", 1, -20, "Open a menu / panel: cue stroke whoosh, lands on the cloth.")
def menu_open(rng, v):
    m = U.Mix()
    m.add(U.felt_swish(0.18, rng, 600, 3000, 0.65), 0, 0.7)
    m.add(U.felt(0.35, rng), 0.16, 0.6)
    m.add(U.tick(0.3, rng, 1500), 0.165, 0.5)
    return m.y


@sound("navigation", "menu_close", 1, -21, "Close a menu / panel: soft thud, whoosh away.")
def menu_close(rng, v):
    m = U.Mix()
    m.add(U.felt(0.3, rng), 0, 0.5)
    m.add(U.tick(0.25, rng, 1500), 0.003, 0.4)
    m.add(U.felt_swish(0.15, rng, 2600, 600, 0.3), 0.01, 0.6)
    return m.y


@sound("navigation", "popup_open", 1, -20, "Dialog / popup appears: soft pocket 'thup' and a rising fifth.")
def popup_open(rng, v):
    m = U.Mix()
    m.add(U.pocket_drop(rng, 0.35, rattle=False), 0, 0.5)
    m.add(U.clack_tone("C5", rng, 0.45, click=0.3), 0.01, 0.6)
    m.add(U.clack_tone("G5", rng, 0.6, click=0.35), 0.06, 0.8)
    return m.y


@sound("navigation", "popup_close", 1, -21, "Dialog / popup closes: falling fifth onto the cloth.")
def popup_close(rng, v):
    m = U.Mix()
    m.add(U.clack_tone("G5", rng, 0.45, click=0.3), 0, 0.6)
    m.add(U.clack_tone("C5", rng, 0.4, click=0.3), 0.05, 0.55)
    m.add(U.felt(0.25, rng), 0.05, 0.4)
    return m.y


def _swipe(direction):
    def fn(rng, v):
        m = U.Mix(stereo=True)
        m.add(U.whoosh(0.22, rng, 500, 2400, peak_at=0.45, bw=1.4, pan_from=-0.6 * direction, pan_to=0.6 * direction))
        m.add(U.tick(0.12, rng, 2000), 0.2, 0.25, 0.6 * direction)
        return m.y

    return fn


sound("navigation", "swipe_left", 2, -23, "Swipe / carousel to the left: cloth swish moving right to left.", stereo=True)(_swipe(-1))
sound("navigation", "swipe_right", 2, -23, "Swipe / carousel to the right: swish moving left to right.", stereo=True)(_swipe(1))


@sound("navigation", "scroll_tick", 3, -30, "One step while scrolling a list.")
def scroll_tick(rng, v):
    return U.tick(rng.uniform(0.04, 0.08), rng, 2500)


@sound("navigation", "slider_tick", 1, -27, "Slider moves one step (raise PlaybackSpeed with the value).")
def slider_tick(rng, v):
    return U.wood_knock(1300, rng, q=14, decay=0.008, k=0.4)


@sound("navigation", "notification", 1, -19, "Toast / notification: two clack tones with a faint bell.", stereo=True)
def notification(rng, v):
    m = U.Mix(stereo=True)
    m.add(U.clack_tone("E5", rng, 0.6, click=0.4), 0, 0.8, -0.1)
    m.add(U.clack_tone("A5", rng, 0.7, click=0.4), 0.11, 1.0, 0.1)
    m.add(U.bell("A6", rng, 0.8, 0.4), 0.11, 0.15, 0.3)
    return U.reverb(m.y, rng, 0.7, 0.12)


# ================================================================== loadout rack
@sound("loadout_rack", "rack_place_ball", 5, -20, "Drop a ball into a slot of the triangle: clack against its neighbour, wooden rack, small settle.")
def rack_place_ball(rng, v):
    m = U.Mix()
    k = rng.uniform(0.45, 0.7)
    m.add(U.felt(0.4, rng), 0, 0.45)
    m.add(U.clack(k, rng), 0.004, 1.0)
    m.add(U.wood_knock(rng.uniform(420, 620), rng, q=10, decay=0.03, k=0.6), 0.006, 0.4)
    m.add(U.clack(k * 0.25, rng), 0.004 + rng.uniform(0.025, 0.045), 0.35)
    return m.y


@sound("loadout_rack", "rack_pick_ball", 3, -24, "Lift a ball out of the rack.")
def rack_pick_ball(rng, v):
    m = U.Mix()
    m.add(U.tick(rng.uniform(0.15, 0.25), rng, 1200), 0, 0.8)
    m.add(U.felt_swish(0.08, rng, 900, 3000, 0.4), 0.005, 0.35)
    return m.y


@sound("loadout_rack", "rack_swap", 2, -21, "Swap two balls in the rack: click, short roll, click.")
def rack_swap(rng, v):
    m = U.Mix()
    m.add(U.clack(0.4, rng), 0, 0.8)
    m.add(U.roll(0.12, rng, 0.8, 0.8, surface=(300, 1000), rumble=(80, 250), ticks=0.15), 0.01, 0.35)
    m.add(U.clack(0.55, rng), 0.13, 1.0)
    m.add(U.wood_knock(500, rng, q=10, decay=0.025, k=0.5), 0.132, 0.3)
    return m.y


@sound("loadout_rack", "rack_invalid", 2, -21, "Ball can't go there: bumps the wooden rack and bounces back.")
def rack_invalid(rng, v):
    m = U.Mix()
    m.add(U.wood_knock(rng.uniform(230, 270), rng, q=7, decay=0.05, k=0.7), 0, 0.9)
    m.add(U.clack(0.4, rng), 0.002, 0.6)
    m.add(U.clack(0.15, rng), 0.07, 0.3)
    m.add(U.clack_tone("Eb4", rng, 0.5, decay=0.1, click=0.2), 0.0, 0.5)
    return m.y


@sound("loadout_rack", "rack_complete", 1, -17, "Rack is full / loadout saved: the triangle tightens the pack, then a rising arpeggio.", stereo=True)
def rack_complete(rng, v):
    m = U.Mix(stereo=True)
    t = 0.0
    for i in range(8):  # the pack pressed together, firmer each time
        k = 0.25 + 0.07 * i
        m.add(U.clack(k, rng), t, k, rng.uniform(-0.3, 0.3))
        t += rng.uniform(0.012, 0.022)
    m.add(U.felt_swish(0.25, rng, 400, 1400, 0.5), 0.0, 0.25)
    m.add(U.wood_knock(480, rng, q=9, decay=0.04, k=0.8), t, 0.6)
    for i, note in enumerate(["C5", "E5", "G5", "C6"]):
        m.add(U.clack_tone(note, rng, 0.55 + 0.08 * i, click=0.35), t + 0.05 + 0.065 * i, 0.8, -0.3 + 0.2 * i)
    return U.reverb(m.y, rng, 0.7, 0.1)


@sound("loadout_rack", "rack_lift", 1, -22, "Lift the triangle off the pack (leave the loadout screen / start).", stereo=True)
def rack_lift(rng, v):
    m = U.Mix(stereo=True)
    m.add(U.scrape(0.08, rng, 500, 2500, (40, 90)), 0, 0.25)
    m.add(U.tick(0.2, rng, 1500), 0.06, 0.5)
    m.add(U.whoosh(0.3, rng, 400, 2500, peak_at=0.5, bw=1.4), 0.05, 0.5)
    return m.y


@sound("loadout_rack", "rack_shuffle", 2, -20, "Randomise the loadout: balls rattling inside the rack.", stereo=True)
def rack_shuffle(rng, v):
    m = U.Mix(stereo=True)
    t = 0.0
    while t < 0.6:
        k = rng.uniform(0.15, 0.5) * (1 - 0.5 * t / 0.6)
        m.add(U.clack(k, rng), t, k, rng.uniform(-0.5, 0.5))
        t += rng.exponential(0.03) + 0.004
    for t0 in (0.05, 0.3):
        m.add(U.wood_knock(rng.uniform(420, 560), rng, q=9, decay=0.03, k=0.5), t0, 0.35)
    return m.y


@sound("loadout_rack", "rack_clear", 1, -21, "Clear the rack: balls roll out and scatter.", stereo=True)
def rack_clear(rng, v):
    m = U.Mix(stereo=True)
    m.add(U.fade(U.roll(0.9, rng, 1.4, 0.4, surface=(300, 1100), ticks=0.2), 0, 0.3), 0, 0.5, -0.2)
    m.add(U.fade(U.roll(0.8, rng, 1.2, 0.3, surface=(320, 1200), ticks=0.2), 0, 0.3), 0.05, 0.4, 0.25)
    t = 0.0
    for i in range(7):
        k = 0.5 * 0.8**i
        m.add(U.clack(k, rng), t, k * 1.5, rng.uniform(-0.6, 0.6))
        t += rng.uniform(0.05, 0.14)
    return m.y


@sound("loadout_rack", "rack_slot_hover", 2, -32, "Dragged ball hovers over a free slot.")
def rack_slot_hover(rng, v):
    return U.lp(U.tick(0.05, rng, 1500), 6000)


@sound("loadout_rack", "ball_inspect_spin", 1, -25, "Spin a ball to inspect it: rolls on the cloth and slows down.")
def ball_inspect_spin(rng, v):
    return U.roll(1.0, rng, 1.6, 0.3, surface=(250, 900), rumble=(60, 200), bumps=0.8, ticks=0.1) * U.hump(1.0, 0.15, 2.0)


# ================================================================== ball machine (mono: also fine as 3D sounds)
@sound("machine", "token_insert", 2, -19, "Token goes into the slot: slides in, the coin mech clicks, it drops into the box.")
def token_insert(rng, v):
    m = U.Mix()
    m.add(U.token_clink(rng, rng.uniform(2700, 3100), 0.5, 0.06), 0, 0.5)
    m.add(U.scrape(0.09, rng, 2200, 7500), 0.01, 0.4)
    m.add(U.ratchet_click(rng, 0.8, 0.8), 0.1, 0.8)
    m.add(U.ratchet_click(rng, 0.5, 1.1), 0.13, 0.4)
    tb = 0.1 + rng.uniform(0.18, 0.24)
    m.add(U.wood_knock(rng.uniform(160, 220), rng, q=6, decay=0.05, k=0.6), tb, 0.6)
    for j in range(3):
        m.add(U.token_clink(rng, rng.uniform(2400, 3400), 0.6, 0.08), tb + j * rng.uniform(0.03, 0.06), 0.7 * 0.6**j)
    return m.y


@sound("machine", "token_reject", 1, -20, "Token rejected: drops back into the return cup and rattles.")
def token_reject(rng, v):
    m = U.Mix()
    m.add(U.ratchet_click(rng, 0.6, 0.9), 0, 0.5)
    t, dt, k = rng.uniform(0.12, 0.16), 0.08, 0.8
    for _ in range(5):
        m.add(U.token_clink(rng, rng.uniform(2600, 3200), k, 0.09), t, k)
        m.add(U.plastic_hit(rng, 0.3 * k, 1200), t, 0.3 * k)
        t += dt
        dt *= 0.6
        k *= 0.6
    return m.y


@sound("machine", "crank_click", 3, -23, "One ratchet click (for a crank the player drags step by step).")
def crank_click(rng, v):
    return U.ratchet_click(rng, rng.uniform(0.5, 0.8), [0.95, 1.0, 1.05][v])


def _crank(rng, dur, n_clicks, ease=True):
    m = U.Mix()
    u = np.linspace(0, 1, n_clicks, endpoint=not ease) if ease else np.arange(n_clicks) / n_clicks
    times = (0.5 - 0.5 * np.cos(np.pi * u)) * (dur - 0.05) if ease else u * dur
    for i, t0 in enumerate(times):
        jit = rng.uniform(-0.003, 0.003) if ease and i else 0.0
        m.add(U.ratchet_click(rng, rng.uniform(0.55, 0.8), 1 + 0.03 * np.sin(i)), t0 + jit, 1.0)
    return m


@sound("machine", "crank_turn", 2, -21, "One full turn of the crank: ratchet clicks speed up and slow down, gears, spring, final clunk.")
def crank_turn(rng, v):
    dur = 1.15
    m = _crank(rng, dur, 12)
    t = U.taxis(dur)
    bed = U.bp(U.pink(dur, rng), 180, 900) * (0.5 + 0.5 * np.abs(np.sin(np.pi * 12 * t / dur)))
    m.add(U.norm(bed) * U.hump(dur, 0.5, 2.0), 0, 0.12)
    m.add(U.chalk_twist(dur * 0.8, rng, rate=(60, 140), bright=(700, 2200)), dur * 0.1, 0.1)
    m.add(U.mech_clunk(rng, 0.8), dur, 0.9)
    return m.y


@sound("machine", "crank_turn_loop", 1, -23, "Seamless loop of continuous cranking (1 s, 10 clicks) while the player holds the crank.", loop=1.0)
def crank_turn_loop(rng, v):
    L = 1.0
    m = _crank(rng, L, 10, ease=False)
    ev = U.loop_fold(m.y, L)
    bed = U.bp(U.pink(L + 0.4, rng), 180, 900)
    bed = U.loop_xfade(U.norm(bed), L, 0.3)
    t = U.taxis(L)
    bed *= 0.6 + 0.4 * np.abs(np.sin(np.pi * 10 * t / L))
    return ev + 0.1 * bed


def _rattle_events(rng, m, dur, env_fn):
    t = 0.0
    while t < dur:
        e = env_fn(t)
        k = float(rng.uniform(0.15, 0.6) * (0.4 + 0.6 * e))
        if rng.uniform() < 0.7:
            m.add(U.clack(k, rng), t, k)
        else:
            m.add(U.glass_tink(rng, k), t, 0.5 * k)
        t += rng.exponential(1 / (8 + 40 * e)) + 0.003


@sound("machine", "globe_rattle", 2, -19, "Balls tumbling in the glass globe while the machine mixes (swells and settles, 2 s).")
def globe_rattle(rng, v):
    dur = 2.0
    env = U.hump(dur, 0.35, 2.5)
    m = U.Mix()
    _rattle_events(rng, m, dur, lambda t: float(env[min(U.ns(t), len(env) - 1)]))
    m.add(U.norm(U.bp(U.pink(dur, rng), 90, 400)) * env, 0, 0.15)
    return m.y


@sound("machine", "globe_rattle_loop", 1, -21, "Seamless 2 s loop of the globe rattling, for a mixing animation of any length.", loop=2.0)
def globe_rattle_loop(rng, v):
    L = 2.0
    m = U.Mix()
    _rattle_events(rng, m, L, lambda t: 0.75)
    ev = U.loop_fold(m.y, L)
    rum = U.loop_xfade(U.norm(U.bp(U.pink(L + 0.4, rng), 90, 400)), L, 0.3)
    return ev + 0.15 * rum


@sound("machine", "ball_release", 2, -18, "The gate opens: mechanism clunk, the ball drops onto the chute.")
def ball_release(rng, v):
    m = U.Mix()
    m.add(U.mech_clunk(rng, 0.9), 0, 1.0)
    m.add(U.ratchet_click(rng, 0.7, 0.7), 0.03, 0.5)
    m.add(U.whoosh(0.1, rng, 800, 2500, 0.6, ch=1), 0.04, 0.15)
    m.add(U.plastic_hit(rng, 0.75, 760), 0.14, 0.9)
    m.add(U.clack(0.2, rng), 0.19, 0.25)
    return m.y


@sound("machine", "ball_roll_chute", 2, -20, "Ball rolls down the spiral chute, speeding up (1.6 s).")
def ball_roll_chute(rng, v):
    dur = 1.6
    y = U.roll(dur, rng, 0.6, 1.8, surface=(420, 1500), rumble=(90, 300), bumps=0.7, ticks=0.3)
    t = U.taxis(dur)
    y = y * (0.75 + 0.25 * np.sin(2 * np.pi * (1.2 * t + 0.6 * t**2)))  # going round the spiral
    y = 0.7 * y + 0.5 * U.norm(U.bp(y, 600, 900))  # hollow chute resonance
    m = U.Mix()
    m.add(U.fade(U.norm(y), 0.05, 0.03), 0, 1.0)
    for t0 in (0.45, 0.9, 1.25):  # joints in the chute
        m.add(U.tick(0.25, rng, 1500), t0 + rng.uniform(-0.03, 0.03), 0.25)
    return m.y


@sound("machine", "ball_drop_tray", 2, -18, "Ball lands in the prize tray: bounces and settles.")
def ball_drop_tray(rng, v):
    m = U.Mix()
    f0 = rng.uniform(650, 900)
    m.add(U.bounces(rng, lambda r, k: U.plastic_hit(r, k, f0), n=5, first_dt=rng.uniform(0.08, 0.11), e=0.55, k0=0.85), 0, 1.0)
    m.add(U.roll(0.35, rng, 0.5, 0.05, surface=(400, 1400), ticks=0.2), 0.2, 0.2)
    return m.y


@sound("machine", "tray_flap", 1, -22, "The little prize door flaps open.")
def tray_flap(rng, v):
    m = U.Mix()
    m.add(U.chalk_twist(0.07, rng, rate=(300, 600), bright=(1500, 4500)), 0, 0.15)
    m.add(U.plastic_hit(rng, 0.5, 1100), 0.06, 0.8)
    m.add(U.plastic_hit(rng, 0.2, 1100), 0.13, 0.35)
    return m.y


@sound("machine", "machine_denied", 1, -20, "Not enough tokens / machine busy: dull clunks and a falling semitone.")
def machine_denied(rng, v):
    m = U.Mix()
    m.add(U.mech_clunk(rng, 0.5), 0, 0.6)
    m.add(U.clack_tone("C5", rng, 0.5, decay=0.12, click=0.3), 0.02, 0.6)
    m.add(U.clack_tone("B4", rng, 0.5, decay=0.15, click=0.3), 0.13, 0.6)
    m.add(U.mech_clunk(rng, 0.4), 0.13, 0.4)
    return m.y


# ================================================================== render
def render(specs, out_dir, folder):
    manifest = []
    for s in specs:
        files = []
        q = None
        for v in range(s["variants"]):
            rng = np.random.default_rng(zlib.crc32(f"{s['name']}:{v}".encode()))
            y = s["fn"](rng, v)
            if s["loop"]:
                y = U.master_loop_level(y, s["target"])
                red = 0.0
            else:
                y, red = U.master(y, s["target"])
            fname = s["name"] if s["variants"] == 1 else f"{s['name']}_{v + 1:02d}"
            rel = f"{s['group']}/{fname}"
            U.save(os.path.join(out_dir, folder, rel), y)
            q = U.qa(y)
            q["limited_db"] = round(red, 1)
            files.append({"file": rel, **q})
        manifest.append({"name": s["name"], "group": s["group"], "variants": s["variants"], "loop": bool(s["loop"]),
                         "channels": 2 if files and "lr_corr" in files[0] else 1, "target": s["target"],
                         "description": s["desc"], "files": files})
        worst = max(files, key=lambda f: f["limited_db"])
        print(f"{s['group']:12s} {s['name']:20s} x{s['variants']}  {files[0]['dur_s']:5.2f}s  loud {files[0]['loud']:6.1f}"
              f"  peak {files[0]['peak_db']:5.1f}  limited {worst['limited_db']:4.1f} dB  tail {files[0]['tail_db']:6.1f}")
    return manifest


def main(out):
    import shutil

    shutil.rmtree(os.path.join(out, "ui-sounds"), ignore_errors=True)
    manifest = render(SPECS, out, "ui-sounds")
    with open(os.path.join(out, "ui-sounds", "manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=1)


if __name__ == "__main__":
    main(sys.argv[1])
