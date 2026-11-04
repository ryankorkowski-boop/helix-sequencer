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

## Change Ledger — main-path xLights contract

### 2026-11-04 — Failed audio or a missing sequence exits non-zero
**Branch:** `cursor/main-path-xsq-fixes-41d8`

**Goal:** A per-audio generation error, or a run that does not write a new `.xsq`, must fail the process and be visible in the run manifest and the per-audio report (issue #114).

**Changed:** `core/effect_engine.py`, `core/effect_engine_beat_grid.py`, `core/sequence_builder.py`, `tests/test_sequence_generation_failures.py`, `tests/test_sequence_builder_orchestrator_promotion.py`

**Preserved:** Successful runs still finalize `success: true`. Orchestrator promotion and BeatGrid flag stripping are unchanged. The birdsong post-hook can still fail without failing the sequence.

**New behavior:** `effect_engine.main_for` records each audio failure (exception text plus traceback) in `*.report.json` and raises `SequenceGenerationError`. `run_profile` finalizes the manifest as failed and exits 1 when that exception escapes, when the engine raises `SystemExit`, or when no new `.xsq` appears under the output root.

**Tests:** `tests/test_sequence_generation_failures.py` and the orchestrator promotion tests.

**Limitations:** The underlying Lights Out render exception from the original workflow run was not reproduced here. This commit fixes the success contract, not a specific effect-engine crash.

**Deferred:** Overlap with open PRs #206/#207, which also edit `sequence_builder.py` (duplicate helper removal and effective engine args). Those edits are left in place on their branches. #188 is untouched.

**Regression risks:** Callers that treated a logged `FAILED:` line as a successful process exit now get a non-zero exit. Tests that mock the engine must write an `.xsq` if they expect success.

### 2026-11-04 — Sequence duration follows the audio
**Branch:** `cursor/main-path-xsq-fixes-41d8`

**Goal:** `<head><sequenceDuration>` matches the audio length, and effect rows and timing marks do not extend past that end.

**Changed:** `xlights/xml_io.py`, `xlights/xsq_writer.py`, `core/effect_engine.py` (`run_variant`, immediately before the `.xsq` write), `tests/test_sequence_duration.py`

**Preserved:** `replace_audio_references` still only swaps the media filename. Effect placement still uses the analyzed `song_length_ms`. A non-positive duration raises instead of writing a zero-length sequence.

**New behavior:** `apply_sequence_duration` writes the duration in seconds (3 decimal places, matching the template) and clips or drops `Effect` rows, including timing-track marks, at the audio end. `run_variant` calls it with `audio.dur_s` from `xsq_writer.analyze`.

**Tests:** `tests/test_sequence_duration.py` loads `template.xsq` (132.039 s) and applies a generated 30.000 s WAV. A second case clips a crossing effect and drops a timing mark that starts at the boundary.

**Limitations:** Not opened in xLights. Duration comes from the analyzer's sample count (`len(y) / sr`), which matches the WAV header used in the test. MP3 frame padding was not compared against an xLights media import.

**Deferred:** Showcase generation (`GENERATE_SHOWCASE`) rewrites a second file and does not call this helper itself.

**Regression risks:** Template effects that used to survive past a shorter song are now clipped or removed on write.

### 2026-11-04 — Effects store ref and palette indexes
**Branch:** `cursor/main-path-xsq-fixes-41d8`

**Goal:** Placed effects carry `ref` and `palette` indexes into `EffectDB` and `ColorPalettes`, the way `template.xsq` and xLights store them, instead of inline `settings` / palette strings.

**Changed:** `xlights/xml_io.py`, `xlights/xsq_writer.py`, `core/effect_engine.py`, `helix_intent/xsq_template_writer.py`, `tests/test_effect_db_roundtrip.py`, `tests/test_xsq_template_writer.py`

**Preserved:** Reading still accepts an inline `settings`/`data` string or an inline palette string when no index is present. An existing EffectDB or ColorPalettes row is reused when the text matches. Callers that do not pass the document root still write the legacy attributes.

**New behavior:** `add_effect(..., root=)` and the orchestrator template writer intern settings and palette text, then write `ref` and `palette` indexes. Readers resolve those indexes back to the stored strings. A round-trip check reports any Effect whose index does not resolve.

**Tests:** `tests/test_effect_db_roundtrip.py` proves every Effect `ref` and `palette` resolves after write and reparse, including a newly appended EffectDB row. The template-writer test now checks the resolved strings.

**Limitations:** Not opened in xLights. EffectDB child order is the index, matching xLights. Timing-mark rows that only carry a `label` are not required to have a `ref`.

**Deferred:** None for this storage format.

**Regression risks:** Code that read the `settings` attribute off a newly written Effect now has to resolve `ref`. The main path and the template writer were updated.

## Next actions
1. Preserve the prior known-good drummer behavior as the regression baseline.
2. Reconcile xLights drummer geometry with the nine canonical composites.
3. Add event provenance/debug output.
4. Run detector on the repository's real song and inspect event counts by class/confidence.
5. Generate full-song XSQ.
6. Render full-song MP4 with real audio.
7. Compare rendered component flashes to actual audible drum events and the prior known-good render.
8. Iterate only on measured false positives/false negatives.
