# Variant Lanes Test Plan

Status: planning and safe test instructions only.

This document defines the next controlled experiment for running Helix variants as either separate candidate outputs or as contributors to a future composite lane render.

## Current supported behavior

Helix currently supports running variants as separate candidate outputs through the existing engine path:

```text
core.sequence_builder -> core.effect_engine -> xlights/xsq_writer.py -> template.xsq
```

The Legacy 256 profile wrapper exposes this through:

```bash
PYTHONPATH=. python -m tools.run_legacy_256_profile legacy_256_clean
PYTHONPATH=. python -m tools.run_legacy_256_profile legacy_256_showcase
PYTHONPATH=. python -m tools.run_legacy_256_profile legacy_256_pro
```

Dry-run command checks:

```bash
PYTHONPATH=. python -m tools.run_legacy_256_profile legacy_256_clean --dry-run
PYTHONPATH=. python -m tools.run_legacy_256_profile legacy_256_showcase --dry-run
PYTHONPATH=. python -m tools.run_legacy_256_profile legacy_256_pro --dry-run
```

Unit check:

```bash
PYTHONPATH=. python -m pytest tests/test_legacy_256_profiles.py tests/test_variant_quality_gates.py -q
```

## Current profile output counts

```text
legacy_256_clean      -> 2 candidates
legacy_256_showcase   -> 3 candidates
legacy_256_pro        -> 5 candidates
```

Across all three profiles, a full run may evaluate 10 candidate outputs.

## Runtime variant roles

The current runtime candidate labels should be treated as roles:

```text
signature      -> safe base structure and backbone
hook_focus     -> hooks, melodic accents, chorus memory, call-response
wide_stage     -> spatial movement, yard sweeps, neighbor reactions
stem_story     -> stem-aware layering, vocals, bass, controlled breathing
cinematic_arc  -> section contrast, reveals, bridge/finale storytelling
```

## Future composite-lane concept

Do not stack full variants blindly. A naive stack can create clutter, collisions, excessive rejected effects, and poor legacy-channel readability.

The future composite mode should use variants as contributors:

```text
1. Generate variant candidates separately.
2. Score each candidate normally.
3. Extract each variant's strongest sections or moments.
4. Assign accepted moments into named lanes.
5. Resolve collisions and density conflicts.
6. Render one composite sequence plus the individual reports.
```

Proposed flag names:

```text
--variant-lanes
--composite-variants
```

## Proposed lane mapping

```text
lane_signature_backbone  <- signature
lane_hook_accents        <- hook_focus
lane_spatial_motion      <- wide_stage
lane_stem_story          <- stem_story
lane_cinematic_reveals   <- cinematic_arc
```

## Initial acceptance criteria

The first implementation slice should not alter the default render path. It should only add dry-run/reporting behavior that proves lane assignment decisions.

A safe first test should pass when:

```text
- all known runtime variant labels map to a lane
- unknown labels fall back to a safe auxiliary lane
- lane assignment produces deterministic JSON
- no output sequence is modified unless the composite flag is explicitly enabled
```

## Recommended first implementation slice

Add a small helper module only:

```text
tools/build_helpers/variant_lanes.py
```

Suggested API:

```python
lane_for_variant(label: str) -> str
build_variant_lane_plan(entries: list[dict]) -> dict
```

Suggested tests:

```text
tests/test_variant_lanes.py
```

This keeps the experiment testable without taking over the renderer.
