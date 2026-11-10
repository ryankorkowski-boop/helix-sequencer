# Manual Lock Contract

Status: Slice 7 parser/contract helper  
Behavior change: none unless a caller explicitly imports and uses it

## Purpose

Helix should eventually be able to auto-fill around human-authored hero moments instead of overwriting them. Manual locks define protected timing windows, target groups/models/effects, and conflict policies in a sidecar-friendly format.

`tools/build_helpers/manual_locks.py` provides a parser and normalizer for manual-lock sidecars. It does not enforce locks in the renderer yet.

## Why This Matters

A strong workflow is:

1. Human places or locks important moments.
2. Helix recognizes those protected regions.
3. Helix fills around them.
4. Reports explain what was protected, trimmed, avoided, or left alone.

Slice 7 only defines the contract and validation rules for that workflow.

## Sidecar Shape

```json
{
  "version": "0.1",
  "sequence_id": "song_02",
  "sequence_plan_ref": "sequence_plan.json",
  "source_audio_ref": "2.wav",
  "fps": 40,
  "timebase": "ms",
  "defaults": {
    "mode": "protect",
    "strength": "hard",
    "padding_before_ms": 100,
    "padding_after_ms": 120,
    "require_user_consent": false
  },
  "locks": []
}
```

See:

```text
docs/samples/manual_locks.sample.json
```

## Lock Concepts

### Anchor

Defines when the lock applies.

Supported anchor types:

- `cue_ref`
- `section_ref`
- `time_range`

`cue_ref` and `section_ref` can include a fallback interval so the lock remains usable before full cue/section resolution exists.

### Selector

Defines what the lock applies to.

Supported selector targets:

- `all_groups`
- `groups`
- `models`
- `layers`
- `effect_ids`

A selector must target at least one of `all_groups`, `groups`, `models`, or `effect_ids`.

### Freeze Fields

Supported freeze fields:

- `occupancy`
- `timing`
- `targeting`
- `payload`

For example, a hero burst may freeze all four fields, while a singer phrase may only freeze occupancy so auto-fill cannot overwrite that lane.

### Policy

Supported modes:

- `protect`: keep generated effects out of the shadow window
- `trim`: allow generated effects nearby if they can be trimmed safely
- `avoid`: prefer other groups/times before conflict occurs
- `override`: reserved for explicit user-approved behavior only

Supported strengths:

- `hard`
- `soft`

Override policies must require user consent.

## Timing Semantics

Intervals use millisecond `[start_ms, end_ms)` half-open semantics.

That means:

- `[1000, 2000)` and `[2000, 3000)` touch but do not overlap
- `[1000, 2100)` and `[2000, 3000)` overlap

Padding creates a shadow window around a lock:

```text
shadow_start = max(0, start_ms - padding_before_ms)
shadow_end = end_ms + padding_after_ms
```

## Important Boundary

This module does not:

- render effects
- write XSQ data
- mutate layout files
- delete generated effects
- enforce manual locks in `core.effect_engine.py`
- change current output by default
- promote or reject variants by itself

It only parses, validates, normalizes, and summarizes lock contracts.

## Intended Future Use

Near-term integrations:

1. Load manual-lock sidecars in report-only mode.
2. Count generated effect candidates that would touch lock shadow windows.
3. Report `would_protect`, `would_trim`, `would_avoid`, and `would_require_consent` actions.
4. Later, allow planner/scoring to penalize variants that collide with manual locks.
5. Only after stable reporting, enforce protect/trim/avoid behavior in generation.

## Validation

Run:

```bash
PYTHONPATH=. pytest tests/test_manual_locks.py
```

Recommended combined validation for Slices 2-7:

```bash
PYTHONPATH=. pytest tests/test_prop_roles.py tests/test_restraint.py tests/test_section_identity.py tests/test_palette_discipline.py tests/test_motif_memory.py tests/test_manual_locks.py
```

## Future Wiring Rule

When manual locks get wired into the active engine, they should first appear in reports only. Enforcement should come later and should never override user-authored work unless an explicit override policy requires user consent.
