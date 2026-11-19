# Helix running checklist and recovery handoff

Updated: 2026-10-17. This is the **continuously maintained implementation tracker and standalone recovery handoff**.
Repository: https://github.com/ryankorkowski-boop/helix-sequencer
Working branch: `codex/showcase-pilot-recovery-20261017`
Open PR: https://github.com/ryankorkowski-boop/helix-sequencer/pull/172
Release gate: **Do not merge, publish or claim approved showcase videos without owner review and explicit approval.**

## Status convention

- [ ] Not started / unfinished
- [x] Code committed (not automatically tested or approved)
- [!] Blocked; see explanation

Each milestone records code, tests, and native validation separately. A committed implementation is not equivalent to a tested or validated release.

## Recovery and stability

- [x] Recover branch and PR context; prior checkpoint `1b16dff5f6d9f50bdec759b9ccbead3a378b3b30`.
- [x] Fix stale GUI export-selector test assertion, commit `0c0e0887bdb9abb823683f367d2563faee47f396`; test now matches the GUI's current fail-closed warning.
- [x] Create this persistent running checklist/handoff document.
- [ ] Execute focused export/GUI tests on actual checkout; **not yet run in this session**.
- [ ] Confirm latest GitHub Actions results. No workflow runs were returned for commit `0c0e088` at initial inspection; earlier workflows were queued, not verified passing.
- [ ] Run full regression/CI suite; document command, SHA, result and failures.
- [ ] Resolve cancelled/queued workflows without treating cancellation as a test failure.

## Export integration

- [x] Validated `ShowExportRequest` and export rollback contract in `core/show_export_request.py` (earlier commits).
- [x] Legacy AC-only LMS converter exists: `tools/legacy_lms_export.py`. Requires explicit controller mapping CSV; cannot claim arbitrary pixel or modern LOR format support.
- [x] XSQ/LMS/Both conversion bridge: `tools/dual_format_export.py`, CLI and tests; recent commits `9df1a10`, `96fb86d`.
- [x] Source-based GUI action to convert an **existing** AC-only XSQ into XSQ + legacy LMS, commits `36e9a9c`, `16e903f`, `2697e27`.
- [ ] Connect output selection to the **main Run Sequence Build** pipeline. Current Both selector warns and resets to XSQ; separate conversion button is not automatic dual export.
- [ ] Include and test dual export in Windows packaged GUI. Current frozen build explicitly refuses the new separate action.
- [ ] Validate rollback including sidecars and avoid deleting any preexisting user files.
- [ ] Native import of generated LMS in compatible Light-O-Rama application.
- [ ] Native import/render of generated XSQ in xLights.

## Layout, music, band, and video

- [ ] Verify custom imported xLights layout and controller mapping end to end; never guess AC wiring.
- [ ] Verify small, traditional, mega-tree, band, advanced 3D and AC16 variants are materially distinct.
- [ ] Verify AC16, RGB pixel and mixed hardware routing.
- [ ] Verify seven standalone band xmodels, individual channel budgets, drum-stick contacts, vocal phonemes and 2D/3D parity.
- [ ] Verify note/instrument/lyric analysis against source audio and native rendered output.
- [!] Native xLights showcase MP4s: no newly verified native render or final approved videos in this session. Requires real renderer, source music and artifact validation.
- [ ] Verify Windows desktop and Android build artifacts and real startup behavior.
- [ ] Owner review and approval of authentic new videos before release integration.

## Current checkpoint / next actions

**Latest implementation commit before this report:** `0c0e0887bdb9abb823683f367d2563faee47f396`. **This report's commit will become the new branch head.** Always re-fetch the current branch head before edits.

1. Check `tests/test_gui_export_selector_contract.py` and `gui_launcher.py` are consistent, then execute focused tests (`python -m pytest -q tests/test_show_export_request.py tests/test_dual_format_export.py tests/test_gui_export_selector_contract.py`).
2. Inspect `gui_launcher.py::_run_sequence`, `_run_subprocess` and resulting XSQ path before integrating automatic Both. Require verified CSV and AC-compatible output; do not fabricate conversion for RGB.
3. Inspect Windows packaging/HelixCLI dispatch before enabling dual export in frozen GUI.
4. Inspect native xLights/LOR test infrastructure and music provenance; do not substitute synthetic MP4s.

**Environment limitation:** This session can read/write GitHub via connector but has not checked out and run this repository's tests or native xLights/LOR applications. GitHub commits are real; test success and native import are unverified.

**Resume protocol:** Read this file, `docs/SHOWCASE_REMAINING_WORK_20261017.md`, PR #172, latest branch commits, and CI runs; preserve all newer work. Update this document after each meaningful implementation/test milestone, with exact SHA and failures. If blocked or time expires, commit a complete checkpoint with next command and unresolved tasks.

## 2026-10-17 continuation checkpoint
- [x] Protect preexisting LMS validation sidecar from overwrite or failure cleanup: `tools/dual_format_export.py`, commit `e1d621bb3bc508cc02b76f541c5b8450b65ebd5d`.
- [x] Add regression test for sidecar preservation: `tests/test_dual_format_export.py`, commit `9d0e163bec00b192a97fd2adcedc4d32c1eb112f`.
- [ ] Tests not executed locally or confirmed passing by CI in this session. Next: `python -m pytest -q tests/test_dual_format_export.py tests/test_show_export_request.py tests/test_gui_export_selector_contract.py`.
- [ ] Main Run Sequence Build still does not automatically export Both. Inspect actual generated XSQ path and supported effects before wiring conversion; require verified controller mapping.

## 2026-10-17 continuation: source XSQ collision guard
- [x] `tools/dual_format_export.py` now rejects the source `Performance.xsq` when it would also be the export target; commit `e06a24ae720d3b49033b9785224833069275564a`.
- [x] Regression `test_source_named_performance_xsq_is_preserved` confirms original bytes survive; commit `2c9b88897c9e02b43bfe5be776ded1eb19c9b387`.
- [ ] Tests still require execution and CI confirmation. Next command: `python -m pytest -q tests/test_dual_format_export.py tests/test_show_export_request.py tests/test_gui_export_selector_contract.py`.
- [ ] Next implementation: integrate verified mapping and dual output into the actual completed sequence-generation pipeline, with safe handling for all output paths.

## 2026-10-17 snowman pixel/AC inventory implementation
- [x] Added `models/snowman_wiring_inventory.py` with per-submodel unique pixel-node counts, AC circuit counts, geometry-position counts, and explicit unknown physical bulb/strand fields; commit `1b2eca0119e801ebeda16e8e34eaa3fe54bf3eb9`.
- [x] Added regression tests `tests/test_snowman_wiring_inventory.py` for counts, AC16 limits, and non-overwriting output; commit `94176901c46e34a0d6426bd045b1c692f3ab3d87`.
- [x] Integrated inventory creation into `tools/build_spatial_review.py::build` for snowman band layouts; JSON and CSV emitted in the native show folder; commit `409f2b734a992aee9c58bb51e074a551c1fa6344`.
- [ ] Run `python -m pytest -q tests/test_snowman_wiring_inventory.py` and actual native band build to validate generated counts and xmodel compatibility.
- [ ] Populate verified bulb-per-strand and LOR Unit/Circuit values from owner-provided hardware mapping, not from geometry. Check controller loading and electrical capacity separately.
- [ ] Inventory outputs are *not* hardware-tested or manufacturing-ready until physical wiring verification.

## 2026-10-17 inventory CI follow-up
- [x] CI path filters now include `models/snowman_wiring_inventory.py` and `tests/test_snowman_wiring_inventory.py`; dedicated pytest step added in `.github/workflows/showcase-recovery-guards.yml`; commit `67fc653d8d960d1afd41c410fc67535bb428a1fa`.
- [ ] Workflow lookup for that commit returned zero runs; do not represent the suite as passing.
- [ ] Produce actual Pixel_Band and AC16_Band inventories, inspect counts and exported xmodels, then review CTB16PC physical strand plan with verified wiring values.

## 2026-10-17 standalone snowman inventory generator
- [x] Implemented `python -m tools.export_snowman_band_inventory --output-dir build/snowman_wiring`; generates independent `pixel/` and `ac16/` JSON/CSV inventories from native seven-snowman geometry without requiring song/audio. Commit `abddb5eaa5dc4d80c477352f6a75118a687a36cc`.
- [x] Added command path to showcase CI workflow filters; commit `d2b967933377738c3d2aacd7cb1761606aecb4ec`.
- [ ] Execute standalone command in environment with Helix dependencies and inspect actual generated counts and xmodels. No execution/CI pass verified in this session.
- [ ] Physical AC bulb-per-strand values, LOR Unit IDs and circuits must come from inspected wiring, not generated geometry.

## 2026-10-17 native inventory artifact CI
- [x] Showcase CI now executes `python -m tools.export_snowman_band_inventory --output-dir build/snowman_wiring` and uploads `snowman-band-wiring-inventories` artifact, even if a later step fails; commit `b02342f5036112656fe1eef3ec319f023b14e31f`.
- [ ] CI must run and artifact must be inspected to claim actual seven-snowman pixel totals, AC circuits and model compatibility. Local runtime has no GitHub DNS/repository checkout, so no native execution result was obtained.
- [ ] Verify CTB16PC hardware circuit wiring, actual strand bulbs, load and controller mapping with owner before asserting build-ready specifications.

## 2026-10-17 GitHub-connected verification continuation
- [x] Confirmed PR #172 remains open/unmerged at head `662123e3d9d2fb34a227a85c26471d93edfabd9f` before new writes. The showcase recovery guards run `39027950978` was queued and native proof run `39027950963` was in progress when inspected; no artifacts yet. Do not claim test pass.
- [x] Inventory now refuses duplicate snowman model names before writing outputs; commit `879e45a2b5f2eca4c89f1d545606087b37adfaac`.
- [x] Added duplicate-name regression test; commit `738e44c147a8644f23c6efed9c2b95b25ba6b5a3`.
- [ ] Recheck showcase recovery CI and download `snowman-band-wiring-inventories` artifact when complete. Inspect generated JSON/CSV for actual seven roles and circuit counts.

## 2026-10-17 pixel geometry validation
- [x] Pixel inventory validates submodel IDs against `CustomModelCompressed` exported node identifiers; commit `d4594415c0cc714fd27d114191f7c6fbcf7dff02`.
- [x] Added fixture geometry and regression for undefined pixel nodes; commit `0c92d98dec428de6b97b3f7c37bc7c4b40857603`.
- [ ] CI runs were queued when checked; await native inventory artifacts and verify actual pixel totals and AC circuits before declaring complete.

## 2026-10-17 complete-band inventory gate
- [x] Standalone generator refuses inventories unless seven distinct roles (drummer, bass, guitar, piano, xylophone, lead, harmony) are present and AC variants have at most 16 submodels; commit `da6569f932397ddf6242cf50b6c64944d9e39f08`.
- [x] Regression added for incomplete band; commit `9fe54b58a73a2aca99133063f9bdae2ce5bd7739`.
- [ ] Showcase recovery runs still queued when last checked; await run and inspect generated artifact for actual counts.

## 2026-10-17 pixel ownership guard
- [x] Inventory rejects nodes appearing in multiple pixel submodels; commit `067135b9f3d13a7c375d0eead23a4dca4c8907f7`.
- [x] Regression test for overlapping ownership; commit `81134dcdd701e1dce8f090b6eec9fe8f7e7df02f`.
- [ ] GitHub Actions showcase recovery jobs still queued when inspected. Verify native seven-snowman artifact before making numerical or hardware claims.

## 2026-10-17 CI queue consolidation
- [x] Added workflow-level concurrency group and `cancel-in-progress: true` to `.github/workflows/showcase-recovery-guards.yml`, so newer PR runs supersede stale runs instead of accumulating indefinitely; commit `6022e94237a4bda1fa875830e49dfbf815f7cdb3`.
- [ ] Wait for a *completed* current showcase recovery run and inspect its snowman-band-wiring-inventories artifact. Do not infer pixel counts from code alone.
- [ ] If no runner starts, inspect Actions runner/concurrency policy and account limits before additional commits; avoid generating more redundant runs.

## 2026-10-17 current CI blocker recovery
- [x] Corrected GUI AST export-selector test (`item.value.elts` instead of `item.elts`); commit `15cb21afa44cb35fca4ed97b57d555aa328dbdde`; source inspection confirms GUI choices XSQ/LMS/Both. **New CI verification pending**.
- [ ] P0: Showcase recovery guards run `39058893880` awaits completion; obtain real seven-snowman inventory artifact, verify counts and per-role submodel ownership.
- [ ] P0: Native proof previously failed because `VALIDATION.json` and non-diagnostic MP4 were absent (run `39029072914`); produce authentic native showcase and acceptance evidence, do not relax gate.
- [ ] P0: Helix CI previously failed at SHA `c006d94`; inspect latest job logs after run completion and resolve remaining errors.
- [ ] P1: Reconcile PR #173 stage-address/original-audio fixes with PR #172 before integration; preserve release approval hold.
- [ ] FUTURE/APPROVAL-GATED: Issue #154 and dependencies #155-166 remain pending owner authorization.

## 2026-10-17 verified CI inventory evidence (run 39058926422)
- [x] Showcase recovery guards passed at `55f3d752848919c6eecaf75294045595e7a9afd2` and uploaded `snowman-band-wiring-inventories` artifact ID `12110586721`.
- [x] Inspected generated JSON inside artifact. **Pixel addressable node counts:** drummer 5,607 (10 submodels); bass 4,771 (10); guitar 5,471 (12); piano 3,143 (43); xylophone 5,371 (55); lead 2,987 (16); harmony 2,987 (16).
- [x] **AC logical circuit counts:** drummer 10; bass 9; guitar 11; piano 15; xylophone 15; lead 14; harmony 14. These sum to 88 circuits across seven separate models; none exceeds 16 per model. This is not a verified physical bulb count or controller assignment.
- [ ] P0: Native proof run `39058926434` still failed: `VALIDATION.json` absent and only diagnostic MP4 present; artifact ID `12110742428` is diagnostic evidence, **not** an accepted musical showcase. Complete original-song native render and acceptance.
- [ ] P0: Confirm current Helix CI full regression audit passes at or after `55f3d752`; status was in progress when checked.

## 2026-10-17 native acceptance pipeline diagnosis
- [x] Fixed archive verifier's incorrect root-only `VALIDATION.json` lookup; supports `native-proof/VALIDATION.json` and root location; commit `004ece73260b819fcedffe9e2329a7eafac4ba9b`.
- [x] Added regression proving nested validation is read while synthetic/diagnostic-only media still fails strict showcase acceptance; commit `aab815336b530e5921cf89c8da5c6dd706b2c836`.
- [ ] P0: Native full-band fixture (`validation/final_band_native_proof.py`) is explicitly authored diagnostic, not original-song transcription. Six sampler native proofs (`validation/six_layout_native_proof.py`) validate cue rendering but exclude soundtrack. Build original-song end-to-end band output, native render, real MP4 with synchronized licensed audio, and evidence manifest; do not set completion flags based on synthetic fixtures.
- [ ] P0: Re-run strict acceptance with `--require-showcase`; assert genuine original-song provenance and complete-band verification before marking done. Latest native proof run `39058926434` failed correctly for diagnostic-only output.

## 2026-10-17 strict acceptance schema hardening
- [x] Reject non-object `VALIDATION.json` in strict native-showcase acceptance, even if an MP4 with a non-diagnostic filename exists; fix `e6ca1c39e97f744c600df3a747ef54570774ebc0`, regression `05812e14bdd741ae2c84082fc92ff03949a81d6c`.
- [ ] Verify new regression on latest CI run; previous latest run at `ab1f92f` had queued/in-progress jobs when inspected.
- [ ] P0: genuine original-song and native full-band showcase output/validation still not produced. Do not claim release readiness based on format acceptance tests.

## 2026-10-17 MP4 evidence guard
- [x] Strict archive acceptance now rejects mislabeled MP4 files whose first bytes do not contain a valid `ftyp` container header; implementation `8f2fa3ba2c9dc7a87012a842933b1f2374a130d5`, regression `acc2423a43f4f6ed560ebea19944531c479fcf52`.
- [ ] P0: MP4 header validation alone does not prove playable audio/video or musical synchronization. Verify media streams and source provenance in native end-to-end showcase before approval.
- [ ] P0: Latest full-band native proof still must produce non-diagnostic, real-song performance video and manifest; preserve strict acceptance failure until authentic output exists.
