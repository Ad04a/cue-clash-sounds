# Cue Clash: impact sounds

Sounds for cue strikes, ball-on-ball hits, rail hits and balls landing on the cloth, plus a mechanism that
turns the game's simulation events into sound. It scales from a soft tap up to a
full 16-ball break. Everything here was made from the recordings in
`ball-hit-sounds/` by the scripts in `tools/`.

Open **`listen.html`** in a browser to play every sound and every break preview.

**Also here:** [`ui-sounds/`](ui-sounds/README.md) covers buttons, menus, swipes, the loadout
rack and the ball machine. [`ambient-sounds/`](ambient-sounds/README.md) covers match
events, scoring, win and lose, buying, the **rarity reveals** (common to mythic) and
ambience loops. Both are played in Roblox through `roblox/GameSounds.luau` (three atlases,
three uploads). The improved impact bank built from new recordings is in `../v3/`.

## Folder layout

| Path | What it is |
|---|---|
| `sounds/recorded/{cue,ball,rail,cluster}/{soft,medium,hard}_NN.wav/.ogg` | The cleanest real hits cut from the recordings (7 cue, 10 ball, 2 rail), each in 3 velocity layers, tails damped |
| `sounds/synth/{cue,ball,rail,table,cluster}/...` | Synthesized hits, 8 variants per layer, one material model per surface (see below). No third-party licence |
| `sounds/bank_report.json` | Where each recorded clip came from, plus measured centroid, low-band ratio, decay and ring (Q) |
| `roblox/impact_atlas_hybrid.ogg` | **The file to upload.** Recorded cue and ball hits, synth rails and cloth landings, recorded clusters, all in one 67 KB file |
| `roblox/impact_atlas_synth.ogg` | The same thing built only from synth sounds (no licence questions) |
| `roblox/ImpactAtlas.luau` | Generated table of where each clip starts and how long it is inside the atlas files |
| `roblox/ImpactAudio.luau` | The runtime mechanism (Luau, `--!strict`) |
| `roblox/AudioController.luau` | Drop-in version of the game's AudioController that uses ImpactAudio |
| `break_renders/` | The simulated breaks at 35 / 55 / 75 / 90 / 100 % power: event logs, `summary.json` and `break_overview.png`. The rendered WAV/OGG files of these breaks are now in `../real-shit/` |
| `analysis/` | Spectrogram of every source file, `analysis.json` (each detected impact) and `bank_contact_sheet.png` |
| `tools/ring_metrics.py`, `tools/calib.py` | Measure how "metallic" a clip is (ring time, tail level, Q) and print the calibration table |
| `ui-sounds/`, `ambient-sounds/` | UI and game-event sounds, each with a README, `manifest.json` and preview reels |
| `roblox/{ui,machine,game}_atlas.ogg`, `roblox/GameSounds.luau`, `roblox/GameSoundAtlas.luau` | The UI and game sounds packed for Roblox, plus the player module |
| `tools/` | All scripts. Re-run them to rebuild everything (see the end of this file) |

## What the analysis found

About 300 impacts were detected in the 11 recordings. Their measured traits:

| Hit | Attack | Energy | Decay (−30 dB, dry) | Signature |
|---|---|---|---|---|
| **Cue tip → ball** | 1.1–1.5 ms (soft leather) | centroid ~1.4 kHz | ~20–30 ms | Same peaks in every shot: ~400–650 Hz (cue shaft) and **1170 / 1430 Hz** |
| **Ball ↔ ball** | 0.5–0.9 ms | 1.3–3.5 kHz band, almost nothing under 450 Hz | 10–30 ms (dry) | Dense cluster of partials between 1.4 and 3.2 kHz. Quiet hits are about 30 % darker |
| **Ball → rail** | slow | ~60 % of energy under 450 Hz, centroid ~480 Hz | ~25–60 ms | Rubber thump, wood body 90–550 Hz, plus a little ball "tock" |

The cleanest source is `2.3 kvv_audio` (96 kHz, dry, gated). Most cue and ball
clips come from it. The break recordings (`1.x`, `3.4`) have too much reverb and
overlap to cut usable single hits, so they were only used as reference. Rail hits
are rare and quiet in all the recordings. The three recorded rail clips are short
and noise-gated, so the **hybrid** bank uses the synthesized rails instead.

### Materials (v2: the metallic sound fixed)

v1 sounded metallic. That shows up in the measurements: its resonances had
Q 100–140 and rang for 30–45 ms, and a fake "room" made of short echoes added
comb filtering. Metal rings (Q in the hundreds or more), while resin, wood and
cloth die within a few ms. v2 models each surface with its own damping:

| Sound | Model | Q | Ring (−30 dB) |
|---|---|---|---|
| Ball ↔ ball (phenolic resin) | 0.15–0.35 ms contact, 8 resonances at 1.2–4.2 kHz, broadband crack | 16–40 | ~9–10 ms |
| Cue (wooden cue, leather tip) | 0.34 ms soft contact, tip "thock" 420/620 Hz, cue-ball response 1175/1430 Hz, shaft, chalk slap | 4–24 | ~8–10 ms |
| Rail (cloth over the rubber nose, wooden rail) | 1.2 ms contact, rail body 85–1100 Hz, small ball tock, cloth noise | 2–7 | ~9–11 ms |
| Table (ball landing on the cloth-covered bed) | 1 ms contact, 65–700 Hz thud, cloth noise, almost no ring | 1.5–4 | ~9–11 ms |

For comparison, the real dry kvv ball hits ring for ~11 ms.

Recorded clips are now damped from 4 ms after the peak. Any clip whose tail is
still louder than −12 dB is rejected; za-games and bsumusictech had rung for
~37 ms. There is no echo effect any more.

**Variance:** every synth hit randomizes its contact time (±15–25 %), each
resonance's frequency (±5–12 %), Q and level, the noise, and its speed within the
layer. At runtime, each hit also gets ±2 % pitch and ±12 % volume.

Physics (Hertzian contact): contact time τ ∝ v^-1/5, so harder hits are shorter
and brighter. Radiated amplitude ∝ v^1.2.

## The mechanism (ImpactAudio)

The game's `Simulation` already sends `{kind, speed}` events. `speed` is the
closing speed along the contact normal (ball/cushion) or the shot speed (cue).
Each event goes through these steps:

1. **Intensity**: `k = clamp(speed / vref, 0, 1)`. vref is 25 studs/s for cue, 16 for ball, 12 for cushion and 6 for bounce. Bounce plays the cloth `table` sound.
2. **Volume**: `vmax · k^curve`. curve is about 1.2 (the Hertz pressure law). Hits below `k = 0.012` are silent.
3. **Layer**: soft if k < 0.22, medium if k < 0.55, otherwise hard. There is ±0.06 of random jitter so you never hear a step where one layer switches to the next.
4. **Variant**: round-robin, never the same clip twice in a row. Each hit also gets ±2 % pitch and ±12 % volume jitter, and harder hits are pitched up a little.

Then, **once per frame** (all events fired in one frame are mixed together through `task.defer`):

5. **Voice budget**: the loudest events of the frame get their own Sound. The budget is ball 6, cushion 3, bounce 2, cue 2, counted over a sliding 80 ms window.
6. **Chatter**: the ball events left over are not thrown away. Their energy is summed (`g = 0.8·√Σg²`, the way independent sources add up) and played as **one "cluster" sample**. That sample holds several clacks spread over ~40 ms, and its layer is picked from their average intensity. This is what makes a break sound full and powerful: dozens of contacts → a few voices plus one cluster.
7. **Loudness guard**: every volume is divided by `√(1 + E_recent / 1.6)`, where `E_recent` is the energy played in the last ~60 ms (decaying). A hard break gets loud but never piles up into clipping.
8. A hard cap of 24 live Sounds.
9. **Room**: the hits are dry, like a close mic. `Config.Room` routes them through a SoundGroup with a light diffuse `ReverbSoundEffect` (0.6 s, −17 dB wet). Set `Enabled = false` if the place already has its own reverb.

Measured on simulated breaks (`break_renders/summary.json`):

| Power | Ball contacts | Voices played |
|---|---|---|
| 35 % | 33 | 9 |
| 55 % | 35 | 16 |
| 75 % | 34 | 21 |
| 90 % | 93 | 33 |
| 100 % | 40 (+18 rail) | 31, versus 55 when every event is played (`break_power100_NAIVE_every_event.wav`) |

`tools/impactmix.py` is the Python version of the same rules, used to make the
renders. I also ran the Luau module headless (`tools/test_impactaudio.luau`, Lune
with mocked Roblox APIs) on the same event logs. It plays exactly the same number
of voices at every power level.

## Adding it to the game (later)

1. Upload `roblox/impact_atlas_hybrid.ogg` (or `_synth`) to Roblox. It is one upload instead of about 60.
2. Copy `roblox/ImpactAudio.luau` and `roblox/ImpactAtlas.luau` into `ReplicatedStorage/Shared/Audio/`.
3. In `PoolConfig.luau` add:
   ```lua
   PoolConfig.ImpactAtlas = { Id = "rbxassetid://<atlas id>", Bank = "hybrid" } -- or "synth"
   ```
4. Replace `Client/Controllers/AudioController.luau` with `roblox/AudioController.luau`. It sends cue, ball, cushion and bounce events to ImpactAudio and keeps the pocket, UI and music sounds as they are. You can then remove `CueStrike`, `BallClackSoft`, `BallClackHard` and `Rail` from `PoolConfig.Sounds`.
5. Check in Studio: ImpactAudio plays slices of the atlas using `Sound.PlaybackRegion`. If a slice ever cuts off or overruns, the fallback is to upload the separate `.ogg` files and build the bank with `ImpactAudio.bankFromIds`.

Optional: `ImpactAudio.push({kind, speed, position = Vector3})` plays the hit in 3D
at that position. The renderer knows where the balls are, so it could pass this in.

**Tuning:** every number above is in `ImpactAudio.Config`. To try a change
offline, edit the matching value in `tools/impactmix.py` `CONFIG` and re-run
`breaksim.py`.

## Licences (checked on Freesound, 2026-11-19)

The recorded bank and the hybrid atlas use clips from:
- 830221 KVV_Audio (**CC-BY 4.0**)
- 432592 coral_island_studios (**CC-BY 4.0**)
- 350918 csaszi, 62331 bsumusictech, 539854 Za-Games and 204187 reg7783 (all CC0)

Commercial use is fine. **Credit KVV_Audio and coral_island_studios** in the game.
No CC-BY-NC file (that is 3.2 snooker sinking) is used. The **synth** bank and
`impact_atlas_synth.ogg` contain no third-party audio and need no credit. See
`ROYALTY_FREE_SOURCES.md` for every file's licence and for new CC0 and Pixabay
sources.

## Rebuilding

Run from `ball-hit-sounds/`. Needs Python with numpy, scipy, soundfile and matplotlib.

```
python output/tools/analyze.py . output/analysis
python output/tools/make_sounds.py . output
python output/tools/breaksim.py output
python output/tools/make_atlas.py output
python output/tools/contact_sheet.py output
python output/tools/make_ui_sounds.py output
python output/tools/make_game_sounds.py output .
python output/tools/make_game_atlas.py output
python output/tools/make_previews.py output
python output/tools/make_sound_docs.py output
python output/tools/make_listen_page.py output
```
