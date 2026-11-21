# Cue Clash UI sounds

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

## The sounds (52 sounds, 87 files)

### Buttons

| Sound | Files | Length | Use |
|---|---|---|---|
| **button_hover** | `buttons/button_hover_01` … ×3 | 0.03 s | Pointer enters a button: two balls barely touching. |
| **button_click** | `buttons/button_click_01` … ×4 | 0.05 s | Generic button press: a crisp ball clack with a little wood. |
| **button_confirm** | `buttons/button_confirm_01` … ×2 | 0.79 s | Confirm / OK / Play: cue tip taps the ball, two rising clack tones. |
| **button_back** | `buttons/button_back_01` … ×2 | 1.04 s | Back / cancel / close: two falling clack tones onto the cloth. |
| **button_error** | `buttons/button_error_01` … ×2 | 0.80 s | Error / not allowed: a miscue (tip skids off the ball) and two dull knocks. |
| **button_disabled** | `buttons/button_disabled` | 0.04 s | Pressing a disabled button: a muted felt thud. |
| **toggle_on** | `buttons/toggle_on` | 0.49 s | Switch / checkbox on: short roll, ball clicks into place, small up-tone. |
| **toggle_off** | `buttons/toggle_off` | 0.43 s | Switch / checkbox off: click, small down-tone, short roll away. |
| **select** | `buttons/select_01` … ×2 | 0.53 s | Select an item in a list or grid: clack plus a short tone. |
| **select_note_1** | `buttons/select_note_1` | 0.95 s | Pitched select (C5); play 1..8 in order for steps, combos or a count-up. |
| **select_note_2** | `buttons/select_note_2` | 0.90 s | Pitched select (D5); play 1..8 in order for steps, combos or a count-up. |
| **select_note_3** | `buttons/select_note_3` | 0.85 s | Pitched select (E5); play 1..8 in order for steps, combos or a count-up. |
| **select_note_4** | `buttons/select_note_4` | 0.78 s | Pitched select (G5); play 1..8 in order for steps, combos or a count-up. |
| **select_note_5** | `buttons/select_note_5` | 0.74 s | Pitched select (A5); play 1..8 in order for steps, combos or a count-up. |
| **select_note_6** | `buttons/select_note_6` | 0.68 s | Pitched select (C6); play 1..8 in order for steps, combos or a count-up. |
| **select_note_7** | `buttons/select_note_7` | 0.64 s | Pitched select (D6); play 1..8 in order for steps, combos or a count-up. |
| **select_note_8** | `buttons/select_note_8` | 0.61 s | Pitched select (E6); play 1..8 in order for steps, combos or a count-up. |
| **equip** | `buttons/equip` | 0.74 s | Equip a ball / cue: chalk twist on the tip, then a firm clack. |
| **unequip** | `buttons/unequip` | 0.54 s | Unequip: lighter clack, falling tone, brush away. |
| **coin_tick** | `buttons/coin_tick_01` … ×3 | 0.18 s | One coin in a currency count-up (play rapidly, pitch up slightly). |

### Navigation

| Sound | Files | Length | Use |
|---|---|---|---|
| **tab_switch** | `navigation/tab_switch_01` … ×3 | 0.06 s | Switch tab / page: quick brush and a light clack. |
| **menu_open** | `navigation/menu_open` | 0.20 s | Open a menu / panel: cue stroke whoosh, lands on the cloth. |
| **menu_close** | `navigation/menu_close` | 0.16 s | Close a menu / panel: soft thud, whoosh away. |
| **popup_open** | `navigation/popup_open` | 0.96 s | Dialog / popup appears: soft pocket 'thup' and a rising fifth. |
| **popup_close** | `navigation/popup_close` | 1.00 s | Dialog / popup closes: falling fifth onto the cloth. |
| **swipe_left** | `navigation/swipe_left_01` … ×2 | 0.23 s | Swipe / carousel to the left: cloth swish moving right to left. |
| **swipe_right** | `navigation/swipe_right_01` … ×2 | 0.23 s | Swipe / carousel to the right: swish moving left to right. |
| **scroll_tick** | `navigation/scroll_tick_01` … ×3 | 0.03 s | One step while scrolling a list. |
| **slider_tick** | `navigation/slider_tick` | 0.03 s | Slider moves one step (raise PlaybackSpeed with the value). |
| **notification** | `navigation/notification` | 1.00 s | Toast / notification: two clack tones with a faint bell. |

### Loadout rack (picking balls into the triangle)

| Sound | Files | Length | Use |
|---|---|---|---|
| **rack_place_ball** | `loadout_rack/rack_place_ball_01` … ×5 | 0.07 s | Drop a ball into a slot of the triangle: clack against its neighbour, wooden rack, small settle. |
| **rack_pick_ball** | `loadout_rack/rack_pick_ball_01` … ×3 | 0.09 s | Lift a ball out of the rack. |
| **rack_swap** | `loadout_rack/rack_swap_01` … ×2 | 0.18 s | Swap two balls in the rack: click, short roll, click. |
| **rack_invalid** | `loadout_rack/rack_invalid_01` … ×2 | 0.53 s | Ball can't go there: bumps the wooden rack and bounces back. |
| **rack_complete** | `loadout_rack/rack_complete` | 1.14 s | Rack is full / loadout saved: the triangle tightens the pack, then a rising arpeggio. |
| **rack_lift** | `loadout_rack/rack_lift` | 0.35 s | Lift the triangle off the pack (leave the loadout screen / start). |
| **rack_shuffle** | `loadout_rack/rack_shuffle_01` … ×2 | 0.60 s | Randomise the loadout: balls rattling inside the rack. |
| **rack_clear** | `loadout_rack/rack_clear` | 0.89 s | Clear the rack: balls roll out and scatter. |
| **rack_slot_hover** | `loadout_rack/rack_slot_hover_01` … ×2 | 0.03 s | Dragged ball hovers over a free slot. |
| **ball_inspect_spin** | `loadout_rack/ball_inspect_spin` | 0.95 s | Spin a ball to inspect it: rolls on the cloth and slows down. |

### Ball machine (mono, so they also work as 3D sounds on the machine)

| Sound | Files | Length | Use |
|---|---|---|---|
| **token_insert** | `machine/token_insert_01` … ×2 | 0.85 s | Token goes into the slot: slides in, the coin mech clicks, it drops into the box. |
| **token_reject** | `machine/token_reject` | 0.78 s | Token rejected: drops back into the return cup and rattles. |
| **crank_click** | `machine/crank_click_01` … ×3 | 0.02 s | One ratchet click (for a crank the player drags step by step). |
| **crank_turn** | `machine/crank_turn_01` … ×2 | 1.23 s | One full turn of the crank: ratchet clicks speed up and slow down, gears, spring, final clunk. |
| **crank_turn_loop** (loop) | `machine/crank_turn_loop` | 1.00 s | Seamless loop of continuous cranking (1 s, 10 clicks) while the player holds the crank. |
| **globe_rattle** | `machine/globe_rattle_01` … ×2 | 1.98 s | Balls tumbling in the glass globe while the machine mixes (swells and settles, 2 s). |
| **globe_rattle_loop** (loop) | `machine/globe_rattle_loop` | 2.00 s | Seamless 2 s loop of the globe rattling, for a mixing animation of any length. |
| **ball_release** | `machine/ball_release_01` … ×2 | 0.23 s | The gate opens: mechanism clunk, the ball drops onto the chute. |
| **ball_roll_chute** | `machine/ball_roll_chute_01` … ×2 | 1.60 s | Ball rolls down the spiral chute, speeding up (1.6 s). |
| **ball_drop_tray** | `machine/ball_drop_tray_01` … ×2 | 0.55 s | Ball lands in the prize tray: bounces and settles. |
| **tray_flap** | `machine/tray_flap` | 0.16 s | The little prize door flaps open. |
| **machine_denied** | `machine/machine_denied` | 0.91 s | Not enough tokens / machine busy: dull clunks and a falling semitone. |

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
