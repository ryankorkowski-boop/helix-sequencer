# Helixville4 Inflatable Tube Man Target

## Goal

Create a high-impact inflatable tube man performer for Helixville4, designed for the DJ/radio booth or special-lot stage area.

The tube man should be visually simpler than the snowman band but more kinetic: tall, readable, bendy, colorful, and beat-reactive.

## Approved Direction

The tube man should feel like a festive LED prop version of an inflatable air dancer:

- tall waving body
- floppy arms
- expressive face
- fan/base at the bottom
- segmented body wave zones
- exaggerated lean states
- high-energy chorus/freakout motion
- readable from the xLights layout preview

## Required xLights Submodels

- HX_TUBEMAN_BODY
- HX_TUBEMAN_HEAD
- HX_TUBEMAN_FACE
- HX_TUBEMAN_MOUTH
- HX_TUBEMAN_LEFT_ARM
- HX_TUBEMAN_RIGHT_ARM
- HX_TUBEMAN_LEFT_HAND
- HX_TUBEMAN_RIGHT_HAND
- HX_TUBEMAN_BASE_FAN
- HX_TUBEMAN_AIR_COLUMN
- HX_TUBEMAN_BODY_WAVE_LOW
- HX_TUBEMAN_BODY_WAVE_MID
- HX_TUBEMAN_BODY_WAVE_HIGH
- HX_TUBEMAN_LEFT_ARM_WAVE
- HX_TUBEMAN_RIGHT_ARM_WAVE
- HX_TUBEMAN_COLOR_STRIPES
- HX_TUBEMAN_PLATFORM

## Required Animation States

1. IDLE_FLUTTER
2. BEAT_BOUNCE
3. LEFT_WAVE
4. RIGHT_WAVE
5. BOTH_ARMS_UP
6. LEAN_LEFT
7. LEAN_RIGHT
8. COLLAPSE_DIP
9. FULL_FLAIL
10. CHORUS_FREAKOUT

## Reactive Behavior

### Beat Bounce

Kick/downbeat events should pulse the base fan, air column, and low body wave.

### Body Wave

Continuous groove should chase from BODY_WAVE_LOW to BODY_WAVE_MID to BODY_WAVE_HIGH.

### Arm Flail

Accent hits should alternate left and right arm wave regions.

### Chorus Freakout

High-energy chorus sections should trigger full-body color stripes, both arms up, and fast wave chases.

### Collapse Dip

Breaks, drops, or low-energy gaps should briefly dim the air column and collapse the body toward the base.

## Helix Mapping Concepts

- kick/downbeat -> BASE_FAN + AIR_COLUMN + BODY_WAVE_LOW
- snare/accent -> LEFT_ARM_WAVE / RIGHT_ARM_WAVE alternation
- groove energy -> body wave speed
- chorus energy -> CHORUS_FREAKOUT
- section break -> COLLAPSE_DIP
- sustained synth/pad -> COLOR_STRIPES shimmer

## Implementation Requirements

The finished exporter must:

- create a real xLights custom model with non-placeholder dimensions
- export all required submodels
- place the tube man in the Helixville4 DJ/radio booth or special-lot region
- include animation-state metadata
- include validation tests preventing static/tiny placeholder export

## Validation Requirements

Tests should fail if:

- HX_TUBEMAN is exported as a 12x12 placeholder
- BODY_WAVE_LOW/MID/HIGH are missing
- LEFT_ARM_WAVE or RIGHT_ARM_WAVE are missing
- BASE_FAN or AIR_COLUMN are missing
- fewer than 14 tube man submodels are exported
- animation-state metadata is missing

## Status

Specification accepted. Exporter implementation pending.
