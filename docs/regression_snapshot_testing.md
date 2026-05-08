# Regression Snapshot Testing

Status: Slice 9 advisory/test helper  
Behavior change: none unless tests or callers explicitly import and use it

## Purpose

Helix needs regression coverage that catches output-quality drops without snapshotting full `.xsq`, `.lms`, video, or vendor/proprietary sequence files.

`tools/build_helpers/regression_snapshots.py` provides compact quality-report snapshot helpers. The target is to compare stable metrics with tolerances instead of brittle full-file output.

## Why Compact Snapshots

Full sequence files are noisy and can change for harmless reasons. Compact quality snapshots focus on measurable output health:

- `quality_score`
- `audit_score`
- `explainable_score`
- `restraint_score`
- `section_identity_score`
- `palette_discipline_score`
- `motif_memory_score`
- `manual_lock_respect_score`
- `rejected_effects`

## Example

```python
from tools.build_helpers.regression_snapshots import (
    compact_quality_snapshot,
    assert_quality_snapshot_within_tolerance,
)

expected = {
    "quality_score": 94.0,
    "audit_score": 88.0,
    "rejected_effects": 10000,
}

actual = compact_quality_snapshot({
    "variant_id": "variant_01",
    "quality_score": 93.8,
    "audit_score": 87.8,
    "rejected_effects": 10400,
    "volatile_render_path": "test_runs/tmp/output.xsq",
})

assert_quality_snapshot_within_tolerance(expected, actual)
```

## Default Tolerances

Initial tolerances:

| Metric | Tolerance |
| --- | ---: |
| `quality_score` | 0.5 |
| `audit_score` | 0.5 |
| `explainable_score` | 0.02 |
| `restraint_score` | 0.03 |
| `section_identity_score` | 0.03 |
| `palette_discipline_score` | 0.03 |
| `motif_memory_score` | 0.03 |
| `manual_lock_respect_score` | 0.03 |
| `rejected_effects` | 500 |

Improvements outside tolerance are warnings, not failures. Regressions outside tolerance are failures.

## Important Boundary

This module does not:

- render effects
- write XSQ data
- mutate layout files
- require proprietary/vendor sequences
- snapshot full generated sequence files
- change current output by default

It only compares compact quality-report metrics.

## Intended Future Use

Near-term integrations:

1. Store one or more baseline quality snapshots for small deterministic fixtures.
2. Compare fresh reports against the baseline in CI or local smoke tests.
3. Keep tolerances loose enough to avoid false failures from harmless noise.
4. Fail when major quality, audit, or rejected-effect regressions occur.
5. Add advisory scores from Slices 3-8 as they are wired into reports.

## Validation

Run:

```bash
PYTHONPATH=. pytest tests/test_regression_snapshots.py
```

Recommended combined validation for Slices 2-9:

```bash
PYTHONPATH=. pytest tests/test_prop_roles.py tests/test_restraint.py tests/test_section_identity.py tests/test_palette_discipline.py tests/test_motif_memory.py tests/test_manual_locks.py tests/test_explainable_variant_scoring.py tests/test_regression_snapshots.py
```

## Future Wiring Rule

When this is wired into the active engine, snapshot the quality report, not the generated sequence file. Baselines should use Helix-generated fixtures only and avoid third-party/vendor choreography.
