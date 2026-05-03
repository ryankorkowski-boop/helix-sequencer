# Helixia Creative Direction

## Purpose

Helixia is a fictional Christmas-light city used as the primary spatial environment for Helix Sequencer.

It is a:

1. layout system
2. visualization environment
3. multi-style sequencing testbed

It is NOT:

1. an autosequencer
2. an audio engine
3. an effects generator

## Absolute Prohibitions

Do NOT implement:

1. audio analysis
2. beat detection
3. librosa
4. xsq generation
5. effect placement
6. sequencing logic
7. timing logic
8. model discovery from existing layouts

If any of the above appear, the implementation is invalid.

## Core Identity

Helixia is a futuristic Christmas-light city centered around a glowing DNA helix.

Design goals:

1. clean in 2D (xLights preview)
2. meaningful in 3D (future spatial mapping)
3. modular and testable
4. scalable without destroying performance

## Global Layout Rules

1. Built in 3D, must present cleanly in 2D.
2. All lots must function independently.
3. All lots must function as part of `HELIXIA_ALL`.
4. Layout must remain performant.
5. Stage occupies 2 front-center lots.

## Helix Style Representation System

Each lot represents a different Helix output style.

A style defines:

1. color palette
2. effect philosophy
3. motion characteristics
4. future timing strategy

IMPORTANT:

This is NOT implemented in the layout builder.

The layout builder only provides:

1. spatial structure
2. grouping
3. placeholders

## Lots Overview

## Lot 1 - White Mansion (Elegant Hybrid)

1. Large mansion with pillars.
2. Strictly white lights.
3. Includes icicles, arches, roofline, and pillars.
4. Mix of AC and pixel.

Rules:

1. No color variation.
2. Must feel premium and symmetrical.

## Lot 2 - GP Legacy 3D Interpretation

1. Based on GP legacy structure.
2. Recreated in 3D.

Rules:

1. NOT visually identical.
2. Must allow similar sequencing behavior.
3. Legally distinct but structurally compatible.

## Lot 3 - Classic RGB Vintage

1. Red / white / green pixel layout.
2. Traditional house styling.

Rules:

1. Nostalgic feel.
2. Avoid modern/minimalist design.

## Lot 4 - Futuristic Minimalist

1. Minimal elements.
2. Maximum impact.

Rules:

1. Low model count.
2. Strong geometric identity.
3. High contrast motion potential.

## Lots 5-8 - Mega Showcase Property (4 Lots)

1. Large multi-lot installation.
2. Demonstrates xLights capabilities.

Include:

1. mega trees
2. matrices
3. arches
4. spinners
5. complex props

Constraint:

1. Must NOT tank performance.

## Park Lot - Fibonacci Spiral

1. Tree variants arranged in Fibonacci spiral.
2. Central mega tree.

Rules:

1. Mathematically consistent.
2. Visually organic.

## Rear Matrix Wall

1. Large matrix backdrop.

Purpose:

1. text
2. global effects
3. animations

## Vendor Prop Showcase Lot

Includes:

1. coro-style props
2. singing faces
3. bulbs
4. singing trees

Rules:

1. NOT visually identical to vendors.
2. MUST remain technically compatible with sequences.

## Stage Area (2 Lots)

Contains placeholders only:

1. `HX_STAGE_SNOWMAN_BAND`
2. `HX_STAGE_CACTUS_TUBE_DJ`

No behavior implemented at layout stage.

## Snowman Band (Future System)

Members:

1. bassist
2. guitarist
3. drummer
4. singer

