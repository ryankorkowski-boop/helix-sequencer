# Legal-Safe Showcase Parity Plan

Status: report-only instrumentation plan  
Goal: improve Helix toward showcase-tier output without copying, scraping, training on, or reproducing copyrighted creator choreography

## Principle

Helix should learn and score general sequencing grammar:

- energy arcs
- chorus contrast
- focal clarity
- motion continuity
- palette discipline
- contrast and restraint
- drop/finale payoff

Helix should not learn or store creator-specific choreography.

## What This Plan Does Not Do

This plan does not:

- download public YouTube videos
- store copyrighted video/audio
- train on public videos
- extract frame-by-frame choreography from creators
- clone vendor or creator sequence files
- build a named-creator emulator

## What This Plan Does

This plan starts with report-only metrics over safe traces:

- synthetic fixtures
- internal Helix-generated telemetry
- user-owned or permissioned sequence traces
- user-authored rules

The showcase metric stack is:

```text
tools/showcase/energy_curve.py
tools/showcase/hero_dominance.py
tools/showcase/motion_continuity.py
tools/showcase/palette_arc.py
tools/showcase/impact_model.py
tools/showcase/showcase_score.py
```

They measure:

- `energy_curve_score`
- `chorus_contrast_delta`
- `drop_amplification_index`
- `finale_escalation_index`
- `showcase_energy_score`
- `focal_clarity_score`
- `hero_moment_score`
- `support_balance_score`
- `visual_mush_penalty`
- `showcase_hero_score`
- `direction_coherence_score`
- `family_continuity_score`
- `transition_smoothness_score`
- `hard_cut_penalty`
- `showcase_motion_score`
- `warm_cool_flow_score`
- `palette_continuity_score`
- `contrast_rhythm_score`
- `abrupt_palette_shift_penalty`
- `showcase_palette_score`
- `anticipation_score`
- `drop_punch_score`
- `finale_payoff_score`
- `peak_density_score`
- `showcase_impact_score`
- composite `showcase_score`

## Source Registry

Any external source used for benchmark planning, metric calibration, or heuristic extraction should be registered and reviewed.

See:

```text
docs/legal/source_registry_contract.md
tools/showcase/source_registry.py
```

## Data Boundary

Allowed to store:

- synthetic test traces
- internal generated output telemetry
- aggregate, non-reconstructive metrics from permissioned sources
- high-level manually reviewed heuristics

Not allowed to store without permission:

- raw third-party media
- third-party sequence files
- frame-by-frame effect mappings
- recognizable creator choreography

## Showcase Metric Rollout

### Slice 1: Compliance and Registry

Implemented:

- `docs/legal/compliance_principles.md`
- `docs/legal/source_registry_contract.md`
- `tools/showcase/source_registry.py`
- `tests/showcase/test_source_registry.py`

### Slice 2: Safe Trace Contract

Implemented:

- `tools/showcase/trace.py`

This creates a source-neutral data shape for synthetic/internal/permissioned traces.

### Slice 3: Showcase Energy Metrics

Implemented:

- `tools/showcase/energy_curve.py`
- `tests/showcase/test_energy_curve.py`

This is report-only. It does not influence generation.

### Slice 4: Showcase Hero Dominance Metrics

Implemented:

- `tools/showcase/hero_dominance.py`
- `tests/showcase/test_hero_dominance.py`

This measures focal clarity, hero moments, support balance, and visual mush risk using only trace summaries. It is report-only and does not influence generation.

### Slice 5: Showcase Motion Continuity Metrics

Implemented:

- `tools/showcase/motion_continuity.py`
- `tests/showcase/test_motion_continuity.py`

This measures directional coherence, motion-family continuity, transition smoothness, and hard-cut risk using only synthetic/internal/permissioned motion traces. It is report-only and does not influence generation.

### Slice 6: Showcase Palette Arc Metrics

Implemented:

- `tools/showcase/palette_arc.py`
- `tests/showcase/test_palette_arc.py`

This measures warm/cool flow, palette continuity, contrast rhythm, and abrupt palette shift risk using only synthetic/internal/permissioned palette traces. It is report-only and does not influence generation.

### Slice 7: Showcase Impact Model Metrics

Implemented:

- `tools/showcase/impact_model.py`
- `tests/showcase/test_impact_model.py`

This measures anticipation, drop punch, finale payoff, and peak density using only synthetic/internal/permissioned impact traces. It is report-only and does not influence generation.

### Slice 8: Composite Showcase Score

Implemented:

- `tools/showcase/showcase_score.py`
- `tests/showcase/test_showcase_score.py`

This combines available showcase component reports into a single explainable composite score. It is report-only and does not influence generation.

## Future Safe Slices

Recommended next slices:

1. explainable comparison only
2. optional soft bias behind flags
3. optional enforcement only after validation

## Acceptance Criteria

Every slice must:

- use synthetic/internal/permissioned fixtures in tests
- avoid raw third-party copyrighted assets
- be report-only at first
- avoid renderer changes
- avoid default output changes
- include tests
- include docs or update this plan

## Audit Statement

This plan is intended to make Helix more cinematic through measurable, original sequencing principles. It is not a plan to imitate or copy any particular creator.
