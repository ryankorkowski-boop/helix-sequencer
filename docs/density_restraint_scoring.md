# Density and Restraint Scoring

Status: Slice 3 advisory helper  
Behavior change: none unless a caller explicitly imports and uses it

## Purpose

Helix output should look intentional instead of constantly busy. The renderer needs a way to detect clutter before future quality gates or shortlist scoring promote a sequence variant.

`tools/build_helpers/restraint.py` provides advisory scoring for cue density and restraint. It does not reject or rewrite effects by itself.

## What It Detects

Current checks:

- too many whole-layout / whole-house hits in one section
- major hits placed too close together
- too many dominant groups targeted by one high-intensity cue
- strobe-like effects used when strobe is disabled
- strobe-like effects used below a configured peak-energy threshold

## Why This Improves Output

Professional-looking sequencing uses contrast. Verses need room to breathe, choruses need more energy, and finales need to feel earned. If Helix fires every prop constantly, the show becomes visually flat even when lots of effects are present.

The restraint scorer gives future reports and variant selection a measurable way to reward:

- cleaner pacing
- stronger musical peaks
- better negative space
- fewer chaotic whole-layout blasts
- safer strobe usage
- more readable layering

## Example

```python
from tools.build_helpers.restraint import RestraintRules, score_restraint

report = score_restraint([
    {
        "time": 45.0,
        "kind": "section_peak",
        "intensity": 0.9,
        "target_groups": ["whole_layout"],
        "effect_family": "burst",
        "section": "chorus",
    }
])

print(report.as_dict())
```

## Report Shape

```json
{
  "cue_count": 1,
  "major_hit_count": 1,
  "whole_house_hit_count": 1,
  "strobe_count": 0,
  "density_penalty": 0.0,
  "score": 1.0,
  "findings": []
}
```

## Important Boundary

This module does not:

- render effects
- write XSQ data
- mutate layout files
- replace `core.effect_engine.py`
- delete or reject generated effects
- change current output by default

It only reports density/restraint issues that future planning, scoring, or candidate-shortlist code can use.

## Intended Future Use

Near-term integrations:

1. Add restraint reports to generated quality reports.
2. Include `density_penalty` in shortlist scoring.
3. Penalize clutter without fully banning creative high-energy styles.
4. Let style presets tune restraint rules: `general`, `showcase`, `vendor`, `edm`, `ballad`, `comedy`.
5. Use findings to explain why one variant won over another.

## Validation

Run:

```bash
PYTHONPATH=. pytest tests/test_restraint.py
```

Recommended combined validation with Slice 2:

```bash
PYTHONPATH=. pytest tests/test_prop_roles.py tests/test_restraint.py
```

## Future Wiring Rule

When this gets wired into the active engine, it should first appear in reports only. Only after report output is stable should it influence shortlist scoring or candidate promotion.
