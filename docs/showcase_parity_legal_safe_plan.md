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

The first metric slice is:

```text
tools/showcase/energy_curve.py
```

It measures:

- `energy_curve_score`
- `chorus_contrast_delta`
- `drop_amplification_index`
- `finale_escalation_index`
- `showcase_energy_score`

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

## Future Safe Slices

Recommended next slices:

1. `tools/showcase/hero_dominance.py`
2. `tools/showcase/motion_continuity.py`
3. `tools/showcase/palette_arc.py`
4. `tools/showcase/impact_model.py`
5. `tools/showcase/showcase_score.py`
6. report-only integration into output quality reports
7. explainable comparison only
8. optional soft bias behind flags
9. optional enforcement only after validation

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
