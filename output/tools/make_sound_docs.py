"""Write ui-sounds/README.md and ambient-sounds/README.md from their manifests.
usage: python make_sound_docs.py <output_dir>"""

import json
import os
import sys

GROUP_TITLES = {
    "buttons": "Buttons", "navigation": "Navigation", "loadout_rack": "Loadout rack (picking balls into the triangle)",
    "machine": "Ball machine (mono, so they also work as 3D sounds on the machine)", "match": "Match flow",
    "scoring": "Scoring", "results": "Results", "economy": "Economy", "machine_reveal": "Ball machine: the winning ball",
    "loops": "Ambience loops",
}

UI_INTRO = """# Cue Clash UI sounds

Sounds for buttons, menus, swipes and lists, the loadout screen (racking your balls into
the starting triangle) and the gumball-style ball machine. They are built from billiards
materials: resin ball clacks, the wooden cue and rack, felt cloth, leather pockets and
chalk. Musical feedback uses *clack tones*: ball clacks tuned to notes, like a marimba made
of billiard balls. The machine parts (metal token, plastic ratchet and chute, glass globe)
use their own materials.

**Everything here is synthesized. There is no third-party audio, so no credit or licence
is needed.**

Listen first:
- `preview_all.ogg`: every sound once.
- `preview_machine_sequence.ogg`: token, crank, rattle, release, chute, tray, then a reveal.
- `preview_loadout_rack.ogg`: picking, placing, swapping, an invalid drop, completing and
  lifting the rack.

The machine's **winning-ball / rarity reveal** sounds are in `../ambient-sounds/machine_reveal/`.

"""

GAME_INTRO = """# Cue Clash game sounds (ambient-sounds)

Event sounds and stingers for a match, scoring, results and the economy. Also here:
**the ball machine's winning-ball reveals, one per rarity**, plus ambience loops. The
one-shots are synthesized from the same billiards materials as the UI sounds (ball
clacks, pocket drops, the break, chalk, the cue) with musical layers: clack tones, brass,
pads, bells and sparkle. Everything is in C major, so the sounds fit together.

Listen first:
- `preview_rarity_ladder.ogg`: the anticipation, then common, uncommon, rare, epic,
  legendary and mythic.
- `preview_all.ogg`: every sound once.

The rarities escalate in length, weight and brightness:

| Rarity | Length | What happens |
|---|---|---|
| common | 1.6 s | a plain clack and an open fifth |
| uncommon | 1.7 s | a rising three-note arpeggio, a faint bell |
| rare | 2.4 s | whoosh, pocket thump, a Cmaj9 arpeggio over a soft pad, sparkles |
| epic | 3.3 s | riser, a break hit, Ab-to-C brass, a fast nine-note run, choir |
| legendary | 4.5 s | clacks speeding up into a big break, a "da-da-DAA" fanfare, choir, gold shimmer |
| mythic | 6.1 s | heartbeat clacks, a huge break, a Lydian chord opening to a wide C major, all 15 rack balls ringing up and down |

Play `reveal_anticipation` while the ball drops. It ends at its peak, so start the reveal
right as it ends. Use `ball_won` when the reveal is skipped or for repeats.

**Licence:** the one-shots and `lobby_room_tone_loop` are synthesized (no third-party
audio). `pool_hall_ambience_loop` and `pool_hall_ambience_distant_loop` are cut from the
**CC0** recording `4.1_68218` (damien bazin, Freesound 68218), so no credit is needed.

"""

COMMON_TAIL = """
## In Roblox

Every sound has a `.wav` and an `.ogg` file. To avoid about 90 separate uploads, use the
atlases in `../roblox/`:

1. Upload `ui_atlas.ogg`, `machine_atlas.ogg` and `game_atlas.ogg`, plus the six loop
   `.ogg` files listed at the bottom of `GameSoundAtlas.luau`.
2. Copy `GameSounds.luau` and `GameSoundAtlas.luau` into `ReplicatedStorage/Shared/Audio/`.
3. On the client:
   ```lua
   GameSounds.init(
       { ui = "rbxassetid://...", machine = "rbxassetid://...", game = "rbxassetid://..." },
       { pool_hall_ambience_loop = "rbxassetid://...", globe_rattle_loop = "rbxassetid://...", ... }
   )
   GameSounds.play("button_click")
   GameSounds.play("rack_place_ball")
   GameSounds.play("select_note_" .. combo)                 -- 1..8 climbing tones
   GameSounds.play("token_insert", { parent = machinePart }) -- 3D, from the machine
   local hall = GameSounds.loop("pool_hall_ambience_loop")  -- :Stop() it later
   ```

Variants are picked at random and never repeat twice in a row. Each sound already sits at
the right level relative to the others, so one volume per atlas works
(`GameSounds.Volume`). If an atlas slice ever cuts off in Studio, upload that sound's own
`.ogg` instead.

## Levels

Loudness is the loudest 100 ms (K-weighted, LUFS-like). The ceiling is −1 dBFS, and no
sound is limited by more than 2 dB, so clicks keep their snap.
"""


def table(man):
    rows, group = [], None
    for e in man:
        if e["group"] != group:
            group = e["group"]
            rows += ["", f"### {GROUP_TITLES.get(group, group)}", "", "| Sound | Files | Length | Use |", "|---|---|---|---|"]
        n = len(e["files"])
        files = f"`{e['files'][0]['file']}`" + (f" … ×{n}" if n > 1 else "")
        dur = e["files"][0]["dur_s"]
        kind = " (loop)" if e["loop"] else ""
        rows.append(f"| **{e['name']}**{kind} | {files} | {dur:.2f} s | {e['description']} |")
    return "\n".join(rows) + "\n"


def main(out):
    for folder, intro in (("ui-sounds", UI_INTRO), ("ambient-sounds", GAME_INTRO)):
        man = json.load(open(os.path.join(out, folder, "manifest.json"), encoding="utf-8"))
        n_files = sum(len(e["files"]) for e in man)
        body = intro + f"## The sounds ({len(man)} sounds, {n_files} files)\n" + table(man) + COMMON_TAIL
        with open(os.path.join(out, folder, "README.md"), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(body)
        print(folder, len(man), "sounds", n_files, "files")


if __name__ == "__main__":
    main(sys.argv[1])
