# Birdsong Issue #2 Runtime Architecture

Issue #2 moves Helix from direct reactive triggers toward a guarded sequencing path:

```text
audio features -> FeatureState -> Birdsong runtime adapter -> sequence rows -> add_model/xLights output
```

## Current slice

This branch adds:

- `core/birdsong_issue2_runtime.py`
- `tests/test_birdsong_issue2_runtime.py`

The adapter exposes:

- `BirdsongRuntimeConfig`
- `BirdsongSequenceRow`
- `generate_birdsong_rows(...)`
- `emit_birdsong_rows(...)`

It consumes existing `FeatureStateFrame` objects from `core.feature_state` and produces deterministic placement rows that can be emitted through the current `add_model(...)` callback.

## Safety rule

The adapter is default-off. `generate_birdsong_rows(...)` returns no rows unless the caller passes `BirdsongRuntimeConfig(enabled=True)`. This keeps stable v27.3/default output unchanged until a guarded runtime hook is added and tested.

## Motifs

The initial Issue #2 motif set remains capped at five:

- `wave_sweep`
- `spiral`
- `pulse_cascade`
- `orbit`
- `sparkle_field`

The first effect mapping is conservative: `Single Strand`, `Wave`, `On`, `Ramp`, `Spirals`, and `Twinkle`.

## Current contract

```python
rows = generate_birdsong_rows(frames, model_names, config=BirdsongRuntimeConfig(enabled=True))
emitted = emit_birdsong_rows(rows, add_model)
```

`emit_birdsong_rows(...)` calls the existing callback shape:

```python
add_model(model, start_ms, end_ms, "birdsong_issue2", eff=effect, stem="other")
```

## Next step

Add a tiny guarded hook in the existing engine path or engine facade:

1. Build/reuse `FeatureStateFrame` objects from existing audio features.
2. Collect the active target model list.
3. Call `generate_birdsong_rows(...)` only when an explicit Issue #2/Birdsong v2 config flag is enabled.
4. Emit rows with `emit_birdsong_rows(...)`.
5. Record row counts and motifs in the report payload.
6. Verify default/non-enabled runs produce zero Issue #2 rows.

## Suggested tests

```bash
PYTHONPATH=. pytest -q tests/test_birdsong_issue2_runtime.py tests/test_feature_state.py tests/test_birdsong_engine.py
```

## Remaining Issue #2 work

- Wire the guarded adapter into runtime behind an explicit flag.
- Add a 15-20 second fixture-driven integration test.
- Add phrase persistence so motif choice lasts across musical phrases instead of only frame-local decisions.
- Connect spatial map/adjoining target logic when available on the remote branch.
- Add scoring/report fields for the Issue #2 quality dimensions.
- Keep Issue #2 open until the enabled path generates a short sequence and the default path remains unchanged.
