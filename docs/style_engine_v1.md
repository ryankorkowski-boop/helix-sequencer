# Helix Style Engine v1

## Purpose

Translate audio intelligence + timing into deterministic choreography decisions.

This is the missing layer between:

- audio analysis
- layout mapping

## Inputs

- AudioSegment (normalized features)
- LayoutProfile (props + roles + 3D capability)
- StylePreset (BeatDrive, ClassicChristmas, CinematicSweep, PartyMode, SpatialHelix)

## Output

StyleDecision:

- intent (pulse, chase, sweep, sparkle, burst, fade, texture, blackout)
- effect (deterministic mapping)
- targets (prop names)
- palette
- motion
- intensity

## Supported Styles

### BeatDrive
- tight rhythm focus
- favors pulse and chase

### ClassicChristmas
- red/green/white/gold palette
- readable, traditional phrasing

### CinematicSweep
- slow builds and dramatic hits
- sweep + burst dominant

### PartyMode
- aggressive, high density
- burst + rapid chase

### SpatialHelix
- 3D-aware
- Z-axis motion
- prefers props that support 3D

## Design Rules

- Deterministic (same input → same output)
- No randomness
- Layout-aware targeting
- Style-first decision making

## Not Yet Integrated

This module is NOT wired into rendering yet.

Next step:
- connect StyleDecision → xLights effect generator

## Test Coverage

- high energy → sweep/burst
- low energy → fade/texture
- BeatDrive bias
- ClassicChristmas palette enforcement
- SpatialHelix 3D targeting + motion
- determinism guarantee

## Why This Matters

This converts Helix from:

"audio reactive"

into:

"intentional choreography engine"
