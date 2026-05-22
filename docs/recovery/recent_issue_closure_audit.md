# Recent Issue Closure Audit

This recovery audit separates merged code slices from acceptance criteria that still need CI, generated artifacts, xLights import evidence, visual review, or controller/runtime proof. Closed issues should be treated as implemented or partially implemented only where the evidence below supports that claim.

## Audit rules

- PR #75 merged a guarded, default-off Issue #2 adapter only. Its own notes leave runtime wiring, fixture integration, phrase persistence, spatial mapping, and scoring/report fields open.
- PR #74 merged a high-quality preview wrapper and preset validation path. Its own notes say runtime rendering was not executed and it does not provide true xLights per-node/OpenGL preview parity.
- PR #73 is still open and unmerged, so `scripts/ci/verify_recovery_gate.py` is a focused recovery gate for now rather than a replacement for the planned shared beta check runner.
- PR #66 is still open and unmerged.
- Manual claims require artifacts. xLights import, render, channel safety, controller safety, and visual review stay unproven until evidence is stored.

## Closure audit table

| Issue | Actually implemented | Evidence found | Not yet proven | Recommended status | Recommended follow-up issue/PR |
| --- | --- | --- | --- | --- | --- |
| #2 Birdsong Engine | Feature state and guarded Issue #2 row adapter slice. | `core/feature_state.py`, `core/birdsong_issue2_runtime.py`, focused tests, PR #75 notes. | Runtime hook, 15-20s fixture run, phrase persistence, spatial adjacency, scoring/reporting, subjective flow. | Roadmap/umbrella: do not call complete; reopen or supersede with bounded slices. | Keep a runtime integration PR and separate phrase/spatial/scoring issues. |
| #20 Helixia xLights import and production validation | Tracker documents already-known parser and local test facts. | Issue body lists import/controller/visual checks as remaining. | xLights import warnings, channel/controller safety, visual review, path normalization decision. | Validation-heavy tracker should remain open until artifacts exist. | Capture xLights import report, screenshots, controller assumptions, and any layout fix PR. |
| #23 Showcase parity initiative | Roadmap for showcase metrics and cinematic parity. | Issue body is an umbrella plan with phased proposed work. | Benchmark improvement, reports, snapshots, renderer stability. | Roadmap/umbrella: not complete unless intentionally superseded. | Split metrics, orchestration, motion, palette, and benchmark gates into verifiable PRs. |
| #24 Showcase bias caps | Preset cap behavior appears implemented as a deterministic scoring slice. | `tools/build_helpers/explainable_variant_scoring.py` and `tests/test_explainable_variant_scoring.py` reference `showcase_bias` caps/findings. | Current branch full CI state after recent merges. | Keep closed only as a bounded deterministic slice after CI evidence is recorded. | Add a recovery comment linking tests/CI if acceptance evidence is missing. |
| #28 Quality escalation plan | Master roadmap for elite sequencing quality. | Issue body explicitly calls itself a master roadmap. | Energy, scenes, hierarchy, contrast, motion grammar, score target. | Roadmap/umbrella: do not treat as complete. | Supersede intentionally with roadmap docs or reopen as umbrella tracker. |
| #29 GUI state audit | Investigation request. | Issue body asks for screenshot walkthrough, parity matrix, friction notes, diagram, recommendation. | GUI audit artifacts and visual review. | Validation-heavy investigation should remain open. | Produce audit artifacts in a focused GUI review PR. |
| #35 Lyric to phoneme timing | Deterministic mapping/allocation modules and tests. | `core/lyric_phoneme_mapper.py`, `core/lyric_timing_allocator.py`, related tests. | Broad CI status and real lyric/audio alignment outside stated v1 non-goals. | Bounded v1 can be considered implemented with test evidence, not broader singing parity. | Record CI/test proof or open an audio alignment follow-up. |
| #37 Multi-line lyric scheduling | Deterministic section scheduler and tests. | `core/lyric_section_scheduler.py`, `tests/test_lyric_section_scheduler.py`. | Broad CI status and real song-section validation. | Bounded v1 can be considered implemented with test evidence. | Add generated artifact proof where scheduler feeds export. |
| #39 Section energy scaling | Deterministic energy scaler and tests. | `core/energy_scaler.py`, `tests/test_energy_scaler.py`. | Broad CI status and downstream visual impact. | Bounded v1 can be considered implemented with test evidence. | Add export/report integration evidence if it becomes runtime-critical. |
| #41 / #42 Beat-grid alignment | One deterministic beat aligner implementation. | Both issues have matching titles/bodies; `core/beat_aligner.py` and `tests/test_beat_aligner.py` exist. | Which duplicate issue is canonical and whether export integration acceptance was verified. | Mark duplicate relationship explicitly; do not count both as separate completed work. | Keep one canonical issue with test/CI evidence and mark the other duplicate only if maintainers agree. |
| #44 XSQ emitter | Deterministic emitter slice. | `core/xsq_emitter.py`, `tests/test_xsq_emitter.py`. | xLights import/render acceptance. | Code slice may be implemented; xLights deployment claim remains unproven. | Pair emitted XSQ artifacts with import validation work. |
| #46 Real xLights import workflow | Structure validator and docs exist. | `docs/xlights_import_validation.md`, `tools/validate_xsq_structure.py`. | Manual xLights import, render timing, real layouts/controllers. | Validation-heavy issue should remain open or narrowed. | Store manual import evidence and generated artifact matrix. |
| #48 CI-tested XSQ validation fixtures | Validator fixture/test coverage exists. | `fixtures/xsq_validation/`, `tests/test_xsq_validation_tool.py`. | Manual xLights proof, intentionally outside fixture scope. | Closed is reasonable only for automated fixture coverage with CI evidence. | Keep manual import proof tracked under #46 or recovery gate. |
| #50 Generated XSQ export command | Export command and tests exist. | `tools/export_demo_xsq.py`, `tests/test_export_demo_xsq.py`. | Generated artifact attached to review and xLights import outcome. | Code slice can be implemented; artifact proof still needed for recovery. | Generate and store representative XSQ evidence for import validation. |
| #52 Band geometry validation gate | Manifest/status validation exists around accepted band geometry. | `fixtures/band_geometry/geometry_manifest.json`, band geometry tests/status tool. | Physical geometry parity and binding to real xLights assets. | Keep claims narrow to validation metadata unless geometry artifacts prove more. | Track missing `.xmodel` and import/render evidence separately. |
| #54 Band geometry manifest seed | Manifest seed and tests exist. | Geometry manifest plus manifest/status tests. | Physical render or controller proof, explicitly excluded by issue body. | Bounded metadata slice can be closed with CI evidence only. | Follow with actual asset/import validation PRs. |
| #56 Draft band xmodel generation | Generator/draft asset work may exist as a deterministic asset slice. | Issue body explicitly limits claims to generated draft `.xmodel` files and deterministic tests. | xLights acceptance, layout preview, controller output. | Validation-heavy downstream claims must stay open. | Keep import/render validation issue separate and artifact-backed. |
| #60 Legacy runtime consolidation | Cleanup plan and inventory requirement. | Issue body requires inventory, keep/archive/delete decisions, parity, CI. | Runtime parity for deletions and canonical path proof. | Do not call complete without parity evidence; archive before deleting. | Add focused inventory/archive PRs by subsystem. |
| #61 Promote band xmodels to imported status | Promotion requires evidence directory and screenshots/metadata. | Issue body claims import milestone but still asks for evidence updates. | All five assets, preview animation, controller validation, physical pixels. | Validation-heavy: verify evidence before treating as complete. | Store import artifacts and keep preview/controller follow-ups open. |
| #72 Full-suite Helix CI failure triage | Targeted beta CI context documented. | Issue body states broad full pytest failure still needed triage. | Failing test names, root cause, restored full-suite CI. | Should not be closed complete until full-suite triage is recorded. | Capture failing job details and repair or document narrow expected failures. |

## Validation flags

Roadmap or umbrella closures that need an explicit supersession decision: #2, #23, #28, and #60.

Validation-heavy closures that require xLights, manual, visual, controller, or artifact evidence before they are treated as complete: #20, #29, #44, #46, #50, #52, #56, #61, and #72.

Duplicate hygiene: #41 and #42 describe the same deterministic beat-grid aligner. Count one implementation and record the maintainer-selected canonical issue before marking the duplicate.

## Local verification snapshot

Recovery checks attempted on May 22, 2026 from `codex/recover-premature-issue-closures`:

- `PYTHONPATH=. python -m pytest -q tests/test_birdsong_issue2_runtime.py` passed: 19 passed.
- `PYTHONPATH=. python tools/preview_hq.py --validate-quality-presets` passed and printed the four quality presets.
- `PYTHONPATH=. python scripts/ci/verify_recovery_gate.py` passed the focused compile, Birdsong, feature-state, preview preset, xLights contract validator, and sequence-builder smoke checks.
- `PYTHONPATH=. python -m pytest -q` failed: 770 passed, 6 failed, 5 skipped.

The full-suite failures were:

- `tests/test_build_helixia_layout_cli.py::BuildHelixiaLayoutCliTests::test_cli_can_enable_spec_driven_band_layout`
- `tests/test_export_helix_flow_review_artifacts.py::test_export_review_artifacts_writes_all_expected_files`
- `tests/test_helix_flow_review_artifacts_workflow.py::test_review_artifact_workflow_uploads_expected_artifacts`
- `tests/test_issue_resolution_workflow_contract.py::test_issue_resolution_workflow_runs_validation_paths`
- `tests/test_legacy_256_profiles.py::Legacy256ProfileTests::test_runner_builds_existing_engine_command_for_pro_profile`
- `tests/test_sequence_builder_orchestrator_promotion.py::test_run_profile_promotes_orchestrated_xsq_as_next_template`

That full-suite state is evidence for keeping Issue #72 open as triage work, not a reason to weaken unrelated tests.

## MP4 and preview truthfulness

`tools/preview_hq.py` proves that Helix has a clean wrapper for preview quality presets and a dry validation command:

```bash
PYTHONPATH=. python tools/preview_hq.py --validate-quality-presets
```

That command proves preset definitions import and print; it does not render an MP4. The wrapper also does not prove xLights/OpenGL preview parity, layout correctness, node binding, or controller safety.

For a real local preview check, use repo-safe copied inputs only. If `lightsouttheme.mp3` and an `aaatest` XSQ are present locally, run a targeted render with the intended layout and keep the output with the evidence bundle:

```bash
PYTHONPATH=. python tools/preview_hq.py path/to/aaatest.xsq --layout path/to/xlights_rgbeffects.xml --audio path/to/lightsouttheme.mp3 --quality-preset xlights
```

Generated evidence should be stored outside source input folders and then curated into the review record:

- XSQ artifacts: a recovery evidence folder such as `artifacts/recovery/xsq/` or a CI artifact upload.
- MP4 artifacts: a recovery evidence folder such as `artifacts/recovery/mp4/` or a CI artifact upload.
- Manual xLights notes, screenshots, and import metadata: a recovery evidence folder such as `artifacts/recovery/xlights/` or a documented external evidence link when binary artifacts should not enter git.

Do not claim rendering is fixed from preset validation alone.
