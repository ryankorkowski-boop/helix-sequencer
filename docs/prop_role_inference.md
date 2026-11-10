# Prop Role Inference

Status: Slice 2 advisory helper  
Behavior change: none unless a caller explicitly imports and uses it

## Purpose

Helix output quality improves when the engine knows what each prop is good at. A mega tree, roofline, arch, singer, drummer, and random fill prop should not receive the same kind of sequencing by default.

`tools/build_helpers/prop_roles.py` provides a small source-agnostic helper that infers advisory role hints from model or group names.

## Current Roles

Supported role hints:

- `centerpiece`
- `outline`
- `accent`
- `character`
- `singer`
- `percussion`
- `background`
- `foreground`
- `strobe`
- `fill`

## Example

```python
from tools.build_helpers.prop_roles import infer_prop_role, summarize_roles

hint = infer_prop_role("Mega Tree")
print(hint.as_dict())

summary = summarize_roles([
    "Mega Tree",
    "Roofline Left",
    "Snowman Singer",
    "Snowman Drummer",
    "Mini Tree 1",
])
```

## Important Boundary

This module does not:

- render effects
- write XSQ data
- mutate layout files
- replace `core.effect_engine.py`
- force routing decisions

It only returns hints that future planning, scoring, or reporting code can use.

## Intended Future Use

Near-term integrations:

1. Add role summaries to generated quality reports.
2. Use role hints in section coverage scoring.
3. Penalize mismatched placement, such as vocals routed only to non-character fill props.
4. Reward strong role usage, such as percussion hits on drummer/percussion props and finales on centerpiece/whole-layout groups.

## Validation

Run:

```bash
PYTHONPATH=. pytest tests/test_prop_roles.py
```

The tests prove that common names infer expected advisory roles while unknown names safely fall back to `fill`.
