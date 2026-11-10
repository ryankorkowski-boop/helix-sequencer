# Showcase Bias Activation Guide

## Overview

Phase 3 introduces an optional `showcase_bias` weight to the explainable
variant scoring system. By default this value is `0.0`, which preserves
identical behavior to previous scoring logic.

When enabled (> 0.0), the final explainable score is blended with an
optional `showcase_score` present in the variant payload.

```
blended_score = (1 - showcase_bias) * explainable_score
                + showcase_bias * showcase_score
```

## Safety Properties

- Default behavior unchanged (`showcase_bias = 0.0`)
- Deterministic scoring preserved
- Threshold gates still enforced
- Ranking remains sorted by `(passed, score)`
- No renderer mutation

## Recommended Safe Ranges

| Preset     | Suggested Max Bias |
|------------|-------------------|
| general    | 0.25              |
| showcase   | 0.40              |
| vendor     | 0.20              |

Bias values above 0.5 are discouraged unless running controlled experiments.

## Example Usage

```python
rank_variants(
    variants,
    preset="showcase",
    weights={"showcase_bias": 0.3},
)
```

## Activation Strategy

1. Run baseline scoring (bias = 0.0)
2. Log top-N ordering
3. Re-run with small bias (0.2–0.3)
4. Compare ordering shifts
5. Approve only if improvements are intentional

---

This feature is experimental and intended for controlled showcase tuning,
not core engine replacement.
