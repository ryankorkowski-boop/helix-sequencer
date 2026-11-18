# Unified Beta Completion — Live Handoff

Updated: 2026-11-17 UTC. Status: IN PROGRESS; no release approval.

## Baseline
Integration branch: `integration/unified-beta-completion-20261117`, created from PR #248 head `bb41f078a92e02ccb1980785efe1c1be741a9d16`. This is a stacked audit branch, NOT the default branch. No merge or publication authorized.
Default branch: `feature/restructure-core`. Read AGENTS.md and MASTER_TODO.md before changes. Preserve accepted drummer reference `b27e8d77a63027ed32bcf6851dcff3925472c155`, but resolve legacy four-tom contract against owner's latest exactly-three-tom requirement. Do not replace canonical six snowmen with humans or introduce xylophonist/mallet cues.

## Completed this session
- Inspected repository rules and default-branch master ledger.
- Identified missing handoff/status/manifest files on default branch.
- Inspected PRs #188, #205, #208, #217, #240 and #248 metadata; #248 is stacked on #247 and has pending CI/native proof.
- Created isolated integration branch from #248 without merging any PR.

## Active task
HBC-001: reconcile branch ancestry, code and evidence. Current status IN PROGRESS. No runtime tests executed in this session.

## Priority task ledger
| ID | Workstream | Priority | Status | Blocker / evidence | Exact next action |
|---|---|---|---|---|---|
| HBC-001 | A | P0 | IN PROGRESS | Stacked PRs, no verified execution-path matrix | Compare branch ancestry and inspect actual CLI/GUI orchestration call sites |
| HBC-002 | A | P0 | NOT STARTED | Engine participation not proven | Instrument real run and compare emitted XSQ and native FSEQ |
| HBC-003 | Band | P0 | BLOCKED | Ledger lists four toms; owner requires three; visual proof pending | Compare known-good drummer source, truths references, cue schema, and nine-cue mapping |
| HBC-004 | Vocals | P0 | NOT STARTED | Independent real harmony unverified | Inspect separation and ten-phoneme output; run real dual-vocal test |
| HBC-005 | B | P0 | NOT STARTED | Android/Windows build and runtime evidence absent | Audit band-stage render, eight variants, exports, API 30 memory |
| HBC-006 | C | P0 | NOT STARTED | Real nine-panel native output absent | Validate locked layouts and real audio, then short native render |
| HBC-007 | All | P0 | NOT STARTED | Release acceptance gates outstanding | Run regression and owner review; do not publish |

## Failures / blockers
- Default branch lacks three requested persistent evidence/handoff files (created on this integration branch).
- Legacy drummer contract conflicts with current three-tom owner directive; do not silently change geometry without oracle comparison.
- PR #248 explicitly says CI and native evidence pending; do not count its instrumentation as native sequencing proof.

## Exact continuation
1. `git fetch --all --prune`
2. `git switch integration/unified-beta-completion-20261117`
3. `git status --short && git log -1 --oneline`
4. `git diff feature/restructure-core...HEAD --stat`
5. Read `AGENTS.md`, `MASTER_TODO.md`, this handoff, and both JSON manifests.
6. Inspect `core/sequence_builder.py` and real CLI/Android/Windows entry points, plus PR #248 regression tests; run targeted tests.
7. Update all four handoff files after each milestone, with branch/commit, files, test logs, failures and next command.

## Protected behavior
No main/default-branch edits, no merges/releases/uploads without owner approval. Preserve deterministic effect timing, original AC channel compatibility, owner-approved drummer visuals, locked 3x3 nine-panel order and actual native xLights validation. Never call an unrendered preview approved.

## 2026-11-17 follow-up — production routing inspection
Read actual `core/sequence_builder.py` (529 lines), `core/effects_orchestration_bridge.py` and `core/engine_activation_audit.py` from integration branch. `_orchestration_enabled` defaults true unless `--no-effects-orchestrator`; `run_effects_orchestration` invoked at lines 407-413; `_promote_orchestrated_template` at lines 142-159 only substitutes `--template` when `--promote-orchestrated-template` is explicit AND report says invoked, XSQ written and path available. Default therefore leaves orchestration sidecar-only. This is a confirmed wiring/activation condition, NOT yet proof that final sequences are unaffected: independent effect-engine behavior still requires testing. `engine_activation_audit.py` computes `promoted_to_renderer` from invocation, sidecar, and flags rather than the effective template argument; audit status should be reconciled with actual renderer input before trusting it. Do not change default promotion blindly; preserve deterministic output and legacy behavior until real-audio regression comparison. Next action: add a targeted test proving effective `--template` propagation and audit truthfulness; run the relevant pytest suite, then a native XSQ/FSEQ comparison with the same audio and layout. No tests executed or video rendered during this follow-up.

## Implementation checkpoint — 2026-11-17
Commits `ee03ead0` and `284288e0` change only promotion audit truthfulness and its focused test. Previously `promoted_to_renderer` could be true when `xsq_written=True` and the flag was set but no `orchestrated_xsq_path` existed, while `_promote_orchestrated_template` would decline promotion. The audit now requires the path to be nonempty. This does not prove file existence or renderer use. Tests NOT executed. Next action: `python -m pytest -q tests/test_engine_activation_audit.py tests/test_sequence_builder.py`; inspect and compare effective template routing in a real audio run. HBC-001 remains IN PROGRESS, HBC-002 not started. No platform/video artifacts created.

## Continuation checkpoint — explicit routing test
Added `tests/test_sequence_builder.py::SequenceBuilderTests::test_orchestration_template_requires_explicit_promotion_and_written_path` (commit `e6c2e4cb`). Confirms expected sidecar-only default, promoted template argument substitution, explicit opt-out and missing-path guard at unit-test level once executed. Current head had no reported GitHub PR-triggered workflow runs or combined commit statuses at time of check. This is NOT a passed test or native render. Run `python -m pytest -q tests/test_sequence_builder.py tests/test_engine_activation_audit.py` in a checkout and compare actual exported XSQ/FSEQ. Do not promote by default until evidence shows no deterministic regressions.

## Input-template prerequisite discovery
Inspected `core/effects_orchestrator_bridge.py` lines 231-260. `_write_orchestrated_xsq` refuses to write a sidecar if no `--template` argument or template file is missing. This is a second gating condition before explicit promotion in `sequence_builder.py`. Next investigation must identify actual app/CLI argument construction for `--template` and whether a generated XSQ can be used as an orchestration input without circularity. No production change made; no tests/native rendering run. Maintain HBC-001 IN PROGRESS. Prior added regression test is unexecuted.

## Launcher investigation and config parity checkpoint
Source audit found Android `helix_mobile.build_args` unconditionally includes `--no-effects-orchestrator` while supplying `--template`, `--audio`, and `--layout-file`. This is a confirmed Android choreography integration opt-out; do not remove without memory/performance proof. Windows portable entry delegates to sequence_builder. Existing `tests/test_sequence_builder_orchestrator_promotion.py` covers fake-engine routing. `core/run_config_v2.RunConfig` default promotion True conflicted with actual serialization (no positive flag); corrected default False (commit `00aa7364`) and explicit True serialization (commit `34876e7e`), added tests (commit `54143fb7`). These are unexecuted. Next: run `python -m pytest -q tests/test_run_config_v2_orchestration.py tests/test_sequence_builder_orchestrator_promotion.py tests/test_engine_activation_audit.py tests/test_sequence_builder.py`; review Android resource budget and compare with opt-in on desktop. HBC-001 in progress; no verified native exports or app builds.

## Ground-truth discovery and CI execution checkpoint — 2026-11-17
Branch-scoped `.github/workflows/helix-unified-beta-integration.yml` added at commit `214d8d5` because pre-existing `unit-tests.yml` and `helix-ci.yml` push branches exclude `integration/**`. GitHub run `44213308493` (https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/44213308493) started Python 3.11/3.12 focused regressions and was IN PROGRESS at inspection; **do not count as passing** until completion. The source audio and owner reference files were located via the connected Google Drive: Truths folder `1SUtLHdk1nncBrQssmBpYHUeE327Q1VJj`, containing `Aaadrummertruth.mp4` id `1qDjj8JJ3Z-rZfFUntidsnPkq5DRqOsMm`, `Aaadrummergroundtruth.mp4` id `1cPHct6XEhZM_-9x9lkCP-7tN_DfIKo7b`, `Bbb Vocalstruth.mp4` id `1FN29mXUxy5dDJ0VIn6Wy7K-4llFHzGAs`, `Bbb vocals.mp4` id `1PPPz4TbYIS0Z9D6zRHScfnQoom38ltxX`; Songs with Lyrics `1JqYbCEn0rywNJhigYEywCEtscxn6kXFc`, `Tinsel Tornado.mp3` id `1Z_WvwVcp2tOytfF63SVgJf1VUCkRpfD4`, `Phoneme Test Hook.mp3` id `1gKAW9-S6TJNuKudC_TCEv2uabx36Aszj`. Files found, not yet independently decoded/visually verified. No raw Drive audio/video copied to GitHub, no app artifacts or MP4 created. Next: inspect run 44213308493 job conclusions/logs; fix failures and rerun if necessary; visually inspect ground truth and compare before drum changes.

## Android eight-variant export checkpoint
Added Python `result.sequence_paths` list, forwarded it through EngineService checkpoint state, and added MainActivity results-page spinner for choosing and exporting any generated XSQ. LOR LMS fallback preserved. Commits `4982c173`, `c65ccdd8`, `6bd3ca30`, `de332c50`. **Unverified:** no Android compile/device test, no individual per-variant MP4 playback (still only one preview), no Windows parity verification. Must not mark eight-variant acceptance passed. Next inspect Android lifecycle/selection, Gradle build, and implement per-variant playback/export without uncontrolled RAM growth. GitHub focused CI 44213308493 Python 3.11 test step passed while overall run was still in progress when checked.

## Android picker stability and CI gates — 2026-11-17
GitHub Actions run `44213308493` **completed SUCCESS** for both Python 3.11 and 3.12 focused orchestration regression jobs. This is not a native render or Android acceptance pass. Fixed `MainActivity` variant picker to retain `selectedSequencePath` across service polling and avoid adapter recreation when paths are unchanged (commit `eff2c1d1`). Added `.github/workflows/helix-android-variant-compile.yml` (commit `a86114e2`) to compile Android debug Java with SDK 36, Gradle 8.11.1 and Python 3.10 on integration branch changes. No Android run was visible immediately after workflow-file commit. Next inspect workflow registration/run and repair compile failures; test actual 8-variant UX and per-variant MP4 generation on Android. No new MP4, APK, EXE, merge or release.

## Android compile CI setup failure and repair
Run `44214052900` failed **before Gradle** because `android-actions/setup-android@v3` called `sdkmanager tools` and the package no longer exists. This does not prove Java source failure. Removed obsolete setup action and now invoke hosted SDK `sdkmanager` directly in `.github/workflows/helix-android-variant-compile.yml` at commit `14f3d642`. Next inspect new workflow run and logs, repair Gradle/Chaquopy if needed. Android variant picker remains unverified.

## Android compile retry 2
Run `44214269832` failed before Gradle at `sdkmanager: command not found` (exit 127), despite Java/Gradle setup succeeding. Changed workflow to find sdkmanager under `ANDROID_HOME/cmdline-tools` and fail clearly if missing (commit `e89bec5c`). Check next run before claiming compilation.

## Android compilation pass and APK assembly checkpoint
Android CI run `44214343888` completed SUCCESS including `Compile debug Java sources`. This validates compilation of updated results UI but not runtime behavior or packaging. Added `gradle :app:assembleDebug` to branch-scoped Android workflow at commit `a4818a7a`, without publishing or releasing the APK. Next inspect resulting CI run, diagnose any packaging failures, then test on device; 8 playable MP4 variants and native xLights outputs remain unverified.

## Android recreation state fix
Commit `b59aaa35` saves/restores `selectedSequencePath` via Android saved-instance state. This complements poll-stable variant picker. No device test yet. APK packaging CI run `44217648117` was still in progress at last check; it predates the new state fix and must not be used as proof of this latest source. Next verify new CI and device rotation, plus all-eight MP4 playback remains unimplemented.

## Android APK clean runner plugin resolution
Run `44217648117` was cancelled by concurrency when later Android commit arrived. Run `44217769589` FAILED at Gradle plugin resolution, before Java compilation: `com.chaquo.python:17.0.0` not found in configured Google/Maven Central/Plugin Portal repositories. Added Chaquopy Maven plugin repository in `android/settings.gradle` at `97aad439`. Await new run before asserting plugin or APK success. Previous Java compile run `44214343888` passed; full APK remains unverified.

## Full Android debug APK assembly passed
Run `44217948986` PASSED both Java compilation and `gradle :app:assembleDebug` on the integration branch. This is a CI debug build, not a signed production release and not a device acceptance test. Added archive CRC, AndroidManifest.xml, classes.dex, assets and SHA-256 checks in workflow at `e625e8b3`; await next run. Do not publish or release APK without owner approval. Next: test device install/variant picker/preview, then implement all-eight per-variant MP4s and native xLights band verification.

## Android spinner listener lifecycle repair
At commit `b5b80e10`, variant spinner listener moved from repeated `poll()` registration to one-time initialization. Restored selection is explicitly synchronized after adapter refresh, reducing selection churn and unexpected resets. Prior APK integrity run `44218445981` passed all steps, but predates this fix. Next check fresh CI and test on actual device. All-eight MP4 preview/export remains open.

## Per-variant MP4 preview implementation
Commits `7a7ff384`, `275effef`, `988dd56a` implement sequential per-variant Android MP4 rendering, `preview_paths` propagation, and selected-variant MP4 play/save binding. Failed previews leave blank entries; successful XSQ outputs remain accessible. This is NOT device-verified and does not repair simulated band geometry or guarantee 8 successes. Check latest Android compile/assemble CI and test 8 variants on phone, including playback, sound sync, storage and API30 memory. Earlier APK integrity run `44218445981` passed before these changes.

## Python syntax validation gate for per-variant MP4
Commit `7ae93315` adds host Python 3.10 syntax compilation of Android `helix_mobile.py` and `helix_mp4.py` before expensive Gradle steps. Previous per-variant CI run `44219712984` was still in progress at last inspection; follow-up CI required for this change. No actual device playback verification yet.

## Multi-variant MP4 partial-success accounting
Run `44219873839` PASSED Android Python syntax, Java compile, debug APK assembly and integrity for the new per-variant preview code. Commit `c78f9595` repairs false all-success reporting: status is `partial` if fewer than all variants render, with failed filenames and counts. Await next CI and device testing. Do not claim eight MP4s passed merely from build success.

## Visible partial preview status
Commit `8a6b1c5e` shows MP4 rendered/requested count and failed variant filenames on the Android results page. Combined with `c78f9595` partial-status accounting, failed previews are now visible to owner. Pending Java CI and on-device acceptance. No native band rendering verification yet.

## Bounded preview count
Commit `97d19c23` limits Android MP4 encoding to the requested number of variants (at most eight) even if the engine emits additional XSQs. Extras remain available for sequence export. The cap reduces risk of unbounded video encoding, but sequence ordering must be checked against actual eight-variant runs; no device acceptance yet.

## Primary-first preview mapping correction
Commit `53a776a8` corrects capped preview ordering: primary XSQ renders first, remaining candidates fill the cap, while `preview_paths` retains exact original `sequence_paths` index alignment. Failed/skipped variants remain blank. CI/device testing pending; no claim of eight successful videos.

## Android acceptance artifact
Run 44247185516 PASS (syntax, Java, assembly, integrity); zero retained artifacts prevented device installation. Commit 45955934 adds debug APK retention for seven days after verification. Fresh run pending. No device acceptance or beta release claimed.

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
