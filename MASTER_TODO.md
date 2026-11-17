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

### 2026-11-04 — Layout bench videos use xLights FSEQ channel data
**Agent:** Cursor cloud agent
**Branch:** `cursor/layout-test-bench-f36b`

**Goal:** Comparison panels must show xLights-rendered channel values, not a whole-model timing approximation.

**Changed files/modules:**
- `tools/layout_bench/xlights_fseq.py` runs `xLights --headless` and decodes FSEQ v2 (including zstd blocks).
- `tools/layout_bench/render_comparisons.py` paints each node from that FSEQ and stitches the same 10 variant grids.
- Layout fixtures: `DisplayAs` for canes is the xLights type `Candy Canes`. Faces, snowmen, and snowflakes are poly lines with real node counts, because xLights Custom models with no pixel image have zero nodes and drop effects. Default `ScaleX`/`ScaleY` is 1 so render buffers stay the size of the prop. Groups that shared a model name were renamed to `All Roofline`.

**Intentionally preserved behavior:** The sequencer was not rerun and its effect placement was not changed. The same canonical XSQ files are the render input.

**New behavior:** Videos are built from xLights 2026.19 FSEQ output at the sequence step time (50 ms / 20 fps).

**Tests/evidence:** Fixture tests still check channel counts. Headless renders of the heavy layouts completed and produced non-empty FSEQ files. Per-model lit/blank stats are written beside the render run.

**Limitations:** Node positions are the layout parser's virtual pixels, placed in channel order from each model's start channel. xLights still drops zero-length timing marks. One-channel props are drawn along their strand at the single rendered level.

**Deferred work:** Human review of the new videos. The snowman-band `composite_submodels` crash is unchanged.

**Regression risks:** Layout XML scale and the cane display type changed so xLights can load the fixtures. Helix sequencing code did not change. Existing XSQ files still address the same model names.

### 2026-11-04 — Layout test bench fixtures and comparison runner
**Agent:** Cursor cloud agent
**Branch:** `cursor/layout-test-bench-f36b`

**Goal:** Give the owner several distinct, judgeable views of the same songs sequenced onto different xLights layouts, from a 16-channel LOR yard through a snowman-band stage and optical-illusion props.

**Changed files/modules:**
- `tools/layout_bench/generate_layouts.py` writes 16 clean-room `xlights_rgbeffects.xml` layouts and paired empty templates.
- `tools/layout_bench/run_bench.py` invokes `main.py --profile master` once per layout and song.
- `tools/layout_bench/render_comparisons.py` builds labeled 12- and 16-panel preview videos from the canonical XSQ files.
- `tools/layout_bench/summarize_runs.py` writes `fixtures/layout_bench/FINDINGS.md`.
- `fixtures/layout_bench/` holds the layouts, templates, manifest, README, and findings.
- `tests/test_layout_bench.py` checks channel counts, face phoneme markup, and clean-room templates.

**Intentionally preserved behavior:** No sequencing, effect, parser, or preview-renderer behavior was changed. The bench calls the existing master CLI and the existing preview geometry helpers.

**New behavior:** A repeatable layout bench. AC layouts are exactly 16, 32, and 64 single-color channels. Pixel, band, and wow layouts use common model types and hobbyist names, including singing-face NodeRange phonemes and the nine drum-hit prop names. Comparison videos stay out of git.

**Tests/evidence:** `python3 -m pytest tests/test_layout_bench.py -q` (5 passed). Master profile completed 112 sequences (16 layouts × 7 songs) with return code 0. Coverage is in `fixtures/layout_bench/FINDINGS.md`. Preview MP4s are artifacts, not commits. xLights import of the new XML was not run in this environment.

**Limitations:** Preview panels show whole-model effect timing, not per-pixel xLights shaders. Snowman-band planning still raises `KeyError: 'composite_submodels'` and is skipped; that bug was documented, not patched. A few props are dark on a single song (`Snowflake 5`, `Star 4`, `Ring 1`).

**Deferred work:** Human approve/veto of each comparison video. Real xLights import of the fixtures. Fixing the snowman-band `composite_submodels` crash, which is outside this bench task.

**Regression risks:** None in the sequencer. The new modules are additive. Template sync still removes the seed `Bench Palette` row at runtime.

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


### 2026-11-16 — Nine-panel locked manifest and gap audit
**Goal:** Prevent synthetic sixteen-panel fixtures from being misrepresented as owner's requested nine-panel approval video.
**Changed files/modules:** fixtures/layout_bench/nine_panel_lock.json.
**Preserved behavior:** Existing 16-fixture generator, runner, renderer and deterministic effect mapping untouched; no approved drummer geometry changed.
**New behavior:** Machine-readable locked 3×3 positions, exact owner requirements, provisional fixture candidates and explicit missing/blocked status, real full-vocal audio and native FSEQ/1920×1080 MP4 requirements.
**Tests/evidence:** Inspected PR #208 fixture manifest (16 fixtures). 16-channel fixture exists; no 256-channel fixture; synthetic band_stage fixture cannot demonstrate canonical six-member 3D band. Manifest committed e916b0cf7474cc529b87ca5faa91e3b0c2b3cbc0. JSON is data only; no render has been executed.
**Limitations:** Manifest does not itself implement the missing fixtures, audio acquisition, drummer renderer or approval output.
**Deferred work:** Build exact missing AC256, singing-face/tree, piano-driven, Birdsong/spatial and dense showcase fixtures; validate canonical drummer and independent vocals; run real-song native xLights FSEQ and visual MP4.
**Regression risks:** None to runtime because new standalone manifest is not wired to existing 16-panel runner; future integration must reject blocked slots.


### 2026-11-16 — Nine-panel fail-closed approval gate and regression tests
**Goal:** Stop incomplete/synthetic fixture sets being presented as an approved nine-panel real-audio render.
**Changed files/modules:** tools/layout_bench/validate_nine_panel.py; tests/test_nine_panel_gate.py.
**Preserved behavior:** Existing 16-panel bench sequencing, xLights FSEQ renderer, effect engine, audio and canonical drummer are untouched.
**New behavior:** CLI validates exact 3x3 order, snowman center requirement, distinct known fixture IDs, verified slot statuses, real vocal audio and native-render metadata; --structural-only checks the plan without claiming approval. Five unittest cases guard known gaps, reordering, unknown and duplicate fixtures.
**Tests/evidence:** Added five regression tests; execution not yet confirmed by CI. Commits add1092023feeb4d659a5a1626ebc1e5668ff319 and b0c307aa0739de47531b7336bf877a673d03b350.
**Limitations:** Metadata gate does not authenticate audio or FSEQ itself; real media inspection and visual acceptance remain necessary. It is not yet integrated into renderer invocation.
**Deferred work:** Add exact missing fixtures, wire fail-closed preflight into a nine-panel runner, run actual vocal audio with native xLights and visually review drummer/voices.
**Regression risks:** Future schema or fixture rename requires corresponding validator/test updates; current sixteen-panel workflow unaffected.


### 2026-11-16 — Connect nine-panel preflight to native comparison CLI
**Goal:** Ensure explicit --nine-panel never silently produces a legacy 12/16-panel video or falsely claims approval.
**Changed files/modules:** tools/layout_bench/validate_nine_panel.py; tools/layout_bench/render_comparisons.py; tests/test_nine_panel_gate.py.
**Preserved behavior:** Existing legacy variants and renderer unchanged without --nine-panel; canonical drummer and engine untouched.
**New behavior:** --nine-panel invokes locked manifest verification before audio lookup/native render; requires all nine fixtures and real vocal audio marked verified; render-complete status is not required before rendering (avoids circularity). Explicit NotImplementedError prevents legacy fallback once metadata passes until nine-panel rendering is wired. Additional regression test covers render preflight vs approval.
**Tests/evidence:** Commits f9450cbec496a4267122fad3155ad54e144c0434, f710e995f3af1b4612a71dba66dacb133f2a9a8e, 2f859214e8c889b8dd393326632e862c89365a56. Tests committed; CI not yet run.
**Limitations:** Nine-panel renderer still needs actual nine-layout processing and a real-song MP4; current --nine-panel deliberately fails closed.
**Deferred work:** Implement all missing exact fixtures and nine-panel native pipeline, run test suite and real full-vocal media, verify visual/drum/singer output.
**Regression risks:** Import path of validator and preflight behavior must be tested in CI; legacy path should remain unaffected.


### 2026-11-17 — Native nine-panel execution path
**Goal:** Wire the locked 3x3 nine-panel plan to existing xLights FSEQ renderer rather than stopping after preflight.
**Changed files/modules:** tools/layout_bench/render_comparisons.py.
**Preserved behavior:** Legacy 12/16-panel plan and existing per-panel xLights FSEQ channel painter; approved drummer logic unchanged.
**New behavior:** --nine-panel --nine-panel-audio /path/to/full-vocal-song.mp3 validates all nine slot statuses, real-audio metadata and distinct fixture IDs, then reuses existing XSQ lookup, xLights FSEQ generation, panel painting, stitching and catalog. Legacy --only IDs forbidden with --nine-panel. Legacy --audio-dir still required only for legacy modes.
**Tests/evidence:** Commits 84d68ffbb22a9ba38d0233764533fd22470c1497 and c0ccedff5ab30570caa06924d5349de26728f475; CI/runtime not yet run. Current locked manifest deliberately blocks due to unverified/missing fixtures and audio.
**Limitations:** Existing stitch outputs 1440x858 with banner, not target 1920x1080; still needs output scaling and media QA. No MP4 produced. Current fixture set does not satisfy canonical band, advanced layouts, or vocal mapping.
**Deferred work:** Build/verify exact fixtures; run XSQ on full vocal audio; native FSEQ/MP4 render; validate audio sync, decode, brightness, framing and drummer/singer animation.
**Regression risks:** New --nine-panel branch uses existing renderer, but legacy behavior should be regression-tested before approval.


### 2026-11-17 — Owner-directed vocal consolidation and native model zoo
**Goal:** Consolidate singing faces and singing trees in panel 4; replace panel 6 with broad native xLights model showcase; require maximum musical grouping across all nine panels.
**Changed files/modules:** fixtures/layout_bench/nine_panel_lock.json; tests/test_nine_panel_gate.py.
**Preserved behavior:** Locked 3x3 order and six-member canonical snowman band at center, other seven panel concepts, native renderer, existing 16-panel fixtures, drummer ground truth.
**New behavior:** Panel 4 now requires Coro faces + singing trees + vocal matrices with separate lead/harmony and mouth/eye groups. Panel 6 now requires diverse native custom trees, stars, spinners, candy canes, mega trees, arches, snowflakes, matrices and more, grouped by model family, instrument role, geometry, spatial depth and independent submodels. Global grouping policy requires musical phrases, chases, builds, layering, counterpoint and rest suppression, not global beat pulsing.
**Tests/evidence:** Added three regression assertions for panel 4, panel 6 and all-panel grouping. Commits ede3119d26f6bb594fa8055c38029ccc74ef9cc4 and 81accece7c14e6b22877be54100270f3bf3c0678. Tests not executed in this turn.
**Limitations:** Specification and regression tests only; actual xLights models, native group routing and musical choreography remain unimplemented and unverified. Panel 4 and panel 6 remain explicitly missing.
**Deferred work:** Generate and verify actual layouts, nested model group/channel mapping, independent vocal lanes, real full-vocal native FSEQ and nine-panel MP4; verify dynamic group coverage and visual quality.
**Regression risks:** Downstream nine-panel layout generator must honor new model families and grouping policy; do not substitute generic singing tree fixture or generic pixel yard.


### 2026-11-17 — Advertising grid decision and full-HD compositor output
**Goal:** Keep nine panels for primary advertising legibility and correct MP4 output geometry.
**Changed files/modules:** tools/layout_bench/render_comparisons.py.
**Preserved behavior:** Locked 3x3 panel order and band center; existing native FSEQ channel data, panel labels, audio mux and all legacy comparison plans.
**New behavior:** Final composite filter converts any supported grid output to 1920x1080 with aspect-preserving scale/pad, square pixels and 30 fps H.264/AAC. Primary advertisement remains nine panels; 12-panel expansion deferred to separate technical demo.
**Tests/evidence:** Commit 88015006a273e20157034c11b1f54dc835304118. Static implementation review only; no ffmpeg/xLights render or visual QA executed in this turn.
**Limitations:** Nine-panel source fixtures remain missing/unverified; audio sync, 30fps frame cadence, visual fidelity and decode must be measured on actual MP4 before approval.
**Deferred work:** Build exact panel 4 vocal group and panel 6 native model zoo with deep musical group routing; run real-audio nine-panel xLights FSEQ; validate MP4 and canonical band.
**Regression risks:** Full-HD scaling changes legacy 12/16 panel composite output resolution; confirm downstream consumers and test output dimensions.


### 2026-11-17 — Native model zoo fixture generator (panel 6)
**Goal:** Start implementing panel 6 as a broad native xLights model showcase with meaningful musical grouping rather than another singing-tree panel.
**Changed files/modules:** tools/layout_bench/generate_layouts.py; tests/test_nine_panel_gate.py.
**Preserved behavior:** Original 16 fixture builders, canonical snowman band, approved drummer, panel order, sequencing engines and 16-panel renderer untouched. New builder appended only.
**New behavior:** build_native_model_zoo() creates 76 synthetic native xLights model objects (12 custom-style flat trees, 8 mega trees, 12 stars, 10 spinners, 16 candy canes, 8 arches, 6 snowflakes, 4 matrices) and groups by model family, left/right, foreground/background and melodic/rhythmic roles. Added generator to BUILDERS and regression test for diversity and group memberships.
**Tests/evidence:** Commits b096c6813bb250b27966dac292aa9c6a22ba8fbc and 3011994914e23c03ad8636ed1caa678385b29496. Code committed; tests, fixture generation and native xLights import/render NOT yet run.
**Limitations:** Fixture manifest and XML are not regenerated or committed; panel 6 remains missing in nine_panel_lock.json. Models use common xLights native display types, but custom-style flat trees are not verified as xLights Custom model type. Engine routing into new groups remains unverified.
**Deferred work:** Run generator and parser, inspect generated XML/model counts, verify xLights native import, add spiral/custom models and more complex nested groups, wire verified fixture ID into locked nine-panel manifest, test real audio and native FSEQ output.
**Regression risks:** New builder runs during build_all; ensure xLights parser accepts all model definitions and channel mapping before enabling CI-wide fixture regeneration.


### 2026-11-17 — Model zoo parser roundtrip and focused CI
**Goal:** Exercise new panel 6 generator through XML serialization and Helix model parsing, and run nine-panel lock tests in GitHub Actions without touching concurrent development branches.
**Changed files/modules:** tests/test_nine_panel_gate.py; .github/workflows/nine-panel-layout-bench.yml.
**Preserved behavior:** Existing renderer, engine, canonical drummer, original fixture generation and all other workflows unchanged.
**New behavior:** Regression test generates native model zoo XML and template in a temporary directory, parses stats, verifies 76 models, group count, channel count and template existence. Branch-scoped focused CI runs pytest, structural gate and expected fail-closed approval gate.
**Tests/evidence:** Commits 17b3ee2e9ff045f7d2b3ac33e77a8de4956f2318 and 97fb2b021087f0274145091469feb584f8518d15. CI trigger added; no successful CI result or native xLights import yet confirmed.
**Limitations:** Parser roundtrip is not proof xLights accepts all models; no generated fixture XML committed or real FSEQ/MP4 render.
**Deferred work:** Review CI results and repair failures, regenerate/commit verified panel 6 fixture, add authentic Custom models, verify native xLights, finish other missing panels and audio.
**Regression risks:** CI may expose parser or dependency failures; new workflow runs only on this branch.
