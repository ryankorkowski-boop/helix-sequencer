# Layered Drummer Asset Spec

This spec defines the approved Helix drummer image stack: one locked dim background plus transparent physical-hit overlays.

## Physical kit

Exactly:

- kick
- snare
- left tom
- right tom
- floor tom
- hi-hat
- left crash
- right crash

There is no fourth tom, extra far-right drum, or separate ride cymbal in the production physical contract.

## Contact rules

- Kick: kick plus foot/beater pulse; **no stick**.
- Hi-hat: hi-hat plus **foot/pedal**; **no stick**.
- Snare: snare plus appropriate arm/stick.
- Left/right/floor tom: target tom plus appropriate arm/stick.
- Left/right crash: target cymbal plus appropriate arm/stick.

The snowman body, head, scarf and hat stay registered and stationary. Only the event target/contact overlay changes.

## Canvas contract

Every PNG shares the exact same canvas and registration point.

- Format: PNG
- Event background: transparent
- Base: full-canvas locked/dim drummer
- Scaling: no per-layer resizing
- Recommended canvas: 2048 x 2048 or the approved source canvas

## Required files

```text
drummers/snowman_locked/drummer_base_locked_dim.png
drummers/snowman_locked/drummer_hit_kick.png
drummers/snowman_locked/drummer_hit_snare.png
drummers/snowman_locked/drummer_hit_left_tom.png
drummers/snowman_locked/drummer_hit_right_tom.png
drummers/snowman_locked/drummer_hit_floor_tom.png
drummers/snowman_locked/drummer_hit_hihat.png
drummers/snowman_locked/drummer_hit_crash_left.png
drummers/snowman_locked/drummer_hit_crash_right.png
```

## Canonical event IDs

```yaml
base_layer: DRUMMER_BASE_LOCKED_DIM

events:
  kick: DRUMMER_KICK
  snare: DRUMMER_SNARE
  tom_left: DRUMMER_TOM_L
  tom_right: DRUMMER_TOM_R
  floor_tom: DRUMMER_FLOOR_TOM
  hihat: DRUMMER_HIHAT
  crash_left: DRUMMER_CRASH_L
  crash_right: DRUMMER_CRASH_R
```

## Timing defaults

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

## Acceptance checklist

- Three toms are visible and separately addressable.
- No fourth tom or extra far-right drum appears.
- Kick overlay contains no stick.
- Hi-hat overlay contains pedal/foot motion and no stick.
- Snare/tom/cymbal overlays contain the appropriate contacting arm/stick.
- Every event PNG has transparent background outside the active components.
- Every event PNG aligns over the base without manual repositioning.
- The character remains recognizable with only the locked base active.
