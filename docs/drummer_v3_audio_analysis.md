# Drummer V3 audio analysis

This document records the Helix-specific multi-detector audio architecture.

## Goals

- Analyze drums from an isolated drum stem when available, while retaining full-mix evidence.
- Run independent detector families rather than one classifier.
- Use adaptive, track-relative thresholds rather than fixed global thresholds.
- Use beat/bar context as evidence, never as permission to invent a hit.
- Produce typed performance events with confidence and provenance.
- Suppress ambiguous `DRUM_BUS` events when typed evidence exists.
- Preserve the canonical `HX_SNOWMAN_DRUMMER_V3` visual: kick, snare, hi-hat, left/right cymbals, and exactly three toms (high/mid/floor), with contact-stick poses on applicable components.

## Detector families

1. Waveform/RMS transient detector.
2. Positive spectral-flux detector on adaptive low/mid/high bands.
3. Band-energy ratio detector.
4. Isolated drum-stem detector when source separation is available.
5. Beat/bar context scorer.

The detector layer produces candidate events. A consensus layer combines candidates by timestamp and target family. No candidate is promoted solely because it falls on a beat.

## Typed-event rules

- Kick: low-band transient plus drum-stem support where available.
- Snare: broadband transient with mid/high support and insufficient low-band dominance.
- Hi-hat: short high-frequency transient; repeated dense hats are allowed.
- Cymbal: high-frequency event with longer decay and/or strong high-band energy; left/right alternation occurs in the performance planner.
- Toms: lower-mid spectral peaks on the drum stem, classified into high/mid/floor by robust frequency ranking and local context. Exactly three targets exist.

## Confidence and abstention

Each event records detector votes, confidence, and provenance. Low-confidence events are dropped instead of being converted into `DRUM_BUS` activity. `DRUM_BUS` remains an explicitly ambiguous diagnostic stream only.

## Regression requirements

A Drummer V3 render must contain evidence for kick, snare, hi-hat, high tom, mid tom, floor tom, left cymbal, and right cymbal. The validator must reject a render where the bus dominates or where any canonical component receives no typed activity.
