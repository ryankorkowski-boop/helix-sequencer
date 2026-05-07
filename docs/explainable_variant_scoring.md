# Explainable Variant Scoring

Status: Slice 8 advisory helper  
Behavior change: none unless a caller explicitly imports and uses it

## Purpose

Helix should be able to explain why one generated variant won over another. A candidate should not win only because of an opaque score. It should show which parts helped or hurt: quality, audit, density restraint, section identity, palette discipline, motif memory, prop-role usage, manual-lock respect, and rejected-effect count.

`tools/build_helpers/explainable_variant_scoring.py` provides a report-only combiner for candidate metrics. It does not replace existing quality gates or promote variants in the active engine yet.

## Inputs

A candidate variant can provide metrics such as:

```json
{
  "variant_id": "variant_01",
  "quality_score": 95.0,
  "audit_score": 89.0,
  "rejected_effects": 9000,
  "restraint": {"score": 0.9},
  "section_identity": {"score": 0.88},
  "palette_discipline": {"score": 0.9},
  "motif_memory": {"score": 0.82},
  "prop_roles": {"score": 0.86},
  "manual_lock_respect": {"score": 1.0}
}
```

## Presets

Initial preset thresholds mirror the existing calibration direction:

| Preset | Min Quality | Min Audit | Max Rejected Effects | Min Explainable Score |
| --- | ---: | ---: | ---: | ---: |
| `general` | 90 | 80 | 28000 | 0.70 |
| `showcase` | 93 | 86 | 18000 | 0.78 |
| `vendor` | 96 | 90 | 12000 | 0.86 |

## Weighted Components

Default weights:

- `quality`: 0.18
- `audit`: 0.14
- `restraint`: 0.12
- `section_identity`: 0.14
- `palette_discipline`: 0.12
- `motif_memory`: 0.10
- `prop_roles`: 0.08
- `manual_lock_respect`: 0.07
- `rejected_effects`: 0.05

The helper normalizes components to `0.0`-`1.0`, computes weighted contributions, and returns findings explaining weak or failing parts.

## Example

```python
from tools.build_helpers.explainable_variant_scoring import rank_variants

shortlist = rank_variants([
    {
        "variant_id": "variant_01",
        "quality_score": 95.0,
        "audit_score": 89.0,
        "rejected_effects": 9000,
        "restraint": {"score": 0.9},
        "section_identity": {"score": 0.88},
        "palette_discipline": {"score": 0.9},
        "motif_memory": {"score": 0.82},
        "prop_roles": {"score": 0.86},
        "manual_lock_respect": {"score": 1.0},
    }
], preset="showcase")

print(shortlist.as_dict())
```

## Report Shape

```json
{
  "preset": "showcase",
  "winner": "variant_01",
  "variants": [
    {
      "variant_id": "variant_01",
      "passed": true,
      "score": 0.88,
      "weighted_components": {},
      "normalized_components": {},
      "raw_metrics": {},
      "findings": []
    }
  ]
}
```

## Important Boundary

This module does not:

- render effects
- write XSQ data
- mutate layout files
- replace `core.effect_engine.py`
- replace existing quality gates
- change current output by default
- promote variants in the active engine by itself

It only explains candidate scores for future reporting and controlled integration.

## Intended Future Use

Near-term integrations:

1. Generate explainable shortlist reports from existing variant metrics.
2. Include Slice 3-7 advisory scores when available.
3. Show pass/fail reasons for `general`, `showcase`, and `vendor` presets.
4. Later, use this as a transparent layer before candidate promotion.

## Validation

Run:

```bash
PYTHONPATH=. pytest tests/test_explainable_variant_scoring.py
```

Recommended combined validation for Slices 2-8:

```bash
PYTHONPATH=. pytest tests/test_prop_roles.py tests/test_restraint.py tests/test_section_identity.py tests/test_palette_discipline.py tests/test_motif_memory.py tests/test_manual_locks.py tests/test_explainable_variant_scoring.py
```

## Future Wiring Rule

When this gets wired into the active engine, it should first produce reports only. After report output is stable, it may become a transparent candidate-promotion input, not an opaque replacement for existing quality gates.
