# README_CURRENT

## What 414 Contains
- Active source tree for sequencing, layout, audio intelligence, previews, tests, and tools.
- Guardrail harness for high-risk core work:
  - `tools/core_sandbox.py`
  - `tests/test_core_sandbox.py`
  - `tests/snapshots/core_sandbox_snapshot.json`
  - `tests/snapshots/core_audio_intelligence_snapshot.json`
- Core dependency and merge planning docs:
  - `docs/core_dependency_graph.md`
  - `docs/core_safe_merge_order.md`
- Styler/mixup preview sweep artifacts:
  - `test_runs/styler_mixup_sweep/`

## Run Tests
- Regression guardrail tests:
  - `python -m pytest tests/test_core_sandbox.py -q`
- Full suite:
  - `python -m pytest`

## Generate Previews
- Generate one sequence (explicit all-models layout + LightsOutTheme.mp3):
  - `python -m core.sequence_builder --profile v27.3 -- --template template.xsq --audio LightsOutTheme.mp3 --layout-file allmodels/xlights_rgbeffects.xml --single --output-dir test_runs/manual_preview --variants 1 --no-prompt --no-save-settings --no-workspace-history --no-polish --no-auto-timing-tracks --no-matrix-intelligence`
- Render preview MP4:
  - `python -m tools.preview_renderer test_runs/manual_preview/LightsOutTheme,v27.3.xsq --layout allmodels/xlights_rgbeffects.xml --audio LightsOutTheme.mp3 --fps 10 --width 960 --height 540`

## Run Styler/Mixup Sweep Again
- Sweep outputs location:
  - `test_runs/styler_mixup_sweep/`
- Inventory:
  - `test_runs/styler_mixup_sweep/STYLER_INVENTORY.md`
- Results:
  - `test_runs/styler_mixup_sweep/RESULTS.md`
- Manifest:
  - `test_runs/styler_mixup_sweep/results_manifest.json`

## Where Preview MP4s Are Saved
- Per-run subfolders under:
  - `test_runs/styler_mixup_sweep/<run_name>/`
- E2E proof run:
  - `test_runs/self_contained_e2e/`

## Old Folders Likely Safe To Delete Later
- See `CLEANUP_CANDIDATES.md` for risk-rated candidates.
- No cleanup has been performed.

## Next Verification Command
Run this command from `C:\Users\User\Desktop\414`:

`python -m tools.core_sandbox --audio 2.wav --output-dir outputs/core_sandbox_after_merge --disable-effect-engine --enable-self-improving-scoring --disable-spatial-mapping-engine --disable-audio-intelligence; python -m pytest tests/test_core_sandbox.py -q; python -m pytest`
