# HELIX MASTER TODO & AGENT HANDOFF LEDGER

> Canonical project roadmap and cross-agent handoff layer.

## Current mission
Build Helix into a reliable AI-assisted xLights auto-sequencer while preserving deterministic sequencing, verified artifacts, and cumulative behavior.

## Beta roadmap baseline status

This repo is currently in the beta-safety phase described by `ROADMAP_BETA_TODO.md`.

- [x] Phase 0 guidance is in place: beta roadmap, safety baseline, and support/data-use policy are documented.
- [x] Core beta docs are linked from the README and are available under `docs/`.
- [x] Agent task index is aligned with the roadmap and points to the current next tasks.
- [x] Sample beta tester feedback checklist exists and is documented for testers.
- [ ] Continue with Phase 0/1 execution in the exact order called out by the roadmap before moving into engine-facing refactors.
- [ ] Keep this ledger updated as each beta phase completes.

## Current priority
The current repo priority is the beta-readiness sequence defined in `ROADMAP_BETA_TODO.md`:

1. Add/maintain `TASKS.md` pointing to the beta roadmap.
2. Maintain `docs/SUPPORT_MATRIX.md` and `docs/BETA_POLICY.md`.
3. Normalize dependencies and CI with `requirements-dev.txt`.
4. Add repo-safe smoke fixtures and structural validation.
5. Add run manifest/output safety behavior.
6. Add GUI beta mode + dry-check behavior.
7. Add beta tester docs and issue templates.
8. Add Windows packaging smoke coverage.
9. Only then begin engine facade/extraction work.

## Drummer / band current state
- [x] Canonical nine-component drummer contract documented.
- [x] Runtime drummer state model changed to nine integrated hit components.
- [x] Structure catalog changed to nine drummer sequencing components.
- [x] XML exporter no longer emits the legacy `line0="1-4"` placeholder for drummer components.
- [x] Pose geometry spec now defines nine component composites with embedded contacting-stick geometry.
- [~] xLights model exporter still needs to emit the new component composites as the nine canonical sequencing submodels.
- [~] Drum detector uses HPSS/percussive onset analysis plus spectral features.
- [x] Classification now rejects high harmonic-contamination candidates when unsupported and suppresses ambiguous low-margin classifications into `drum_bus`.
- [ ] Add per-event source/stem provenance to rendered XSQ debug metadata.
- [ ] Validate detector against real-song audio and quantify false positives.
- [ ] Generate real-song XSQ.
- [ ] Render full-song MP4 with audio.
- [ ] Human visual review of rendered drummer timing.

## Canonical drummer components
1. `HX_SNOWMAN_DRUMMER_KICK` = KICK + KICK_RIM
2. `HX_SNOWMAN_DRUMMER_SNARE` = SNARE + SNARE_RIM + SNARE_CONTACT_STICK
3. `HX_SNOWMAN_DRUMMER_TOM_1` = TOM_1 + TOM_1_CONTACT_STICK
4. `HX_SNOWMAN_DRUMMER_TOM_2` = TOM_2 + TOM_2_CONTACT_STICK
5. `HX_SNOWMAN_DRUMMER_TOM_3` = TOM_3 + TOM_3_CONTACT_STICK
6. `HX_SNOWMAN_DRUMMER_TOM_4` = TOM_4 + TOM_4_CONTACT_STICK
7. `HX_SNOWMAN_DRUMMER_HI_HAT` = HI_HAT + HIHAT_CONTACT_STICK
8. `HX_SNOWMAN_DRUMMER_CYMBAL_LEFT` = CYMBAL_LEFT + CYMBAL_LEFT_CONTACT_STICK
9. `HX_SNOWMAN_DRUMMER_CYMBAL_RIGHT` = CYMBAL_RIGHT + CYMBAL_RIGHT_CONTACT_STICK

**Physical rule:** the contacting stick is part of the corresponding hit component. There are no independent stick sequencing channels. Kick has no stick.

## Detection architecture
**audio → HPSS/percussive isolation → onset candidates → spectral/transient features → confidence-gated drum classification → nine-component mapper → XSQ**

## Ground-truth regression oracle
A prior drummer render was explicitly identified by the user as having the **correct drummer logic** and must be preserved as the behavioral reference while the implementation is upgraded.

- Known-good commit: `b27e8d77a63027ed32bcf6851dcff3925472c155`.
- Prior successful artifact lineage: **Helix Full Current 256 + Drummer**; published workflow run `35486153096` was previously identified as the MP4-producing run.
- The repository's dedicated ground-truth workflow at that point exercised the real V3 drummer submodels and generated deterministic audio/XSQ/preview artifacts.
- Current nine-component geometry remains authoritative for the new implementation: four tom zones and contacting-stick geometry integrated into the hit component.

**Rule:** do not discard or rewrite the behavior that made the prior render correct. New detection/mapping logic must be compared against the prior oracle before being accepted.

## Verification gate
**audio → detected events → mapped components → XSQ → full-song MP4 with real audio → compare against prior correct drummer render → human visual review**

Do not mark complete from unit tests alone.

## Change Ledger

### 2026-11-09 — Part B: share a whole-layout flash cooldown
**Goal:** stop chained red/green/white whole-layout flashing and honor full flash restraint.
**Changed files:** `core/global_flash_policy.py`, `core/effect_engine.py`, `tests/test_global_flash_policy.py`, `MASTER_TODO.md`.
**Preserved behavior:** existing musical selection, per-model effects, and probability gates (including chorus floors) at default flash_guard 0.80; other effect cooldowns remain intact. No whole-run unit test was introduced.
**New behavior:** pure `allows_global_flash` checks all accepted flash start times with one 1000/cap ms spacing across colors. Generation calls it at final clipped placement time through the shared add_model placement path, covering bass, green VU, vocals, chorus drops, and helper-selected whole-layout color targets. Out-of-order passes are supported; rejected placements consume no flash slot. Per-color cooldowns are replaced for these targets. RuntimeTuning/CLI expose `max_global_flashes_per_sec` / `--max-global-flashes-per-sec`, default 2; nonpositive caps disable flashes. flash_guard >= 1 disables all whole-layout color placements and explicitly disables both chorus drop blocks. Reports include cap and accepted flash count.
**Tests/evidence:** 17 pure policy tests pass (shared colors, full guard, exact cooldown boundaries, out-of-order history, fractional/disabled caps, nonfinite values, no mutation). Combined audio/cache/policy selection: **46 passed**. CLI `main(["--help"])` exposes the new flag. `git diff --check` passed. Existing failures remain recorded under Part A; full comparison follows Part C.
**Limitations:** counts flash starts, not illuminated duration or all other aggregate groups (house/perimeter); long effects may still sustain broad illumination. Placement-pass order determines which competing flash survives. Accepted history is conservative if later priority replacement removes a flash.
**Deferred work:** do not wire `core/power_engine.py`, `core/effect_layering_engine.py`, `helix_style/restraint_engine`, or `helix_style/brightness_budget` into generation in this change. Real-song XSQ/MP4/xLights visual review remains outstanding.
**Regression risks:** fewer whole-layout effects can reduce accent density; all references resolving to the same whole-layout target are restrained, regardless of which helper requests them. Existing placement retry shifts remain subject to the same final-time cap.


### 2026-11-09 — Part A: cache separated stems and reuse mix HPSS
**Goal:** avoid repeating stem separation, mix loading/HPSS, and stem-summary STFT work.
**Changed files:** `core/audio_intelligence.py`, `tests/test_audio_stem_cache.py`, `MASTER_TODO.md`.
**Preserved behavior:** separator preference (Moises → Demucs → local → direct), per-stem timing/feature analysis on every invocation, local DSP output when mix is omitted, and spectral band totals. No patch attachment was available.
**New behavior:** `stems_manifest.json` under each audio-stem cache directory uses audio SHA-256, use_moises, and Demucs PATH availability; only existing files resolving within that directory are reused. Corrupt/incomplete/escaped entries miss; empty direct fallbacks are never cached. `analyze_audio_file` supplies its computed mix and HPSS arrays to local separation. Stem summaries share one magnitude STFT.
**Tests/evidence:** dependencies installed with the requested requirements command after installing CPU PyTorch (the initial CUDA dependency download was interrupted to preserve disk space). `python -m pytest` before changes stopped at the existing `test_drum_mapping.py` import error (`assign_hand` absent). Expanded baseline, `python -m pytest --continue-on-collection-errors`: **19 failed, 910 passed, 5 skipped, 1 xfailed, 1 collection error**. `python -m pytest tests/test_audio.py tests/test_audio_stem_cache.py -q`: **30 passed**. Tests cover round trip/separation once per file (including preserved relative-path metadata), changed content at equal length, Moises/Demucs fingerprint changes, missing files, relative/absolute/symlink escapes, corrupt manifests, no caching of direct fallback, forwarding/reusing mix, identical synthetic local outputs, and single-STFT band totals. `git diff --check` passed.
**Limitations:** cached stems still incur timing/classification work; no concurrent-writer locking, separator-version fingerprinting, cache eviction, or real-audio timing claim in this part. A failed remote/Demucs attempt can cache its successful local fallback until the fingerprint changes.
**Deferred work:** broader audio feature caching and benchmark/render validation; Part B flash cap and Part C background-vocal diagnostics follow.
**Regression risks:** same-stem filenames share a cache slot (content SHA invalidates it); PATH changes trigger re-separation; cached PCM output can outlive separator/config changes not represented by the requested fingerprint.
**Branch/base:** `perf/audio-stem-cache-hpss-once` starts at `feature/restructure-core` (`59f3240`), as explicitly selected by the user. A PR to main includes that branch's pre-existing changes.

**Pre-existing expanded-baseline failures (not changed or weakened):**
- `test_band_export_manifest_tool.py::test_export_band_performance_manifest_writes_expected_files`
- `test_band_geometry_manifest.py::test_geometry_status_reports_all_manifested_models`
- `test_band_runtime_catalog.py::test_performer_runtime_catalog_contains_all_five_members`
- `test_band_runtime_full_band_alignment.py::test_runtime_catalog_matches_full_band_model_specs`
- `test_band_vocal_face_export.py::test_band_demo_manifest_includes_vocal_face_export`
- `test_drum_detection.py::DrumDetectionTests::test_classifier_maps_frequency_profiles`
- `test_drum_detection.py::DrumDetectionTests::test_mixed_track_profiles_do_not_collapse_to_bus`
- `test_drummer_v3_pose_sheet.py::test_drummer_v3_xmodel_has_exactly_three_tom_zones`
- `test_helixia_props.py::HelixiaPropsTests::test_all_snowman_band_members_have_structural_models`
- `test_helixia_props.py::HelixiaPropsTests::test_member_specific_instrument_submodels_are_present`
- `test_helixia_props.py::HelixiaPropsTests::test_snowman_drummer_models_submodels_and_groups`
- `test_helixia_xlights_band_specs.py::HelixiaXlightsBandSpecsTests::test_opt_in_band_model_specs_are_stem_map_compatible`
- `test_helixia_xlights_band_specs.py::HelixiaXlightsBandSpecsTests::test_opt_in_band_model_specs_generate_real_band_models_and_submodels`
- `test_preview_mux.py::test_mux_success_first_attempt`
- `test_preview_mux.py::test_mux_fallback_then_success`
- `test_preview_mux.py::test_mux_both_fail_preserve_silent`
- `test_snowman_band.py::SnowmanBandTests::test_structured_drum_events_drive_intelligent_drummer_cues`
- `test_working_drummer.py::WorkingDrummerTests::test_reactive_drummer_uses_legacy_marks_when_typed_streams_missing`
- `test_xsq_validation_tool.py::test_valid_fixture_passes`


### 2026-10-02 — Beta tester feedback checklist documented
**Agent:** GitHub Copilot
**Branch:** `feature/restructure-core`

**Recorded:**
- Added a repo-safe beta tester feedback checklist document for single-run evidence collection.
- Linked the checklist from the root README so testers can find it from the main entrypoint.
- Kept the checklist focused on privacy-safe, local-only evidence collection without requiring private asset disclosure.

**Limitations:**
- This is a documentation gate only; it does not claim xLights import success or visual quality.
- The beta roadmap still requires run manifest, GUI, and packaging safety work before broader beta claims.

### 2026-10-02 — Beta roadmap baseline alignment
**Agent:** GitHub Copilot
**Branch:** `feature/restructure-core`

**Recorded:**
- Restored the task index to the beta-roadmap-first workflow required by `ROADMAP_BETA_TODO.md`.
- Added a repo-level beta baseline status note to this ledger so the project continues in the intended order.
- Preserved the active drummer work while making the higher-priority beta safety work explicit.

**Limitations:**
- This does not replace the deeper engineering work required for drum detection or xLights import validation.
- Beta-safety milestones must still be executed in order before engine refactor work begins.

### 2026-09-30 — Ground-truth regression oracle locked
**Agent:** ChatGPT/GitHub
**Branch:** `feature/restructure-core`

**Recorded:**
- Prior known-good drummer behavior is anchored to commit `b27e8d77a63027ed32bcf6851dcff3925472c155`.
- The historical 8-submodel V3 workflow is retained as a behavioral regression reference while the physical model evolves to nine components.

### 2026-09-30 — Confidence-gated drum classification
**Agent:** ChatGPT/GitHub
**Branch:** `feature/restructure-core`
**Commit:** `b8e7f8fa5ab5044c774b3ca482711b47b89fb61c`

**Changed:** `audio/drum_classification.py`
- Added harmonic-contamination gating using the existing percussive/harmonic ratio.
- Added a minimum score-margin requirement between the best and runner-up drum classes.
- Ambiguous or weak events now become `drum_bus` instead of being confidently misclassified.

**Preserved:** existing kick/snare/tom/hat/cymbal feature scoring and six-stream event schema.

**Not yet verified:** real-song false-positive rate, XSQ output, and MP4 behavior.

### 2026-09-30 — Nine-component drummer geometry spec
**Agent:** ChatGPT/GitHub
**Branch:** `feature/restructure-core`

**Changed:** `fixtures/band_geometry/drummer_v3_pose_spec.json`
- Four distinct tom zones and nine canonical hit composites.
- Contacting sticks are embedded in snare/tom/hi-hat/cymbal components.

**Known limitation:** xmodel exporter still needs to make the nine composites the canonical sequencing submodels.

## Next actions
1. Preserve the prior known-good drummer behavior as the regression baseline.
2. Reconcile xLights drummer geometry with the nine canonical composites.
3. Add event provenance/debug output.
4. Run detector on the repository's real song and inspect event counts by class/confidence.
5. Generate full-song XSQ.
6. Render full-song MP4 with real audio.
7. Compare rendered component flashes to actual audible drum events and the prior known-good render.
8. Iterate only on measured false positives/false negatives.
