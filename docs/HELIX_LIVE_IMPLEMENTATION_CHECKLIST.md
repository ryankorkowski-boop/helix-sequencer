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
