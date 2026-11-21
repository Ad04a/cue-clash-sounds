# Cue Clash game sounds (ambient-sounds)

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

## The sounds (41 sounds, 45 files)

### Match flow

| Sound | Files | Length | Use |
|---|---|---|---|
| **match_found** | `match/match_found` | 1.63 s | Opponent found: whoosh in, rising arpeggio, a ball clack accent. |
| **countdown_tick** | `match/countdown_tick` | 0.64 s | 3... 2... 1...: a cue-butt knock with a short tone. |
| **countdown_go** | `match/countdown_go` | 1.69 s | GO!: the break (cue strike into the pack), a bright chord and a low thump. |
| **round_start** | `match/round_start` | 2.25 s | Round starts: chalking up, a rising whoosh, then the break with a short brass stab. |
| **round_end** | `match/round_end` | 2.94 s | Round over: a ball rolls to a stop and drops; falling tones over a soft chord. |
| **turn_yours** | `match/turn_yours` | 1.41 s | It's your shot: two bright rising clack tones and a chalk accent. |
| **turn_opponent** | `match/turn_opponent` | 1.38 s | Opponent's shot: softer, falling clack tones. |
| **shot_clock_tick** | `match/shot_clock_tick_01` … ×2 | 0.03 s | Shot clock tick / tock (cue butt on the floor). |
| **shot_clock_warning** | `match/shot_clock_warning` | 0.60 s | Last seconds on the shot clock: quick double knock and a high tone. |
| **shot_clock_expired** | `match/shot_clock_expired` | 1.34 s | Time's up: a miscue, a low clashing pair of tones, a dull thud. |

### Scoring

| Sound | Files | Length | Use |
|---|---|---|---|
| **score_pot** | `scoring/score_pot_01` … ×3 | 1.61 s | A ball is potted: drops into the leather pocket, a bright tone and a little shine. |
| **score_combo_1** | `scoring/score_combo_1` | 1.66 s | Pot number 1 in a row: the tone climbs (C6); from 3 a chord, 4 brass, 5 sparkle. |
| **score_combo_2** | `scoring/score_combo_2` | 1.69 s | Pot number 2 in a row: the tone climbs (D6); from 3 a chord, 4 brass, 5 sparkle. |
| **score_combo_3** | `scoring/score_combo_3` | 1.77 s | Pot number 3 in a row: the tone climbs (E6); from 3 a chord, 4 brass, 5 sparkle. |
| **score_combo_4** | `scoring/score_combo_4` | 1.76 s | Pot number 4 in a row: the tone climbs (G6); from 3 a chord, 4 brass, 5 sparkle. |
| **score_combo_5** | `scoring/score_combo_5` | 2.02 s | Pot number 5 in a row: the tone climbs (C7); from 3 a chord, 4 brass, 5 sparkle. |
| **score_eight_ball** | `scoring/score_eight_ball` | 2.65 s | The 8-ball goes down: deep thump, minor chord resolving to major, rising arpeggio. |
| **foul** | `scoring/foul` | 2.21 s | Foul / scratch: the cue ball drops, falling tones end in a low 'womp', dull knocks. |
| **trick_shot** | `scoring/trick_shot` | 1.23 s | Bank / trick shot bonus: cushion, clack, a fast rising run and some shine. |

### Results

| Sound | Files | Length | Use |
|---|---|---|---|
| **win** | `results/win` | 3.78 s | Match won (about 3 s): break, I-IV-V-I brass fanfare, melody, sparkle and a choir pad. |
| **lose** | `results/lose` | 3.97 s | Match lost (about 2.5 s): a ball rattles in the jaws and stays out; falling tones over D minor. |
| **win_short** | `results/win_short` | 1.85 s | Round won / short victory (about 1.2 s). |
| **lose_short** | `results/lose_short` | 1.56 s | Round lost / short defeat (about 1 s). |
| **draw** | `results/draw` | 1.72 s | Draw: an open fifth knocked twice, neither up nor down. |

### Economy

| Sound | Files | Length | Use |
|---|---|---|---|
| **buy** | `economy/buy_01` … ×2 | 1.76 s | Purchase made: tokens clink, drop into a pocket, two bright tones and a glint. |
| **buy_fail** | `economy/buy_fail` | 0.88 s | Can't afford it: two dull knocks and a muted falling semitone. |
| **coins_gain** | `economy/coins_gain` | 1.49 s | Reward / coins collected: a shower of tokens and a fast rising run. |
| **coins_count_loop** (loop) | `economy/coins_count_loop` | 0.60 s | Seamless 0.6 s loop of coin ticks for a counter animation. |
| **level_up** | `economy/level_up` | 3.26 s | Level up (about 2 s): riser into a break hit, brass chord, two-octave arpeggio, sparkle. |
| **achievement_unlock** | `economy/achievement_unlock` | 2.25 s | Achievement / unlock: rising clack tones, bells and a soft add9 pad. |

### Ball machine: the winning ball

| Sound | Files | Length | Use |
|---|---|---|---|
| **reveal_anticipation** | `machine_reveal/reveal_anticipation` | 1.40 s | Build-up before the ball is shown (1.4 s, ends at its peak). |
| **reveal_common** | `machine_reveal/reveal_common` | 1.55 s | Common ball: a plain clack and an open fifth. |
| **reveal_uncommon** | `machine_reveal/reveal_uncommon` | 1.74 s | Uncommon ball: a rising three-note arpeggio with a faint bell. |
| **reveal_rare** | `machine_reveal/reveal_rare` | 2.42 s | Rare ball: whoosh in, pocket thump, a Cmaj9 arpeggio over a soft pad, a few sparkles. |
| **reveal_epic** | `machine_reveal/reveal_epic` | 3.30 s | Epic ball: riser, a break hit, Ab-to-C brass, a fast nine-note run, choir and sparkles. |
| **reveal_legendary** | `machine_reveal/reveal_legendary` | 4.47 s | Legendary ball: clacks speeding up into a big break, 'da-da-DAA' brass fanfare, choir, gold shimmer. |
| **reveal_mythic** | `machine_reveal/reveal_mythic` | 6.05 s | Mythic ball: heartbeat clacks, a huge break, an otherworldly Lydian chord opening to a wide C major, all 15 rack balls ringing up and down. |
| **ball_won** | `machine_reveal/ball_won` | 1.99 s | Short generic 'you got a ball' (for lists, repeats, or when the reveal is skipped). |

### Ambience loops

| Sound | Files | Length | Use |
|---|---|---|---|
| **lobby_room_tone_loop** (loop) | `loops/lobby_room_tone_loop` | 40.00 s | Seamless 40 s synthetic room tone with distant, reverberant ball clacks (licence-free). |
| **pool_hall_ambience_loop** (loop) | `loops/pool_hall_ambience_loop` | 60.00 s | Seamless 60 s pool-hall ambience (CC0 recording, Lyon). |
| **pool_hall_ambience_distant_loop** (loop) | `loops/pool_hall_ambience_distant_loop` | 60.00 s | The same hall, muffled and quieter: for menus and the lobby. |

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
