# Cue Clash impact sounds, v3

Cue strikes, ball-on-ball hits and ball-on-cushion hits, each in **soft / medium / hard** force
layers with several variants per layer. v3 builds on the v2 bank in `../output` (the one behind the
renders in `../real-shit/`) and adds new recordings for the two weak spots: cue strikes and
cushion hits.

Open **`listen.html`** in a browser: every v3 sound is next to the v2 sound it replaces.

## What's in here

| Path | What it is |
|---|---|
| `sounds/v3/cue/{soft,medium,hard}_NN.wav/.ogg` | 27 cue strikes (14 soft, 9 medium, 4 hard) |
| `sounds/v3/ball/...` | 30 ball-on-ball hits (15 / 10 / 5) |
| `sounds/v3/rail/...` | 33 cushion hits (14 / 11 / 8) |
| `sounds/v3/cluster/...` | 12 multi-ball "chatter" clips for breaks, built from the v3 ball hits |
| `sounds/synth/table/...` | the v2 cloth-landing sound, copied so breaks render the same way |
| `sounds/bank_report.json` | per file: source recording, licence, time in the source, measured brightness and decay |
| `showcase/<kind>_soft_to_hard_{v3,v2_hybrid}` | 10 hits from a gentle tap to full force, v3 and v2 side by side |
| `break_renders/break_powerNNN_v3` | the same simulated breaks as `real-shit/break_powerNNN_*`, rendered with v3 |
| `break_renders/compare.json` | loudness, brightness and voices: v3 next to the v2 hybrid renders |
| `tools/` | the scripts that build all of this (they reuse `../output/tools`) |

The file layout is the same as v2's, so `ImpactAudio` / `impactmix.py` load it unchanged
(`load_bank(<v3>/sounds, "v3")`).

## How it was made

**New sources** (all CC0):
- **craigsmith, Freesound 675330**: about 2 minutes of close-miked cue strikes, digitized 1930s-60s
  Hollywood film effects. 28 clean first strikes were found (nothing else within 45 ms after,
  30+ dB above the noise). The darkest ones have no cue-ball click (thuds from the film recording)
  and are left out.
- **papapleygames "Pool And Billiards SFX", itch.io**: the `ball_collide_ball` and `ball_shoot`
  clips are short, bright ball clicks (the "shoot" ones have no cue character, so they're used as
  ball hits). `ball_collide_wall_1/2` are real cushion thumps (~230-310 Hz, 60-100 ms).
  `ball_collide_wall_3` is left out: a regular sine-like burst that sounds synthetic. A stray tick
  ~100 ms into several files is cut off.

**Kept from v2**: the KVV_Audio, csaszi, coral_island_studios, Za-Games and bsumusictech hits that
passed v2's checks, and the v2 synth rail model (which the hybrid renders you liked used for every
cushion).

**Force layers.** A hit's natural force shows in its brightness (Hertz contact: a harder hit has a
shorter contact, so more treble). Within each kind the recordings are ranked by brightness: the
darkest third are soft, the middle medium, the brightest hard. Each recording is used as recorded
in its own layer and softened into the layers below it (never brightened). Cushions also get
2 pitch variants per recording and 5 synth hits per layer at the layer's speed.

**Cleanup** (as in v2): tails are damped from 4 ms after the peak (cue 9 ms, ball 7 ms; cushions
25 ms, so the rubber thump stays), clips that still ring are rejected, and the cleanest are kept.

**Tonal balance toward v2.** The craigsmith strikes are mostly the bright tip-on-ball crack, without
the low cue-shaft "thock". Each new clip is EQ'd part of the way (cue 90 %, ball 60 %) toward the
average spectrum of the v2 bank for the same kind and force layer, with only cuts, at most 8 dB.
The attack and texture of the new recordings stay.

| Average brightness | soft | medium | hard |
|---|---|---|---|
| cue, v2 | 798 Hz | 1022 Hz | 1299 Hz |
| cue, v3 | 842 Hz | 1170 Hz | 1486 Hz |
| ball, v2 | 1811 Hz | 1930 Hz | 1997 Hz |
| ball, v3 | ~1760 Hz | ~1950 Hz | ~2150 Hz |
| cushion, v2 (synth) | 290 Hz | 347 Hz | 387 Hz |
| cushion, v3 | 324 Hz | 379 Hz | 444 Hz |

## Licences and credit

| Source | Licence | Credit |
|---|---|---|
| craigsmith, Freesound 675330 | CC0 | not needed |
| papapleygames / SURAJ KISPOTTA, itch.io "Pool And Billiards SFX" | CC0 | appreciated, not needed |
| csaszi 350918, Za-Games 539854, bsumusictech 62331 | CC0 | not needed |
| **KVV_Audio**, Freesound 830221 | **CC-BY 4.0** | **needed** |
| **coral_island_studios**, Freesound 432592 | **CC-BY 4.0** | **needed** |
| synth cushions | no third-party audio | none |

So, like v2's hybrid bank, v3 needs **KVV_Audio** and **coral_island_studios** in the game's
credits. Every file's source is in `sounds/bank_report.json`.

## Rebuilding

From `ball-hit-sounds/`, with Python + numpy, scipy, soundfile, matplotlib:

```
python v3/tools/make_v3.py
python v3/tools/render_v3.py
python v3/tools/make_listen_page.py
```
