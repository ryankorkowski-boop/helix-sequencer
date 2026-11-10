# Helixia Layout Direction

Status: Active direction document  
Scope: Helixia canonical layout, props, lots, performers, and validation goals

## 1. Purpose

Helixia is the canonical demonstration and regression layout for Helix.

It should prove that Helix can understand a real-feeling show environment rather than only a flat list of models.

Helixia should test:

1. Spatial layout understanding.
2. Prop-role inference.
3. 3D staging.
4. 2D preview readability.
5. Performer-style props.
6. AC and pixel safety.
7. Houses/lots with different sequencing personalities.
8. Export and import sanity for xLights workflows.

## 2. Core Concept

Helixia is a miniature holiday performance neighborhood.

It may include:

- multiple lots or houses
- rooflines
- windows
- doors
- trees
- arches
- matrix surfaces
- mega trees
- mini trees
- snowflakes/stars
- floods/washes
- snowman band
- cactus performer
- tubeman performer
- optional DJ/helper character props
- whole-neighborhood groups

Each lot should be able to demonstrate a different Helix output personality while still belonging to one coordinated show.

## 3. Lot Personality System

Lots should be intentionally varied.

Example lot roles:

1. Traditional lot: clean red/green/white holiday sequencing.
2. Elegant lot: blue/white/gold, restrained motion, slow reveals.
3. Party lot: higher density, playful colors, performer props.
4. Matrix lot: lyrics, icons, detailed visual surfaces.
5. Rhythm lot: arches, mini trees, beat grids, call/response.
6. Finale lot: wide coverage, controlled spectacle, safe brightness.
7. AC legacy lot: lower-frequency AC-safe pulses and fades.
8. Experimental lot: 3D motion, spatial sweeps, depth testing.

The point is not to make chaos. The point is to test whether Helix can coordinate diversity.

## 4. Required Prop Families

Helixia should include enough model families to exercise the planner:

### Structure Props

- rooflines
- windows
- doors
- outlines
- fences or borders

Default role: structure and continuity.

### Travel Props

- arches
- canes
- pathway lines
- side-to-side lanes

Default role: sweeps, chases, handoffs, directional motion.

### Hero Props

- mega tree
- central matrix
- large star
- central house or central lot

Default role: chorus, finale, reveal, emotional focus.

### Rhythm Props

- mini trees
- stakes
- drums
- beat strips

Default role: beat grid, accents, percussion response.

### Vocal/Face Props

- snowman singer
- optional talking face models
- mouth/eye submodels

Default role: lyrics, phonemes, vocal energy.

### Performer Props

- snowman band
- cactus
- tubeman
- optional helper/DJ character

Default role: comedic/performance moments, not constant activity.

### Mood Props

- floods
- washes
- background glow surfaces

Default role: emotional color field and section mood.

## 5. Snowman Band Direction

The snowman band should act like a stage band.

Recommended members:

1. Singer
2. Guitarist
3. Bassist
4. Drummer
5. Optional keyboardist or horn player

Each member should have distinct model names, groups, and submodels where useful.

Minimum behavior targets:

- drummer responds to kick/snare/tom-like cues
- guitarist responds to rhythmic strums or lead accents
- bassist responds to low-energy/bass cues
- singer responds to lyric or vocal cues
- whole band can hit coordinated chorus/finale moments

The snowman band should not run constantly. It should enter, rest, react, and perform.

## 6. Cactus And Tubeman Direction

Cactus and tubeman are character props.

They should be used for:

- comic relief
- DJ-style callouts
- drop reactions
- lyric jokes if user-provided lyrics support it
- finale hype
- contrast against serious/elegant moments

They should not become visual clutter.

Rules:

1. Give them entrances.
2. Give them exits.
3. Use short expressive moments.
4. Avoid constant full-intensity motion.
5. Keep their behavior tied to section intent.

## 7. 3D Layout Direction

Helixia should support 3D spatial reasoning.

3D goals:

- front/back depth
- left/right staging
- height differences
- central hero zones
- side lots
- performer stage area
- audience-facing readability
- distance-based motion and wave propagation

3D coordinates should not break 2D use. The layout should still read cleanly in xLights layout and preview tabs.

## 8. 2D Readability Requirement

Every Helixia 3D concept must remain understandable in a 2D preview.

2D requirements:

1. Houses/lots should not overlap confusingly.
2. Performer props should be visually separated.
3. Major groups should have clear left/right/center identity.
4. Hero props should be obvious.
5. Prop names should encode useful role information.
6. Groups should support sequencing views and render-order sanity.

If a 3D idea looks bad or confusing in 2D, simplify it.

## 9. Model Naming Guidance

Model names should help Helix infer roles.

Use names like:

- lot_01_roofline
- lot_01_windows
- lot_01_arches
- lot_02_matrix
- helixia_mega_tree
- snowman_band_drummer
- snowman_band_singer_face
- cactus_performer
- tubeman_performer
- neighborhood_whole_house
- performer_stage_group

Avoid ambiguous names like:

- model1
- pixels2
- thing_left
- test_copy

## 10. Group Strategy

Required groups should include:

1. whole_helixia
2. all_houses
3. all_rooflines
4. all_windows
5. all_arches
6. all_trees
7. all_matrices
8. snowman_band
9. character_performers
10. mood_washes
11. rhythm_props
12. hero_props
13. each lot as its own group

Group order should be render-aware and documented where order matters.

## 11. Metadata Requirements

Helixia should eventually emit or include metadata for:

- prop family
- visual role
- lot number
- performer identity
- AC/pixel classification
- power notes
- safe maximum density
- default color behavior
- submodel availability
- 2D/3D coordinates

Metadata can live in JSON sidecars, model descriptions, generator constants, or test fixtures, but it must be machine-readable.

## 12. Validation Goals

Tests should prove:

1. Helixia layout file exists or is reproducibly generated.
2. Required prop families exist.
3. Required groups exist.
4. Snowman band members exist.
5. Cactus and tubeman exist.
6. Lots/houses exist.
7. 3D coordinates are present where intended.
8. No obvious duplicate names are generated.
9. Group references point to existing models.
10. Generated XML is parseable.

## 13. Sequencing Goals For Helixia

Helixia should support these sequencing test scenarios:

1. Subtle/elegant ballad.
2. Classic Christmas song.
3. High-energy dance track.
4. Comedy character moment.
5. Vocal/face-driven section.
6. Drum/percussion-heavy section.
7. Finale escalation.
8. AC-safe legacy behavior.
9. Pixel-dense showcase behavior.
10. 3D spatial sweep behavior.

## 14. First Implementation Slice

The first implementation slice should not try to make every prop beautiful.

It should prove structure:

1. Build or update Helixia generator.
2. Generate deterministic XML.
3. Add role metadata.
4. Add tests that inspect generated XML and metadata.
5. Produce a layout intelligence report.

Visual polish can come later.

## 15. Done Definition

Helixia is usable as the canonical layout when:

1. It builds from code.
2. It has stable tests.
3. It has lots/houses.
4. It has snowman band, cactus, and tubeman.
5. It has role-aware groups.
6. It has metadata for layout intelligence.
7. It can be used by the visual intent planner.
8. It remains readable in both 2D and 3D contexts.
