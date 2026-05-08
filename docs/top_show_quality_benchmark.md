# Source-Agnostic Quality Benchmark

Status: Active, source-agnostic replacement.

This benchmark must be based only on original Helix metrics, internal fixtures, lawful user inputs, and explicit source-hygiene rules.

## Goal

Grade Helix-generated output using original, source-agnostic engineering criteria:

- musical phrase alignment
- visual readability
- layer discipline
- prop-family coverage
- color discipline
- motion coherence
- contrast and rest usage
- flash-safety constraints
- reproducible validation reports

## Safe Perceptual Principles

- Create one clear focal family at a time, then rotate focus intentionally.
- Use anticipation and release through original Helix planning.
- Use proximity, symmetry, similarity, and common motion as general visual-design principles.
- Make fast changes read as trajectories rather than random blinking.
- Use darker windows so bright moments have contrast.
- Repeat original Helix motifs with controlled variation.

## Safety Guardrails

- Do not chase seizure-triggering strobe effects.
- High density should come from distributed prop changes, motion, color evolution, note lanes, and family call/response.
- Keep full-field, high-contrast flash-like events restrained.
- Favor synchronized or intentionally grouped flashes over unsynchronized multi-source flashing.
- Treat saturated red full-field flashing as especially sensitive and keep it rare.
- Let "max" mean technically dense, not visually abusive.

## Implementation

The benchmark is computed inside `core.effect_engine.compute_quality_score` and appears in report payloads at:

- `quality.top_show_benchmark`
- `quality.component_scores.top_show_benchmark`

The field name is retained for backward compatibility, but the benchmark must be interpreted only as a source-agnostic Helix quality metric.

## Generator Response

The audio-reactive generator should gain technical density from safe, original Helix mechanisms:

- `energy_wave`
- `mid_sweep`
- `treble_sparkle`
- `build_ramp`
- distributed motion
- note lanes
- texture changes
- family call/response

Do not tune this benchmark from external choreography, source-derived styles, restricted files, or unclear-rights media.
