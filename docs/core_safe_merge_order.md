# Core Safe Merge Order

## Preconditions
- Core sandbox harness must pass:
  - `python -m pytest tests/test_core_sandbox.py`
- Full suite must remain green:
  - `python -m pytest`
- No slice larger than 2 files.
- No merge of `core/effect_engine.py` or `core/self_improving_scoring.py` until preceding guard slices pass.

## Slice Plan (1-2 files each)

1. `core/self_improving_scoring.py`
- Prerequisites:
  - None for import-level safety (standalone pure scoring module).
- Validation:
  - `python -m tools.core_sandbox --audio 2.wav --enable-self-improving-scoring`
  - Confirm deterministic `intensity_map` metric values across two runs.

2. `core/spatial_mapping_engine.py`
- Prerequisites:
  - `core/spatial_scene.py` present in branch being merged.
  - `core/sequence_context.py` present or shimmed.
- Validation:
  - `python -m tools.core_sandbox --audio 2.wav --enable-spatial-mapping-engine`
  - Confirm `modules.spatial_mapping_engine.status == "ok"` and non-empty `effect_timeline`.

3. `core/audio_intelligence.py` (runtime update slice)
- Prerequisites:
  - Sandbox snapshot baseline recorded before merge.
- Validation:
  - `python -m pytest tests/test_audio.py tests/test_core_sandbox.py`
  - In sandbox, verify stable `spatial_coordinates` + `intensity_map`.

4. `core/effect_engine.py` (high risk, single-file gated slice)
- Prerequisites:
  - Steps 1-3 merged and stable.
  - Sandbox snapshot updated only with intentional diff review.
- Validation:
  - `python -m pytest tests/test_effects.py tests/test_core_sandbox.py`
  - `python -m pytest`
  - Diff `outputs/core_sandbox/core_sandbox_report.json` for:
    - `effect_timeline`
    - `intensity_map`
    - `color_distribution`
    - `spatial_coordinates`

## Rollback Rule
- If any slice fails targeted tests or changes sandbox artifacts unexpectedly, revert only that slice and stop integration.
