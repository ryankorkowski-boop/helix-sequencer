# Helixville4 Floor Piano Target

## Goal

Create a deterministic, note-reactive floor piano prop for Helixville4 that showcases Helix musical intelligence more clearly than a simulated inflatable prop.

The floor piano should act as a giant stage-floor keyboard that can visualize melody, chords, bass notes, pitch movement, velocity, sustain, and song-section energy.

## Placement

Recommended placement: front-center performance area, visible from the Helixia/xLights layout camera.

It can also serve as a musical bridge between:

- snowman band
- DJ/radio booth
- Helixia special lots
- audio-reactive sequencing demos

## Required Layout

Initial implementation target:

- 2 octaves
- 24 white keys
- 14 black keys
- readable oversized floor footprint
- deterministic key order from low to high
- named note submodels
- octave groups
- chord groups
- sustain/glow regions

## Required xLights Model

Primary model:

- HX_FLOOR_PIANO

Required global submodels:

- HX_FLOOR_PIANO_WHITE_KEYS
- HX_FLOOR_PIANO_BLACK_KEYS
- HX_FLOOR_PIANO_OCTAVE_LOW
- HX_FLOOR_PIANO_OCTAVE_HIGH
- HX_FLOOR_PIANO_CHORD_BLOOM
- HX_FLOOR_PIANO_SUSTAIN_GLOW
- HX_FLOOR_PIANO_LEFT_TO_RIGHT_CHASE
- HX_FLOOR_PIANO_VELOCITY_LANE
- HX_FLOOR_PIANO_PLATFORM

Required note submodels:

- HX_FLOOR_PIANO_C_LOW
- HX_FLOOR_PIANO_CS_LOW
- HX_FLOOR_PIANO_D_LOW
- HX_FLOOR_PIANO_DS_LOW
- HX_FLOOR_PIANO_E_LOW
- HX_FLOOR_PIANO_F_LOW
- HX_FLOOR_PIANO_FS_LOW
- HX_FLOOR_PIANO_G_LOW
- HX_FLOOR_PIANO_GS_LOW
- HX_FLOOR_PIANO_A_LOW
- HX_FLOOR_PIANO_AS_LOW
- HX_FLOOR_PIANO_B_LOW
- HX_FLOOR_PIANO_C_HIGH
- HX_FLOOR_PIANO_CS_HIGH
- HX_FLOOR_PIANO_D_HIGH
- HX_FLOOR_PIANO_DS_HIGH
- HX_FLOOR_PIANO_E_HIGH
- HX_FLOOR_PIANO_F_HIGH
- HX_FLOOR_PIANO_FS_HIGH
- HX_FLOOR_PIANO_G_HIGH
- HX_FLOOR_PIANO_GS_HIGH
- HX_FLOOR_PIANO_A_HIGH
- HX_FLOOR_PIANO_AS_HIGH
- HX_FLOOR_PIANO_B_HIGH

## Required Animation States

1. IDLE_SHIMMER
2. NOTE_HIT
3. MELODY_RUN
4. CHORD_BLOOM
5. BASS_NOTE_PULSE
6. SUSTAIN_TRAIL
7. OCTAVE_SWEEP
8. LEFT_TO_RIGHT_CHASE
9. DROP_IMPACT
10. FINALE_ALL_KEYS

## Reactive Behavior

### Note Hit

Individual note submodels should pulse when corresponding pitch classes are detected or generated.

### Chord Bloom

Multiple simultaneous notes should trigger a harmonic bloom across the chord notes plus HX_FLOOR_PIANO_CHORD_BLOOM.

### Velocity

Velocity/intensity should control brightness, pulse width, and sustain duration.

### Sustain

Held notes should continue glowing through HX_FLOOR_PIANO_SUSTAIN_GLOW.

### Melody Run

Fast melodic passages should chase across keys in pitch order.

### Drop Impact

Drops should trigger alternating white/black key impacts, octave sweeps, and full platform pulse.

## Helix Mapping Concepts

- MIDI/note pitch -> matching note key submodel
- chroma energy -> pitch-class keys
- bass notes -> low-octave key emphasis
- chords -> multiple note keys + chord bloom
- melody contour -> left-to-right or right-to-left chase
- sustain/pads -> sustain glow
- chorus/drop -> octave sweep + all-key impact

## Implementation Requirements

The finished exporter must:

- create a real xLights custom model with non-placeholder dimensions
- export named note submodels
- export global key groups
- preserve key ordering low-to-high
- include animation-state metadata
- support future MIDI/audio-derived note mapping
- include validation tests preventing placeholder or missing-note exports

## Validation Requirements

Tests should fail if:

- HX_FLOOR_PIANO is exported as a 12x12 placeholder
- fewer than 24 note submodels exist
- global white/black/octave/chord/sustain groups are missing
- note ordering metadata is missing
- animation-state metadata is missing
- the layout cannot be built with the floor piano enabled

## Status

Specification accepted. Exporter implementation started.
