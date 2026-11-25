## November 25 · Native physical row buffers for advanced phrase surfaces

**Goal:** Correct flattened native render buffers on genuine rectangular matrix/lattice surfaces, so native effects travel through physical columns rather than serialized node order.
**Files:** `tools/build_helpers/ultimate_showcase.py`, `tools/source_spatial_direction.py`, `tools/build_approval_collection.py`, `tests/test_source_spatial_direction.py`, `MASTER_TODO.md`.
**Preserved:** All channel addresses, node membership, existing note submodels, authored song/source clocks, band and AC geometry, ordinary submodel XML and native effect settings.
**Change:** Production phrase export marks SPATIAL_SURFACE for physical-row rendering. The shared native XML serializer uses one line per actual row, sorts rows by physical Y and nodes by physical X, and only applies the new shape when all rows are rectangular, disjoint, and cover the exact original node set. Irregular surfaces retain the prior representation. Layout and exported custom model files use the same serializer; provenance hashes now cover it. The xLights manual documents node-range rows as buffer dimensions.
**Evidence:** Regression checks a real moire layout's 240-node rows, exact channel membership, physical order, unchanged ordinary row submodel, fallback for incomplete coverage, and native Bars emission. Source committed; CI/native visual performance pending.
**Limitations/risk:** A rectangular buffer improves geometry semantics, not a proven reduction in total buffer cells or wall time. Native xLights may apply layer ordering and row orientation differently; verify actual FSEQ and visual review before expansion to other effects or arbitrary 3-D layouts. No merge/release/approval. Next: verify native effect settings and buffer sizes under a short real-source pilot.

## November 25 · Section-aware native surface effect variation

**Goal:** Give advanced surfaces different motion across actual musical sections without inventing notes or introducing a second choreography engine.
**Files:** `tools/source_spatial_direction.py`, `tests/test_source_spatial_direction.py`, `MASTER_TODO.md`.
**Preserved:** Retained source note times, phrase merging and rests, section-derived colors, native On note lanes, existing Bars cycles/palettes, simple surface direction, AC and band routing.
**Change:** Advanced optical/depth/cathedral/helix/matrix/spatial surfaces now select native Bars H-expand/H-compress for builds, Alternate Left/Right for choruses, and existing Left/Right for ordinary phrases. Native settings and direction provenance are emitted directly through the production XSQ writer, not a sidecar. Direction choices are documented in the xLights Bars effect manual/wiki; the newer 2026.19 custom-angle option is not used.
**Evidence:** Added regression for both spatial directions, section-specific native EffectDB references, and breakdown/rest preservation. Source implemented; native 2026.18 visual behavior, buffer geometry, CI and actual speed are not yet verified.
**Risk/deferred:** Native custom-model buffers may project geometry differently; inspect real FSEQ/MP4 before widening effect families or changing buffer dimensions. No fabricated native pass, release or merge. Continue with native effect fixtures and Wub Wub Wonderland source-qualified pilot.

## November 25 · Reuse source clocks in the production native collection

**Goal:** Eliminate repeated source-event indexing and geometry serialization on actual 12-layout native export path.
**Files:** `tools/source_spatial_direction.py`, `tools/build_approval_collection.py`, `tests/test_source_spatial_direction.py`, `MASTER_TODO.md`.
**Preserved:** Existing musical role routing, note/section order, source-event IDs, independent estimated singer clocks and abstention, authored native surface effects, canonical band, AC wiring and final layout/submodel serialization.
**New behavior:** Prepare each source role's onset index and vocal windows once per collection, pass them through the production exporter, and retain lane-local standalone behavior. Write the layout, assets, geometry and model inventory once after submodels are authored. Export provenance includes the routing implementation, native writer and effect table serializer.
**Evidence:** New regression compares shared versus original lane-local schedules, tests independent voice onset clocks, rejects per-prop reindexing and checks native effect provenance. Committed to PR #255; runtime and full native render pending.
**Limitations/deferred:** Not a measured speedup. Need verify all 9/12/16 production paths use shared analysis or equivalent, and review native effect/layer/buffer fixtures before introducing more effect types. No owner approval.
**Risk:** Consumers relying on partial pre-export layout files after a failed build may no longer find them. Final layout is still written before vocal export; verify final manifest/model parity. No release/merge.

## November 25 · Native xLights workflow and spatial propagation optimization

**Goal:** Improve actual native approval pipeline throughput and keep short musical events visible in large advanced prop banks.
**Changed files:** `tools/source_role_routing.py`, `tools/fseq_pixel_preview.py`, `.github/workflows/helix-infinity-layout.yml`, `tests/test_source_spatial_direction.py`, `tests/test_fseq_pixel_preview.py`, `MASTER_TODO.md`.
**Preserved:** Existing source-bound choreography, selection widths, pitch mapping, AC route timing/wiring, band and vocal logic, native FSEQ authority, original Bells source checksum, disabled controller output, media duration/decode gates, visible and internal provenance.
**New behavior:** Advanced bank inter-prop delays scale down for short measured notes; the existing 35 ms maximum and source timestamps remain. Native FSEQ preview resolves RGB wire order once per node and optionally encodes directly at 30 fps; the bounded Infinity workflow uses the option and removes its second video encode. Cache the original pinned AppImage across eligible runs and verify SHA-256 before extraction, redownloading if invalid. PR-triggered focused regression tests do not run the costly full-song render.
**Evidence:** Two focused regressions authored (short 100-prop bank, exact 20-to-30 fps source clock). Source committed on isolated candidate branch; CI, local xLights execution, measured runtime/memory improvements and owner visual approval pending.
**Deferred:** Verify native renderer installation and effect settings; trace and widen production native mappings only with real xLights fixtures, profile model-group buffers, audit production palette/layer order and existing choreographer participation, generate short vocal-qualified comparison then full 9/12/16 and Infinity approval candidates. This is not a full 10,240-prop proof.
**Risk:** Compressed bank timing may look too simultaneous at native frame resolution; test with short and sustained notes on real spatial layouts. Direct output must retain audio synchronization, color, and readable geometry. No merge/release/owner approval claimed.

## November 24 · Restore bounded vivid accent palette

**Goal:** Repair the sole full-suite failure on 11bc211 without restoring white-only flashing. **Files:** core/vivid_style.py, MASTER_TODO.md. **Preserved:** section palettes, accent cadence, AC wiring and existing acceptance tests. **Change:** existing occasional AC accent now references the mixed white/magenta/cyan palette instead of a single ordinary section color. **Evidence:** run 45063651475 reported 2781 passed, 1 failed, 6 skipped on Python 3.12; existing white-accent regression remains unchanged. Fresh CI pending. **Risk:** native visual balance still requires review; no approval or release claimed. Panel pilot timing/reference gate remains unresolved.

## November 22 · Physical inter-prop choreography for advanced customer layouts

**Goal:** Replace global source-cue broadcast between advanced props with coordinated, physical-position-based source note travel while keeping Helix's existing semantic role and section logic.
**Changed files:** `tools/source_role_routing.py`, `tools/build_approval_collection.py`, `tests/test_source_spatial_direction.py`, `MASTER_TODO.md`.
**Preserved:** All native song-analysis events, original source timing, canonical band and singers, 16/64/256 AC wiring, source role ownership, existing per-prop geometry paths, simple house layouts, all native rendering and approval gates.
**New behavior:** Before native layout export, advanced depth, cathedral, optical, spiral, helix, DNA, matrix and grove pixel props are grouped by actual musical role and ordered along the dominant physical axis of their centers. Helix's existing `route_event` now selects a subset of spatially ordered props for a measured note/phrase rather than broadcasting that cue to every eligible prop. Builds and choruses retain their source-bound strategies. No invented source notes or new effect engine.
**Tests/evidence:** Added regression for unique physical ranks, selective inter-prop routing, insertion-order independence, and AC/starter exclusion. Source authored; CI and fresh native video verification pending.
**Limitations/deferred:** The full customer realism/artistic variety bar is not met by a unit test. Need review of 9/12/16 native MP4s for recognizable homes, independently acting spatial groups, dramatic changes in sections, absence of global pulse, and canonical band behavior. Release/merge remains blocked.
**Regression risks:** An advanced musical role with many props may become too sparse. Validate visible density and route balance in native MP4; adjust the existing bank strategy if needed, not by reintroducing global broadcast.

## November 22 · Owner rejects global-pulse customer layouts; first geometry-path repair

**Goal:** Make advanced native customer layouts spatially active, not whole-prop beat flashes, using the existing source-bound choreography and native xLights exporter.
**Changed files:** `tools/source_spatial_direction.py`, `tests/test_approval_collection.py`, `MASTER_TODO.md`.
**Preserved:** All actual source cue clocks, silence, role routing, section strategies, native XSQ/FSEQ export, AC16/64/256 channel budgets, explicit native strands/rows/rays/sectors, vocal/band handling, owner approval gates, and existing simple customer house behavior.
**New behavior:** When an advanced 3-D/cathedral/depth/optical/matrix/helix pixel model has no authored spatial segmentation, split its real physical coordinates into up to 12 principal-axis spatial submodels. The existing source-timed phrase choreography now travels through real physical locations instead of turning on the entire prop. It does not invent notes, fake geometry rotation, or add generic beat flashes. The path axis is deterministic and insertion-order independent.
**Tests/evidence:** New focused geometry-order, segment coverage, AC preservation, and starter-house regression authored. CI and new native xLights video still pending; no artistic acceptance claimed.
**Limitations/deferred:** A path within one prop is only the first repair. Customer setup realism, coordinated inter-prop spatial choreography, high-level engine selection, musical counterpoint, varied section choreography, 3D lighting motion, all 9/12/16 panel re-renders, native proof and owner approval remain mandatory. Existing generic source-cue density may still cause pulsing; must inspect the new MP4 and reject if so.
**Regression risks:** Advanced pixel submodel count increases, so memory, xLights model XML and effect tables must be checked on fresh render. No merge or release.

## November 22 · Start full 12-panel production when final presentation is repaired

**Goal:** Allow the corrected final 4x3 layout and required caption logic to be exercised by the real production workflow, rather than leaving the fix unrendered.
**Changed files:** `.github/workflows/final-approval-collection.yml`, `MASTER_TODO.md`.
**Preserved:** Existing workflow job steps, source checksums, pinned native xLights, all visual/readability gates, retained source material, fail-closed rejection, branch isolation, and no auto-merge/release.
**New behavior:** Integration-branch changes to `tools/finish_approval_presentation.py` or its grid regression test now trigger the final native twelve-layout workflow on push. The previous trigger only watched the renderer and layout builder despite failures in the final presentation module; editing this workflow itself also initiates an immediate run.
**Tests/evidence:** Earlier run 45008501418 reached final presentation and failed on the 3x4-vs-4x3 mismatch; commits e4486e5 and ddd5a57 corrected the grid and explicit panel labels. Fresh workflow run and video verification remain pending. No claim of a passed run or owner approval.
**Limitations/deferred:** The 12-panel source is a 34.88-second pilot; no full-song release approval. Any remaining artistic/motion failures must be corrected rather than hidden.
**Regression risks:** A future push touching final presentation/tests now starts an expensive native workflow; concurrency settings continue to cancel superseded same-branch runs.

## November 22 · Follow-up on 12-panel final presentation

**Goal:** Ensure the corrected 4x3 final 12-panel comparison passes both existing strict compositor input contracts.
**Changed files:** `tools/finish_approval_presentation.py`, `tests/test_approval_collection.py`, `MASTER_TODO.md`.
**Preserved:** The renderer's strict explicit-label validation for twelve layouts, unlabeled six/nine/three-panel companion behavior, genuine xLights source visuals and audio, all acceptance thresholds, and owner-review gate.
**New behavior:** Final presentation now passes twelve distinct, human-readable layout captions from the actual individual MP4 filenames. The 4x3 fix alone would otherwise have failed with `Twelve-layout comparison requires explicit panel labels`.
**Tests/evidence:** Added focused regression checking the twelve labels are present and unique, and companions retain their previous unlabeled behavior. Latest source correction awaits CI; not yet proven by a new 12-panel MP4.
**Limitations/deferred:** Re-render the final 12-layout workflow against this source, verify MP4 receipt, resolve any artistic/readability issues, and obtain owner visual approval before release.
**Regression risks:** Changed only metadata labels on final comparison; no change to native XSQ/FSEQ, pixel choreography, audio, or framing.

## November 22 · Real MP4 delivery and final comparison grid repair

**Goal:** Deliver real, viewable approval candidates and repair the twelve-layout final presentation failure without weakening source, geometry, audio, or readability gates.
**Changed files:** `tools/finish_approval_presentation.py`, `tests/test_approval_collection.py`, `MASTER_TODO.md`, `evidence/beta_completion/latest_status.json`.
**Preserved:** Exact original audio, native xLights-generated footage, source hash checking, 12-panel 4-by-3 strict contract, six-panel 3-by-2 companion, nine-panel 3-by-3 collection, all visual acceptance thresholds, six-snowman instrumentation and no automatic owner approval.
**New behavior:** Final presentation now requests the correct 4-column/3-row grid for its 12-layout comparison, rather than the erroneous 3-column/4-row grid. A shared selector fail-closes on any unsupported layout count instead of raising an incidental KeyError. Regression verifies all companion grid dimensions.
**Evidence:** Native Helix Motion 16-panel job [45008501454](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/45008501454) succeeded at pre-fix source `f0e882fa8c47e9aa787d274171422170e58697f0` with [artifact 14755720611](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/45008501454/artifacts/14755720611). Its original-audio full-length H.264/AAC movie is 264.8 s, 1920x1080 at 30 fps; sampled quality receipts recorded zero blank and zero white-dominant frames. **Actual MP4 delivered to Drive:** https://drive.google.com/file/d/1CQHC_5XVRi02nQlmtBjE6QovVzYzktPz/view. Sixteen labeled per-panel audio-attached crops are in https://drive.google.com/drive/folders/1MM54iPDmyMNsD5Ajl-ClbE1MNpDP9LtD (480x270 each; derived from the composite, not separate native renders). Existing genuine nine- and twelve-layout short review MP4s are at https://drive.google.com/file/d/1CmEpUUCG2ckNGs626-oF3VnNCTzNxW_R/view and https://drive.google.com/file/d/1OvKatynrNzbLLTu0-pquFOKdiRH_W8D5/view; their individual panel MP4 bundles are in the same Drive folder.
**Tests/evidence for patch:** The 12-layout run [45008501418](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/45008501418) completed native individual renders and its first 6/12 layout compositions, then failed with `ValueError: Twelve-layout comparison requires four columns and three rows` while the final presentation mistakenly supplied 3x4. New regression authored; CI on this commit pending.
**Limitations/deferred:** Owner visual approval is pending; 9-panel readability/motion gate failed, and 12-panel full final export must be re-run on the corrected source. A 16-panel sampled pixel-quality pass does not prove artistic variety, accurate lead/harmony stem provenance, independent 3D mesh motion, Android eight-variant playback/API30, Windows EXE, or Infinity full tier. Keep release/merge blocked.
**Regression risks:** Final grid selection for nine and twelve layouts; all production outputs must be freshly revalidated. No existing quality threshold removed.

## November 21 · Production audio and native comparison recovery

- Runs 44944727109 and 44944730430 failed in the version probe before separation (torch 2.15.0+cu132, torchaudio 2.11.1+cu132, missing list_audio_backends). Run 44944734212 rejected the E14 mixed vocal bus. No approval MP4 resulted.
- Shared CPU action pins torch/torchaudio 2.5.1+cpu, Demucs 4.0.1, the repository DSP pins and the required Whisper runtime. It verifies the model checksum, separates the real source before the native build, and caches SHA-bound stems. The separator uses one worker, seven-second segments, separate per-attempt logs and an atomic manifest with per-WAV hashes and source-clock validation. Legacy v1 caches regenerate once.
- The 16-panel builder batches missing layouts so they parse one plan and voice clock together. Native mega-tree segments now wind around the cone. Original AC addresses and singer qualification remain in force. Both comparison workflows retain separation failure logs.
- Local Python 3.12: 55 focused regressions passed. Real Phoneme Test Hook: 34.88 seconds, four checked stems; master emitted a source XSQ and band plan. Full-length Helix Motion and native export verification pending. Local files or diagnostics do not imply delivery.
- E14 source archive hash 604107acea8e57e8e5436b6bcbcb6f584806a4bed3a85679f72295d340c37b10, original WAV 8905fcaf105faf5016608517cf2d8a798d1809d8e615f1d4f5bca58e0c0b1171. Manifest has one demucs_mixed_vocals bus and zero independent tracks. No isolated vocal pair identified in Drive music folder listings. Supply aligned original lead and harmony exports for this exact take or a matching master and isolated singers from another take.
- Next: qualify native short pilot against approved reference; verify fresh Actions on this change; render and decode only eligible comparisons. Owner review pending for every production.

## 2026-11-20 · Integrated Android multi-variant preview isolation

- [x] Prevent an unsupported canonical band layout from aborting all other requested preview variants; per-variant preview status remains independently recorded (3bfa5509).
- [x] Add regression for per-variant preview isolation (52da83d7).
- [ ] Run final Android compile/device acceptance on the latest integration SHA; verify eight independent preview playback/export flows.
- [ ] Replace effect-level simulation for canonical six-member band with verified native xLights review output; do not label unsupported previews as approved.

# HELIX MASTER TODO & AGENT HANDOFF LEDGER

## November 20 · Native comparison renderer hardening (implemented, CI unverified)

Commits through b051b04e: strict literal canonical XSQ matching, complete selected-source preflight, duplicate/empty input rejection, isolated 30-fps banner, staged atomic MP4 publication, zero-frame panel rejection, and ffmpeg process cleanup after FSEQ iterator errors. Focused regression coverage is wired into Python 3.11/3.12 CI. This is implementation and test authorship only; do not count tests as passed or review MP4s as accepted until verified. Remaining P0: six-snowman native band, independent vocals, Android eight-variant playback/API30, Windows EXE, native 9/16-panel acceptance, full Infinity 10,240 props, manuals, owner approval. Estimated overall Beta 1.4 completion: ~70% (qualitative, not a verified checklist fraction).


## November 20 · Bounded Infinity native xLights verification (confirmed)

GitHub Actions [44785020701](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/44785020701), source `abc6b2c3a1fc97f2a0710efff52b83ec5434c544`, completed SUCCESS including 7 layout/targeting tests and the full-song xLights FSEQ step. The 155.96-second original Bells of Mathmas source passed its byte hash check; sequencing reported 323/323 editable model rows and zero stale models, plus 30,372 showcase effects and palette dominance 16.4%. Native artifact [14653767707](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/44785020701/artifacts/14653767707) includes XSQ, FSEQ, layout XML, manifest, native xLights log, verification.json. This is bounded-tier native technical proof only: no visual MP4 approval, 10,240-prop full render, band acceptance or public release. Continue by checking verification.json pixel/frame quality, producing a synchronized MP4, and owner-reviewing it before attempting full tier.


## November 20 · Infinity native runner repair

At integration source `e84bcfd1ffd05e78d46d28d6766ada6c4c754ed2`, [run 44711406069](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/44711406069) had produced the bounded-layout Bells XSQ, then xLights exited 127 loading libEGL.so.1. The Infinity workflow now provisions EGL, Mesa and GL on Ubuntu 24.04. Names, channels and authored geometry are preserved. Code implemented. Native rerender, visual verification and owner review pending. Inspect the integration branch's next Helix Infinity run and its verification receipt before using the 10,240-model tier. Full Python suites started in isolated source trees for e84bcfd.


## November 20 · Real-audio inventory, native comparison repair and Infinity geometry

HBC-LIB-PCM VERIFIED. All 91 source entries decoded with original channel layout and sample rate. Every byte hash agrees with the previous Drive inventory. There are 84 distinct source files, 80 distinct PCM recordings and 79 eligible songs after excluding Dry Drum Test.wav. [Per-recording evidence](https://drive.google.com/file/d/1Y86xucK6idATACNrdIeTkDqBpMLdhpdY/view). The historical Helix Motion pilot still needs reconciliation against current visual and band requirements.

HBC-COMP-REUSE VERIFIED for the comparison FSEQ and panel stages. Reuse now requires input and output hashes. A corrupted or legacy receipt forces regeneration. Sparse channel gaps stay dark and the comparator streams rows rather than loading every frame into RAM. The sequencing bench's older basename-only XSQ lookup still requires repair.

HBC-GEO-PERF VERIFIED. The model parser reuses the current segment as pixel positions advance. Twenty 512-point projections took 0.16186 s before and 0.01310 s after (seven-run medians, same output hash). See evidence/beta_completion/path_projection_benchmark.json.

HBC-INF-FRONT IMPLEMENTED — UNVERIFIED visually. The former writer applied world translation twice and used depth for vertical height. The repaired layout places upright props in the default preview; the original model names, pixel counts, channels, family groups and nested districts are preserved. Do not reuse prior renders after geometry changes. HBC-INF-NATIVE IMPLEMENTED — UNVERIFIED. The existing Infinity workflow now sequences the full verified Bells source and checks actual native FSEQ duration and family coverage at the bounded tier. This machine's Xvfb cannot open a display socket. The 10,240-prop render, band, mobile, Windows, native acceptance and required comparisons remain open.

Test command: `python -m pytest -q tests/test_infinity_showcase_layout.py tests/test_infinity_showcase_targeting.py tests/test_fseq_pixel_preview.py tests/test_layout_bench.py tests/test_nine_panel_gate.py tests/test_vivid_style.py` (38 passed). The current session did not approve or publish any video. See latest_status.json for per-item dependencies, evidence and blockers.


> **2026-11-20 GitHub/Drive gate:** CI run [44687388477](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/44687388477), head `f8bd364`: focused regression jobs 3.11 and 3.12 passed; full suites pending when inspected. Drive [Beta 1.4 band hook](https://drive.google.com/file/d/1NShBmODsUiToi14bxZ1sptbYrU1CZ_YQ/view) is a **custom OpenGL diagnostic**, explicitly NOT native xLights nor approved; its [receipt](https://drive.google.com/file/d/1CPX59ePv9XyVXUTu2QNU9OZWfYQyQ_93/view) confirms independent backing unverified. [Drive review gate](https://docs.google.com/document/d/1TfhnsrYi7v8-q4BMeSUWDs5owkZUazbdvDNeUyXDsIM/edit). **Open:** finish full-suite verification; add focused orchestration motion tests to workflow; native XSQ/FSEQ six-member band and 9/16 panel visual review; Android eight-variant playback/API30; Windows EXE; manuals; owner approval. No merge or release.

> Beta 1.4 completion status (2026-11-19): see [docs/BETA_1_4_RUNNING_CHECKLIST.md](docs/BETA_1_4_RUNNING_CHECKLIST.md). Unified both lineages; nine-cue drummer with physical ride; full suite green in CI on 3.11/3.12; first real-audio band MP4 (custom renderer, kit fully visible); Windows EXE smoke fix pending re-run; no release approval; MP4 deliverables, nine-layout catalog, Android/Windows acceptance and Drive delivery are still open.

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

### 2026-11-18 — Actual layout inventory
AC root XML has 256 model definitions, unique numeric start channels 1–256, 59 model groups, named arches and mega tree. Allmodels has 368 models, 69 groups, 13 model types including Image/Custom. Updated showcase requirements with counts and caveats. Source inventory only, no changes to original geometry or channel mapping. RGB width, external image dependencies, group references, 16 strip tree specification and native render still need validation. No approval or release.

### 2026-11-18 — Windows packaging parity and portability audit
725d2406 adds explicit catalog asset inclusion and missing-file gate to Windows portable spec, preserving existing package data. Allmodels XML references two absolute developer-local Image paths (hh.png, helixmascot.jpg); root mascot exists but hh.png not found in tracked tree. Fix pending; preserve original layout. Android CI 44267312796 succeeded, retained artifact 14411590439; unified integration CI 44262461545 passed (scope not independently audited). Earlier Android run 44267022917 failed; latest build does not establish runtime or native acceptance. Nine final layouts/theme pending. No merge/release.

### 2026-11-18 — Windows startup and frozen worker repair
2992f2c6 removes stale GP's House dictionary reference introduced by shared catalog migration, validates template/layout as files and dispatches frozen runs through sibling HelixCLI.exe --helix-cli. Source Python invocation preserved. Windows GUI smoke and packaged worker execution pending; CLI argument compatibility and actual previews must be verified. No merge/release.

### 2026-11-18 — Desktop preview producer integration
Restored optional desktop preview path in current sequence builder (a98f2d3b) using existing renderer signature and current changed-artifact tracking; GUI requests via --helix-review-previews. Flag stripped before effect engine, no impact on default Android/CLI. Sequential up to requested 8, soundtrack validation, per-file provenance and error logging. Full-length 12fps simulated output; not native or canonical 3D proof. Need candidate identity checks, band-specific guard, runtime and CI tests; preview failure does not invalidate sequence. No merge/release.

### 2026-11-18 — Recover band preview protection
8d84ae8f restores core/band_visibility.py verbatim from Android repair branch; 36aae599 invokes its canonical stage inspection before desktop simulated preview generation. Preserves original sequences and flags unsupported band rendering rather than pretending ordinary effects are a 3D preview. Recognition limited to known models/group marker; Android wiring, actual canonical renderer, independent vocals, drummer and runtime tests remain pending. No merge/release.

### 2026-11-18 — Android band guard and drummer baseline comparison
58e58e61 connects shared band guard before Android preview; existing private band visibility import now resolves. Baseline b27e8d77 pose spec v1 has two toms; current v3 has three HIGH/MID/FLOOR; pose spec, PNG manifest and XSQ integration differ. Do not wholesale revert: preserve approved geometry and reconcile latest nine cues, ride, alternate sticks/crashes against ground truth. Current composites lack explicit ride and independent snare hand targets. Native and runtime tests pending. No merge/release.

### 2026-11-18 — Drummer hand timing correction
19c77026 alternates every snare event independent of spacing; crash hand follows actual left/right component rather than independent rapid-repeat counter. Preserves physical channel names and deterministic seeded humanization. Added focused slow/fast alternation regression test, execution pending. Ride audio classification and ninth physical target, stick geometry consuming hand metadata, canonical rendering remain unresolved; no approval or release.

### 2026-11-18 — Extend drummer alternation to XSQ export
ba507eb3 adds hand metadata to component/pose mapping; 0b4e6146 preserves sourceHand in exported effects and fixes duplicate empty ElementEffects container bug. Added mapping regression test. Existing eight physical targets preserved; sourceHand is metadata, not proof native xLights or 3D renderer animates independent sticks. Ride and rendered hand geometry still pending. Tests not executed. No merge/release.

### 2026-11-18 — Drummer component preview fixes
132de447 reconciles exporter physical target names with V3 preview aliases, localizes brightness to hit mask, allows inactive instruments and silent song tails instead of demanding every instrument and last hit near end. Added tests for alias and localized brightness. This is standalone component-light preview, not canonical animated band; tests/render pending. Ride and stick animation remain incomplete. No merge/release.

### 2026-11-18 — Enforce drummer regression verification
CI 44271585785 passed Python 3.11/3.12 orchestration suite only; Android 44269896607 passed compile after band guard. 214d0b00 extends unified workflow triggers to animation/mapping/audio/export/preview and runs explicit hand-alternation and mask/alias tests on both versions. Updated CI outcome pending; no claim of visual or runtime acceptance. Ride and canonical animation outstanding. No merge/release.

### 2026-11-18 — Independent instrument clustering
CI 44273455581 succeeded expanded drummer tests on Python 3.11/3.12. 0469d457 fixes interleaved candidate clustering by instrument, preventing other instruments from splitting same-instrument clusters. Added focused regression; new CI pending. Ride distinction remains unsupported; no fabricated ride hits or geometry. Native rendering outstanding. No merge/release.

### 2026-11-18 — Restore original snare contact pose references
CI 44276826411 passed clustering regression on both Python versions. 3883fd9a copies LEFT_STICK_SNARE and RIGHT_STICK_SNARE authored coordinates verbatim from b27e8d77 into separate hand_pose_zones and hand_pose_map fields. Existing zones/composites and channels unchanged. New fields are not yet consumed by renderer; no claim of animated arms. Ride and actual canonical band rendering pending. No merge/release.

### 2026-11-18 — Connect snare hand masks to diagnostic preview
42d6b1c7 loads recovered hand pose zones and selects mask per sourceHand in XSQ; backwards-compatible parse_effects default. Added focused regression. This illuminates original contact paths only, not articulated 3D arm animation. No new MP4; CI pending; ride, six-member renderer and platforms remain open. No merge/release.

### 2026-11-18 — Strike illumination decay
CI 44277732347 passed hand-mask regression on both Python versions. e9ac531b replaces flat full-brightness diagnostic hits with bounded quadratic decay within existing effect interval. Added test for onset/decay/rest. New CI pending. This does not change native XSQ effects or solve articulated limbs/ride. No new MP4 or merge/release.

### 2026-11-18 — Bind reactive performer motions to event identity
CI 44279605011 passed decay regression on both Python versions. a0c78197 replaces nearest humanized timestamp matching with stable originating event order in models/working_drummer.py, eliminating cross-instrument motion assignment and quadratic search. Added simultaneous cue regression; CI pending. Working member slice is not verified canonical 3D renderer. Ride and articulated geometry remain outstanding. No merge/release.

### 2026-11-18 — Preserve instrument effect identity
CI 44280439634 passed reactive motion identity regression. 33c9c14e extends event-index binding to effect cues and correctly reports typed detection with bus suppression. Added effect identity assertion. New CI pending. Ride, physical articulation and canonical render outstanding. No merge/release.

### 2026-11-18 — Downstream duplicate strike scheduling
CI 44281318177 passed effect identity regression. 6e22a9f6 independently merges same-type interleaved events in schedule_drum_events, then restores chronological order. Added regression; CI pending. Existing 24ms merge window retained; rapid genuine hits and distinct tom classes require further validation. No canonical MP4 or release.

### 2026-11-18 — Preserve distinct labeled tom strikes
CI 44282095659 passed interleaved duplicate regression. e0af1288 deduplicates by instrument and explicit tom class; added simultaneous three-tom regression. Existing clutter cap and repeat scaling unchanged. Unlabeled toms still use fallback routing; no ride or canonical render. CI pending. No merge/release.

### 2026-11-18 — Explicit ride routing (partial)
8cb704ea adds ride stream; 16c4202e adds independent ride target and ride_hit timing; separate ride effect cue added. No classifier guesses ride, physical ride asset absent, consumers of DRUMMER_COMPONENTS must be audited for nine-target compatibility. CI and native verification pending. No merge/release.

### 2026-11-18 — Native ride compatibility guard
Existing canonical pose spec declares eight composites, no ride. Native XSQ injector previously derived targets from expanded logical tuple, producing an unsupported empty ride row. Explicitly exclude ride until physical asset is built. Logical ride remains staged; native nine-target support not complete. No merge/release.

### 2026-11-18 — Align asset composite names with exporter
Asset builder creates HX_SNOWMAN_DRUMMER_V3_DRUMMER_* composites while injector emits HX_SNOWMAN_DRUMMER_*. Add exporter-compatible submodel aliases with identical node ranges, preserving legacy geometry and names. Generated asset count metadata and native qualification still require verification; actual XSQ qualified-model targeting remains unverified. Ride not built. No merge/release.

### 2026-11-18 — Ride routing regression and asset count
Integration CI 44285660196 passed existing focused suite. 47f3550d corrects alias counts; added explicit ride stream-to-effect regression. CI pending for new test. Asset build itself not exercised by focused suite; physical ride geometry and qualified native target names remain unverified. No merge/release.

### 2026-11-18 — Autonomous completion authorization
Owner authorizes implementation decisions without repeat approval. Expand integration CI to generate canonical assets and exercise pose/PNG tests; include model/effect/asset changes in triggers. Prioritize native end-to-end rendering, canonical six performers, default layouts/audio and platform runtime over isolated tests. Keep final release approval gate. CI pending; no new MP4.

### 2026-11-18 — Enforce native and logical drummer target consistency
**Goal:** Prevent falsely reporting nine physical cue targets when the canonical native drummer xmodel currently contains eight; detect stale test contract.
**Changed files:** tests/test_drummer_v3_xsq_integration.py, .github/workflows/helix-unified-beta-integration.yml, both handoff files.
**Preserved:** Original drummer PNG and existing eight native nodes, three-tom mapping, accepted appearance and existing exported effects; no native ride invented.
**New:** Assert nine unique logical channels and the exact eight-target native subset; enforce xmodel aliases after actual asset generation on Python 3.11 and 3.12. Expanded test selection catches contract regressions that previously escaped CI.
**Evidence:** Prior workflow run 44286584728 passed asset build and existing tests on both Python versions; expanded XSQ matrix is newly triggered and not yet verified.
**Limitations:** Physical ride geometry, actual xLights qualified model import, vocal harmony and review MP4 still outstanding.
**Regression risks:** Existing xmodel and asset builder aliases may be inconsistent with newly enforced checks; repair based on failing CI before declaring pass. No merge/release.


### 2026-11-18 — Correct native drum On intensity and truthful real-audio excerpt
**Goal:** Repair two concrete sources of false approval evidence: an xLights On effect populated with a generic 0..1 Brightness key, and a "30s" video runner that silently copied the full song.
**Changed:** tools/integrate_drummer_v3_into_xsq.py, tests/test_drummer_v3_xsq_integration.py, tools/run_helixville4_full_band_lightsouttheme_30s.py, tests/test_helixville4_audio_excerpt.py, integration CI, machine status and artifact manifest.
**Preserved:** Owner source drummer PNG, three-tom geometry, original hit timing/targets, audio input identity, preview pipeline, existing variant behavior; no release or merge.
**New:** Native xLights On settings use percentage start/end controls and decay, enabled white palette; XSQ test asserts 72%/4% decay and sourceHand. Band runner FFmpeg-transcodes a bounded 30s MP3 using the input song stem, verifies nonempty output and fails on missing source; dry-run does not manufacture a clip. CI tests synthetic 35s WAV to 30s MP3 and physical/logical target contract.
**Evidence:** GitHub 44286584728 passed asset-generation matrix Python 3.11/3.12. 44288262162 passed native On and target-contract tests Python 3.11/3.12. Media-excerpt run 44288669616 pending at initial check. Native xLights On documentation supports start/end intensity keys; real headless FSEQ verification still absent.
**Limitations:** Requested LightsOutTheme.mp3 not in repo; no nine-panel approval MP4, nor Android device validation, nor full six-member motion proof. Android CI candidate artifact 14412037480 from run 44269896607; not approved.
**Regression risks:** FFmpeg encoder availability, audio filenames, source duration and palette syntax. Next: inspect 44288669616, repair if needed; validate native XSQ/FSEQ with real audio/layout. Release not approved.


### 2026-11-18 — Author distinct ninth ride hardware and repair floor-tom overlay
**Goal:** Upgrade ninth ride from logical placeholder into a physical xLights submodel of the original approved snowman drummer, and stop lighting the extra lower-right drum instead of the designated floor tom.
**Changed files:** fixtures/band_geometry/drummer_v3_pose_spec.json, drummer_v3_png_layer_manifest.json, tools/integrate_drummer_v3_into_xsq.py, tools/render_drummer_v3_preview.py, tools/export_drummer_ground_truth_xsq.py, tests/test_drummer_v3_xsq_integration.py, tests/test_drummer_v3_pose_sheet.py, tests/test_drummer_v3_png_layers.py, .github/workflows/drummer-ground-truth.yml; preserved original PNG/source image bytes.
**Preserved behavior:** The existing kick/snare/hi-hat/three toms/two crashes, original snowman kit source, deterministic event ordering, no mallets or fourth tom, separate snare-hand metadata; no merge/release.
**New behavior:** Authored RIDE ellipse on the smaller lower-right cymbal (separate from upper-right crash) plus a shoulder-anchored contact-stick region and DRUMMER_RIDE composite; native target set and diagnostic masks now include ride. Ground-truth XSQ exports nine targets and explicit ride hits with valid xLights On peak/end settings. PNG strike manifest has ride_hit and fixes FLOOR to lower-left real tom, with high/mid overlays aligned to canonical geometry. Focused tests assert native aliases, positions, nine valid On effects and actual 12-frame/11-layer output.
**Evidence:** Original source drummer image visually inspected and retained unchanged; CI run 44290301048 running for Python 3.11/3.12, diagnostic ground truth run 44290395867 queued with WAV/XSQ/MP4 artifact uploads. These are synthetic diagnostics only and not an approved band/nine-panel real-audio render.
**Limitations:** Audio classifier cannot independently distinguish ride from generic cymbal in full mix; explicit ground-truth ride cue is not detection. Original backing-harmony/drummer full scene and xLights native FSEQ still unverified. Generated xmodel must be built from updated pose spec for native ride; older checked-in xmodel may be stale.
**Regression risks:** New ride location must be visually reviewed against the original kit, PNG contact position and prior oracle; xLights model-submodel naming and scene compatibility need native proof. Tests/CI might fail and require repair. No release.


### 2026-11-18 — Restore existing native xLights layout bench to unified branch
**Goal:** Make buried native XSQ→xLights FSEQ→multi-panel rendering tools available on unified beta branch rather than rebuilding a simulator.
**Changed:** tools/layout_bench six modules, fixtures/layout_bench manifest/lock/docs/variants, tests/test_layout_bench.py, tests/test_nine_panel_gate.py, integration CI, ledger and handoff.
**Preserved:** Existing choreography engine, original source drummer and platform builds, explicitly unapproved provisional nine-panel slots, no merges/releases.
**New:** Restore existing PR #208 clean-room generation/native FSEQ decode/render and a fail-closed 3×3 approval gate. CI regenerates 16 fixtures and checks structural tests; approval remains blocked without real audio, actual canonical band and nine native validated layouts. No 16-panel output counted as approval.
**Evidence:** Source PR #208 head 07dbe0f4; focused CI newly triggered, native renderer not executed yet. Previous drummer ground truth run 44290395867 successfully produced diagnostic nine-cue MP4, not six-member/native FSEQ.
**Limits/risks:** Fixtures generated in CI, not checked-in XML/XSQ; production nine-panel still missing exact 256-channel AC, vocal panel, model zoo final design, piano/3D Birdsong proofs. Native xLights binary must be available for FSEQ. Parser compatibility may require repair from CI. No release.


### 2026-11-18 — Restore native FSEQ bench and export downloadable diagnostics
**Goal:** Restore independently developed layout bench and deliver actual nine-cue original-snowman diagnostic artifacts; expose rich panel-six model-zoo candidate without misrepresenting it as an approved nine-panel comparison.
**Changed files:** .github/workflows/drummer-ground-truth.yml and nine-panel-layout-bench.yml; tools/layout_bench/{generate_layouts,run_bench,render_comparisons,xlights_fseq,summarize_runs,validate_nine_panel}.py; fixtures/layout_bench/{manifest,nine_panel_lock,variants,README,FINDINGS}; tests/test_layout_bench.py, tests/test_nine_panel_gate.py; beta status/manifest and this ledger. Imported relevant source from open PR #208 head 07dbe0f4 without merging PRs or altering core sequencing.
**Preserved:** Original 3x3 owner lock (band center, #4 combined vocals, #6 diverse native-model zoo), provisional/blocked statuses, exact nine-cue original drummer imagery, no fabricated singer pass, no release or merge.
**New:** Native xLights FSEQ read and node-accurate comparison runner available in integration branch; 17 synthetic candidate layouts generatable, including 76-model zoo. CI builds/structurally checks layouts and approval gate. Drummer workflow emits nine-cue XSQ/WAV/12-second H.264/AAC diagnostic; ffmpeg complete decode checked and generated physical xmodel retained as artifact.
**Verified CI and artifact evidence:** Drummer run 44290824555 success: MP4 14419964886, XSQ+audio 14421676007, physical xmodel+source 14421132009. Ground truth 44291594505 also success. Nine-panel candidate run 44291725423 success: model-zoo XML+template 14421831415. Unified bench CI 44291632931 in progress as last checked. Synthetic drum diagnostic is not an actual six-member band/native FSEQ render; model-zoo XML is not an approved panel.
**Limitations:** 17th-model-zoo generator outpaced old checked-in 16-layout manifest; corrected tests to 17 and documentation; generated XML/manifest refreshed by CI, not yet committed. Missing final 256-channel AC, combined vocal, 3D matrix/Birdsong, piano-driven and ultimate RGB approval layouts; real lyrics/harmony and FSEQ proof pending. No Android runtime pass; latest APK is only a debug-build candidate.
**Risks:** Restored PR208 native FSEQ tools may conflict with updated core parser; pending matrix will surface. Need actual xLights AppImage/native render and original-audio access. Diagnostic effect contacts and ride position still require human visual review. Approval gate deliberately rejects unverified layouts.
**Next exact action:** Inspect 44291632931; repair CI if needed; build and verify genuine native XSQ→FSEQ→MP4 using one real track and approved layout, with 9-panel gate fail-closed. No publication/merge before owner approval.

### 2026-11-18 — Final CI reconciliation
Unified integration run 44291632931 succeeded on both Python 3.11 and 3.12: compile, orchestration regression, drummer illumination regression, 17 clean-room layout generation, and nine-panel structural gate all passed. Model-zoo run 44291725423 passed and published provisional XML/XSQ template artifact 14421831415. Drummer nine-cue run 44291594505 passed. None of these verifies genuine native FSEQ sequencing or complete six-snowman/nine-panel real-audio approval. Next: acquire verified xLights render and visually approve, then platform device/runtime retest. No merge/release.

### 2026-11-18 — Bounded drum scheduling
Goal: remove quadratic full-history scans and preserve distinct labeled tom velocities. Changed mapping/drum_mapper.py and focused hand-alternation tests. Preserved stable ordering, priority, merge and clutter windows, repeat attenuation for same target, canonical geometry. New deque finalizes expired hits; explicit tom classes use separate repeat keys. Tests added for window boundary and distinct tom amplitudes; CI pending. Limits: default four-hit clutter cap and existing evicted-hit repeat-history semantics retained; no native render or measured speedup yet. Risks: boundary timing and unusual negative config values; verify focused matrix before further changes. No merge/release.

### 2026-11-18 — Reuse resolved drum component mapping
Prior bounded scheduler checks passed (runs 44296016061 and 44296016075). Reuse one component mapping for poses and component events, and count streams in one pass; preserve output schema and deterministic assignments. Added call-count and output consistency regression. New CI pending; no benchmark or native render claimed. No merge/release.

### 2026-11-18 — Bound diagnostic rendering overhead
Previous commit e906030f passed runs 44308380178 and 44308380349. Optimize tools/render_drummer_v3_preview.py with a forward-only active-interval sweep and once-per-render resized source/masks. Added overlapping-event equivalence and pixel equality regressions. Preserves timing, decay, original artwork and composition order. Scope is diagnostic renderer only; not native FSEQ or full band. CI pending; no measured speedup. No merge/release.

### 2026-11-18 — Birdsong source integrity
Prior renderer optimization passed 44340298697 and 44340298672. Replaced synthetic 20s energy/centroid and fixed tempo in optional Birdsong hook with streamed real audio RMS and spectral centroid; no invented targets or tempo; skip missing/silent input. Per-run manifest avoids overwrites. Audit labels sidecar request, not exported choreography. CI pending; feature extraction is additional analysis, not yet shared; full-song feature arrays and actual production XSQ integration remain outstanding. No merge/release.

### 2026-11-18 — Consolidate Birdsong production dispatch
Prior preview optimization passed runs 44340298697 and 44340298672. Source inspection confirms core/effect_engine.py calls birdsong_engine.place_birdsong_engine with real audio, note events, hats, vocal peaks and placement callback; AC hardKor disables it intentionally. Remove duplicate synthetic 20-second post-run hook from sequence_builder; normalize legacy enable aliases to supported --birdsong. Preserve standalone Issue #2 diagnostic module, default opt-in and explicit disable behavior. Add alias regression. CI pending; actual Birdsong effect survival, geometry and native FSEQ still unverified. No merge/release.

### 2026-11-18 — Birdsong accepted-placement reconciliation
Fix production add_model callback to return True only on accepted effect insertion and False for unavailable targets, cooldown rejection or exhausted conflict resolution. Birdsong records call/echo/trill/sweep timing and counts only when callback does not explicitly reject; retains compatibility with None-returning test callbacks. Added rejection regression. Prior synthetic-hook description corrected: secondary hook was real-audio sidecar analysis but redundant with production analysis. Tests/CI pending; downstream XSQ and native FSEQ proof still required. No merge/release.

### 2026-11-18 — Independent timing export gate
Goal: preserve accepted Birdsong and Snowman band/face timing in XSQ even when Chronoflow emits zero events. Changed core/effect_engine.py to dedent three timing-track writes out of Chronoflow condition; existing Chronoflow behavior, labels, caps and inactive status preserved. Added AST regression in tests/test_birdsong_engine.py. Prior b213f869 integration CI 44346809806 passed on 3.11/3.12. New CI pending; timing-track XML/native FSEQ still needs real-audio verification. Risk: newly present tracks in runs previously missing them by mistake; no merge/release.


### 2026-11-18 — Birdsong final timeline reconciliation
Commit 126c9d91 adds optional source labels to timeline entries and reports surviving XML-backed Birdsong placements after validation and polish, including actual timing and separate final effect counts. Timing labels now describe effect roles rather than species. Existing accepted-placement statistics retained. Tests and native XSQ/FSEQ verification pending; no approval MP4 or release. Next: regression coverage for removed and shifted entries, CI verification and real-audio native proof.


### 2026-11-18 — Strengthen Birdsong final reconciliation regression
Committed test-only change `ea110e82c1082a58feb121b768af538a98d98d00` in `tests/test_birdsong_engine.py`. The existing production-block regression now asserts both the shifted surviving call and surviving sweep are counted with final XML-backed timing, while a removed echo and unrelated piano entry are excluded. No production behavior changed. The commit's combined-status endpoint has not yet returned checks; do not mark the test as passed until the Actions result is inspected. No native FSEQ, real-song MP4, or owner approval is claimed.


### 2026-11-18 — Reconcile owner vocal and Android integration decisions
The 2026-11-15 owner clarification in issue #216/#230 authorizes a separate **ESTIMATED-vocals experimental pilot** for a finished stereo recording with audible lead and backing performances. It does not authorize changing VERIFIED provenance or bypassing `tools/verify_native_vocal_source.py`; reject bleed/duplicate/low-confidence harmony and retain REST where unsupported. The `Bbb vocals.mp4` reference is explicitly visual-only because its original timing failed.

Code inspection also confirms `android/app/src/main/python/helix_mobile.py::build_args` unconditionally includes `--no-effects-orchestrator` for both xLights and LOR modes. This is a real Android parity gap; do not simply remove the safeguard or force template promotion until memory limits and output-parity behavior are covered by tests. LOR's separate AC restrictions remain intentional. The connected Google Drive app is not available in this session, so new source-audio retrieval and real-audio native rendering cannot be performed here until Drive access is enabled or the source is supplied through an accessible workflow. Continue independent repository work; do not fabricate audio evidence.


### 2026-11-18 — Android orchestrator opt-in groundwork
Commit 054f798 enables explicit effects_orchestrator=true in RGB xLights mobile requests, sidecar only; AC/LOR and default mobile behavior remain unchanged. No GUI control, template promotion, memory benchmark or runtime parity claimed. Next: add request argument regression tests, verify bounded memory, then wire UI and validate actual production output before enabling by default. No merge/release.


### 2026-11-18 — Mobile variant preview validation
Commit 7ac1363 adds five Android orchestrator policy regression scenarios; CI not verified. Commit d4740fc validates each candidate's band layout before rendering its preview. Existing backend encodes up to eight variants with index-aligned preview paths and partial failure reporting. GUI playback and physical device testing remain outstanding. Simulation is not native FSEQ evidence. No merge/release.


### 2026-11-18 — Android results-screen playback integration
Commit 97a5c72 preserves primary MP4 fallback even when preview_paths is present but incomplete; aligned variant mappings remain authoritative. Playback checks local file availability before launching PreviewActivity. Existing spinner and eight-variant backend preserved. Compilation and device playback remain unverified; no claim of complete eight-variant acceptance. Next inspect EngineService checkpoint propagation and add device regression coverage. No merge/release.


### 2026-11-18 — Restore phone previews and name each variant state
**Goal:** Make Android preview encoding call the renderer that exists, tell the results screen whether each sequence preview is completed, running, pending, failed, or unavailable, and repair the unverified Birdsong reconciliation fixture.
**Changed files/modules:** `android/app/src/main/python/helix_mobile.py`, `android/app/src/main/java/org/helixsequencer/android/PreviewStatus.java`, `MainActivity.java`, `EngineService.java`, `AndroidManifest.xml`, `core/preview_status.py`, `core/sequence_builder.py`, `tools/preview_renderer.py`, `gui_launcher.py`, `tests/test_birdsong_engine.py`, `tests/test_android_preview_states.py`, `tests/test_preview_intensity_windows.py`, `tests/PreviewStatusChecks.java`, `.github/workflows/helix-unified-beta-integration.yml`.
**Intentionally preserved behavior:** Sequence export still survives preview failure. Primary sequence is still previewed first and the list stays capped at eight, with index alignment to `sequence_paths`. A stage is `success` only when rendered count equals the requested count. RGB orchestrator remains explicit, sidecar-only, and unpromoted; AC/LOR still disable it. Full-timeline intensity matrices are unchanged when no frame window is requested. Birdsong production reconciliation is unchanged. Older checkpoints with no `preview_states` can still play a file that exists. No merge, tag, or release.
**New behavior:** Phone previews call `HouseRenderer.render_frame` and build intensity in 30-frame windows. Checkpoints include `preview_states`. The results screen shows that state and enables play/save MP4 only for `completed` plus a real file. `android:largeHeap="true"` raises the process heap cap. Desktop review logs emit `preview_state: failed <name>`, and the Windows review dialog can list those failures. The Birdsong fixture captures the echo before the live list shifts, and a trill whose XML was removed stays excluded.
**Tests/evidence:** Commit `9d622d67b4efc748210c0626accc8d0dd06d8a3b`. Python 3.11.18 (`/tmp/py311`) and Python 3.12.3 each ran the ten focused modules below and reported `50 passed, 5 subtests passed`. `javac` plus `java PreviewStatusChecks` printed `PreviewStatusChecks ok`. Workflow discovered at `.github/workflows/helix-unified-beta-integration.yml` (Python 3.11/3.12 focused pytest, push paths include `core/**` and `tests/**`) and `.github/workflows/helix-android-variant-compile.yml` (push paths include `android/**`). Actions for this SHA were not inspected. Run 44346809806 does not cover this HEAD.
**Limitations/deferred:** No Gradle assemble, device install, eight-variant playback, API 30 reproduction, Windows EXE, native XSQ/FSEQ, or approval MP4. `largeHeap` and windowed matrices are not an OOM pass. Simulated frames are not native xLights. The layout-picker device failure is untouched. Owner approval is not complete.
**Regression risks:** Windowed intensity math must stay equal to the full matrix (covered by test). A checkpoint that labels a finished file as pending will refuse playback until the state is `completed`. Enabling `largeHeap` changes Android heap limits for every process in the app. The unified workflow now also runs the new preview tests and will fail if they regress.

### 2026-11-18 — Nine-panel benchmark MP4 from verified audio
**Goal:** Render the 3×3 benchmark from one real song, with Helix XSQ output and native xLights FSEQ where the renderer was available.
**Changed files/modules:** `tools/layout_bench/generate_layouts.py` template duration only. The MP4, XSQ, and FSEQ files are in the agent store, not the git tree. `evidence/beta_completion/artifact_manifest.json`, `evidence/beta_completion/latest_status.json`, and this ledger record hashes.
**Intentionally preserved behavior:** The repository 256-channel layout was used for panel 2. Audio was not copied into git. No release and no owner-approval flag.
**New behavior:** Bench templates now declare a 600s sequence duration so a later native render is not clipped to 35s. The song used here already had effect ends at the full duration; headers were patched to 205.800 before FSEQ export.
**Tests/evidence:** Source audio sha256 `8b8caddd6c292a13995bde0e80ac66f948246bd634278ab4ade1a82163aa7086`. Native MP4 sha256 `e55fd0e1af7a1be8ab865193e76e03ba511e0bbb3df85eaab60a76d0dd9def88`, 42076744 bytes, H.264 1920×1080 30fps, AAC-LC 48 kHz stereo, container 205.76s, 0 blackframe hits. xLights 2026.19 wrote nine FSEQs at a 50ms step. A simulated XSQ-timing companion is sha256 `000b87a246fe6215f2c2ee01fa24d4d5987c70fdb6b2cc5c6777c21145454a6d`. Store path `/cursor/stores/self/beta14-nine-panel/`. Frames at 40s and 140s were inspected.
**Limitations/deferred:** Panel 5 is the generated four-snowman bench, not the canonical six. Panel 4 faces are generated NodeRange props. The store rejected a 121MB CRF 18 encode, so the stored native file is CRF 30. Container duration is 205.76s against a 205.80s source measurement. Not owner approval.
**Regression risks:** Generated bench templates now say 600 seconds. Existing checked-in ac16 XML was not rewritten.

### 2026-11-18 — CI passed for the preview repair, not for HEAD
**Goal:** Record the Actions result that was still unknown when `40dca014` was pushed.
**Changed files/modules:** Handoff ledger only.
**Preserved:** Nine-panel MP4 hashes and the statement that panel 5 is not the canonical six-member band.
**New:** `40dca014` has 15 successful checks. Unified integration run `44406112861` passed Python 3.11 and 3.12. Android run `44406112855` assembled and retained a debug APK. Drummer run `44406112840` passed. HEAD `61982611` was still running Unified integration `44412936937` and drummer `44412936902`; nine-panel bench `44412936764` had passed.
**Evidence:** GitHub Actions job conclusions for those run ids. Not a device test and not owner approval.
**Limitations:** The Android APK is a CI debug build of `40dca014`, not proof of eight-variant playback.
**Deferred:** Inspect `61982611` when its remaining jobs finish. Replace panel 5 with the canonical band.


### Beta 1.4 documentation release gate — owner directive 2026-11-18
- [ ] Update and verify Android and Windows user manuals for Beta 1.4: installation, nine bundled layout presets, audio import, AC/LOR and RGB modes, band toggle, eight-variant selection/playback/export, native XSQ/FSEQ versus simulated previews, troubleshooting, memory limits, licensing and donations.
- [ ] Synchronize in-app instructions, distributed manuals and version labels; verify scrolling and recreation on Android and package the manuals with both installers. Document only verified capabilities; explicitly label pending or experimental features.
- [ ] Record manual versions and checksums in the release artifact manifest before owner acceptance.
Mobile checkpoint: 07d1896 resets per-variant encoding progress; device verification pending. EngineService propagates preview_states and aligned paths. No merge/release.

- [x] Confirm desktop and Android share instruction text in source; add desktop scrollbar (8c37f9d).
- [ ] Verify packaged Windows executable includes shared instruction asset and opens it; verify both platform readers and finalize 1.4 documentation after acceptance.


2026-11-18: Shared instruction source expanded in 5b8f300bb62ddfbfeb44a9813363279ade62be8b with nine preset descriptions, experimental singer provenance, desktop recovery and native export guidance. Source committed; compilation, packaged manuals, checksums and device acceptance remain pending. Next: validate Android compile and desktop packaging; verify readers on devices. No merge/release.


Android manual packaging gate implemented in 442d26c3cdae90c252fd65b8926f056bfd37f5d2: APK asset must match source bytes; SHA256 and manual retained with debug APK. CI and device verification pending; Windows parity remains open.


### 2026-11-19 — Owner rejections and required Demucs/Whisper
**Goal:** Record that the nine-panel benchmark and the local v2 16-panel pilot are rejected, and stop production sequencing from silently analyzing the full mix.
**Changed files/modules:** `core/audio_intelligence.py`, `core/effect_engine.py`, `audio/drum_detection.py`, `audio/drum_stem_cohits.py`, `requirements.txt`, `requirements-windows-portable.txt`, `windows_portable.spec`, `tests/test_neural_stems_required.py`, `tests/test_audio.py`, both evidence JSON files, and this ledger.
**Preserved:** Diagnostic HPSS remains available only when `require_neural_stems=False`. Missing audio still returns an empty analysis. Moises remains an explicit optional separator. Whisper transcripts stay labeled CANDIDATE. No merge and no release.
**New:** The default stem path requires Demucs htdemucs, caches stems by source SHA256, and raises `NeuralStemRequired` if Demucs or Whisper is missing or fails. Drum classification reads the drum stem and may add kick/snare co-hits only on that separated stem. Whisper reads the vocal stem.
**Evidence:** Targeted tests in this commit. The rejected nine-panel file remains at `/cursor/stores/self/beta14-nine-panel/nine-panel-tinsel-tornado-native-fseq.mp4` and is not approval.
**Limitations:** Demucs and Whisper model weights are not bundled here. A full-song run will download them on first use. The canonical six-member band, floor-tom detection, and crash-hand alternation from the rejected pilot are not integrated. Layouts are not vendor-dense.
**Regression risks:** Any production sequence now fails until Demucs and Whisper can run. Windows portable builds become much larger. Cached stems are reused only when the source SHA256 matches.

### 2026-11-19 — Classifier, palette, groups, six-member bench, musical bed
**Goal:** Continue the owner list after the Demucs requirement: fix the drum_bus mislabels, bring in the portable v2 palette and geometry grouper, and stop sequences from staying dark between hits.
**Changed:** `audio/drum_classification.py`, `helix_style/palette_chooser.py`, `helix_spatial/auto_groups.py`, `tools/layout_bench/generate_layouts.py`, `fixtures/layout_bench/band_stage/xlights_rgbeffects.xml`, `core/musical_bed.py`, `core/effect_engine.py`, and the matching tests.
**Preserved:** Typed drum hits still suppress the bus stream. Left crash still maps to the left-hand component. Whisper transcripts stay CANDIDATE. The rejected nine-panel and 16-panel videos stay rejected.
**New:** Missing percussive measurements are unknown, not an automatic bus label. A winning family with a strong defining band is kept when the runner's defining band is weak. Palette choice uses lyrics, tempo, intensity, sections, and key. Props can be grouped from geometry. The bench band names the six snowmen and the three-tom-plus-ride kit. Saved XSQ files gain a dim On bed in gaps of at least 700 ms.
**Evidence:** `tests/test_drum_detection.py`, `tests/test_neural_stems_required.py`, `tests/test_palette_chooser.py`, `tests/test_auto_groups.py`, `tests/test_musical_bed.py`, and `tests/test_drummer_hand_alternation.py` were run after these edits. Demucs/Whisper proof is in the handoff. A full CRF 18 nine-panel replacement has not been rendered.
**Limitations:** The v2 16-panel layout module and its runner do not apply onto this branch. Floor-tom *detection* from a full mix is still not proven on Tinsel Tornado; explicit floor-tom labels still route to the floor tom. Android device playback and a Windows EXE were not rebuilt in this pass.
**Risks:** The musical bed adds effects to every model gap and can look like a wash if section energy is high. Level is capped at 28 percent.

### 2026-11-22 — Vivid pass leaves performance props and existing timing alone
**Goal:** Stop the vivid pass from recoloring or retiming singers, the band, and the drummer, and stop it from deleting or shortening any existing effect.
**Changed:** `core/vivid_style.py`, `core/effect_engine.py`, `tests/test_vivid_style.py`.
**Preserved:** AC full-bright chases. Demucs, Whisper, drummer geometry, and hand mapping. Musical bed still optional.
**New:** Performance props are skipped. Existing effects keep their start, end, and palette. Vivid effects go on a layer named Helix Vivid and do not overlap on that layer. Chases step on the phrase beats. Sections come from `detect_sections` in the engine, or from a Sections timing track. Each layout uses a different `choose_palette` strategy.
**Evidence:** `tests/test_vivid_style.py` (6 passed, the librosa-import accent test deselected in this environment). v6 FSEQ on the band panel: mouth phonemes remain 340 ms and light; all nine drum cues light. Active-phrase node lit fraction is in the handoff table. Panel 7 is 0.493 because the matrix dominates its node count.
**Limitations:** Not owner approval. The nine-panel film is a 2D plot of FSEQ pixels.
**Risks:** A group that contains a singer or drummer is not given a vivid group effect, so that group stays on its original effects only.

### 2026-11-19 — Vivid AC banks and saturated RGB on black
**Goal:** Stop the nine-panel shows reading as simple and drab. The AC row has to be full-bright and colored. RGB panels use saturated section colors on black, in the manner of the Helix Prime references.
**Changed:** `core/vivid_style.py`, `core/effect_engine.py`, `tools/layout_bench/xlights_fseq.py`, `tests/test_vivid_style.py`.
**Preserved:** Drummer geometry, hand mapping, Demucs and Whisper. The musical bed function remains and runs only when `HELIX_MUSICAL_BED=1`. `HELIX_VIVID=0` skips the new pass. Group, submodel, and blend keys stay.
**New:** After the optional bed, the default pass removes it. AC channels chase and alternate banks at intensity 100. RGB hits attack at 100 and decay within 140 ms. Palettes are single saturated colors, rotated per model and section. White is every 17th AC accent. Spiral trees and DNA sculptures can be appended without moving existing channels. AC bulbs that were white or gray draw as saturated color.
**Evidence:** `tests/test_vivid_style.py` passed. 30-second preview sha256 `b843d63c2ed2ac1f66f91221da46797081df1ce93b5861c59686c82a72af43c9`. Full-song v5 sha256 `d3091e7553190f2d7eeb9f6e86319d62943732684c065dafffeff6ae58f03bf0`, 4116 FSEQ frames, xLights 2026.19. AC lit pixels are fully saturated and brighter than the reference frames. White fraction of lit pixels is 0.
**Limitations:** The nine-panel picture is a 2D plot of FSEQ pixels, not the reference's perspective camera. Sixteen AC channels cannot match a 36-tree grove in pixel count; they are drawn large so the row reads bright.
**Deferred:** Replacing the real 256-channel house geometry. That file is not densified.
**Risks:** Sequences grow by the chase effects. Set `HELIX_VIVID=0` to keep the previous look.

### 2026-11-19 — Stem ride and floor-tom detection
**Goal:** Find ride and floor-tom hits on a Demucs drum stem without relabeling snares and hi-hats.
**Changed:** `audio/drum_stem_cohits.py`, `mapping/drum_mapper.py`, `tests/test_stem_metal.py`.
**Preserved:** Kick and snare co-hit rules. The classifier still runs first. Demucs and Whisper requirements are unchanged. Drummer geometry and crash hand alternation are unchanged.
**New:** A 110–220 Hz body that is louder than the kick sub and the snare wires, and not on top of a kick or snare, is a floor tom. A 2.8–6.2 kHz ping louder than the 9–14 kHz wash, with a high-band centroid at or below 5.2 kHz, is a ride unless that moment is already a hi-hat or crash. The mapper treats tom_class 3.0 as floor.
**Evidence:** Synthetic burst test passed. Tinsel Tornado stem: floor 40, ride 1. Candy Cane Shockwave stem: floor 6, ride 2. Floor hits were not within 60 ms of a snare.
**Limitations:** These are not a human transcription. Many ride-like pings were already classified as hi-hats and were left as hi-hats.
**Deferred:** A second-pass reclassification of hi-hats into ride when a pattern is steady.
**Risks:** Floor-tom count can rise on bass-heavy stems. The wire and kick exclusions are there to limit that.

### 2026-11-19 — Infinity Showcase groups, submodels, and spatial order
**Goal:** Bring the Infinity layout onto this branch and target it with the new group, submodel, blend, and spatial graph.
**Changed:** `tools/build_infinity_showcase_layout.py`, `tools/infinity_showcase_clip.py`, `tests/test_infinity_showcase_layout.py`, `tests/test_infinity_showcase_targeting.py`, `.github/workflows/helix-infinity-layout.yml`, `docs/INFINITY_SHOWCASE_INTEGRATION.md`, `evidence/beta_completion/infinity_clip/`.
**Preserved:** Drummer geometry, Demucs, Whisper, and the nine-panel sequences. PR #250 was not merged. Its Drive download was not copied.
**New:** Singing faces have Mouth and Eyes. `HX_INFINITY_DISTRICTS` lists family groups. A clip orders faces by X and emits `modelGroup`, `submodel`, Average, and Canvas.
**Evidence:** Layout tests passed, including the 10240 tier. xLights 2026.19 rendered the mouth-only clip: mouth 255, eyes 0, rest of the face 0. FSEQ sha256 `aa3554e0a1f84b12ab6e9db9bb9364ba4221e6bdce8087bddcebaf4e8acf1941`.
**Limitations:** Not the full Bells song and not owner approval.
**Deferred:** Full-song Infinity sequencing.
**Risks:** The 10240 layout test writes a large XML in CI. The new workflow only runs the unit tests.

### 2026-11-19 — Full-song nine-panel color check
**Goal:** Re-render Tinsel Tornado at full length with the dark bed palette and see whether any panel is still washed white.
**Changed files:** evidence contact sheets and `evidence/beta_completion/nine_panel_v4/panel_color.json`. No sequencer code change. The bed fix was already `b706a874`.
**Preserved:** Demucs, Whisper, drummer geometry, hand mapping, and the sequenced effects. Only the bed palette and blend keys were rewritten before the FSEQ pass.
**New behavior:** None in code. The render uses the dark palette index.
**Tests/evidence:** xLights 2026.19, 4116 frames on all nine layouts. No panel's lit pixels were mostly white. Hits read above the bed on every panel except the sparse 16-channel AC panel, whose p95 is only a little above its mean because those channels stay dim. Contact sheets at 42, 96, and 168 s. MP4 sha256 `3300581f0f47dfd7eb4ec36aa3c9bc2ba8c06b1cf6adb78159744ad0e2b257ee`.
**Limitations:** Not owner approval. Panel 1 stays sparse because it is 16 single-channel strands. Panel 8 is bright but colored.
**Deferred:** A new full resequence from scratch. This pass kept the existing effect timing and replaced the bed.
**Regression risks:** None in code.

### Beta 1.4 Windows packaging checkpoint
{"spec_commit":"fe4113264617d20319df4358c34877a921e21bea","workflow_commit":"7e3339d8563d11c5c4d6bab9ff5e11d35439c3e1","workflow":".github/workflows/helix-beta14-windows-candidate.yml","status":"implemented; push build not confirmed; no packaged runtime verification","next_action":"Inspect push Actions run directly; connector commit workflow lookup covers pull-request runs only. Verify ZIP and Windows 11 runtime; no release."}

### 2026-11-19 — Nested groups, spatial routing, and xLights layer blend
**Commit:** `b706a874` on `integration/unified-beta-completion-20261117`.
**Goal:** Let effects target nested groups and submodels, route props from 3D layout coordinates, and write the layer-blend and Canvas XML that xLights 2026.19 accepts. Check the washed-white v3 panels against the musical bed.
**Changed files/modules:** `core/model_parser.py`, `core/helix_flow_spatial_graph.py`, `core/effect_layering_engine.py`, `core/musical_bed.py`, `xlights/layout_sync.py`, `xlights/layer_blend.py`, `tests/test_native_layer_targets.py`, `evidence/beta_completion/layer_blend_clip/`.
**Preserved:** WorldPos model coordinates used by the existing spatial tests. Layer role names and the internal blend labels Normal, Overlay, Screen, and Additive. Drummer hand alternation, Demucs, and Whisper. `ensure_master_view_models` no longer rewrites `modelGroup` or `submodel` back to `model`. PR #188 and PR #250 were not merged. No release.
**New behavior:** `expand_group_members` walks groups that contain groups. Sequence rows for groups and submodels use `modelGroup` and `submodel`. Submodel and group nodes use geometry centroids. `route_names_by_axis` orders the six snowmen by X. Effect settings gain `T_CHOICE_LayerMethod`, `T_CHECKBOX_Canvas`, and, for spatial effects, `T_LayersSelected`. The musical bed uses a dark palette index and Average on its own layer, so it no longer inherits the white palette 0.
**Tests/evidence:** `tests/test_native_layer_targets.py`, `tests/test_musical_bed.py`, and `tests/test_helix_flow_spatial_graph.py`: 12 passed. xLights 2026.19 rendered a 2 second clip to 40 frames. Group members lit, the targeted mouth lit, and the untargeted eyes stayed dark. FSEQ sha256 `de63bf7ff5826c86aa7cdab1f40ab5fedb4f1e380f4fc30c63a112ea2608dd50`.
**Limitations:** This is a short clip, not a full-song nine-panel render. The bed level is still 12–28 percent. Infinity Showcase #250 was inspected only as a named target and was not ported. Ride and floor-tom detection on Tinsel Tornado are unchanged.
**Deferred:** Full-song re-render after this blend fix. Vendor-dense layouts. Android and Windows packaging.
**Regression risks:** Sequences that previously stored groups as `type="model"` now store `modelGroup` after a layout sync. xLights 2026.19 accepted that on the band fixture. Older xLights builds were not tested. Spatial effects gain Canvas settings and can composite differently from a bare effect.


### 2026-11-19 — Restore the ninth canonical drummer lane in the ground-truth oracle
**Goal:** Make the dedicated Drummer Ground Truth workflow test the current nine-component contract, including the physical ride, instead of exporting the stale eight-lane fixture.
**Changed files/modules:** `tools/drummer_ground_truth_oracle.py`, `tools/export_drummer_ground_truth_xsq.py`, new `tests/test_drummer_ground_truth_export.py`, and this ledger.
**Preserved behavior:** Existing kick, snare, hi-hat, three tom, and left/right crash events; canonical xmodel naming; no production detector, mapper, approved engine, or physical show routing changes.
**New behavior:** The deterministic oracle now includes RIDE as its ninth target, emits a ride event in the isolated component sequence, exports nine logical channels and nine physical xmodel targets, and assigns the ride the cymbal palette color. The CLI/help and embedded XSQ contract now consistently report nine lanes.
**Tests/evidence:** Added focused assertions for the nine-target oracle, ride event, palette/physical target coverage, and nine-lane XSQ structure. GitHub Actions Drummer Ground Truth workflow is expected to rerun because its watched `tools/**` and `tests/**` paths changed; execution is pending.
**Limitations/deferred:** This synthetic fixture proves export contract consistency, not real-audio ride detection or native xLights FSEQ/MP4 playback. Full-song canonical drummer acceptance remains open.
**Regression risks:** The fixture now includes a ride event; consumers that intentionally expected the old eight-lane test fixture must be updated to the current nine-cue contract. No merge/release or owner approval implied.


### XSQ cache repair — November 20

- [x] Implement input/output receipt validation and isolated fresh generation (`e0efe160ac0ec7cd4805f9f97ef3f6737cd9667e`).
- [ ] Verify cache hits, changed inputs, dirty tree and failed generation with regression tests.
- [ ] Confirm native MP4 run 44793419539; visual approval remains pending.
