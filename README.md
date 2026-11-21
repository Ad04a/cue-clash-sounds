# Cue Clash sounds

Every sound for **Cue Clash**:

- the source recordings;
- the impact sounds (cue strike, ball on ball, rail) with the break mechanism;
- UI sounds (buttons, menus, the loadout rack, the gumball-style ball machine);
- game-event sounds (match flow, scoring, win and lose, buying, rarity reveals, ambience);
- the scripts that generate all of it.

Open **`output/listen.html`** in a browser to hear everything.

## Where things are

| Path | What it is |
|---|---|
| `output/ui-sounds/` | Buttons, navigation, swipes, the **loadout rack** and the **ball machine** (token, crank, globe rattle, chute, tray). See its README. |
| `output/ambient-sounds/` | Match flow, scoring, win / lose, economy, the machine's **winning-ball reveals (common → mythic)**, ambience loops. See its README. |
| `output/roblox/` | Ready for Roblox: `ui_atlas.ogg`, `machine_atlas.ogg`, `game_atlas.ogg` + `GameSounds.luau` / `GameSoundAtlas.luau` (UI and game sounds); `impact_atlas_*.ogg` + `ImpactAudio.luau` / `ImpactAtlas.luau` (ball impacts and the break mechanism); a drop-in `AudioController.luau` |
| `output/sounds/` | Impact sounds v2: `recorded/` and `synth/` banks, soft / medium / hard layers |
| `v3/` | Impact sounds v3: adds the craigsmith cue strikes and the itch.io CC0 pack. See its README. |
| `real-shit/` | Picks: the v2 hybrid break renders and favourite source files |
| `output/README.md` | How the impact sounds and the break mechanism work |
| `output/tools/` | Python and Luau scripts that build and test everything |
| `output/analysis/` | Spectrograms and measurements |
| `*.wav`, `*.mp3`, `*.aiff` in this folder | The original recordings (see `CREDITS.md`) |
| `downloads/` | Other downloaded sources: Freesound (CC0), the itch.io pack (CC0) |

## Using the sounds in Roblox

1. Upload `output/roblox/ui_atlas.ogg`, `machine_atlas.ogg` and `game_atlas.ogg`, plus the
   loop files listed in `GameSoundAtlas.luau`.
2. Copy `GameSounds.luau` and `GameSoundAtlas.luau` into `ReplicatedStorage/Shared/Audio/`.
3. Call `GameSounds.init({ ui = ..., machine = ..., game = ... }, loops)`, then
   `GameSounds.play("button_click")`.

The details are in `output/ui-sounds/README.md` and in `output/README.md` (impacts).

## Licences

The UI and game sounds are synthesized, and the pool-hall loops come from a CC0 recording,
so **none of them needs credit**. The recorded impact banks (v2 recorded / hybrid, v3)
include **CC-BY 4.0** clips: credit **KVV_Audio** and **coral_island_studios**. Every
source file and its licence is listed in [`CREDITS.md`](CREDITS.md). The Pixabay downloads
are not in this repo: their licence doesn't allow redistributing the raw files.

## Rebuilding

Needs Python with numpy, scipy, soundfile and matplotlib. Run the commands listed at the
end of `output/README.md` from this folder.
