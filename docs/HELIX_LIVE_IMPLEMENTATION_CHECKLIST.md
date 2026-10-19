# Helix live implementation checklist

## 1. Executive status summary
Recovery started 2026-10-19 09:01:49 UTC (04:01 Chicago). Fixed lookback: 2026-10-19 01:01:35–09:01:35 UTC. Default branch is **feature/restructure-core**, initial head `59f32408469e68651b853994a40f97e4745bf9b4`; `main` is a divergent older line, not the implementation baseline. Development: `codex/eight-hour-recovery-20261019`. No release merge, publication, music distribution, or production artifact replacement authorized. This checklist is the current recovery authority; MASTER_TODO.md retains the historical ledger.

## 2. Eight-hour activity timeline
- 01:50 UTC: PR178 source-event integrity validator.
- 01:56–04:07: PR179–181 universal keyboard, shorter arms, native framing, regression/readability gates.
- 03:59: PR182 PolyForm license merged before this session into default branch.
- 04:40–05:21: PR183 singing-face discovery and phoneme routing.
- 05:32–08:21: PR184 style adapter and opt-in CLI tuning.
- 08:27–08:31: PR185 public showcase archetype metadata (not native layouts).
- 08:33–08:40: PR186 desktop evidence workflow, layout persistence, standalone show-folder preparation.
- 08:45: PR187 editable model/submodel row validation.
- Four standalone policy/test artifacts recovered from conversation Library; 14-test claim not yet independently run.

## 3. Current branch and PR inventory
| PR | Branch | Retrieved head | Actual status |
|---|---|---|---|
|175|codex/fresh-real-band-mp4-20261017|a410c7a|merged; historical native renderer lineage|
|178|codex/source-event-validation-20261018|c9120d5|draft; validator standalone|
|179|codex/universal-keyboard-routing-20261018|0dc2133|draft; consolidation partly superseded by 181|
|180|codex/keyboard-arm-proportions-20261018|b63bba8|draft; overlaps 181|
|181|codex/keyboard-source-guardrails-20261018|8b26245|draft; native MP4/CI failing|
|182|codex/polyform-noncommercial-license-20261018|aaf4c56|merged into default as 59f3240|
|183|codex/auto-detect-singing-faces-20261018|5cf2e19|draft; based on old main|
|184|codex/style-engine-v1-integration-20261019|64656ab|draft; based on old main|
|185|codex/community-layout-presets-20261019|b7a7b7f|draft; metadata only|
|186|codex/gui-evidence-capture-20261019|04d0c77|draft; screenshot workflow failed|
|187|codex/xsq-editable-model-row-validation-20261019|8433c2f|draft; tests/import not yet verified here|
No recently updated non-PR issues returned by GitHub search. Full workflow inventory pagination pending (755 runs reported, first 100 inspected).

## 4. Critical blockers
- xLights executable not found on PATH in this Linux workspace; native rendering must be provisioned or use a real Actions runner.
- Windows/Android packaged app execution unavailable locally; CI build success alone is not runtime evidence.
- Preferred audio is not yet acquired.
- Recent draft PRs target divergent old main; cherry-pick focused changes rather than merging stale branches wholesale.

## 5. Master task checklist
Every row inherits branch `codex/eight-hour-recovery-20261019` and draft integration PR pending; source PRs listed separately. Latest commit starts at `59f3240`; subsequent milestone sections record actual SHAs.

| ID | Priority / status | Description / files / source PR | Dependencies | Acceptance and evidence | Blocker / exact next action |
|---|---|---|---|---|---|
|HX01|P0 [~] IN PROGRESS|Recover eight-hour activity; this document, MASTER_TODO.md|none|All accessible refs, PRs, workflows, artifacts accounted for; initial refs retrieved|Paginate Actions; inventory history|
|HX02|P0 [~] IN PROGRESS|Persistent committed checklist and handoff|HX01|Early commit plus updates at milestones|Commit now; update with every milestone|
|HX03|P0 [ ] NOT STARTED|Recover and integrate model_effect_policy.py, helix_effect_adapter.py, tests; core/effect_engine.py|HX01|14 original tests run; production call, safe native effects, integrated XSQ evidence|Recover files into scratch; inspect placement code|
|HX04|P0 [ ] NOT STARTED|Style engine native integration; core/style_engine.py, style_effect_contract.py; PR184|HX03|Same audio/layout produces measurable style differences; user overrides preserved|Inspect and cherry-pick focused commits|
|HX05|P0 [ ] NOT STARTED|Meteors and Shader settings/assets/native visibility|HX03,HX04|Valid native settings, resources, XSQ, visible native render|Find catalog/renderer contracts|
|HX06|P0 [ ] NOT STARTED|Layout detection incl. groups/submodels/AC/RGB/custom fallback; xlights/layout_sync.py|HX01|Unfamiliar mixed fixture coverage; original mapping retained|Audit parser and test diverse fixtures|
|HX07|P0 [ ] NOT STARTED|Editable XSQ rows; xlights/xsq_writer.py; PR187|HX06|No duplicate names; populated and empty models/submodels retained; native import|Inspect PR187 validator against real writer|
|HX08|P1 [ ] NOT STARTED|Layout persistence; core/layout_preferences.py, desktop/Android GUI; PR186|HX06|Validate/save/relaunch/use/change/missing-file recovery; actual apps|Integrate and test desktop; audit Android permissions|
|HX09|P0 [ ] NOT STARTED|Show-folder preparation in normal sequencing; core/show_folder.py; PR186|HX06,HX07|Layout+audio+resources, collision-safe outputs, portable references|Inspect execution entrypoints; integrate|
|HX10|P1 [ ] NOT STARTED|Public native showcase layouts separate from GUI; PR185|HX06,HX09|Eight native layouts; same song, multiple XSQs+MP4s; GUI personal layout only|Recover presets; generate native layout resources|
|HX11|P1 [ ] NOT STARTED|Real Windows GUI screenshots; tools/capture_desktop_gui.py; PR186|HX08|Actual packaged EXE behavior/persistence evidence|Inspect failed run 39224466573 and packaging|
|HX12|P1 [ ] NOT STARTED|Real Android APK screenshots/persistence|HX08|Actual packaged APK running; permissions and restart evidence|Inspect Android source and workflow 39197885676|
|HX13|P1 [ ] NOT STARTED|Licensing audit: LICENSE, metadata, GUI, packaging; PR182|HX01|Official terms checked, first-party inconsistencies fixed; ambiguities documented|Audit first-party MIT notices; preserve third-party licenses|
|HX14|P0 [ ] NOT STARTED|Singing-face production routing; PR183|HX06,HX07|Discovered face definitions receive actual timed native effects|Inspect detection/router and emitter|
|HX15|P0 [ ] NOT STARTED|Keyboard and integrity recovery; PR178–181|HX01|Role ownership/short arms/hi-hat gates pass; genuine native visual review|Recover focused commits; inspect failing CI|
|HX16|P0 [ ] NOT STARTED|Bells of Mathmas authentic XSQ/show-folder/native MP4, band+5 layouts|HX03–HX10,HX14,HX15|Exact authorized audio; native render/decode/sync/editability/inventory evidence|Acquire Drive file 1Zjyz9b-V0SdJ-p9K2FN6ryUR2H88DELG; provision renderer|
|HX17|P0 [ ] NOT STARTED|Regression tests, draft PR, final evidence|HX03–HX16|Relevant/full tests pass without exclusions; reviewable commits and linked evidence|Run focused suites then broader CI; preserve failures|

## 6. Integration dependencies
HX03→HX04/HX05; HX06→HX07/HX08/HX09/HX14; HX09→HX10; HX03–HX15→HX16; HX17 validates all. Independent modules may be worked in separate worktrees; only integration owner edits this checklist.

## 7. Test and validation evidence
Recovery test evidence: original 14 supplied policy tests PASS (0.02s), package-import adaptation and style contract/CLI tests 19 PASS (1.17s). Retrieved prior runs: keyboard focused 39197885634 success; Helix CI 39197885661 failure; native MP4 39197885669 failure; GUI evidence 39224466573 failure; editable-row Unit Tests 39225057032 success. These are historical workflow statuses, not validation of the recovery branch.

## 8. Native XSQ and MP4 artifact inventory
No new outputs yet. Do not present existing diagnostics as new deliverables. Query source-bound native run 39197885669 for failure logs/artifacts.

## 9. Windows EXE and Android APK status
Prior Windows Portable GUI 39197885629 and Android offline beta 39197885676 report success at 8b26245. Packaged runtime, persistence, and actual screenshots are unverified.

## 10. Known regressions
Native band render fails; full Helix CI fails; final band/native output verification 39197885642 fails; desktop evidence fails. Logs inspected: native export is 248x442 rather than required 1920x1080; CI has BODY KeyErrors in final native export and infinite symphony scale tests; screenshot script cannot import gui_launcher. No checks weakened.

## 11. Work completed during this session
- Fresh filtered clone, all remote branch refs fetched, default branch and divergent main established.
- PR175 and PR178–187 metadata inspected; first Actions page inspected; four supplied policy artifacts read.

## 12. Remaining tasks
All incomplete rows above remain active until verified or explicitly blocked/superseded with evidence. Release, final advertisement publication, music distribution, commercial-term expansion and replacing known-good artifacts require owner approval.

# NEXT AGENT START HERE
- Branch: codex/eight-hour-recovery-20261019; baseline 59f32408469e68651b853994a40f97e4745bf9b4. Read latest git log for checklist checkpoint SHA.
- Active source PRs: 178–181, 183–187. No integration PR yet.
- Exact next step: commit this early checklist, recover focused source commits onto this branch, run original 14 policy tests, connect policy at actual effect placement.
- Start commands: `git status --short`; `git log -8 --oneline`; `python -m pytest --version`; `rg -n 'def |insert|add_effect' core/effect_engine.py`; `command -v xLights`.
- No audio/new artifacts in workspace yet. ffmpeg available; xLights not on PATH. Windows/Android runtime absent.
- Do not merge any release branch or publish music/ads. Keep MASTER_TODO.md updated in the same change sets.

## Recovery milestone 1
Source PR183–187 changes recovered onto modern default, then native PR181 development lineage merged (460 missing commits). Original 14 policy tests independently pass. Parallel worktrees own GUI/show folder, parser/editable rows, native band regressions, public layout generator/license audit. Integration commit SHA: consult commit containing this milestone. No native render or packaged runtime acceptance yet.


## 2026-10-19 continuation — live verified gate inventory (PR #188)
This section supersedes older status assertions where newer CI evidence conflicts. Keep original historical ledger intact. Development branch remains unmerged.

### Completed and independently evidenced
- [x] HX15 partial: native band missing-BODY crash guarded at commit `469e54e`.
- [x] HX15 partial: visible consolidated piano native geometry, individual `NOTE_MIDI_*` submodels, event routing and corresponding test/proof expectations updated at `74300ee`, `b415c74`, `7f7dd0e`, `3e4dd4f`, `f6831d1`, `72dc2bd`. **Do not mark native render acceptance complete**.
- [x] Helix CI: run 39239071725 success at `72dc2bd`.
- [x] Keyboard focused regression: run 39239071744 success.
- [x] Showcase recovery guards: run 39239071726 success.
- [x] Helix Beta CI: run 39239071781 success.
- [x] Birdsong CI: run 39239071752 success.
- [x] Drum benchmark: run 39239071754 success.
- [x] Compliance/license bundle: run 39239071826 success.
- [x] Original V3 drummer real-audio review workflow: run 39239071799 success (does not certify requested final comparison).
- [x] Real animated seven-snowman workflow: run 39239071876 success (separate from six-performer keyboard deliverable).

### Blocking failures — exact follow-up
- [ ] **P0 native final band proof**: run 39239071737 failed. Inspect `native-proof-acceptance.json` artifact and complete native-output acceptance, not just unit tests. Ensure keyboard source event timing and independently editable model/submodel tracks.
- [ ] **P0 six-snowman real-audio MP4**: run 39239071802 preflight passed, render failed. Inspect uploaded `helix-fresh-original-audio-six-snowmen-keyboard` diagnostics, repair failing real-output gate and rerender; deliver verified MP4 only.
- [ ] **P0 Windows packaged GUI**: run 39239071739 failed because `windows_portable_entry.py --helix-gui-smoke` asserts layout selection even in a clean first-run profile. Fix first-run vs persisted-layout expectations without fabricating a layout; verify EXE packaged smoke.
- [ ] **P1 Android API 30 default flavor**: run 39239071777 failed at Chaquopy `cffi==1.15.1` unavailable; API 36 google_apis flavor passed. Inspect flavor-specific requirements, remove incompatible pin only with compatible tested replacement; rerun both.
- [ ] **P1 desktop GUI evidence**: run 39239071771 failed `ModuleNotFoundError: gui_launcher`; repair module path/workflow invocation, then capture actual GUI screenshots.
- [ ] **P0 HX16 final deliverable**: authenticated Bells of Mathmas source, real native xLights XSQ and MP4 for band + five distinct layouts, audio sync, editability, six-panel comparison, owner review still outstanding.
- [ ] **P0 HX17 release gate**: rerun all failed workflows at new head, inspect artifacts and full test matrices; no merge/public release without owner approval.
- [ ] **P1 HX03–HX14**: revisit each historical checklist acceptance criterion with direct code/test evidence. CI success alone does not mark individual features complete.

### Working protocol
1. Triage the P0 native-proof acceptance artifact and real-audio render log; fix the concrete failure and commit.
2. Resolve Windows first-run smoke and desktop evidence import; verify both packaged workflows.
3. Resolve Android API 30 dependency; verify both matrix variants.
4. Produce native editable XSQ, six-panel real-audio MP4, evidence bundle and owner review.
5. Reconcile all HX01–HX17 statuses and keep this file updated after each verified milestone.
Evidence must identify run IDs and artifact names; never mark a failed workflow as passed because a different workflow succeeded.

### 2026-10-19 follow-up CI at `1bb1360`
- [x] Windows Portable GUI packaged smoke: run 39261085109 **success**, after clean-first-run preference assertion correction `1bb1360`.
- [x] Authentic desktop GUI screenshot capture workflow: run 39261086080 **success**, after script import-path fix `b317f68`. Review uploaded screenshot before claiming design approval.
- [x] Android offline beta workflow: run 39261085178 **success**. Both matrix variants must still be inspected individually before broad device-compatibility claims.
- [x] Helix CI 39261085172, keyboard integration 39261085220, Beta CI 39261085150, Birdsong CI 39261085195, drum benchmark 39261085121, recovery guards 39261085223, compliance 39261085139, V3 drummer review 39261085417, animated seven-snowman workflow 39261085124: **success**.
- [ ] **P0** Native final band acceptance: run 39261085110 **failure**. Prior proof produced 12 working diagnostic performer tracks but full-song showcase/complete-band/non-diagnostic MP4 acceptance was false; do not bypass.
- [ ] **P0** Fresh real-audio universal-keyboard MP4: run 39261085166 **failure**. Inspect renderer logs, output artifacts, and native gate; correct actual failure.
- [ ] **P0** Deliver the finished full-song six-panel comparison with audio, validated native xLights rendering and independently editable XSQ tracks; owner review required.

### 2026-10-19 native preview root cause / regression protection
- [x] Identified xLights 2026.18 REST `exportVideoPreview` ignoring requested 1920x1080 and returning a 248x442 docked House Preview in run 39261085166.
- [x] Commit `5f2f56b`: inspect actual *native-silent.mp4* video stream dimensions before audio mux or success status. Report requested/actual dimensions and reject mismatch; do not silently upscale GUI frames.
- [ ] **ROOT CAUSE STILL OPEN**: obtain a genuine 1920x1080 native House Preview export from xLights (reconfigure docked preview/window layout or use a supported native export API). Verify by ffprobe before muxing, then rerun real-audio six-snowman workflow.
- [ ] Add focused automated tests for native resolution mismatch and correct-size success paths; rerun CI. Do not call the MP4 fixed until genuine 1920x1080 native output passes.

### 2026-10-19 xLights resolution rerun
- [x] Run 39275234883 confirms 248x442 native export persists after targeting xLights window; guard correctly rejects before mux (`status=fallback`).
- [x] Initial native-preview stream tests committed as `4acc102`.
- [ ] **P0** Find supported xLights 2026.18 REST export resolution parameters or configure the native House Preview resolution via xLights itself. Do not assume GUI 2026.16 resolution selector is honored by REST automation.
- [ ] **P0** End-to-end verified 1920x1080 native MP4 with original audio; still blocked. No approval artifact exists.

### 2026-10-19 native renderer failure follow-up
- [x] Run 39288171559: source identity, xLights installation, editable XSQ regeneration and native FSEQ creation succeeded; MP4 step failed before export because wmctrl could not match a titled xLights window.
- [x] Commit d23bdf4: make wmctrl maximization best-effort; preserve strict native-resolution and audio gates.
- [x] Commit 2b634f5: capture X11 geometry evidence; commit 8cbd61c uploads it with the workflow artifact.
- [ ] Rerun native MP4 on d23bdf4 or newer, inspect native_window_geometry.txt, ffprobe actual native-silent.mp4, and determine whether the 248x442 docked-preview issue persists.
- [ ] Fix genuine native 1920x1080 export, mux verified original audio and deliver reviewable MP4; do not accept upscale or placeholder.
- [ ] Resolve final-band acceptance gate failure from run 39288171378 independently of the preview-export blocker.


## Production style integration audit — 2026-10-19
- [x] Verified `core/effect_engine.py` already maps explicit `--music-style` through `core.style_engine.style_effect_contract` into base/motion/accent settings. Explicit effect flags override style defaults; hardkor mode remains a separate AC-first route. Preserve this working behavior.
- [ ] Model-aware policy remains unverified: expected `core/model_effect_policy.py` and `core/helix_effect_adapter.py` are absent at those paths; main engine has no references to them. Recover source policy and validate at `attempt_place_effect`, after existing duration, overlap, layer and prop-rule checks.
- [ ] `tools/run_full_helix_pipeline.py` uses a fixed five-prop demonstration layout; `tools/emit_sequence_plan.py` marks output shadow-only. Neither alone establishes production XSQ integration.
- [ ] Confirm Meteors and Shader are actually selected and emitted; both exist in `xlights/effect_catalog.json` but have no literal reference in the main effect engine.
- [ ] Run two-style same-audio/layout XSQ comparison, mixed AC/RGB model rules, manual overrides and native import validation before declaring full integration.

## 2026-10-19 execution reconciliation — current authoritative status
This section supersedes stale task statuses above; the historical content is preserved. User authorization permits development commits and private review artifacts, but no release merge, public distribution, or license changes. MASTER_TODO.md is maintained as the historical change ledger; this file is the authoritative task and recovery checklist.

Latest inspected head: `3e8f21041d1c9fbaf3d8fa54d9799f13a6aff682`, PR #188. All fourteen current head workflow runs have finished; twelve succeeded and two failed. They are not stuck queued.
- Native MP4 run **39312455343**: preflight passed, render job **118265640683** failed during source retrieval. Root cause is **gdown 6.4.2 rejects --fuzzy**, not evidence of a Drive quota/sharing failure. All three attempts failed at CLI argument parsing.
- Native band proof **39312455512**, job **118265575323**: native diagnostic checks passed, showcase acceptance failed correctly: full-song false, complete-band false, no non-diagnostic MP4. Artifact **12216707771** contains diagnostic evidence only.
- Windows **39312455783**, Android **39312455452**, desktop GUI evidence **39312455836**, core CI **39312455302**, keyboard **39312455561**, drum benchmark **39312455693**, beta **39312455325**, birdsong **39312456120**, recovery guards **39312455632**, compliance **39312455530**, V3 review **39312455470**, animated band **39312455337** succeeded. These do not establish artistic approval or physical device/controller validation.
- Upstream xLights 2026.18 tag resolves to **839c0f590dc454bb7adb8a16c4dd92a70b46156e**. Source `src-ui-wx/automation/xLightsAutomations.cpp` reads width/height. `src-ui-wx/xLightsMain.cpp::ExportVideoPreview` changes canvas size and immediately reads cached getWidth/getHeight, suggesting a pending-size-event issue; this is a hypothesis until native validation. AppImage digest remains the release's published **62affb88b9a9b03cf5164974ac69bcefe35c559719d157b3364e4d4a5ab4214b**.
- Environment: direct GitHub/pip network unavailable; source fetched using GitHub connector into a **sparse local workspace**. Do not treat its local root commit as the repository's upstream history. No pytest or xLights installed locally. Native execution must use Actions; standard-library unit tests and ffmpeg are available.

Every task below inherits branch `codex/eight-hour-recovery-20261019` and PR #188. Statuses are conservative: successful compilation is not production completion.

| ID / category | Priority / status | Dependencies | Exact affected files and existing evidence | Remaining implementation / acceptance / next action |
|---|---|---|---|---|
| RC01 Critical release blockers | P0 IN PROGRESS | NR01, NR02, SH01, QA01 | `tools/native_preview.py`, `.github/workflows/fresh-real-band-mp4.yml`; head 3e8f210; runs 39312455343/39312455512 failed | Fix source command, produce actual HD artifact, then evaluate all release gates; no release-ready claim |
| NR01 Native xLights rendering: source | P0 IN PROGRESS | exact archive identity | `.github/workflows/fresh-real-band-mp4.yml`; job 118265640683 logs reject --fuzzy | Use supported download CLI, retain archive/audio SHA256 and analysis binding; rerun real workflow. Completion requires exact source recovered |
| NR02 Native xLights rendering: dimensions | P0 IN PROGRESS | NR01 | `tools/native_preview.py`, `tests/test_native_preview_resolution.py`; prior run 39311062728 returned 248x442 | Configure native canvas and verify actual 1920x1080 before mux; test mismatch rejection and success through preview_run; no upscale |
| AU01 Audio analysis and musical intelligence | P0 NOT STARTED | source audio | `audio/drum_classification.py`, `tools/native_source_pose_band.py`; drum CI 39312455693 passed | Audit production instrument/phrase/lyric paths with real audio; ground-truth timing, false-trigger and fallback evidence still required |
| EF01 Effect and style engines | P0 NOT STARTED | layout classification | `core/effect_engine.py`, `core/style_engine.py`, `xlights/effect_catalog.json`; commits 280cf765/245db2e require inspection | Trace policy to production placement, recover missing policy files, exercise Meteors/Shader and same-audio distinct styles; native import/render evidence |
| LM01 Model detection and layout mapping | P0 NOT STARTED | source layout | `xlights/layout_sync.py`, `core/layout_preferences.py`, `core/show_folder.py` | Mixed AC/RGB, groups/submodels, saved reload and missing-file recovery; inspect current code before changes |
| BP01 Band performer animation | P0 BLOCKED | NR02, AU01 | `tools/native_source_pose_band.py`; keyboard 39312455561, V3 39312455470, animated 39312455337 passed | Full six-performer snowman band review, universal keyboard natural reach, independent drums/bass/guitar and restrained singers; complete real sequence required |
| EX01 XSQ/FSEQ/LMS export | P0 IN PROGRESS | NR01, LM01 | `xlights/xsq_writer.py`, `tools/quality/native.py`; proof 39312455512 includes 22 XSQ/11 FSEQ/2 LMS diagnostics | Actual independently editable production tracks and supported dual export; LOR import/hardware and full-song render unverified |
| WI01 Windows GUI and packaging | P1 TESTED | LM01 | `.github/workflows/windows-portable.yml`; build+packaged smoke 39312455783 success | Inspect artifact and clean-install/audio/layout/export behavior; owner machine verification may be necessary |
| AN01 Android GUI and packaging | P1 TESTED | LM01 | `.github/workflows/android-offline.yml`; run 39312455452 success | Inspect each matrix job; emulator/device startup, storage, saved settings and long-run stability remain required |
| LI01 Licensing and distribution | P1 NOT STARTED | owner-approved terms | `LICENSE`, `NOTICE`, GUI/packaging; compliance 39312455530 success | Audit first-party consistency and commercial interface without altering terms; preserve third-party notices; ambiguities require owner review |
| SH01 Showcase and advertisement production | P0 BLOCKED | NR01, NR02, AU01, BP01 | `.github/workflows/fresh-real-band-mp4.yml`, source Drive 1Zjyz9b-V0SdJ-p9K2FN6ryUR2H88DELG | Exact Bells of Mathmas full-song source, band+five distinct native layouts and synchronized comparison; then features/ads/teasers. E14 36s recovery is a distinct prerequisite, not full-song delivery |
| QA01 Automated tests and regression protection | P0 IN PROGRESS | implementation changes | `tests/test_native_preview.py`, `tests/test_native_preview_resolution.py`, current CI runs above | Add real orchestration resolution and CLI contract regressions; run focused tests locally when dependencies permit and Actions suites; retain existing failing acceptance |
| PF01 Performance optimization | P2 NOT STARTED | working pipeline | `tools/native_preview.py`, audio/sequence modules selected after profiling | Record real timing/memory before optimizing; no measured benchmark yet |
| DO01 Documentation and release readiness | P0 IN PROGRESS | all gates | `docs/HELIX_LIVE_IMPLEMENTATION_CHECKLIST.md`, `MASTER_TODO.md` | Keep evidence and exact next steps current; owner video review and final integration approval remain open |

## AGENT HANDOFF — RESUME HERE
**Last verified commit:** 3e8f21041d1c9fbaf3d8fa54d9799f13a6aff682 (CI inventory verified; native MP4 failed).
**Current branch:** codex/eight-hour-recovery-20261019.
**Open PR:** https://github.com/ryankorkowski-boop/helix-sequencer/pull/188 (draft).
**Last completed task:** Current-head workflow triage and upstream resolution source inspection.
**Task currently in progress:** NR01 supported gdown command, then NR02 native canvas sizing and strict resolution regression.
**Latest workflow IDs and results:** 39312455343 failure (--fuzzy unsupported); 39312455512 failure (missing showcase); twelve successes listed above.
**Outstanding blockers:** No accepted native HD MP4; full Bells source not acquired; packaged device validation absent; no local xLights/pytest/network package install.
**Files modified:** This checklist and MASTER_TODO.md for the initial reconciliation; subsequent entries must list code changes.
**Tests executed:** Initial existing resolution unittest import blocked by sparse checkout lacking tools.quality.scoring; dependency files recovered next. pytest not installed. No passing-test claim from these attempts.
**Artifacts generated:** None in this continuation.
**Artifacts still missing:** Accepted native original-audio HD MP4, full-song six-panel comparison, production XSQ/FSEQ/LMS review bundle, functional packaging evidence.
**Next five implementation actions:**
1. Replace gdown --fuzzy with supported ID/URL invocation and validate against upstream CLI contract; retain identity checks.
2. Commit focused source repair with regression coverage and both ledgers; rerun the real native workflow.
3. Inspect Openbox/window-tree evidence and actual ffprobe dimensions; fix native canvas size, never upscale.
4. Verify original-audio mux, frames/decode/editable tracks and review complete band output.
5. Continue independent style/policy/layout/export/packaging gates while native job runs.
**Exact commands or tool actions needed to resume:** GitHub get_pr_info repository_full_name=ryankorkowski-boop/helix-sequencer pr_number=188; fetch current checklist at head; fetch_workflow_run_jobs run_id=39312455343; fetch_workflow_job_logs job_id=118265640683. Full checkout: git fetch origin codex/eight-hour-recovery-20261019; git switch codex/eight-hour-recovery-20261019; python -m pytest tests/test_native_preview.py tests/test_native_preview_resolution.py -q. Sparse connector workspace is /workspace/scratch/d25d780c599d/helix-work; fetch missing imports before local tests.
**Owner approvals required:** Final release integration, public release/music/advertisement distribution and any licensing decisions. Routine development is already authorized.

### Source download repair and resolution regression — development checkpoint
- NR01 **IMPLEMENTED**, native validation pending: pinned gdown==6.4.2 and use its supported positional Drive ID. Upstream v6.4.2 `gdown/__main__.py` line 82 accepts url_or_id, line 253 routes an ID; --fuzzy is absent. SHA256, retries, source-analysis identity and archive safety checks remain strict.
- NR02/QA01 **TESTED (unit orchestration only)**: `_export_size()` always supplies 1920x1080 defaults instead of requesting no dimensions when environment variables are absent, validates even 320..4096 sizes, and shares sizing with acceptance. Corrected literal backslash-newlines in X11 diagnostics. No native-size workaround claimed yet.
- Tests: `python -m unittest discover -s tests -p test_native_preview_resolution.py -v`: **7 passed**, including production preview_run mismatch-before-mux, matching-HD-then-selected-audio mux, source preservation and persistent manifest evidence. Fixtures are mocks, never native output. `git diff --check` and compileall passed. First new orchestration fixture lacked mocked FSEQ bytes and failed; fixture corrected to emulate renderer output, acceptance unchanged.
- Files: `.github/workflows/fresh-real-band-mp4.yml`, `tools/native_preview.py`, `tests/test_native_preview_resolution.py`, both ledgers. Workflow preflight executes the seven standard-library tests.
- Latest documentation push b6fa1175 triggered broad existing push/PR workflows. Future checklist-only checkpoints use [skip ci]; one code push is necessary to validate current renderer. Do not rerun the old immutable --fuzzy failure.
- Next: inspect native run from this code commit, recover exact original source, read actual Openbox/X11 tree and native GUI log, then fix the real native size if still undersized.

### Native run 39324057707 and targeted production repairs
- **NR01 VERIFIED**: run **39324057707**, render job **118305569139**, downloaded exact original archive and validated E14 audio/analysis successfully with repaired gdown command. Native xLights installation and editable sequence regeneration passed. Local authenticated source recovery independently matched archive SHA256 **604107acea8e57e8e5436b6bcbcb6f584806a4bed3a85679f72295d340c37b10**, WAV **8905fcaf105faf5016608517cf2d8a798d1809d8e615f1d4f5bca58e0c0b1171**.
- **NR02 still IN PROGRESS**: run exported **248x602**, not HD; strict gate rejected. Openbox now works, main window is 2560x1421, and a unique native child is 248x602. X11 log provides actual target, confirming maximization alone is insufficient. Artifact **12221837144**, digest **4ef9be184a621e8851d60791818d04974fabd6bb403be61351635a1aedda5aeb**, retains XSQ/FSEQ/source/logs only, no accepted MP4.
- Native fix candidate: `_resize_native_canvas` scopes discovery to the unique fresh XSQ title, locates deepest unique child matching the actual exported size, refuses ambiguous candidates, resizes the real X11 child with xdotool, waits for wxGTK ConfigureNotify and verifies retained geometry, then requests a fresh native export. Actual ffprobe HD acceptance is unchanged. Adds xdotool to workflow. **Native rerun required; resize unit tests do not prove video success.**
- **LM01 partial TESTED**: `core/layout_preferences.py` now ignores non-object JSON settings rather than crashing GUI startup on .get. Three standard-library tests cover damaged JSON, choosing a layout after corruption, switching, missing-file recovery, and retaining other settings.
- **EF01 partial TESTED (isolated source)**: production `allowed_requested_effects_for_target` and `pick_runtime_effect` now apply AC constraints per actual model in mixed layouts, not only global AC-only mode. Learned, manual, style fallback choices cannot assign spatial RGB effects to single-color/unknown targets; RGB neighbors retain spatial effects. Five tests exercise exact production selection bodies with real Model/catalog normalizers locally; full imports and CI still required.
- Original supplied policy/adapter and fourteen tests recovered from Library read. They are conservative standalone candidates and overlap the existing production selector; not blindly wired because catalog membership alone cannot prove Shader resources/native support. Current production compatibility fix is focused; broader Meteors/Shader acceptance remains EF01.
- **SH01 source VERIFIED**: exact Drive ID **1Zjyz9b-V0SdJ-p9K2FN6ryUR2H88DELG**, filename **Bells of Mathmas.mp3**, **3,620,694 bytes**, SHA256 **beb2a064595a64d4924847ccd68ca0f2897d5de3ae5064e6e2023a68b7b8ce8a**, ffprobe **156.000000s**, 48kHz stereo MP3, start_time 0.023021. Authenticated download succeeded. Full-song analysis/native six-panel output remains unimplemented, not blocked by source permission.
- Local tests: **10 native-resolution/X11 orchestration unittests PASS**, **3 persistence recovery unittests PASS**, **5 exact-source selector checks PASS** (full-module import not claimed), compileall/diff-check PASS. Source bytes and existing strict acceptance preserved.
- Files changed in this checkpoint: tools/native_preview.py, tests/test_native_preview_resolution.py, .github/workflows/fresh-real-band-mp4.yml, core/effect_engine.py, tests/test_learned_effect_model_compatibility.py, core/layout_preferences.py, tests/test_layout_preferences_recovery.py, both ledgers.
- Next: inspect the new native run and full regression matrix from this commit; fix the actual next native failure; preserve the source identity and no-upscale gate.


## 2026-10-19 continuation — starred music priority and native build
- [x] Source patch now applies in the upstream xLights 2026.18 build; previous compile run 39335660330 reached Makefile but failed because `cbp2make` was absent.
- [x] Commit `7753408efcead0e84c61c6a872d55f9159ba2abb` adds `cbp2make`, `glslc`, and `glslang-dev` build dependencies.
- [~] Native 1920x1080 render run [39336982567](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39336982567): preflight passed; renderer compilation in progress at last observation. Do not claim MP4 success until decoded resolution, frames, music identity, and six-performer acceptance pass.
- [ ] Final native-proof run [39336982557](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39336982557) failed because `full_song_showcase_complete`, complete-band verification, and a non-diagnostic MP4 are missing. Artifact 12226723921 retains diagnostics. Keep these gates strict.
- [ ] **NEW OWNER REQUIREMENT — STARRED MUSIC PRIORITY:** Before generating preview MP4s, full-song showcases, or advertisement clips, query the owner's Helix Music Mix Drive catalog for files marked starred by the owner; prioritize eligible starred originals. For excerpts select verified high-activity portions; avoid repeats where other starred originals are eligible. Retain exact file IDs and SHA256 provenance. For a specifically requested song (e.g., Bells of Mathmas), honor the explicit selection over general starred priority. Never substitute audio if inaccessible.
- [ ] **Starred metadata integration blocked on verified Drive access:** A connected Drive search with `starred = true and trashed = false` returned no items at this checkpoint. This is not evidence that no songs are starred. Confirm Drive API permissions/metadata access or obtain a starred catalog through an authorized workflow before asserting a prioritized list. Do not guess favorites.

### NEXT AGENT START HERE — latest operational checkpoint
1. Inspect run 39336982567 render job 118349611400. If failed, retrieve full logs and fix the precise xLights compile error; if successful, verify the authentic 1920x1080 MP4 and native XSQ/FSEQ.
2. Reconcile final-proof acceptance with a genuine full-band, full-song non-diagnostic MP4, not relaxed assertions.
3. Implement starred-song metadata selection in the showcase audio catalog once Drive metadata can be verified, with explicit song requests taking precedence.
4. Complete all older HX01–HX17 tasks, update their evidence and statuses, and commit a new checkpoint before exhaustion.


### Starred source folder — verified 2026-10-19
- [x] Located owner-curated Drive folder **Starred**: https://drive.google.com/drive/folders/1TM4Yo763FnHIOkmy8V72xzLCGy5IHLxg (ID `1TM4Yo763FnHIOkmy8V72xzLCGy5IHLxg`). Connector listing returned **30 audio/mpeg files**. This folder, rather than Drive's starred metadata flag, is the priority music source for native MP4s and advertisements.
- [ ] Integrate folder-first catalog discovery in production showcase workflow; select source by Drive file ID, verify SHA256 and duration, retain source provenance. Explicit owner-selected tracks supersede folder priority.
- [ ] Detect duplicate copies by content SHA256/duration, not title alone; folder includes `Copy of ...` and original-named files, plus numbered versions of Christmas in the Ether. Do not discard distinct versions based only on name.
- [ ] Choose high-activity segments for short clips, full songs for full-song comparisons, and rotate distinct starred songs across showcase outputs. Native render acceptance still mandatory.
- [ ] Current renderer job 118349611400, run 39336982567 was in progress during this update; inspect current result before claiming delivery.


### Starred catalog implementation checkpoint
- [x] `showcase/starred_music_catalog.json` contains 30 verified audio Drive IDs from owner-curated Starred folder (commit `d203656`).
- [x] `tools/select_starred_music.py` implements deterministic rotation, used-ID avoidance, and explicit requested-ID selection (commit `8122244`).
- [x] `tests/test_select_starred_music.py` adds six focused tests (commit `74759dd`); tests are committed but their execution is not yet confirmed.
- [x] Native showcase workflow preflight now executes the focused tests and catalog selection (commit `ce38982`).
- [ ] Actual native render remains on pinned E14 archive, **not** yet driven by Starred selection. Implement authenticated download, exact audio SHA256, compatible musical analysis, and a source-agnostic band sequence before replacing pinned E14. Do not claim automatic Starred rendering is complete.
- [ ] Confirm workflow run and actual tests at new head, and continue renderer build resolution. Maintain strict 1920x1080 and complete-band acceptance.


### Starred audio source retrieval milestone
- [x] Added `.github/workflows/verify-starred-audio.yml` (commit `cac24a6`) for explicit source ID or deterministic rotation, actual Drive download, ffprobe duration/codec check, full ffmpeg decode, SHA256 provenance, and fail-closed behavior. It does not upload or redistribute audio.
- [ ] Execute workflow dispatch on branch and inspect verification artifact. Workflow has not been run yet; unauthenticated Drive access could be blocked.
- [ ] Build analysis adapter to generate genuine drum/keyboard/guitar/bass/vocal cues for arbitrary Starred audio, then produce editable XSQ and authentic native xLights MP4. E14 source-pose pipeline requires retained E14 analysis and cannot safely be fed a different song without this adapter.
- [ ] Keep restored E14 ZIP until its existing native workflow is verified or replaced by proven Starred-native workflow.


### Latest continuation
- [x] Starred selector now fails closed when all IDs have been used instead of silently recycling the catalog (commit `cbb6f1a`); added exhaustion regression test (commit `8b00c74`).
- [ ] Execute focused tests in GitHub Actions; no workflow dispatch action is exposed through the connected GitHub interface in this session.
- [ ] Native render run 39336982567 was still in the `Install checksum pinned native xLights` step at last check. Do not report completion without successful job, downloadable artifact and independent MP4 verification.
- [ ] Existing `tools/native_source_pose_band.py` uses `ReviewBandPerformance` with E14 retained analysis and drummer.xsq; generic Starred audio requires an actual source-analysis adapter. Do not relabel E14 render as Starred output.


### Starred source verification automation update
- [x] Corrected Drive retrieval to `python -m gdown --id "$SELECTED_DRIVE_ID"` (commit `b0aee10`), rather than passing an opaque ID as an inferred URL.
- [x] Configured `.github/workflows/verify-starred-audio.yml` push trigger on recovery branch changes to selector, catalog, tests, or workflow (commit `b645913`). This should start a verification job on matching pushes; its execution and success are not yet confirmed.
- [ ] Inspect the new push-triggered Starred source verification run and `source_provenance.json`; investigate Drive permission or quota failures rather than substituting media.
- [ ] Native xLights build run 39336982567 remains in install/build step at last observation; retrieve logs if failed or timed out and fix actual cause.


### Native xLights build diagnostics checkpoint
- [x] Native xLights compilation in `.github/workflows/fresh-real-band-mp4.yml` now has a 35-minute timeout, `pipefail`, tee'd `xlights-native-build.log`, and build-log artifact inclusion (commit `9115b2d`). This is a diagnostic/reliability change, **not** a claim of a successful renderer build.
- [ ] New workflow run must exercise the updated build script; the older run 39336982567 still reported `Install checksum pinned native xLights` in progress and cannot validate this change.
- [ ] Review preserved compiler output, fix any real errors, render fresh 1920x1080 MP4, verify FSEQ/XSQ/audio and visibility, and deliver actual artifact.
