# Palette Discipline Scoring

Status: Slice 5 advisory helper  
Behavior change: none unless a caller explicitly imports and uses it

## Purpose

Color discipline is one of the fastest ways to make Helix output look more professional. A generated sequence can have good timing and prop placement but still look chaotic if every section changes to unrelated colors.

`tools/build_helpers/palette_discipline.py` provides advisory scoring for palette consistency, style alignment, color churn, and recurring motif color reuse.

## What It Measures

Current report scores:

- `palette_consistency_score`: whether sections declare palette/color intent without using too many unrelated palettes
- `style_alignment_score`: whether selected palettes match the requested style
- `color_churn_score`: whether adjacent sections keep enough color-family continuity
- `motif_reuse_score`: whether repeated section kinds reuse recognizable color identity
- `score`: weighted combined advisory score

## Named Palettes

Initial palette families include:

- `classic_christmas`
- `classic_christmas_bright`
- `classic_christmas_finale`
- `winter_soft`
- `winter_bright`
- `warm_elegant`
- `rock`
- `edm_neon`
- `comedy_bright`
- `spooky`
- `patriotic`

These are advisory names only. They do not recolor a sequence by themselves.

## Style Alignment

Initial style mappings include:

- `general`
- `showcase`
- `vendor`
- `classic_christmas`
- `edm`
- `rock`
- `ballad`
- `comedy`
- `spooky`
- `patriotic`

`edm` and `comedy` are intentionally more tolerant of abrupt color changes.

## What It Flags

Current findings include:

- no sections provided
- missing palette/color intent
- too many distinct palettes across sections
- palette/style mismatch
- abrupt color family changes
- weak recurring-section palette motif

## Why This Improves Output

Professional sequences usually use controlled color language. Sections can still contrast, but the show should not feel like every measure forgot what the previous one looked like.

Palette discipline helps Helix reward:

- readable color identity
- style-appropriate palettes
- recurring chorus/section motifs
- intentional contrast instead of random churn
- polished finale color treatment

## Example

```python
from tools.build_helpers.palette_discipline import score_palette_discipline

report = score_palette_discipline([
    {
        "name": "intro",
        "kind": "intro",
        "palette": "classic_christmas",
        "colors": ["red", "green", "warm_white"],
    },
    {
        "name": "chorus_1",
        "kind": "chorus",
        "palette": "classic_christmas_bright",
        "colors": ["red", "green", "white", "gold"],
    },
], style="classic_christmas")

print(report.as_dict())
```

## Report Shape

```json
{
  "section_count": 2,
  "palette_count": 2,
  "palette_consistency_score": 1.0,
  "style_alignment_score": 1.0,
  "color_churn_score": 0.93,
  "motif_reuse_score": 0.85,
  "score": 0.95,
  "findings": []
}
```

## Important Boundary

This module does not:

- render effects
- write XSQ data
- mutate layout files
- recolor effects
- replace `core.effect_engine.py`
- change current output by default
- promote or reject variants by itself

It only reports palette-discipline quality for future scoring and explainability.

## Intended Future Use

Near-term integrations:

1. Run palette scoring against generated or inferred `sequence_plan` data.
2. Add the report to sequence quality artifacts.
3. Include palette consistency and color churn in shortlist explainability.
4. Let `showcase` and `vendor` presets require stronger palette discipline.
5. Let style presets intentionally relax or tighten color-change tolerance.

## Validation

Run:

```bash
PYTHONPATH=. pytest tests/test_palette_discipline.py
```

Recommended combined validation for Slices 2-5:

```bash
PYTHONPATH=. pytest tests/test_prop_roles.py tests/test_restraint.py tests/test_section_identity.py tests/test_palette_discipline.py
```

## Future Wiring Rule

When this gets wired into the active engine, it should appear in reports first. Only after reports are stable should it influence shortlist scoring, color selection, or quality-gate presets.
