# Top Show Quality Benchmark

Goal: grade Helix against the practical standard of top viral and vendor-grade synchronized light shows, while rewarding capabilities that are only realistic in a digital engine: hundreds or thousands of deterministic cue placements, dense timing tracks, per-family routing, and aggregate effect-change rates in the tens per second.

## Rubric Dimensions

- Technical density: rewards 35-180 aggregate effect placements per second. This is aggregate layout density, not whole-house strobe rate.
- Musicality: rewards scene architecture, phrase/build/drop/vocal tokens, keyboard or real-note behavior, and audio-reactive timing events.
- Clarity: rewards prop-family coverage, family diversity, and avoiding one placement family dominating the entire show.
- Psychology: rewards attention steering, anticipation/release, Gestalt grouping, continuity of motion, and contrast adaptation.
- Flash safety: penalizes high-contrast flash-like placements above the safety target. Dense motion, sweeps, sparkles, keyboard notes, and texture changes can be fast; full-field flash-like events must remain restrained.

## Safe Perceptual Principles To Use

- Attention steering: create one clear focal family at a time, then rotate focus.
- Anticipation and release: build motion before drops, then resolve with a strong but bounded hit.
- Gestalt grouping: use proximity, symmetry, similarity, and common motion so dense cues read as designed patterns.
- Motion continuity: make fast changes feel like trajectories, not random blinking.
- Contrast adaptation: use visual rests and darker windows so bright moments feel bigger.
- Predictive rhythm: repeat a motif enough for the viewer to learn it, then vary the next repetition.

## Safety Guardrails

- Do not chase seizure-triggering strobe effects. High density should come from distributed prop changes, motion, color evolution, note lanes, and family call/response.
- Keep high-contrast flash-like placements below the benchmark target of 2.7 per second.
- Favor synchronized or intentionally grouped flashes over unsynchronized multi-source flashing.
- Treat saturated red full-field flashing as especially sensitive and keep it rare.
- Let "max" mean technically dense, not visually abusive.

## Implementation

The benchmark is computed inside `core.effect_engine.compute_quality_score` and appears in report payloads at:

- `quality.top_show_benchmark`
- `quality.component_scores.top_show_benchmark`

The overall quality score blends this benchmark into the existing rubric, so Helix can strive for viral-show technical density while still respecting validation, coverage, audit, and safety constraints.
