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

### 2026-11-17 — Correct public Demucs checkpoint integrity validation
**Goal:** Check full SHA256 of downloaded public model bytes, not the eight-hex Demucs model identifier preceding the filename hash.
**Changed files:** `.github/workflows/helix-demucs-public-checkpoint.yml` and this ledger.
**Preserved behavior:** Existing music analysis, user audio, band and drummer; no sequence changes.
**New behavior:** Require full expected SHA256 `8726e21a993978c7ba086d3872e7608d7d5bfca646ca4aca459ffda844faa8b4` (as published for model file `955717e8-8726e21a.th`) instead of wrong `955717e8` prefix; prevents erroneously rejecting authentic model bytes.
**Tests/evidence:** Initial runner fetched file but rejected it under incorrect hash check; corrected workflow job and local Demucs re-analysis pending.
**Limitations/deferred:** Public model availability and CPU inference unverified. No native FSEQ/MP4 yet.
**Regression risks:** Public download and temporary artifact only, no runtime changes or owner approval.


### 2026-11-17 — Public Demucs model dependency for real-audio stem validation
**Goal:** Avoid accepting poor fallback drum and vocal classifications after pretrained Demucs weights failed to download in an isolated runtime.
**Changed files:** `.github/workflows/helix-demucs-public-checkpoint.yml` and this ledger.
**Preserved behavior:** No runtime effect, vocalist, or drummer edits; no fabricated kick or lead events; existing source bytes, owner ground truth, release restrictions maintained.
**New behavior:** On a branch-scoped workflow-file push, retrieve only the public htdemucs checkpoint on GitHub runner, validate the expected SHA256 prefix, and retain it as a two-day CI artifact with provenance receipt. No user music or Drive identifiers enter GitHub.
**Tests/evidence:** Earlier Tinsel Tornado run had Demucs DNS failure and fallback drum stream with zero kicks and two snares; public model fetch and local reanalysis remain pending.
**Limitations/deferred:** Model may fail remote fetch, CPU inference, or provide imperfect singer separation. Native xLights FSEQ/MP4 still unverified.
**Regression risks:** Short CI job uses external download and storage; no runtime sequencing effect. No merge/release without owner approval.


### 2026-11-17 — Real-run XSQ reconciliation filters out non-sequence artifacts
**Goal:** Reconcile authoritative XSQ candidates rather than listing unrelated JSON, HTML and notes from the actual Tinsel Tornado run.
**Changed files:** `core/orchestration_xsq_reconciliation.py`, `tests/test_orchestration_xsq_reconciliation.py`, and this ledger.
**Preserved behavior:** Engine output, band, drummer, audio analysis and existing native preview untouched.
**New behavior:** Only changed `.xsq` files other than the orchestration sidecar are final candidates.
**Tests/evidence:** First real 205.8s source run exposed 8 candidate paths but only one was XSQ; unit regression added and 30 focused tests passed locally.
**Limitations/deferred:** Filename and XML provenance alone do not prove final rendered FSEQ or nine-panel playback.
**Regression risks:** Diagnostics only. No merge/release without explicit owner approval.


### 2026-11-17 — Real Tinsel Tornado run exposed skipped snowman-band planner
**Goal:** Restore typed-drum snowman-band planning without altering canonical drummer assignments or falsifying drum detections.
**Changed files:** `core/snowman_band.py`, `tests/test_snowman_band.py`, and this ledger.
**Preserved behavior:** Existing drum event classifier, mapper, nine-cue canonical drummer geometry, effect selection/timing/model targeting, source vocal data and native xLights exports; no fabricated events.
**New behavior:** Accept missing optional `composite_submodels` metadata from `mapping.drum_mapper.map_events_to_submodels`, defaulting to an empty list rather than raising `KeyError` and disabling the entire snowman-band plan.
**Tests/evidence:** Reproduced exact exception locally on a typed kick event. After fix, 29 tests passed across snowman-band, engine audit and XSQ reconciliation suites. First real source SHA256 `8b8caddd6c292a13995bde0e80ac66f948246bd634278ab4ade1a82163aa7086`, original Drive Tinsel Tornado (205.8s), generated 32,540 XSQ effects; original run had `[WARN] Snowman band planning skipped: KeyError('composite_submodels')`. Confirmation rerun pending.
**Limitations/deferred:** The same real-song run fell back when Demucs separation failed, classified zero kick and two snare hits despite legacy stem marks, and did not generate native FSEQ/MP4; band cue recovery does not establish playable approval. `tests/test_drum_mapping.py` has pre-existing collection failure (removed `assign_hand` import); tracked separately, not fixed here.
**Regression risks:** Empty optional composite metadata may omit composite-specific visual overlays but avoids total loss of all band cues. Native band and drum-strike illumination must be verified before approval. No merge/release without owner authorization.


### 2026-11-17 — Isolated source snapshot for verified Tinsel Tornado run
**Goal:** Obtain a bounded, reproducible source checkout for a local real-audio sequencing run; avoid treating synthetic outputs as review-ready.
**Changed files:** `.github/workflows/helix-source-review-snapshot.yml` and this ledger.
**Preserved behavior:** All engines, band/drummer ground truth, Android behavior, native export and existing CI; no merges or release.
**New behavior:** On a single branch-scoped push of the new workflow file, archive small tracked text-source files (excluding audio/video, Git history and oversized artifacts) and upload as a short-lived GitHub Actions artifact for isolated inspection and validation.
**Tests/evidence:** Commit and CI pending; source manifest includes exact commit and tar SHA256; externally sourced Tinsel Tornado audio remains outside Git.
**Limitations/deferred:** Snapshot excludes oversized and binary assets and does not supply xLights native renderer. Real-audio sequencing, XSQ/FSEQ validation and nine-panel MP4 remain unverified.
**Regression risks:** Actions minutes and ephemeral source artifact; no change to runtime sequencing. Do not merge/release without approval.


### 2026-11-17 — End-to-end audit integration regression
**Goal:** Exercise run-audit JSON writing with a real temporary orchestration sidecar and downstream XSQ candidate in one test.
**Changed files:** `tests/test_engine_activation_audit.py` and this ledger.
**Preserved behavior:** No production code changes; existing orchestration, engine placement, export and canonical band behavior unchanged.
**New behavior:** CI now checks that run-scoped audit includes both XML inventory and sidecar/final-candidate reconciliation, with native verification explicitly false.
**Tests/evidence:** Added integration-style temporary-file regression; GitHub CI pending for this commit. This does not execute xLights or use real audio.
**Limitations/deferred:** Full song/XSQ/FSEQ/MP4 acceptance run remains outstanding; no CI artifact produced from this test.
**Regression risks:** Minimal test-only overhead; no merge without approval.


### 2026-11-17 — Repair shadowed artifact collector and stale sidecar evidence
**Goal:** Make the changed-XSQ audit functional and avoid counting stale orchestration sidecars.
**Changed files:** `core/sequence_builder.py`, `core/orchestration_xsq_reconciliation.py`, `tests/test_orchestration_xsq_reconciliation.py`, and this ledger.
**Preserved behavior:** Existing engine invocation, effect placement, drummer, singer, Android flags and output formats.
**New behavior:** Remove duplicate late helper definitions that shadowed the artifact collector's list return (and could make XSQ audit fail); snapshot before orchestration; count sidecar XML only when its path was changed during this run.
**Tests/evidence:** Added stale/current sidecar tests and duplicate-definition regression check. CI and real native run pending.
**Limitations/deferred:** Concurrent runs writing the same output filename can still race; source tagging does not prove native FSEQ. Follow-up should use run-unique artifact paths and authoritative output selection.
**Regression risks:** Earlier snapshot includes orchestration outputs and may record additional changed artifacts; diagnostics remain best effort. No merge without approval.


### 2026-11-17 — Orchestration sidecar versus changed XSQ reconciliation
**Goal:** Prevent orchestration-sidecar effects from being counted as final renderer output and detect provenance tags in changed non-sidecar XSQ candidates.
**Changed files:** `core/orchestration_xsq_reconciliation.py`, `core/sequence_builder.py`, `tests/test_orchestration_xsq_reconciliation.py`, and this ledger.
**Preserved behavior:** Engine selection, effect placement, orchestration promotion semantics, Android safeguards, snowman drummer, xLights rendering and export untouched.
**New behavior:** Run audit separately inventories orchestrated sidecar tags and changed non-sidecar XSQ candidates, explicitly reporting whether candidate XML contains orchestration provenance. No native FSEQ or final-authority claim.
**Tests/evidence:** Unit tests for sidecar-only, tagged non-sidecar output, and malformed XML. CI/native real-song evidence pending.
**Limitations/deferred:** Changed XSQ candidates are not independently proven authoritative final outputs. XML tags may not survive canonical writer; native FSEQ decode, playback and engine-by-engine placement attribution remain outstanding.
**Regression risks:** Additional XML parse of sidecar and candidates; diagnostic-only, best effort. No merge or release without owner approval.


### 2026-11-17 — XSQ orchestrator-authored provenance
**Goal:** Distinguish explicitly tagged orchestration effects from untagged effects in changed XSQ files without falsely asserting native export or planner attribution.
**Changed files:** `core/xsq_effect_inventory.py`, `tests/test_xsq_effect_inventory.py`, and this ledger.
**Preserved behavior:** XML effect writer, placement decisions, engine flags, renderer, native export, band and drummer ground truth.
**New behavior:** Streaming inventory counts `Effect` rows with `source=HelixOrchestrator`, unique nonempty source visual intent IDs, and other/untagged effects. Malformed XML yields null counts; native FSEQ and planner attribution remain unverified.
**Tests/evidence:** Regression tests for tagged/untagged counts, deduplicated intent IDs, and malformed XML. CI and real native render pending.
**Limitations/deferred:** XML provenance can be spoofed or stripped by downstream writers; tags prove only presence in parsed output, not render success or musical validity. Need source-tag continuity tests through canonical engine and FSEQ verification.
**Regression risks:** Added constant-work per XML effect and set of distinct IDs; diagnostic-only. No merge/release without owner approval.


### 2026-11-17 — Nine-pass orchestration provenance and count chain
**Goal:** Surface synthetic seed-section usage and distinguish intent, placement, contract and sidecar counts from verified final export.
**Changed files:** `core/engine_activation_audit.py`, `tests/test_engine_activation_audit.py`, and this ledger.
**Preserved behavior:** Existing orchestration seed/fallback, optional source-section validation, all placement/rendering decisions, Birdsong and matrix behavior, canonical band, Android safeguards.
**New behavior:** Activation audit records whether source-timed sections were requested and successfully accepted by an invoked orchestrator, whether the run used synthetic seed sections only, input/final intents, placement candidates, contract placements, sidecar effects and layout/fallback placement source.
**Tests/evidence:** Regression tests cover synthetic-only reporting, count chain, failed section invocation and successful source-section acceptance. CI and real native renders pending.
**Limitations/deferred:** Counters are report-derived, not independent reconciliation of the final XSQ/FSEQ. Source-section validation success means the orchestration bridge returned invoked, not that music structure was independently reviewed. Placement source may still include fallback candidates.
**Regression risks:** Diagnostic-only schema extension; no change to effect selection. Do not merge/release without approval.


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

### 2026-11-17 — Unified beta completion handoff initialized
**Agent:** ChatGPT GitHub integration session
**Branch:** `integration/unified-beta-completion-20261117`

**Goal:** Establish crash-resistant integration baseline for engine audit, Android/Windows parity, canonical band and nine-panel real-audio showcase.

**Changed files/modules:** `MASTER_TODO.md`, `docs/BETA_COMPLETION_LIVE_HANDOFF.md`, `evidence/beta_completion/latest_status.json`, `evidence/beta_completion/artifact_manifest.json`.

**Preserved behavior:** No sequencing, drummer, Android, Windows, or rendering logic modified. No PR merged. Branch forked from PR #248 head `bb41f078` for non-destructive reconciliation.

**New behavior:** Persistent task IDs HBC-001 through HBC-007, explicit blockers, next actions, empty verified-artifact manifest, and Beta Version 1.4 pending label.

**Tests/evidence:** Repository metadata and mandatory files inspected; no executable tests or native renders run. GitHub file commits are documentation evidence only.

**Limitations / deferred work:** Engine execution-path matrix, CI, real-audio native verification, Android/Windows builds and nine-panel MP4 remain unfinished. Existing four-tom ledger conflicts with current owner-required three toms; investigate before code changes.

**Regression risks:** Documentation only; future integration must not overwrite concurrent branches or claim audit instrumentation proves native output.

### 2026-11-17 — Audit promotion requires a usable orchestrated template path
**Goal:** Avoid false-positive promotion reporting when orchestration claims a sidecar but supplies no template path.
**Branch:** `integration/unified-beta-completion-20261117`; implementation commit `ee03ead0`, test commit `284288e0`.
**Changed files:** `core/engine_activation_audit.py`, `tests/test_engine_activation_audit.py`, handoff documents.
**Preserved:** Default sidecar-only behavior, explicit promotion flag, effect selection/timing/model targeting and drummer geometry unchanged.
**New behavior:** Audit no longer claims promotion without `orchestrated_xsq_path`; focused regression test added.
**Tests/evidence:** Test authored but NOT executed in this session. No XSQ/FSEQ or native render evidence. Existing test fixture updated to supply the required path.
**Limitations/deferred:** Existence/content of template and actual final renderer consumption still unverified; source section validation also requires more than a flag. Run targeted pytest and real audio export next.
**Regression risk:** Audit output changes for malformed reports; production sequencing unchanged.

### 2026-11-17 — Explicit orchestration template routing regression coverage
**Goal:** Lock the intended distinction between sidecar planning and actual renderer template selection.
**Changed files:** `tests/test_sequence_builder.py`, `MASTER_TODO.md`, `docs/BETA_COMPLETION_LIVE_HANDOFF.md`.
**Preserved:** Existing opt-in promotion policy, native export logic, audio analysis, all effect choice/timing/targeting, approved drummer.
**New behavior:** Test checks default sidecar-only, explicit promotion replacing `--template`, opt-out overriding promotion, and missing path refusing promotion. No runtime behavior modified.
**Tests/evidence:** Regression authored in commit `e6c2e4cb`; no CI workflows or combined commit statuses observed at prior head. No pytest run or native render performed.
**Limitations/deferred:** Execute targeted tests and prove native XSQ/FSEQ consumption before declaring integration fixed.
**Regression risks:** Test may reveal existing routing mismatch; none introduced to production code.

### 2026-11-17 — Orchestration input-template prerequisite audit
**Goal:** Identify why orchestration plans can exist without renderable orchestrated XSQ.
**Changed files:** `MASTER_TODO.md`, `docs/BETA_COMPLETION_LIVE_HANDOFF.md` (documentation only).
**Finding:** `core/effects_orchestrator_bridge.py::_write_orchestrated_xsq` returns `xsq_written=False` if `--template` absent or its path does not exist. `core/sequence_builder.py` promotes only when `--promote-orchestrated-template` is supplied and report says XSQ written. Hence successful planner invocation alone is insufficient for actual template-based choreography export.
**Preserved:** Production code, default sidecar-only policy, deterministic effect choices, canonical drummer.
**Tests/evidence:** Direct source inspection only. No CI jobs/statuses found at previous branch head; no test or native render executed.
**Next:** Add tests for missing-template bridge results, inspect whether production launchers supply `--template`, then run real-song side-by-side native output with explicit promotion.
**Risk:** Enabling promotion without a valid source template or song-grounded sections can produce misleading choreography; avoid changing default yet.

### 2026-11-17 — Launcher audit and v2 config promotion parity
**Goal:** Reconcile real launcher behavior with orchestration promotion policy.
**Changed files:** `core/run_config_v2.py`, `tests/test_run_config_v2_orchestration.py`, `MASTER_TODO.md`, `docs/BETA_COMPLETION_LIVE_HANDOFF.md`.
**Findings:** Android `android/app/src/main/python/helix_mobile.py::build_args` unconditionally passes `--no-effects-orchestrator` despite providing template and layout. Thus Android currently bypasses the nine-pass orchestrator; whether this is a deliberate mobile resource constraint requires validation before changing. Windows `windows_portable_entry.py` forwards to sequence_builder CLI. Existing `tests/test_sequence_builder_orchestrator_promotion.py` already tests full run_profile fake-engine argument propagation. `core/run_config_v2.RunConfig` previously defaulted promotion True yet emitted no positive promotion flag, so real sequence_builder would not promote.
**Preserved:** Android opt-out and resource safeguards, default renderer sidecar-only behavior, canonical drummer, effect timing/targeting.
**New behavior:** v2 config defaults promotion False and emits explicit `--promote-orchestrated-template` when user opts in. Tests added for default and round trip.
**Tests/evidence:** New tests committed but not executed; no CI workflow/status observed at prior branch head; no native MP4 evidence.
**Limitations:** Need test suite execution, Android performance profiling before enabling orchestration, and real song native XSQ/FSEQ verification. No APK/EXE rebuilt.
**Risk:** Callers of v2 config that assumed True must now explicitly opt in; aligns with effective pre-change renderer behavior.

### 2026-11-17 — Machine-readable handoff reconciliation
**Goal:** Correct stale task states and next commands in `evidence/beta_completion/latest_status.json` following launcher and promotion audit.
**Changed files:** `evidence/beta_completion/latest_status.json`, `MASTER_TODO.md`.
**Preserved:** All production sequencing, effect targeting/timing, drummer ground truth, and release gate.
**New behavior:** HBC-005 marked IN PROGRESS (inspection only), HBC-001 updated with concrete pytest/native verification steps, CI unknown explicitly recorded, and next command now targeted pytest rather than merely switching branches.
**Tests/evidence:** Source inspected; no runnable checkout available in this session and no workflow/status reported for inspected head; tests not run.
**Limitations:** Android and Windows parity, real native outputs, full nine-panel preview remain unverified.
**Regression risks:** None to runtime; documentation-only change.

### 2026-11-17 — Focused CI enabled on integration branch and ground-truth source discovery
**Goal:** Exercise the untested orchestration-routing fixes and inventory owner reference footage/real audio without copying private media into GitHub.
**Changed files:** `.github/workflows/helix-unified-beta-integration.yml`, `evidence/beta_completion/latest_status.json`, `docs/BETA_COMPLETION_LIVE_HANDOFF.md`, `MASTER_TODO.md`.
**Preserved behavior:** Original/approved drummer; three-tom owner requirement pending reconciliation; original audio stays in Google Drive; production engine, rendering, release and merging untouched.
**New behavior:** Branch-scoped Python 3.11/3.12 targeted CI (GitHub run 44213308493) exercises tests for config, orchestration argument routing, bridge, activation audit and native XSQ reconciliation. Source IDs recorded read-only: `Truths` drummer references `Aaadrummertruth.mp4` and `Aaadrummergroundtruth.mp4`; independent vocal references `Bbb Vocalstruth.mp4`, `Bbb vocals.mp4`; lyrics music `Tinsel Tornado.mp3`, `Phoneme Test Hook.mp3`.
**Tests/evidence:** Workflow triggered and in progress when checked; no passed outcome yet. Drive file names/IDs and sizes confirmed through authenticated discovery; contents NOT inspected and approvals NOT inferred from filenames.
**Limitations/deferred:** Review actual reference video frames, run real-audio engine, native XSQ/FSEQ, nine-panel MP4, Windows and Android APK. Avoid reporting CI pass until job conclusion observed.
**Regression risks:** CI installs dev dependencies and may be resource/time-heavy on hosted runners; no production code change.

### 2026-11-17 — Android generated variant selection and export
**Goal:** Address Android results page exposing only one generated sequence despite requesting up to eight variants.
**Changed files:** `android/app/src/main/python/helix_mobile.py`, `android/app/src/main/java/org/helixsequencer/android/EngineService.java`, `android/app/src/main/java/org/helixsequencer/android/MainActivity.java`, handoff documents.
**Preserved:** Existing selected sequence fallback, original show ZIP, preview path, LOR LMS output, native engine flags and memory constraints; no drummer or vocal changes.
**New behavior:** Python returns `sequence_paths` with each valid generated XSQ, service forwards paths and count, Android results page displays a selection spinner and exports selected sequence; LOR mode continues to expose its selected LMS.
**Tests/evidence:** Source edits committed; no Android Gradle build or device instrumentation test run. Focused Python CI run 44213308493 showed 3.11 regression step success, 3.12 pending at last check; this CI does not compile Android Java.
**Limitations/deferred:** Verify UI lifecycle, 8-variant naming/count, actual 8 playback and MP4 per variant. Existing preview still renders one selected sequence; new UI is sequence export selection, NOT all-eight MP4 playback. Android orchestration still disabled.
**Regression risks:** Recreating spinner adapter during status polling can reset transient selection; test on device. Large number of variant files may strain phone storage.

### 2026-11-17 — Android variant picker stability and compile gate
**Goal:** Prevent the results screen from discarding a user's selected sequence on repeated state polls, and establish Android Java compilation evidence.
**Changed files:** `android/app/src/main/java/org/helixsequencer/android/MainActivity.java`, `.github/workflows/helix-android-variant-compile.yml`, `MASTER_TODO.md`, `docs/BETA_COMPLETION_LIVE_HANDOFF.md`, `evidence/beta_completion/latest_status.json`.
**Preserved behavior:** Engine sequence defaults, existing LOR fallback, show ZIP, one preview, eight-variant export contract, drummer and singer code.
**New behavior:** Picker now remembers the selected path and only replaces its adapter when available paths change; new branch-scoped Android Java compile workflow targets debug source compilation using Java 17, Python 3.10, Gradle 8.11.1 and SDK 36.
**Tests/evidence:** Python focused integration run 44213308493 fully PASSED on 3.11 and 3.12. Android compile workflow file committed but no run observed immediately after commit; Android compilation and device behavior still UNVERIFIED.
**Limitations/deferred:** Eight distinct playable MP4s not implemented, and user selection persistence across process recreation not verified; existing Android simulated preview is not native xLights.
**Regression risks:** Android build dependencies/Chaquopy and SDK may fail on hosted runner; picker adapter uses absolute paths as display labels; selection should be checked under service polling and activity recreation.

### 2026-11-17 — Android compile runner setup repair
**Goal:** Unblock Android Java compilation to verify variant picker after first hosted CI failed before Gradle.
**Changed files:** `.github/workflows/helix-android-variant-compile.yml`, `MASTER_TODO.md`, `docs/BETA_COMPLETION_LIVE_HANDOFF.md`.
**Preserved:** No production Android, Python, audio, drummer, UI, or renderer changes.
**New behavior:** Use hosted runner's Android SDK directly instead of `android-actions/setup-android@v3`, which attempted to install unavailable legacy SDK `tools` package.
**Tests/evidence:** GitHub run 44214052900 FAILED at setup-android; logs say `Warning: Failed to find package 'tools'`. Gradle and Java compilation were skipped. Updated workflow committed and new run pending.
**Limitations/deferred:** Gradle dependencies/Chaquopy might still fail; APK and device behavior unverified.
**Regression risks:** Hosted runner SDK manager environment may vary; license handling should be reviewed if installation fails.

### 2026-11-17 — Android compile retry 2 SDK manager path
**Goal:** Resolve CI infrastructure failures before asserting Android compilation.
**Changed files:** `.github/workflows/helix-android-variant-compile.yml`, `MASTER_TODO.md`, `docs/BETA_COMPLETION_LIVE_HANDOFF.md`.
**Preserved:** Android production code and all sequencing behavior.
**New behavior:** Locate `sdkmanager` inside `ANDROID_HOME/cmdline-tools` rather than assuming it is on PATH; provide explicit error if missing.
**Tests/evidence:** Run 44214269832 failed at `sdkmanager: command not found`; Gradle never executed. Earlier Python 3.11/3.12 regression run 44213308493 passed.
**Limitations/deferred:** Await CI retry; no Android compile or native playback evidence.
**Regression risks:** Runner SDK path may differ; if command-line tools absent, provision explicitly.

### 2026-11-17 — Android compilation passed; full APK assembly gate added
**Goal:** Advance Android verification beyond source compilation without prematurely releasing an APK.
**Changed files:** `.github/workflows/helix-android-variant-compile.yml`, `MASTER_TODO.md`, `docs/BETA_COMPLETION_LIVE_HANDOFF.md`, `evidence/beta_completion/latest_status.json`.
**Preserved behavior:** No runtime code change; no merge, release, artifact publication or production signing.
**New behavior:** Existing branch-scoped CI compiles Java and additionally executes `gradle :app:assembleDebug` to check full debug APK packaging.
**Tests/evidence:** Android CI run 44214343888 fully PASSED including Java compilation. Python 3.11/3.12 regression run 44213308493 fully PASSED. New APK assembly step committed but its result not yet known.
**Limitations/deferred:** APK installation, band preview, per-variant MP4 playback, xLights native validation and Windows EXE parity still pending.
**Regression risks:** APK assembly may expose Chaquopy or packaging issues not encountered in compile-only job.

### 2026-11-17 — Android variant selection across activity recreation
**Goal:** Preserve selected generated XSQ through Android configuration/activity recreation.
**Changed files:** `android/app/src/main/java/org/helixsequencer/android/MainActivity.java`, `MASTER_TODO.md`, `docs/BETA_COMPLETION_LIVE_HANDOFF.md`.
**Preserved behavior:** No sequencing or drummer changes; selection remains job-local and falls back to available variants.
**New behavior:** `selectedSequencePath` saved in `onSaveInstanceState` and restored before results polling, complementing existing polling-stable adapter.
**Tests/evidence:** Java compile previously passed on run 44214343888; this new change requires a fresh compile. Full debug APK assembly run 44217648117 was in progress at last inspection, with no result.
**Limitations/deferred:** Device rotation/process-death testing, 8 MP4 playback, native xLights verification, Windows parity.
**Regression risks:** Selected path may be stale if files are deleted; existing polling logic rejects unavailable paths.

### 2026-11-17 — Clean Android Gradle Chaquopy plugin resolution
**Goal:** Unblock APK assembly on a clean hosted runner.
**Changed files:** `android/settings.gradle`, `MASTER_TODO.md`, `docs/BETA_COMPLETION_LIVE_HANDOFF.md`.
**Preserved:** Android app source, Python sequencing, drummer, release signing, existing plugin versions.
**New behavior:** Gradle plugin management includes Chaquopy's Maven repository `https://chaquo.com/maven` ahead of Google/Maven Central/Plugin Portal.
**Tests/evidence:** CI run 44217769589 failed before Java compilation: Gradle could not resolve `com.chaquo.python:17.0.0` from configured repositories. Earlier run 44217648117 was cancelled by branch concurrency. Previous run 44214343888 passed Java compilation (cached or previously resolved dependencies); clean runner exposed missing repository. New run pending.
**Limitations/deferred:** Need confirm new Gradle resolution and full debug APK assembly; no on-device runtime, native xLights, or eight MP4 previews yet.
**Regression risks:** External Chaquopy Maven availability; repository trust/availability and version compatibility must be verified by CI.

### 2026-11-17 — Verified debug APK packaging and payload integrity gate
**Goal:** Establish reproducible debug APK assembly and check archive integrity before device testing.
**Changed files:** `.github/workflows/helix-android-variant-compile.yml`, `MASTER_TODO.md`, `docs/BETA_COMPLETION_LIVE_HANDOFF.md`, `evidence/beta_completion/latest_status.json`.
**Preserved behavior:** Existing app, signing, user data, runtime logic, native outputs; no release, Drive upload, or GitHub artifact publication.
**New behavior:** CI now verifies APK exists, ZIP CRC integrity, manifest, DEX and assets, and prints SHA-256 for traceability.
**Tests/evidence:** Run 44217948986 completed SUCCESS for Java compile and `gradle :app:assembleDebug`. New APK payload checks are committed but awaiting execution.
**Limitations/deferred:** Successful assembly does not prove installability on target device, correct six-snowman preview, independent vocal animation, eight MP4 variants, or Windows parity.
**Regression risks:** Asset layout/packaging changes may require updating the simple ZIP structure checks.

### 2026-11-17 — Android variant spinner listener lifecycle repair
**Goal:** Avoid repeated listener registration on every one-second poll and make selected variant restoration deterministic.
**Changed files:** `android/app/src/main/java/org/helixsequencer/android/MainActivity.java`, `MASTER_TODO.md`, `docs/BETA_COMPLETION_LIVE_HANDOFF.md`.
**Preserved:** XSQ generation, preview renderer, approved drummer, export format and layout choices.
**New behavior:** Spinner listener registered once at UI creation, rather than every poll. When choices change, restored selection is explicitly synchronized with `selectedSequencePath` after `setSelection`.
**Tests/evidence:** Previous APK CI run 44218445981 PASSED compile, assemble and ZIP integrity checks. This new change needs a fresh CI run and on-device rotation/poll testing.
**Limitations/deferred:** MP4 still represents only the primary variant; all-eight preview/export is not implemented.
**Regression risks:** Android spinner callback timing and rotation lifecycle require device testing.

### 2026-11-17 — Per-variant Android MP4 generation and selection wiring
**Goal:** Allow users to play/export the MP4 corresponding to each of up to eight generated XSQ variants rather than always playing the first preview.
**Changed files:** `android/app/src/main/python/helix_mobile.py`, `android/app/src/main/java/org/helixsequencer/android/EngineService.java`, `android/app/src/main/java/org/helixsequencer/android/MainActivity.java`, ledger and handoff.
**Preserved:** Existing Helix sequence generation, XSQ/LMS export, 640x360/15fps bounded Android preview renderer, audio synchronization, canonical drummer logic, no merge/release.
**New behavior:** Sequentially render each variant's preview, record index-aligned `preview_paths` (empty string for failed variants), checkpoint progress; service publishes paths; results selector maps play/save MP4 to selected XSQ and disables unavailable movies. Per-variant failures do not discard successful sequence outputs.
**Tests/evidence:** Previous APK compile/assembly/integrity run 44218445981 passed; new code awaits CI and on-device multi-variant audio/geometry validation.
**Limitations/deferred:** Eight sequential MP4s may take substantial time/storage; no native xLights render on Android; preview still simulated and may be visually incorrect; no device validation; Windows parity pending.
**Regression risks:** Memory/time/space pressure, encoder reuse, failed variant alignment, activity lifecycle. Require measured Android testing before beta approval.

### 2026-11-17 — Android Python preview entrypoint syntax gate
**Goal:** Catch Python syntax errors in the newly added per-variant MP4 loop before costly Gradle/Chaquopy assembly.
**Changed files:** `.github/workflows/helix-android-variant-compile.yml`, `MASTER_TODO.md`, `docs/BETA_COMPLETION_LIVE_HANDOFF.md`, `evidence/beta_completion/latest_status.json`.
**Preserved:** Runtime sequencing, preview semantics, Android UI, no merge/release.
**New behavior:** CI invokes `python -m py_compile` on `helix_mobile.py` and `helix_mp4.py` before Java/Gradle steps.
**Tests/evidence:** Run 44219712984 was still running at inspection (Java compilation not complete). Previous APK run 44218445981 passed, but predates per-variant MP4 implementation. New syntax gate needs fresh CI.
**Limitations/deferred:** Syntax gate does not verify preview correctness, performance, on-device encoder behavior, native xLights, Windows parity.
**Regression risks:** None expected from CI-only change; Python files are checked with host Python 3.10.

### 2026-11-17 — Distinguish partial from complete Android multi-variant preview
**Goal:** Prevent falsely reporting success when only some requested MP4 variants render.
**Changed files:** `android/app/src/main/python/helix_mobile.py`, `MASTER_TODO.md`, `docs/BETA_COMPLETION_LIVE_HANDOFF.md`, `evidence/beta_completion/latest_status.json`.
**Preserved behavior:** Per-variant sequential render, output paths, failure isolation, sequence/ZIP export, audio and canonical drummer logic.
**New behavior:** Preview stage status is `success` only when all requested variants render, `partial` for a subset, and `failed` for none; includes `rendered`, `requested` and failed variant filenames, then checkpoints state.
**Tests/evidence:** Run 44219873839 PASSED Python syntax, Java compilation, debug APK assembly and integrity for prior per-variant code. New partial-status change awaits CI.
**Limitations/deferred:** Actual device playback, preview geometry and eight-variant timing/storage remain unverified.
**Regression risks:** Consumers of stage status should handle `partial` distinctly; UI currently prints status text.

### 2026-11-17 — Surface per-variant MP4 failures in Android results
**Goal:** Make partial rendering visible rather than silently implying all eight MP4s are available.
**Changed files:** `android/app/src/main/java/org/helixsequencer/android/MainActivity.java`, `MASTER_TODO.md`, `docs/BETA_COMPLETION_LIVE_HANDOFF.md`, `evidence/beta_completion/latest_status.json`.
**Preserved behavior:** Preview encoding, audio sync, existing per-variant picker and exports, canonical drummer, no merge/release.
**New behavior:** Results summary displays `rendered/requested MP4s` and names of failed variants when supplied by the preview stage.
**Tests/evidence:** Python syntax gate passed in still-running CI 44246646940; new Java UI change awaits compile/assemble CI.
**Limitations/deferred:** On-device verification of all-eight playback and native snowman geometry still required.
**Regression risks:** Android JSON stage parsing and UI formatting must be validated in CI/device.

### 2026-11-17 — Bound Android MP4 render count
**Goal:** Avoid unexpectedly encoding more than the requested maximum eight videos when the sequencer emits auxiliary XSQs.
**Changed files:** `android/app/src/main/python/helix_mobile.py`, `MASTER_TODO.md`, `docs/BETA_COMPLETION_LIVE_HANDOFF.md`, `evidence/beta_completion/latest_status.json`.
**Preserved behavior:** XSQ generation/export, serial MediaCodec rendering, sequence/preview index mapping, stage reporting, canonical drummer and audio synchronization.
**New behavior:** Preview loop encodes at most `min(requested variants, 8)` sequences; extra XSQs remain exportable; reports requested count for encoded candidates.
**Tests/evidence:** Previous per-variant APK CI `44219873839` passed; latest UI run `44246752957` was still in progress at inspection. New cap requires fresh CI/device validation.
**Limitations/deferred:** Auxiliary XSQ ordering may require explicit canonical variant identification; no on-device performance data; 8 preview files may still be large; no native xLights validation.
**Regression risks:** When engine emits auxiliary XSQs before canonical variants, cap may omit desired preview; inspect actual eight-variant manifest and adjust deterministically.

### 2026-11-17 — Primary-first bounded preview and stable XSQ mapping
**Goal:** Fix risk that a capped Android preview list omits the primary sequence or associates MP4s with the wrong spinner item.
**Changed files:** `android/app/src/main/python/helix_mobile.py`, `MASTER_TODO.md`, `docs/BETA_COMPLETION_LIVE_HANDOFF.md`, `evidence/beta_completion/latest_status.json`.
**Preserved:** Eight-video maximum, sequential bounded rendering, original XSQ output ordering and exports, audio alignment, drummer logic.
**New behavior:** Primary XSQ is rendered first; remaining XSQs fill requested slots; `preview_paths` always maps to original `sequence_paths` indices; skipped/failed entries are empty; stage failures list only attempted variants.
**Tests/evidence:** Previous per-variant CI `44219873839` passed; run `44246963986` was in progress before this commit and may be cancelled by CI concurrency. Fresh syntax/Java/APK CI pending.
**Limitations/deferred:** Engine may emit auxiliary XSQs before desired alternate variants; canonical identification beyond primary needs inspection. Android device acceptance, MP4 decode/audio sync, native xLights, Windows parity still pending.
**Regression risks:** Need actual eight-variant run to verify preview selection and variant identity.

### 2026-11-18 — Android build PASS and acceptance artifact retention
Goal: make verified debug APK accessible for device testing. Changed: Android compile workflow, ledger, handoff, status JSON. Preserved: existing compile/integrity gates, no release or merge. New: seven-day CI artifact retention after integrity checks. Evidence: run 44247185516 passed all gates but retained zero artifacts; commit 45955934 adds retention. Pending fresh CI, download and device tests. Risk: repository artifact access follows GitHub permissions; not a public release or signed production build.

### 2026-11-18 — Verified debug APK retained
Run 44256203127 PASS; artifact 14406022516 (95,917,573 bytes ZIP), expires 2026-11-25. Download: https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/44256203127/artifacts/14406022516 . Build and retention verified, no source behavior modified in this checkpoint. Device playback/export, memory, synchronization and band geometry remain unverified; no release or merge. Debug APK may require uninstalling an incompatible prior signature (preserve user data first).

### 2026-11-18 — Owner layout acceptance failure
Owner device test FAIL: pressing layout closes/minimizes app. Fixes c0727ebc/0504fd5d guard picker launch, resolve default by catalog key, clamp saved index, offer reset to built-in layout; 01dfd21a selects allmodels as interim diverse-prop default, not verified exact panel 6. User requests original Helix Lights Out theme bundled by default; source audio not yet located/packaged. Preserve custom imports and sequencing. CI and device retest pending; root cause not confirmed without logcat. Risks: stale URI, picker activity lifecycle, exact panel identity, audio availability/licensing. No release.

### 2026-11-18 — GUI integration reconciliation
Recovered original PR #233 SequencingLightShowView (19cf22be) and wired into current MainActivity (c7483b68), preserving picker repairs, variant mapping and support navigation. Arches during processing, tree during preview, measured progress only when available; decorative not sequence output. CI/device tests pending. PR #231 variant review and Windows parity still require reconciliation, not wholesale overwrite. Owner requires exact nine showcase layouts bundled on both platforms, #6 default, original LightsOutTheme.mp3 default, thumbnails/descriptions, custom import/reset and eight independently playable/exportable variants. Current tree has no LightsOutTheme.mp3 and no exact nine-panel catalog; older smoke script references that filename. Do not substitute another song or claim nine layouts complete. Locate original assets/branches, validate native layout paths and stage packaging. No merge/release. Risks: lifecycle and runtime UI, missing assets, regressions from overlapping PRs.

### 2026-11-18 — Windows GUI recovery
Recovered gui_lightshow.py from PR #233 (96c0425e) and applied all original gui_launcher.py patch hunks without conflict (f70f7cf8). Preserves sequencing command and existing GUI options; adds dark styling, combined/arches/tree animation, main-thread event queue, instructions and donation navigation. No Windows runtime or frozen packaging validation yet; portable entrypoint and variant-review PR #231 reconciliation pending. Risk: frozen imports/assets and competing GUI paths. Exact nine native layouts and original theme still pending. No release or merge.

### 2026-11-18 — Restore eight actual variants
Shared runtime generator had signature plus four presets; recovered three missing PR #231 presets (00808471) for eight distinct configurations. Existing five preserved. Restored stable-order regression test f1ce9cde and review composer/test 6a4e8f72/c498e689 (serial and grid playback). Composer not yet GUI-wired. Android workflow now rebuilds on variant definitions/catalog changes. Tests and runtime verification pending. No native render or release claimed. Risk: preset fields and downstream shortlist/output identity must be tested; Windows launcher differs substantially from PR #231, needs manual reconciliation. Nine layouts/theme pending.

### 2026-11-18 — Windows variant review UI reconciliation
Commit fca79337 adapts PR #231 review dialog to existing animated launcher queue; preserves run arguments and progress, adds play/previous/next/save individual/save all/serial/grid UI, tracks only current-run preview messages. Android CI 44262496257 PASS, artifact 14409181434 at head f460dcbf. Windows preview generation/log contract, frozen packaging and runtime still unverified; review UI alone does not establish playable files. Exact nine layouts/theme remain pending. No release or merge. Regression risks: alternate CLI path and preview provenance, file paths and frozen runtime.

### 2026-11-18 — Nine-layout provenance and shared catalog
Located original nine-panel branch 93780f30; tools/layout_bench/nine_panel_pilot.py explicitly labels eight fixtures provisional. Locked owner-updated nine requirements in config/showcase_layout_requirements.json (06ea0b60), candidate paths are not approved or guaranteed present. Panel 4 includes both vocal prop types, panel 6 native model collection is default. Windows launcher now resolves existing shared Android catalog and default (07e3cab5); missing files omitted rather than offered as broken choices. Custom remains. Exact nine assets, catalog packaging, thumbnails, default song and runtime checks still outstanding. Do not imply nine finished layouts. Risks: frozen catalog path and default fallback. No merge/release.

### 2026-11-18 — Requested preview count honesty
98d5b9ca fixes Android preview status to compare rendered count against original bounded requested count, records attempted and missing_candidates. Preserves existing rendering and path mapping. Runtime test pending; auxiliary XSQ identity still needs validation. Drive search for Lights Out/LightsOut returned no matching files; Songs with Lyrics folder query returned no entries, not proof of absence. Original theme still unresolved; do not substitute. No merge/release.

### 2026-11-18 — Recover first showcase preset
Recovered exact AC16 fixture XML from nine-panel branch (7fd2bab7), added shared active catalog entry (ea27907c), labeled interim All Models default honestly. Existing sample imports retained. Android staging now fails for missing advertised layout files instead of silently packaging broken catalog. Runtime/native validation pending; remaining eight final layouts and theme incomplete. No merge or release.
