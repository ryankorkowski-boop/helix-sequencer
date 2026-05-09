# Helixville4 Reactive Standup Bassist

## Goal

Upgrade the Helixville4 snowman bassist from pose-based animation into a note-reactive upright bass performer.

The bassist should visually communicate:

- which string is being played
- note movement up/down the neck
- groove intensity
- sustain and resonance
- pluck impact
- bass flow and pocket

## Required String Submodels

- HX_SNOWMAN_BASSIST_STRING_E
- HX_SNOWMAN_BASSIST_STRING_A
- HX_SNOWMAN_BASSIST_STRING_D
- HX_SNOWMAN_BASSIST_STRING_G

## Required Neck Zones

- HX_SNOWMAN_BASSIST_NECK_LOW
- HX_SNOWMAN_BASSIST_NECK_MID
- HX_SNOWMAN_BASSIST_NECK_HIGH
- HX_SNOWMAN_BASSIST_FINGERBOARD

## Required Performance Zones

- HX_SNOWMAN_BASSIST_PLUCK_ZONE
- HX_SNOWMAN_BASSIST_BRIDGE
- HX_SNOWMAN_BASSIST_BODY_RESONANCE
- HX_SNOWMAN_BASSIST_SCROLL

## Reactive Animation Behaviors

### Per-String Illumination

Only the currently active string should strongly pulse.

### Traveling Note Energy

Animated note energy should travel vertically along the active string.

### Neck Position Tracking

Left-hand position should visibly move based on pitch.

### Sustain Shimmer

Held notes should softly shimmer after attack.

### Pluck Impact

Pluck events should briefly flash the pluck zone and bridge.

### Groove Sway

The bassist body should subtly sway with groove timing.

## Helix Mapping Concepts

- E notes -> STRING_E
- A notes -> STRING_A
- D notes -> STRING_D
- G notes -> STRING_G

Velocity controls:

- pulse width
- brightness
- resonance duration

Pitch controls:

- neck position
- note travel direction

## Visual Target

The bassist should feel musically intelligent and groove-oriented.

The approved target direction is the sheet-based reactive bassist concept animation where the strings visibly pulse independently and note energy travels along the bass neck.
