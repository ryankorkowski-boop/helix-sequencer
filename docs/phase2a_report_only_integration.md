# Phase 2A – Report-Only Integration

Status: implemented as a safe aggregation hook  
Behavior change: none unless callers explicitly invoke the hook

## Purpose

Phase 2A is the first controlled integration step after the infrastructure slices.

The goal is:

1. Run normal sequence generation.
2. Run advisory scoring after generation.
3. Attach quality diagnostics beside output artifacts.
4. Avoid changing renderer behavior, candidate selection, or generation output.

## Aggregation Hook

Implemented in:

```text
tools/build_helpers/output_quality_report.py
```

Main entrypoint:

```python
build_output_quality_report(...)
```

The hook combines advisory outputs from:

- prop roles
- density restraint
- section identity
- palette discipline
- motif memory
- manual locks
- explainable variant scoring
- compact regression snapshots

## Safety Boundary

Phase 2A:

- does NOT modify `core.effect_engine.py`
- does NOT render effects
- does NOT write XSQ data
- does NOT mutate layouts
- does NOT reject variants
- does NOT enforce manual locks
- does NOT alter generation behavior

It only generates report payloads.

## Example

```python
from tools.build_helpers.output_quality_report import build_output_quality_report

report = build_output_quality_report(
    options={
        "quality_preset": "showcase",
        "style_preset": "classic_christmas",
    },
    model_names=["mega_tree", "roofline"],
    sections=[...],
    motifs=[...],
    variants=[...],
)

payload = report.as_dict()
```

## Missing Input Handling

The hook is intentionally tolerant.

If a pipeline stage does not yet provide:

- motifs
- sections
- manual locks
- variants
- cues

then the hook skips those reports and emits warnings instead of failing generation.

Example warning:

```text
section_identity skipped: no sections provided
```

## Intended Pipeline Usage

Recommended first integration:

```text
1. Generate sequence normally
2. Build output quality report
3. Serialize JSON beside existing artifacts
4. Review reports manually
```

Example future artifact layout:

```text
outputs/
  song_02.xsq
  song_02.audit.json
  song_02.quality_report.json
```

## Validation

Run:

```bash
PYTHONPATH=. pytest tests/test_output_quality_report.py
```

Recommended combined validation for Slices 2-10 plus Phase 2A:

```bash
PYTHONPATH=. pytest tests/test_prop_roles.py tests/test_restraint.py tests/test_section_identity.py tests/test_palette_discipline.py tests/test_motif_memory.py tests/test_manual_locks.py tests/test_explainable_variant_scoring.py tests/test_regression_snapshots.py tests/test_gui_quality_options.py tests/test_output_quality_report.py
```

## Future Wiring Rule

Phase 2B may integrate explainable reports into shortlist ranking.

Phase 2C may optionally enforce:

- density restraint
- manual lock respect
- motif reuse biasing
- palette discipline

Those later phases should remain feature-flagged and opt-in until validated on deterministic fixtures.
