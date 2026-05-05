# Integration Remaining PRs

## Current Merged Status (as of 2026-04-29)
- Base branch: `feature/restructure-core`
- Latest known upstream commit before this integration step: `71b9f2e`
- Merged slice: `PR-A-safe-docs-ci`
- Merged slice: `PR-B-layout-builders-assets`
- Prior baseline test note: `71 passed, 1 warning`
- Safety checkpoint branch created: `integration/checkpoint-after-pr-b`

## Mapping Note
Explicit branch refs named `PR-C`, `PR-D`, `PR-E`, `PR-F` are not present in remote refs. The remaining unmerged work is mapped from `feature/helixville3-spotlog-birdsong` commit groups after subtracting PR-A/PR-B content.

## PR-C Risk Summary (mapped to `18474b6` remainder)
- Files changed:
  - Source commit touched 88 files.
  - Substantial overlap with PR-A/PR-B in docs/layout assets/builders/tests.
  - Remaining delta still large across runtime modules.
- Systems touched:
  - Core sequencing/effects/spatial/style/vocal/band sync (`core/*`)
  - Audio/mapping/music/render/effects/models/learning stacks
  - Debug utilities and broad tests
- Impact categories:
  - Core sequencing: yes
  - Exports: yes (`export/snowman_band_json_export.py`)
  - Layout generation: yes (through integrated builders/assets and related runtime)
  - Tests: yes
  - CLI: no direct CLI entrypoint but wide runtime surface
  - Assets/docs/compatibility: yes
- Overlap with merged PR-A/PR-B:
  - High overlap with layout/doc slices already merged
- Can it be split smaller?
  - Yes. Recommended split: tests-only, isolated helper modules, then runtime pieces.
- Recommendation:
  - Defer broad merge. Do not cherry-pick as one unit.

## PR-D Risk Summary (mapped to `3e7df8f`)
- Files changed:
  - `.github/workflows/unit-tests.yml`
  - `README.md`
  - `THIRD_PARTY_LICENSES.md`
  - `core/effect_engine.py`
  - `core/self_improving_scoring.py`
  - `gui_launcher.py`
  - `tests/test_self_improving_scoring.py`
  - `tools/build_helpers/variants.py`
- Systems touched:
  - Core scoring/effect logic
  - GUI launcher behavior
  - Test workflow/docs/license metadata
- Impact categories:
  - Core sequencing: yes
  - Exports/layout generation: indirectly via effect engine behavior
  - Tests: yes
  - CLI/assets/docs/compatibility: docs/workflow overlap present
- Overlap with merged PR-A/PR-B:
  - Medium overlap (workflow/docs/helpers)
- Can it be split smaller?
  - Yes. Test-only and metadata-only portions can be separated from runtime changes.
- Recommendation:
  - Partial cherry-pick only if isolated; otherwise defer.

## PR-E Risk Summary (mapped to `64fb303`)
- Files changed:
  - `config/audio_analysis_defaults.json`
  - `core/audio_intelligence.py`
  - `tests/test_audio.py`
- Systems touched:
  - Audio intelligence pipeline and defaults
- Impact categories:
  - Core sequencing: indirect
  - Compatibility/runtime behavior: yes
  - Tests: yes
  - Exports/layout/CLI/assets/docs: minimal
- Overlap with merged PR-A/PR-B:
  - None
- Can it be split smaller?
  - Yes (tests/config/runtime can be staged separately)
- Recommendation:
  - Candidate for narrow partial cherry-pick after targeted audio regression coverage.

## PR-F Risk Summary (mapped to `4531e63` + `34ac5d6`)
- Files changed:
  - Large modular addition across `helix_*` packages, `export/professional_intelligence_export.py`, `tools/helix_cli.py`
  - Plus isolated utility `tools/helix_desktop_cleanup.py`
- Systems touched:
  - Intent/layout/mapping/preview/render/spatial/style/knowledge subsystems
  - CLI and export pipeline
- Impact categories:
  - Core sequencing: adjacency/high integration risk
  - Exports: yes
  - Layout generation: yes (analysis and optimization modules)
  - Tests: one new professional intelligence test path
  - CLI: yes
  - Docs: yes (docs overlap already merged in PR-A)
- Overlap with merged PR-A/PR-B:
  - Docs overlap with PR-A; runtime modules mostly non-overlapping but broad
- Can it be split smaller?
  - Yes. At minimum isolate `tools/helix_desktop_cleanup.py` and keep major module additions separate.
- Recommendation:
  - Defer broad merge; allow isolated helper-only pickup.

## Recommended Order of Integration
1. Isolated helper-only slices (non-runtime), starting with `tools/helix_desktop_cleanup.py`.
2. Tests-only additions that do not require new runtime modules.
3. Small compatibility bug fixes with explicit targeted tests.
4. Audio runtime changes (PR-E) only after additional regression tests.
5. Core sequencing/scoring/runtime cross-cutting slices (PR-C, PR-D runtime pieces, PR-F major modules) last.

## Extra Caution Areas
- `core/effect_engine.py` and `core/self_improving_scoring.py` (sequencing behavior drift)
- `core/audio_intelligence.py` and `config/audio_analysis_defaults.json` (compatibility/regression risk)
- `gui_launcher.py` and `tools/helix_cli.py` (entrypoint behavior and operator workflow)
- `export/*` plus new `helix_*` packages (integration fan-out and import stability)

## Tests To Add Before Risky Merges
- Deterministic sequencing snapshot tests around `core/effect_engine.py` and scoring outputs.
- Regression tests for audio compatibility modes and missing-file handling in audio intelligence.
- Import/load smoke tests for new `helix_*` packages to catch broken wiring early.
- CLI contract tests for `tools/helix_cli.py` (arguments, exit codes, artifact paths).
- Export schema tests for `export/professional_intelligence_export.py` and related JSON outputs.
