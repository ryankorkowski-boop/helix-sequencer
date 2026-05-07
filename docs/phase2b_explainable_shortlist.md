# Phase 2B – Explainable Shortlist Integration

Status: implemented as a report-only adapter  
Behavior change: none unless callers explicitly consume the adapter output

## Purpose

Phase 2B introduces explainable shortlist reporting beside the existing shortlist selection system.

The goals are:

1. Preserve existing candidate generation.
2. Preserve existing quality gates.
3. Preserve existing promotion behavior.
4. Add transparent explainable ranking beside the legacy chooser.
5. Detect and report when the explainable system would disagree.

## Adapter

Implemented in:

```text
tools/build_helpers/explainable_shortlist_adapter.py
```

Main entrypoints:

```python
build_explainable_shortlist_report(...)
attach_explainable_shortlist_report(...)
```

## Relationship to Existing Engine

This adapter intentionally sits beside:

```text
tools/build_helpers/variants.py
```

It does NOT replace:

- `choose_best_candidate()`
- `choose_best_candidate_with_preset()`
- `promote_shortlisted_candidate()`

The existing shortlist path remains authoritative.

## Behavior Boundary

Phase 2B:

- does NOT promote variants
- does NOT copy files
- does NOT mutate outputs
- does NOT override the legacy winner
- does NOT change renderer behavior
- does NOT enforce advisory modules

It only compares shortlist outcomes.

## Example

```python
from tools.build_helpers.explainable_shortlist_adapter import (
    build_explainable_shortlist_report,
)

report = build_explainable_shortlist_report(entries, preset="showcase")

payload = report.as_dict()
```

## Agreement Reporting

The adapter reports:

```json
{
  "legacy_winner": "signature",
  "explainable_winner": "cinematic_arc",
  "agreement": false,
  "warnings": [
    "legacy and explainable shortlist winners differ; report-only adapter did not change selection"
  ]
}
```

This allows Helix to measure disagreement safely before any enforcement or promotion changes occur.

## Intended Pipeline Usage

Recommended first integration:

```text
1. Generate variants normally
2. Run legacy shortlist chooser normally
3. Run explainable shortlist adapter
4. Attach explainable report beside existing artifacts
5. Compare results manually
```

## Validation

Run:

```bash
PYTHONPATH=. pytest tests/test_explainable_shortlist_adapter.py
```

Recommended combined validation for Slices 2-10 plus Phases 2A-2B:

```bash
PYTHONPATH=. pytest tests/test_prop_roles.py tests/test_restraint.py tests/test_section_identity.py tests/test_palette_discipline.py tests/test_motif_memory.py tests/test_manual_locks.py tests/test_explainable_variant_scoring.py tests/test_regression_snapshots.py tests/test_gui_quality_options.py tests/test_output_quality_report.py tests/test_explainable_shortlist_adapter.py
```

## Future Wiring Rule

A future Phase 2C may optionally allow explainable shortlist scoring to influence promotion.

That should only occur after:

- deterministic fixture validation
- disagreement-rate tracking
- manual review of disagreements
- feature-flag rollout
- safe fallback to legacy shortlist logic
