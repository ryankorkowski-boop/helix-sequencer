# Section Identity Scoring

Status: Slice 4 advisory helper  
Behavior change: none unless a caller explicitly imports and uses it

## Purpose

A generated sequence should not feel visually flat. The intro, verse, chorus, bridge, drop, and finale should have readable differences in intensity, density, palette, prop focus, and motion.

`tools/build_helpers/section_identity.py` provides advisory scoring for planned section contrast and shape. It is designed to work with the `sequence_plan` contract and future quality reports before it influences rendering or variant promotion.

## What It Measures

Current report scores:

- `coverage_score`: whether sections have usable duration, prop groups, and palette intent
- `contrast_score`: whether adjacent sections look meaningfully different
- `intensity_shape_score`: whether section intensity fits rough expectations and builds over time
- `finale_strength_score`: whether the final section feels earned and strong
- `score`: weighted combined advisory score

## What It Flags

Current findings include:

- no sections provided
- invalid section duration
- missing prop groups
- missing palette intent
- weak adjacent section contrast
- section intensity outside rough expectations
- weak finale intensity
- weak finale density
- narrow finale coverage

## Why This Improves Output

Auto-sequencing often fails because every part of the song receives similar density and similar effects. A chorus should not look like a verse. A finale should not look like the first 20 seconds.

This scorer gives Helix a measurable way to reward:

- clear section contrast
- planned intensity ramps
- stronger choruses and finales
- purposeful prop focus shifts
- color/motion identity per section

## Example

```python
from tools.build_helpers.section_identity import score_section_identity

report = score_section_identity([
    {
        "name": "intro",
        "kind": "intro",
        "start": 0.0,
        "end": 12.0,
        "target_intensity": 0.3,
        "primary_groups": ["roofline"],
        "palette": "winter_soft",
        "motion_intent": "gentle_reveal",
        "density": "low",
    },
    {
        "name": "chorus_1",
        "kind": "chorus",
        "start": 45.0,
        "end": 72.0,
        "target_intensity": 0.86,
        "primary_groups": ["mega_tree", "roofline"],
        "secondary_groups": ["arches", "snowman_band"],
        "palette": "classic_christmas_bright",
        "motion_intent": "wide_sweeps_and_spirals",
        "density": "high",
    },
])

print(report.as_dict())
```

## Report Shape

```json
{
  "section_count": 2,
  "coverage_score": 1.0,
  "contrast_score": 0.91,
  "intensity_shape_score": 1.0,
  "finale_strength_score": 0.72,
  "score": 0.91,
  "findings": []
}
```

## Important Boundary

This module does not:

- render effects
- write XSQ data
- mutate layout files
- replace `core.effect_engine.py`
- change current output by default
- promote or reject variants by itself

It only reports section-identity quality for future scoring and explainability.

## Intended Future Use

Near-term integrations:

1. Run section identity scoring against generated or inferred `sequence_plan` data.
2. Add the report to sequence quality artifacts.
3. Include `section_contrast` and `finale_strength` in shortlist explainability.
4. Later, allow `showcase` and `vendor` presets to require stronger section identity.
5. Use findings to suggest targeted improvements: stronger finale, more prop contrast, less verse/chorus similarity.

## Validation

Run:

```bash
PYTHONPATH=. pytest tests/test_section_identity.py
```

Recommended combined validation for Slices 2-4:

```bash
PYTHONPATH=. pytest tests/test_prop_roles.py tests/test_restraint.py tests/test_section_identity.py
```

## Future Wiring Rule

When this gets wired into the active engine, it should appear in reports first. Only after reports are stable should it influence shortlist scoring or quality-gate presets.
