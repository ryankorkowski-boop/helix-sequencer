# Layered Drummer Asset Spec

This spec defines the canonical Helix drummer image stack: one locked dim background plus transparent drum-event overlays.

## Goal

The drummer should read as a stable character instead of a random arm sprite sheet. The body, head, scarf, and hat never move. Only the lit strike overlays change per drum event.

## Canvas contract

Every PNG in this asset family must share the exact same canvas size and registration point.

- Format: PNG
- Background: transparent for every event overlay
- Base layer: full-canvas PNG, preferably transparent around the drummer/kit
- Anchor: same x/y origin for every file
- Scaling: no per-layer resizing in xLights or Helix
- Recommended canvas: 2048 x 2048 or the current drummer source canvas

## Layer stack

1. `DRUMMER_BASE_LOCKED_DIM`
   - Always visible while the drummer prop is active.
   - Contains stationary body, head, scarf, hat, torso, legs, and optional dim drum hardware/kit outline.
   - Does not contain active strike arms unless they are very faint neutral idle arms.
   - Suggested brightness: 25-40% of the original.

2. `DRUMMER_EVENT_*`
   - Transparent overlay.
   - Momentary hit layer triggered by percussion analysis.
   - Slightly brighter than the original drummer image.
   - Suggested brightness: 115-140% of original.
   - Contact glow may peak around 150-180%.

## Required files

```text
drummers/snowman_locked/drummer_base_locked_dim.png
drummers/snowman_locked/drummer_hit_kick.png
drummers/snowman_locked/drummer_hit_snare_left.png
drummers/snowman_locked/drummer_hit_snare_right.png
drummers/snowman_locked/drummer_hit_left_tom.png
drummers/snowman_locked/drummer_hit_right_tom.png
drummers/snowman_locked/drummer_hit_floor_tom.png
drummers/snowman_locked/drummer_hit_hihat_closed.png
drummers/snowman_locked/drummer_hit_hihat_open.png
drummers/snowman_locked/drummer_hit_crash_left.png
drummers/snowman_locked/drummer_hit_crash_right.png
drummers/snowman_locked/drummer_hit_ride.png
drummers/snowman_locked/drummer_hit_dual_crash.png
```

## Event overlay composition rule

Each drum-event overlay must include the lit hit target plus the correct contacting arm/stick pose.

Example: `drummer_hit_right_tom.png`

- right tom lit brighter
- right arm positioned so the right stick touches the right tom
- stick contact point visible
- optional tiny impact glow on the tom head
- no duplicated body/head/scarf/hat
- clear transparent background

Example: `drummer_hit_crash_right.png`

- right crash cymbal lit bright
- right arm/stick in cymbal-contact pose
- contact glow at cymbal edge or bell
- short shimmer/ring halo may be included
- no duplicated stationary body elements

## Canonical event IDs

```yaml
base_layer: DRUMMER_BASE_LOCKED_DIM

events:
  kick: DRUMMER_KICK
  snare_left: DRUMMER_SNARE_L
  snare_right: DRUMMER_SNARE_R
  tom_left: DRUMMER_TOM_L
  tom_right: DRUMMER_TOM_R
  floor_tom: DRUMMER_FLOOR_TOM
  hihat_closed: DRUMMER_HIHAT_CLOSED
  hihat_open: DRUMMER_HIHAT_OPEN
  crash_left: DRUMMER_CRASH_L
  crash_right: DRUMMER_CRASH_R
  ride: DRUMMER_RIDE
  dual_crash: DRUMMER_DUAL_CRASH
```

## Timing behavior

The locked base layer stays on through drummer-active sections. Event overlays are short transient hits.

Recommended defaults:

```yaml
base_intensity: 0.32
event_intensity: 1.25
contact_glow_intensity: 1.65
hit_hold_ms: 80
hit_fade_ms: 180
cymbal_shimmer_ms: 450
tom_decay_ms: 220
kick_decay_ms: 260
```

## Mapping guidance

- Kick: light kick drum plus foot/beater pulse if drawn.
- Snare: light snare head plus whichever arm makes contact.
- Toms: light the tom and the matching arm/stick.
- Hi-hat: light hi-hat and left or right stick depending arrangement; closed hits should be tight and short, open hits can shimmer slightly.
- Crash: light cymbal, stick, contact flare, and shimmer decay.
- Ride: smaller repeated cymbal pulse with less explosive glow than crash.
- Dual crash: both cymbals plus both arms/sticks in contact poses.

## Acceptance checklist

- The drummer character remains stationary and recognizable with only the base layer active.
- Every event PNG has transparent background outside the lit moving/strike components.
- Every event PNG aligns exactly over the base image without manual repositioning.
- No event layer re-paints the head, hat, scarf, or torso unless absolutely necessary to cover an overlap artifact.
- Right-side hits use right-side contact poses; left-side hits use left-side contact poses.
- Cymbal hits look different from tom/snare hits by including shimmer or ring glow.
