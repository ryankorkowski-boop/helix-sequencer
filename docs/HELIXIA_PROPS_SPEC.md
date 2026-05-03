# Helixia Props Specification

## Purpose

This document defines the structure, constraints, and future direction for all Helixia character and prop systems.

This includes:

1. snowman band
2. cactus + tube man DJ booth
3. special interactive props

This system is separate from:

1. Helixia layout builder
2. Helix sequencing engine

## Absolute Prohibitions

Do NOT implement:

1. audio analysis
2. beat detection
3. sequencing logic
4. effect placement
5. xsq generation
6. timing logic
7. layout generation
8. modification of Helixia layout XML

If any of the above appear, the implementation is invalid.

## System Architecture

Props must be designed as:

1. modular
2. reusable
3. exportable
4. compatible with xLights sequencing expectations

Each prop must support:

1. model definition
2. submodels
3. grouping
4. future animation hooks, but NOT implemented here

## Export Requirement

All props must be:

1. usable as native Helixia props
2. exportable as standalone xLights-compatible models

This allows:

1. reuse in external sequences
2. compatibility with vendor-style sequencing

## Legal & Compatibility Constraints

Props may be inspired by vendor designs, but must:

1. NOT be visually identical
2. remain legally distinct
3. maintain structural compatibility

Goal:

1. sequences created with Helixia props should transfer to real props with minimal adjustment

## Snowman Band System

## Members

1. `HX_SNOWMAN_BASSIST`
2. `HX_SNOWMAN_GUITARIST`
3. `HX_SNOWMAN_DRUMMER`
4. `HX_SNOWMAN_SINGER`
5. `HX_SNOWMAN_SINGER_FEMALE`

## Structural Requirements

Each band member must include:

1. `BODY` model
2. `INSTRUMENT` model, if applicable
3. submodels for arms
4. submodels for head
5. submodels for torso
6. submodels for instrument sections

Example naming:

1. `HX_SNOWMAN_DRUMMER_BODY`
2. `HX_SNOWMAN_DRUMMER_ARMS`
3. `HX_SNOWMAN_DRUMMER_STICKS`

## Grouping

Each member must have:

1. individual group
2. inclusion in `HX_SNOWMAN_BAND`
3. inclusion in `HELIXIA_STAGE`

## Animation Hooks (Future Only)

Do NOT implement behavior here.

Define structure only.

Future behavior examples:

Drummer:

1. arms raised before tom/cymbal hits
2. stick twirling during idle or transitions

Singer:

1. phoneme/mouth system, optional future
2. emotion-based animation

## Instrument Expectations

1. instruments must be separate models
2. instruments must support independent lighting control
3. instruments must be compatible with sequencing mapping

## Cactus + Tube Man DJ System

## Core Models

1. `HX_CACTUS_BODY`
2. `HX_CACTUS_FACE`
3. `HX_TUBEMAN_BODY`
4. `HX_TUBEMAN_ARMS`
5. `HX_DJ_BOOTH`

## Grouping

1. `HX_CACTUS_TUBEMAN_GROUP`
2. `HELIXIA_STAGE`

## Design Direction

Tube Man:

1. exaggerated proportions
2. chaotic movement potential
3. high visual energy

Cactus:

1. more rigid structure
2. expressive face
3. comedic contrast to tube man

## Behavior Concept (Future Only)

Do NOT implement now.

1. tube man reacts energetically
2. cactus behaves like a confused DJ host

## Special Props

## Floor Piano (Big-style)

Models:

1. `HX_FLOOR_PIANO_BASE`
2. `HX_FLOOR_PIANO_KEYS`

Requirements:

1. each key must be individually addressable
2. consistent spacing and layout

Future Behavior:

1. keys light when triggered
2. optional bouncing snowflake effects

## "Crip-Walking" Reindeer

Model:

1. `HX_REINDEER_DANCE`

Requirements:

1. segmented structure for animation
2. legs and body separable

Future Behavior:

1. rhythmic movement patterns
2. stylized dance motion

## Structural Standards

## Naming Convention

All props must use:

```text
HX_<CATEGORY>_<DETAIL>
```

Examples:

1. `HX_SNOWMAN_DRUMMER`
2. `HX_CACTUS_BODY`
3. `HX_FLOOR_PIANO_KEYS`

## Determinism

All prop generation must be:

1. deterministic
2. reproducible
3. testable

## Test Requirements

Future prop tests must verify:

1. model existence
2. correct grouping
3. correct naming
4. submodel structure

## Performance Constraints

1. avoid excessive submodel counts
2. maintain usability in xLights
3. optimize grouping for large layouts

## Implementation Boundary

This phase MUST ONLY:

1. define prop structure
2. define naming
3. define grouping

This phase MUST NOT:

1. animate
2. sequence
3. simulate behavior
4. integrate audio

## Long-Term Vision

Props become:

1. intelligent sequencing targets
2. exportable assets
3. reusable across Helix layouts
4. compatible with real-world props

## Development Rules

Every change must:

1. be small
2. be testable
3. stay within scope
4. not affect Helixia layout system

## Critical Separation

Helixia System is split into:

1. Layout (spatial)
2. Props (structure)
3. Sequencing (behavior)

These must NEVER be mixed in a single implementation step.

