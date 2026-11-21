"""Listening previews for the UI and game sounds:
  ui-sounds/preview_all            every UI sound once, in manifest order
  ui-sounds/preview_machine_sequence   token -> crank -> rattle -> release -> chute -> tray -> reveal
  ui-sounds/preview_loadout_rack   picking, placing, swapping, an invalid drop, completing, lifting
  ambient-sounds/preview_all       every game sound once (loops: their first 6 s)
  ambient-sounds/preview_rarity_ladder   anticipation + each reveal, common to mythic

usage: python make_previews.py <output_dir>
"""

import json
import os
import sys

import numpy as np
import soundfile as sf

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import uisynth as U  # noqa: E402

SR = U.SR


def clip(out, folder, rel):
    x, sr = sf.read(os.path.join(out, folder, rel + ".wav"), always_2d=True)
    return x if x.shape[1] == 2 else np.repeat(x, 2, axis=1)


def seq(parts):
    """parts: list of (array, start_offset_from_previous_start or None=after previous end + gap)."""
    m = U.Mix(stereo=True)
    t = 0.3
    for x, gap in parts:
        m.add(x, t)
        t += len(x) / SR + gap
    return m.y


def reel(out, folder, loop_seconds=6.0, gap=0.45):
    man = json.load(open(os.path.join(out, folder, "manifest.json"), encoding="utf-8"))
    parts = []
    for e in man:
        x = clip(out, folder, e["files"][0]["file"])
        if e["loop"]:
            x = U.fade(x[: U.ns(loop_seconds)], 0.05, 0.6)
        parts.append((x, gap))
    return seq(parts)


def write(out, rel, y):
    y = y * (10 ** (-1 / 20) / max(np.abs(y).max(), 1e-9)) if np.abs(y).max() > 10 ** (-1 / 20) else y
    U.save(os.path.join(out, rel), y)
    os.remove(os.path.join(out, rel) + ".wav")  # previews are for listening only: keep the small .ogg
    print(f"{rel:45s} {len(y) / SR:6.1f} s")


def main(out):
    ui, gm = "ui-sounds", "ambient-sounds"
    write(out, f"{ui}/preview_all", reel(out, ui))
    write(out, f"{gm}/preview_all", reel(out, gm))

    c = lambda rel: clip(out, ui, rel)  # noqa: E731
    g = lambda rel: clip(out, gm, rel)  # noqa: E731
    machine = [
        (c("machine/token_insert_01"), 0.25),
        (c("machine/crank_turn_01"), 0.1),
        (c("machine/globe_rattle_01"), -0.35),  # overlaps the end of the rattle a little
        (c("machine/ball_release_01"), 0.0),
        (c("machine/ball_roll_chute_01"), -0.05),
        (c("machine/ball_drop_tray_01"), 0.3),
        (c("machine/tray_flap"), 0.25),
        (g("machine_reveal/reveal_anticipation"), -0.02),
        (g("machine_reveal/reveal_legendary"), 0.5),
    ]
    write(out, f"{ui}/preview_machine_sequence", seq(machine))

    rack = [(c("loadout_rack/rack_pick_ball_01"), 0.25)]
    for i in range(1, 6):
        rack.append((c(f"loadout_rack/rack_place_ball_{i:02d}"), 0.35))
    rack += [(c("loadout_rack/rack_swap_01"), 0.4), (c("loadout_rack/rack_invalid_01"), 0.4),
             (c("loadout_rack/rack_shuffle_01"), 0.4), (c("loadout_rack/rack_complete"), 0.3),
             (c("loadout_rack/rack_lift"), 0.5)]
    write(out, f"{ui}/preview_loadout_rack", seq(rack))

    ladder = []
    for r in ("common", "uncommon", "rare", "epic", "legendary", "mythic"):
        ladder += [(g("machine_reveal/reveal_anticipation"), -0.02), (g(f"machine_reveal/reveal_{r}"), 0.8)]
    write(out, f"{gm}/preview_rarity_ladder", seq(ladder))


if __name__ == "__main__":
    main(sys.argv[1])
