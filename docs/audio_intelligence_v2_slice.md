# Audio Intelligence V2 — Slice 1

## Purpose

Introduce a renderer-neutral musical event layer without replacing the existing audio detector, effect engine, Sequence Plan, or XSQ writer.

## Design

The new layer normalizes existing Helix drum detections into a stable event map:

audio -> existing drum detector -> MusicalEventMap -> future Sequence Plan consumers

Each event carries:

- timestamp
- event kind
- confidence
- strength
- source/provider
- instrument
- optional duration/pitch
- diagnostic metadata

## Why this is the first slice

The repository already has substantial audio and drum intelligence. Replacing it wholesale would recreate the multiple-sequencer problem. This slice establishes one downstream contract first.

Future slices can add provider adapters for:

- beat/downbeat analysis
- stem separation
- bass events
- melodic/pitch events
- song sections
- vocal/phoneme events
- confidence fusion across detectors

No XSQ output behavior changes in this slice.

## Safety/compatibility

- Feature is additive.
- Existing sequence commands remain unchanged.
- Existing drum detector remains the source of truth for this first slice.
- Missing/invalid audio fails closed to an empty event map with diagnostics.


## Drummer preview validation
The normalized fused drum events now feed the existing reactive drummer consumer through `models.working_drummer.build_reactive_drummer_from_musical_events`, preserving the existing motion, effect, and XSQ layers.
