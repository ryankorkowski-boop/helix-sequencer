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

### 2026-11-17 — Birdsong synthetic hook truth labeling
**Goal:** Prevent synthetic post-run Birdsong demonstration data from being mistaken for song-driven sequencing evidence.
**Changed files:** `core/engine_activation_audit.py`, `tests/test_engine_activation_audit.py`, and this ledger.
**Preserved behavior:** Existing optional Birdsong hook, engine effect placement, xLights export, all flags and native behavior unchanged.
**New behavior:** Activation audit separately labels explicit Birdsong post-run hook requests as synthetic diagnostic requests and leaves real-audio analysis and exported-effect verification false.
**Tests/evidence:** Added regression test for explicit hook flag. CI pending after new commit.
**Limitations/deferred:** This does not determine whether the hook actually executed or whether core Birdsong generated real-song effects. Future work must trace real Birdsong placements and output.
**Regression risks:** None to rendering; only diagnostic schema extended. No merge without owner approval.


### 2026-11-17 — Changed-XSQ effect inventory
**Goal:** Begin reconciling what reaches output files without inventing per-engine attribution.
**Changed files:** `core/xsq_effect_inventory.py`, `core/sequence_builder.py`, `tests/test_xsq_effect_inventory.py`, and this ledger.
**Preserved behavior:** Effect generation, renderer selection, orchestration promotion, drummer/singer logic, Birdsong and matrix flags, native exports, and existing run manifests.
**New behavior:** The changed-artifact recorder returns paths. Run-scoped engine audits now include a streaming XML inventory of `Effect` elements only for changed XSQ files, including parse errors and explicit unverified engine attribution/FSEQ status.
**Tests/evidence:** Unit tests added for effect counting, exclusion of non-XSQ inputs, malformed XML, and empty outputs. GitHub CI and native xLights rendering not yet verified.
**Limitations/deferred:** XML counts cannot prove effects render or identify originating engine; XSQ output discovery remains limited to existing known-artifact paths. Large files incur additional parse time. Next: trace planner output IDs into accepted placements, then native FSEQ verification.
**Regression risks:** Additional XML parsing can increase run latency, and malformed files are reported rather than raising. No merges/releases without approval.


### 2026-11-17 — Run-scoped engine audit evidence
**Goal:** Prevent concurrent or repeated runs from overwriting engine activation evidence.
**Changed files:** `core/sequence_builder.py`, `tests/test_engine_activation_audit.py`, and this ledger.
**Preserved behavior:** Success/failure/interruption audit generation, run manifest registration, all engine enablement and effect selection, canonical drummer and singers, Android safety flags.
**New behavior:** The audit now writes to `ctx.run_dir/engine_activation_audit.json` instead of the shared output root, using the RunManager's existing unique run directory.
**Tests/evidence:** Added a fake-run-context regression test asserting unique-run placement and artifact registration. GitHub CI and real-run evidence pending.
**Limitations/deferred:** Report still lacks proposed/accepted/exported effect counts and native xLights verification. It is not a full engine integration proof.
**Regression risks:** External scripts expecting the old root-level audit path must instead read the artifact path from the run manifest. No merge or release without owner approval.


### 2026-11-17 — Preserve activation audit when sequencing fails
**Goal:** Avoid losing engine diagnostics when the sequencing engine throws or the user interrupts.
**Changed files:** `core/sequence_builder.py`, `tests/test_engine_activation_audit.py`, and this ledger.
**Preserved behavior:** Existing CLI error exit codes, run manifest finalization, successful audit schema, production effect selection, drummer, vocals, Android resource opt-outs and orchestration promotion.
**New behavior:** A shared best-effort audit writer is invoked for successful, failed, and interrupted runs; failure records include concise error type/message, not the traceback, and `run_completed=false`.
**Tests/evidence:** Added unit tests for failed/interrupted audit payloads. CI and actual failed-run manifest evidence pending.
**Limitations/deferred:** Run initialization failures before `RunContext` creation still have no audit; this is not per-engine effect export reconciliation. Shared output paths can be overwritten by concurrent runs. Future work: unique run-scoped audit files, native effect reconciliation, and planner instrumentation.
**Regression risks:** Audit filesystem failures are warnings only. No changes to renderer behavior; do not merge/release without approval.


### 2026-11-16 — Engine activation evidence report (first integration stage)
**Goal:** Make ignored or unverified engine paths visible without silently claiming that planned effects reached the xLights output.
**Changed files:** `core/engine_activation_audit.py`, `core/sequence_builder.py`, `tests/test_engine_activation_audit.py`, and this ledger.
**Preserved behavior:** Existing nine-pass invocation, explicit sidecar promotion, matrix/Birdsong runtime flags, band, drummer, singers, Android opt-outs, and native effect rendering remain unchanged.
**New behavior:** Successful CLI sequencing runs emit `engine_activation_audit.json` under the configured output root and register it in the run manifest. It reports known nine-pass invocation/sidecar/promotion separately from unknown final effect export; matrix/Birdsong flags are distinguished from verified invocation, while spatial/layering remain unverified. Failed report writing records a warning without failing sequencing.
**Tests/evidence:** Focused tests committed for Android-style opt-outs, sidecar-not-promotion, explicit promotion, failed orchestration, and JSON writing. GitHub CI and actual run artifact verification pending.
**Limitations/deferred:** No per-engine effect counts, no final XSQ/FSEQ reconciliation, no direct instrumentation inside the monolithic effect engine, and no failed-run audit yet. The file is diagnostic, not evidence of successful integration. Next stage should reconcile proposed/accepted/exported effect IDs and instrument skipped/failed planners without changing placement.
**Regression risks:** The output file is overwritten in shared output directories; run-specific manifests must be inspected. Audit write failures do not fail the main run. No merge or release without owner approval.


### 2026-11-16 — Diagnostic recurring music-region evidence (#236)
**Goal:** Identify repeated musical texture independently from energy/chroma novelty transitions without automatically calling repeats choruses.
**Changed files:** `core/music_section_recurrence.py` (bounded, deterministic nonoverlapping chroma-region cosine comparisons); `core/audio_intelligence.py` (exports `debug_summaries.structure_recurrence_candidates` from existing ~1 Hz chroma); `tests/test_music_section_recurrence.py`; this ledger.
**Preserved:** Existing song section labels, effect engine targeting, nine-pass director promotion rules, drummer, vocals, Birdsong, Android and Windows behavior remain unchanged.
**New behavior:** Recurring textured regions can be reported with timestamps, similarity, bounded pair counts and diagnostic confidence below 0.7; stationary chroma is rejected to avoid false repetition.
**Tests/evidence:** Unit tests committed for repeated textures, static-tone rejection, deterministic output, bounds and invalid input. CI and real-song evidence still pending; no native XSQ/FSEQ/MP4 created.
**Limitations/deferred:** Region-average chroma cannot distinguish songs sharing the same harmonic histogram; the detector may report false repeats. Future work needs beat-aligned sequences, temporal chroma trajectories, timbral recurrence and owner-reviewed real recordings. Diagnostic evidence is not a verified chorus label and is never eligible for automatic template promotion.
**Regression risks:** O(N²) region-pair comparisons on long songs, bounded output but not pair evaluations; currently uses fixed eight-second windows and ~1 Hz sampling. Limit full-song duration or optimize candidate indexing before large batch runs. No merge or release without owner approval.


### 2026-11-16 — Diagnostic music-structure novelty detector (#236)
**Goal:** Begin replacing forced equal-third song labels with evidence from actual audio features, without pretending change points are confirmed verses or choruses.
**Changed files:** `core/music_structure_candidates.py` (pure-Python, deterministic energy/chroma novelty detector); `core/audio_intelligence.py` (1 Hz sampled features and diagnostic-only `debug_summaries.structure_change_candidates`); `tests/test_music_structure_candidates.py`; this ledger.
**Preserved:** `section_events` and `_detect_song_sections` remain unchanged; no effect selection, timing, native output, drummer, vocals, Birdsong, Android/Windows behavior or orchestration promotion changes. No dependency or model downloads.
**New behavior:** Existing analysis exposes feature-driven candidate change points based on local energy and harmonic/chroma contrasts, minimum eight-second separation, absolute and relative novelty thresholds, deterministic tie-breaking and bounded output. Confidence deliberately capped at 0.65; candidate labels are neutral, not verse/chorus. Downsampled processing avoids expensive full-frame quadratic scans.
**Tests/evidence:** Unit tests committed for a known feature transition, stationary audio, deterministic bounded changes, malformed input and short clips. Tests not yet observed passing; real-song diagnostics and native XSQ/FSEQ/MP4 pending.
**Limitations/deferred:** These are only candidate boundaries; no repetition-based section identity, verified semantic labels, source-level ground truth or confidence calibration yet. They do not qualify for automatic promotion by the source-timeline gate. More accurate musical segmentation must compare self-similarity, recurrence, beat-grid boundaries, stems, and real audio against ground truths before upgrading confidence. Current analysis still exposes legacy equal-thirds `section_events` separately.
**Regression risks:** Additional CPU work proportional to downsampled song length and context size; pathological inputs are validated. Avoid interpreting candidate novelty as proven song form. No merge or release without owner approval.


### 2026-11-16 — Bind orchestrated sections to real source audio (#236)
**Goal:** Close a provenance gap where the nine-pass bridge accepted any well-formed source timeline without verifying it matched the requested audio file.
**Changed files:** `core/song_section_choreography.py`, `core/effects_orchestrator_bridge.py`, `tests/test_song_section_choreography.py`, and this ledger.
**Preserved:** Existing seed graph, nine-pass logic, effect routing, drummer, vocals, Birdsong, GUI defaults, and opt-in template promotion; legacy direct graph calls without audio identity remain usable for diagnostic-only fixtures.
**New behavior:** Bridge runs with `--orchestration-sections-json` now require an existing `--audio` file and a matching `audio_sha256` in the timeline JSON. A mismatch or missing hash fails closed and is recorded in the orchestration error report; matching hashes allow the nine passes to run. The SHA-256 check is streaming.
**Tests/evidence:** Updated nine-pass bridge test to use a real temporary audio fixture and matching hash, added mismatch rejection test. CI not yet confirmed; no native XSQ/FSEQ/MP4 evidence.
**Limitations/deferred:** No genuine musical-structure classifier integrated; existing energy-thirds fallback is low-confidence and rejected by the prior adapter. Audio hashing reads source bytes once more. This does not validate section semantic accuracy or automatically enable orchestration on Android.
**Regression risks:** Older manual section JSON without audio_sha256 will now fail at the bridge rather than silently producing a misleading sidecar. Explicitly regenerate/verify the timeline; never bypass source identity for production. No merge/release without owner approval.


### 2026-11-16 — Audio-analysis provenance gate for orchestration (stage 1b of #236)
**Goal:** Connect existing `audio_analysis.json` output to the strict source-timed orchestration adapter without treating the existing energy-third heuristic as verified music structure.
**Changed files:** `core/audio_intelligence.py` now writes `audio_sha256` into exported analysis metadata when the original audio exists; `core/audio_section_timeline_adapter.py` converts only matching-hash, high-confidence, non-fallback `section_events` into the strict section schema; `tests/test_audio_section_timeline_adapter.py` covers accepted timings, fallback/low-confidence rejection and hash mismatch; `tests/test_song_section_choreography.py` corrected an invalid test assertion to use supported `IntentGraph` iteration; `MASTER_TODO.md` handoff.
**Preserved:** No change to detection algorithms, generated section guesses, stem separation, drummer, vocals, Birdsong, output targeting, xLights render or Android/Windows defaults. Orchestrated XSQ promotion remains opt-in.
**New behavior:** Analysis exports include source SHA-256; an explicit converter can produce validated choreography input from trusted section events. The present `_detect_song_sections` produces low-confidence `energy_curve_fallback`/ `tail_fill` events; the converter deliberately rejects these rather than labeling synthetic intro/verse/chorus as musical truth.
**Evidence:** New unit tests committed but not yet independently run/passed; CI and real audio MP4 still pending.
**Limitations/deferred:** Current automatic audio structure detector does **not** produce qualifying verified sections; a stronger novelty/repetition-based segmentation model, source confidence and verified audio-duration matching must be implemented before automated integration. Adapter currently must be invoked explicitly by a caller; no end-to-end CLI, GUI, or Android wiring. No xLights FSEQ or MP4 delivered.
**Regression risks:** SHA-256 hashing at analysis export adds a streaming read of the audio file. If the source file is unavailable, no hash is emitted and the converter correctly refuses automatic trust. Do not merge or release without approval.


### 2026-11-16 — Source-timed nine-pass choreography input (stage 1 of #236)
**Agent:** ChatGPT / connected GitHub
**Branch:** `feature/orchestration-source-timeline-20261116`

**Goal:** Allow the existing nine-pass director to consume validated, externally verified music sections rather than only its synthetic 30-second seed.
**Changed files:** `core/song_section_choreography.py` (new adapter); `core/effects_orchestrator_bridge.py` (optional input); `core/sequence_builder.py` (strip private timeline flag before production engine); `tests/test_song_section_choreography.py`; this ledger.
**Preserved behavior:** Without `--orchestration-sections-json`, the old seed/sidecar behavior is unchanged; production promotion remains explicitly opt-in under #235. No changes to drummer, singer clocks, native xLights effect selection, model routing, Birdsong, or platform defaults.
**New behavior:** When passed `--orchestration-sections-json PATH`, orchestration reads a JSON object with `source` (`audio_analysis` or `verified_manual`), positive `duration_seconds`, and contiguous `sections` with `label`, `start_seconds`, `end_seconds`, and `energy` 0–1. Invalid/missing/nonfinite/out-of-range/gapped/overlapping timelines fail closed in the bridge report rather than silently using synthetic sections. Section labels/energy drive deterministic per-section motion grammar. The private CLI option is not passed into the effect engine.
**Tests/evidence:** Nine focused test cases committed, covering real timings, invalid boundaries, provenance, nine-pass handoff, and CLI flag filtering. Tests not yet observed passing; hosted CI and real-song native renders pending.
**Limitations/deferred:** The adapter **does not infer** song structure or verify that a JSON artifact was actually derived from its matching audio. Caller must provide independently validated source timing. Current director still only seeds section-level intents; deeper beat, harmony, phoneme, instrument and spatial choreography is future work. No GUI option or APK integration yet. Do not advertise full song-derived choreography.
**Regression risks:** Wrong but well-formed section JSON could mismatch the audio; future integration must compare audio hashes and durations. Legacy synthetic behavior remains when no JSON is supplied. Do not auto-promote unverified XSQs. No merge or release without owner approval.


### 2026-11-16 — Safe choreography-promotion contract (audit follow-up)
**Agent:** ChatGPT via connected GitHub
**Branch:** `fix/orchestrator-promotion-contract-20261116`

**Goal:** Ensure the run configuration tells the sequence builder whether orchestrated output actually replaces the production XSQ input. Close the mismatch where `RunConfig` defaulted to promoting, but `to_engine_args()` never emitted the builder's required `--promote-orchestrated-template` flag.

**Changed files/modules:**
- `core/run_spine.py`: promotion defaults off, and explicitly opted-in promotion serializes `--promote-orchestrated-template`. Sidecar-only still serializes `--no-orchestrator-template-promotion`.
- `tests/test_orchestrator_promotion_contract.py`: six new regression cases for default sidecar, explicit opt-in, config round-trip, actual template substitution, unwritten XSQ, and orchestrator-disabled precedence.
- `MASTER_TODO.md`: this audit/handoff ledger.

**Intentionally preserved behavior:** Existing nine-pass orchestration and its reports; output selection without explicit promotion; no changes to `effect_engine.py`, drum geometry, event detection, vocals, effect placement, model targeting, or audio timing; no auto-enablement of Birdsong.

**New behavior:** Programmatic `RunConfig(promote_orchestrated_template=True)` now emits the explicit opt-in accepted by `sequence_builder.py` instead of silently leaving promotion inactive. Default sidecar mode is now explicit and agrees with the builder.

**Evidence / tests:** Source-path inspection of `core/sequence_builder.py`, `core/run_spine.py`, and `core/effects_orchestrator_bridge.py`; six regression tests committed. GitHub CI, local pytest, real-song XSQ comparison, native FSEQ/MP4 decode and visual acceptance must be checked separately; no passing results claimed merely because tests were written.

**Limitations / deferred work:**
- `build_seed_graph()` in `core/effects_orchestrator_bridge.py` still fabricates a five-section, 30-second show when no duration is given. It does **not** derive actual music sections or singer/drum events. Keep template promotion opt-in; do not auto-enable this graph on release paths.
- The unused-looking duplicate `core/run_config_v2.py` still claims default promotion on. Determine all import consumers before removing/changing it (PR #207 proposed cleanup on a different branch).
- Verify launch arguments in Windows EXE, Android APK, and CLI independently; not established by a Python config unit test.
- Compare identical source audio and nine-panel layouts with orchestration sidecar-only vs explicit promotion; measure timeline alignment, XSQ placements, FSEQ channels, native xLights effects, visual variety, singer accuracy and drummer oracle, before enabling broadly.
- Birdsong in `core/effect_engine.py` is directly wired but defaults off, and is not evidence that the nine-pass orchestration output reached native renders.

**Regression risks:** An operator that previously constructed `RunConfig(promote_orchestrated_template=True)` but relied on its silently ignored setting will now actually promote the synthetic orchestrated XSQ; until musical alignment is proven, only opt in for isolated test runs. Keep this PR unmerged until focused tests and the no-surprises behavior are verified.


### 2026-11-13 — Beta 1.3 packages the palette fix for Windows and Android
**Agent:** Cursor cloud agent
**Branch:** `cursor/beta-1-3-release-1aae`

**Goal:** Ship the white-output fix from pull request #218 in the Windows portable zip and Android APK testers install, labeled Beta 1.3.

**Changed files/modules:**
- Merged #218 (`core/effect_engine.py`, `tests/test_palette_not_white.py`).
- `core/helix_version.py`, desktop title/About, CLI `--version`, Android `versionName` `1.3.0-beta` / versionCode 9, and the Windows version resource.
- Restored the November Drive packaging shape: `windows_portable.spec` one-folder zip and the Chaquopy `android/` debug project, with `.github/workflows/beta-v1.3-packages.yml`.
- `tools/palette_smoke.py` generates a synthetic sequence and fails if effects still resolve to a white-only palette.

**Intentionally preserved behavior:** Effect choice, timing, and model targeting from the merged default branch. A template palette that already enables a chromatic color is left unchanged. Release signing still requires the owner's keystore; the handoff APK stays the debug build testers already install. Layouts that are not on this branch were dropped from the Android sample list.

**New behavior:** User-visible version is Beta 1.3. Packaged effects point at section palette rows instead of a white-only palette 0.

**Tests/evidence:** `tests/test_palette_not_white.py` and `tests/test_helix_version.py`. Full suite: 916 passed, 19 failed, 5 skipped, 1 xfailed, 1 collection error in `tests/test_drum_mapping.py`. The 19 failures are the pre-existing band, drummer, preview-mux, and xsq-validation tests. A local synthetic-tone sequence wrote 2128 named effects, none on a white-only palette, across palette indexes 3–8. Packaged Windows and Android evidence is produced by `.github/workflows/beta-v1.3-packages.yml`.

**Limitations:** The historical `windows-portable.yml` and `android-offline.yml` files are not on this branch, so the new workflow rebuilds that package shape without the emulator matrix or release keystore. The cloud agent token cannot call `workflow_dispatch` (Actions permission denied), so the workflow also starts on a push that changes the packaging files. Run 43430925127 failed in the workflow, not the engine: the smoke command passed a bare `--` that argparse rejected, and `android-actions/setup-android@v3` asked sdkmanager for the removed `tools` package. Android code that depended on `core.band_visibility`, `core.output_provenance`, and later-only CLI flags is skipped when those modules are absent. The separate palette-variety pull request is not included.

**Deferred work:** Production Android signing (`HELIX_ANDROID_KEYSTORE`, `HELIX_ANDROID_STORE_PASSWORD`, `HELIX_ANDROID_KEY_ALIAS`, `HELIX_ANDROID_KEY_PASSWORD`) and the API 30/36 emulator matrix from `android-offline.yml`.

**Regression risks:** Desktop About/title text moved the layout-preset row down one. Android LOR runs use AC-safe effects without the later source-LMS binder.

### 2026-11-13 — Default sequences no longer collapse to a white-only palette
**Agent:** Cursor cloud agent
**Branch:** `cursor/rich-palettes-f36b`

**Goal:** Master-profile output should use multiple hues, change color with the song section, and reserve white for accent effects.

**Changed files/modules:**
- `core/effect_engine.py` replaces a white-only template palette (including palette index `0`) before effects are written, on both `add_model` and the all-models showcase path.
- The polish pass no longer copies a white-only template palette back onto effects near section boundaries.
- `tests/test_palette_not_white.py` fails if that path returns palette `0` or any white-only palette again.

**Intentionally preserved behavior:** A template palette that already enables a chromatic color is left unchanged. Effect choice, timing, and model targeting are unchanged. `palette_mode=template` still starts from the template palette.

**New behavior:** When the resolved palette enables only near-white, Helix appends a ColorPalettes row of section hues and sets the effect palette to that index. xLights ignores an inline palette string and falls back to palette 0, so an index is required. Twinkle, Shimmer, Strobe, Snowflake, and Sparkle also check a white accent. Other effects do not.

**Tests/evidence:** `tests/test_palette_not_white.py` (4 passed) plus `tests/test_palette_discipline.py` (8 passed). Full suite: 914 passed, 19 failed, 5 skipped, 1 xfailed, 1 collection error in `tests/test_drum_mapping.py`. The 19 failures are pre-existing band, drummer, preview-mux, and xsq-validation tests. Imageio is installed in this environment, so the previously cited 24 imageio failures are not all present. Before the change, real xLights 2026.19 FSEQ renders averaged 91.1% near-white lit RGB pixel-frames across 22 layout/song pairs. After the index fix the same metric is 0.040% (highest pair 0.169% on wow_spinners / north_pole_overdrive). AC layouts have no multi-pixel RGB nodes, so they stay out of that metric; their visible color is still the model color times intensity. An isolated probe rendered palette index 0 red and an inline blue string red as well, confirming xLights discards the inline string.

**Limitations:** Color still follows song sections already detected by Helix. A song that stays in one section keeps one hue family, with the lead color rotating per effect. Single-channel AC props are not recolored by this change.

**Deferred work:** None for this item. V01-NPO-ALL16 and V06-CLF-WOW12 were re-rendered from the new FSEQ files.

**Regression risks:** Sequences whose template palette 0 was intentionally white-only will now gain color. That is the requested change. The sequence gains extra ColorPalette rows.

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
