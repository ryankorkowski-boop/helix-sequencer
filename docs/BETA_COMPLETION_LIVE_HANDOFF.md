# Unified Beta Completion — Live Handoff

Updated: 2026-11-19 UTC. Status: IN PROGRESS; no release approval. Owner rejected the nine-panel benchmark and the local Tinsel Tornado v2 16-panel pilot. Zero panels passed. The later v3 panels also looked washed out. Do not treat those videos as approval. The newest code change emits xLights modelGroup, submodel, and layer-blend XML and proves it with a 2 second xLights 2026.19 FSEQ. Read that section at the end. No approval MP4, device pass, or release.

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

### 2026-11-18 — Phone preview repair and local regression pass
Commit `9d622d67b4efc748210c0626accc8d0dd06d8a3b` on `integration/unified-beta-completion-20261117`.

**What was wrong:** `helix_mobile.render_preview` called `build_leaf_color_matrix` and passed `frame_colors` to `HouseRenderer.render_frame`. Neither exists, so every phone preview failed after the sequence and ZIP were saved. The Birdsong fixture then called `layer.remove(entries[1])` after `remove_entry` had already shifted the list, so it deleted the surviving sweep XML. Production reconciliation correctly ignored that missing element. The fixture was wrong.

**What changed:** Previews use `HouseRenderer` and 30-frame intensity windows. `EngineService` copies `preview_states`. `MainActivity` shows completed, running, pending, failed, or unavailable and plays only a completed file. `android:largeHeap="true"` is set. Desktop logs emit `preview_state: failed <name>`. The unified workflow pytest list includes the new tests.

**Workflows that actually exist:** `.github/workflows/helix-unified-beta-integration.yml` runs on push to this integration branch when `core/**`, `tests/**`, or the workflow file changes. It is the Python 3.11/3.12 focused runner. `.github/workflows/helix-android-variant-compile.yml` runs when `android/**` changes. `.github/workflows/helix-birdsong-ci.yml` is a separate Birdsong matrix and was not the gate for this fixture.

**Tests actually run:** Python 3.11.18 and 3.12.3, each `50 passed, 5 subtests passed`, for `tests/test_birdsong_engine.py`, `tests/test_android_preview_states.py`, `tests/test_preview_intensity_windows.py`, `tests/test_android_orchestrator_policy.py`, `tests/test_run_config_v2_orchestration.py`, `tests/test_sequence_builder_orchestrator_promotion.py`, `tests/test_engine_activation_audit.py`, `tests/test_sequence_builder.py`, `tests/test_effects_orchestrator_bridge.py`, and `tests/test_orchestration_xsq_reconciliation.py`. Host `javac`/`java` printed `PreviewStatusChecks ok`. No Gradle, emulator, device, native xLights, or MP4.

**Not verified:** eight playable variant videos, API 30 memory, Windows EXE, layout picker, native FSEQ, approval MP4s, owner approval. Run 44346809806 predates this commit.

**Exact next command:** After this commit is pushed, open the Actions run for `9d622d67` on Helix Unified Beta Integration and Helix Android Variant Compile. Repair a failing job before packaging an APK or rendering a native sequence. Do not mark eight-variant playback or Beta 1.4 approval complete from this source change.

### 2026-11-18 — Nine-panel MP4
Native file, checked: `/cursor/stores/self/beta14-nine-panel/nine-panel-tinsel-tornado-native-fseq.mp4`

sha256 `e55fd0e1af7a1be8ab865193e76e03ba511e0bbb3df85eaab60a76d0dd9def88`, 42076744 bytes. H.264, 1920×1080, 30 fps, AAC-LC 48 kHz stereo, container 205.76 s, 0 blackframe hits. Soundtrack sha256 `8b8caddd6c292a13995bde0e80ac66f948246bd634278ab4ade1a82163aa7086`. Nine xLights 2026.19 FSEQs and the Helix XSQ files are beside it. A simulated XSQ-timing companion is `nine-panel-tinsel-tornado-simulated.mp4`, sha256 `000b87a246fe6215f2c2ee01fa24d4d5987c70fdb6b2cc5c6777c21145454a6d`.

Panels: 16ch LOR AC, repository 256ch AC, RGB house, generated singing-face house, four-snowman bench, model zoo, moire grid, sequential groups, ultimate showcase. Panel 5 is not the canonical six-member band. This is not owner approval.

Next: replace the center panel with the canonical six-member geometry and re-render. Do not commit the audio.

### 2026-11-18 — CI for the preview repair
Commit `40dca014` finished with 15 successful checks. Push run `44406112861` passed Helix Unified Beta Integration on Python 3.11 and 3.12, including orchestration, Birdsong, drummer geometry, and the nine-panel structural gate. Android compile run `44406112855` passed Java compile, debug APK assembly, payload checks, and APK retention. Drummer ground truth `44406112840` also passed. These runs do not cover HEAD `61982611`. At inspection, that later push still had Unified Beta Integration `44412936937` and Drummer Ground Truth `44412936902` in progress. Nine-panel layout bench `44412936764` had already passed. No device playback and no owner approval.


### Beta 1.4 documentation release gate — owner directive 2026-11-18
- [ ] Update and verify Android and Windows user manuals for Beta 1.4: installation, nine bundled layout presets, audio import, AC/LOR and RGB modes, band toggle, eight-variant selection/playback/export, native XSQ/FSEQ versus simulated previews, troubleshooting, memory limits, licensing and donations.
- [ ] Synchronize in-app instructions, distributed manuals and version labels; verify scrolling and recreation on Android and package the manuals with both installers. Document only verified capabilities; explicitly label pending or experimental features.
- [ ] Record manual versions and checksums in the release artifact manifest before owner acceptance.
Mobile checkpoint: 07d1896 resets per-variant encoding progress; device verification pending. EngineService propagates preview_states and aligned paths. No merge/release.


2026-11-18: Shared instruction source expanded in 5b8f300bb62ddfbfeb44a9813363279ade62be8b with nine preset descriptions, experimental singer provenance, desktop recovery and native export guidance. Source committed; compilation, packaged manuals, checksums and device acceptance remain pending. Next: validate Android compile and desktop packaging; verify readers on devices. No merge/release.


Android manual packaging gate implemented in 442d26c3cdae90c252fd65b8926f056bfd37f5d2: APK asset must match source bytes; SHA256 and manual retained with debug APK. CI and device verification pending; Windows parity remains open.


### 2026-11-19 — Stem proof, classifier, palette, groups, six-member bench
Demucs htdemucs and Whisper small ran on a 12s excerpt of unique soundtrack sha256 `75287928c8c062bb` (Lethal Christmas Logic). Excerpt sha256 `b949e2c193ddbfa29bcd2f8ccf7532ab510f2b7b2696ae4fe66fea9f930785b9`. First Demucs pass 11.4s, second run reused the SHA cache in 1.9s. Whisper small wrote 34 CANDIDATE words in 9.9s; the second call reused the transcript immediately. The drum classifier no longer treats a missing percussive ratio as proof of a non-drum, and a mid-dominant snare is no longer erased by a weak hi-hat runner-up. `choose_palette` and geometry `auto_groups` are in the tree. The bench band stage is six snowmen with three toms and a ride. A dim musical bed fills long gaps after an XSQ is saved. Crash hands already alternate left/right with the physical crash in `test_drummer_hand_alternation.py`. No release.

Replacement nine-panel, not approval: CRF 18 H.264 1920×1080 30 fps, AAC, container 205.76 s, 0 blackframe hits. Full file 143,639,909 bytes stayed on the runner because the store rejects that size. Stream-copy parts are in `/cursor/stores/self/beta14-nine-panel/v3/`:
- part 00 sha256 `50f32776c63ac9fe9bb67f229fe228e70f6380a9db8374a79b6d331306e56935` (39,618,647 bytes)
- part 01 sha256 `5f9978edbc38f94b69b099628ccd8bdd28df0786bf6b7c9dd535816b5a392c2d` (32,586,080 bytes)
- part 02 sha256 `408e048f88288b586f3d8397d1fa6d483d9eb4e22adb404ab64d1af62622f4b8` (36,170,042 bytes)
- part 03 sha256 `a84c0908230222b30a325aef051205e43723c9a88c575d4412ec280e8ec59c5c` (35,269,360 bytes)
Simulated companion sha256 `44aa62c559667639c0924715d2e57261be8c27f2af7ce3b7593264186828ffc4`. Soundtrack sha256 `8b8caddd6c292a13995bde0e80ac66f948246bd634278ab4ade1a82163aa7086`. Demucs on that song reported kicks 195, snares 220, toms 2, ride 0. The bed kept model timing coverage near the full duration at about 19 percent. This does not replace the owner rejection of the earlier nine-panel.

### 2026-11-19 — Rejections and required neural stems
Owner rejected the nine-panel benchmark (zero panels passed) and the local Tinsel Tornado v2 16-panel pilot. Those files are not approval. Production sequencing now requires Demucs htdemucs and Whisper on the vocal stem. A missing tool raises `NeuralStemRequired` instead of analyzing the full mix. Stems and the CANDIDATE transcript cache by source SHA256. Drum hits are read from the Demucs drum stem, with kick/snare co-hit recovery only on that stem. Windows portable requirements now include torch, demucs, and whisper, and the spec no longer excludes them. Canonical six-member band, floor tom, crash-hand alternation, and vendor-dense layouts are still open. No release.

### Beta 1.4 Windows packaging checkpoint
{"spec_commit":"fe4113264617d20319df4358c34877a921e21bea","workflow_commit":"7e3339d8563d11c5c4d6bab9ff5e11d35439c3e1","workflow":".github/workflows/helix-beta14-windows-candidate.yml","status":"implemented; push build not confirmed; no packaged runtime verification","next_action":"Inspect push Actions run directly; connector commit workflow lookup covers pull-request runs only. Verify ZIP and Windows 11 runtime; no release."}


### 2026-11-19 — xLights groups, submodels, and layer blend
Commit `b706a874` on `integration/unified-beta-completion-20261117`.
The washed-out v3 panels match the musical bed. Its On effect stored an inline palette string. xLights resolves `palette` as an index into `ColorPalettes`, so the bed fell through to palette 0, which is white on the real templates. The bed now adds a dark `#1A2744` palette, points at that index, and sets `T_CHOICE_LayerMethod=Average` on its own bottom layer. Spatial effects get `T_CHECKBOX_Canvas=1` and `T_LayersSelected=1`. Those keys are the ones in xLights 2026.19 `Blending.json` and the BlendingPanel help text inside the 2026.19 binary. Overlay maps to Average and Screen maps to Highlight, because those Helix names are not xLights labels.

Layout sync now writes `type="modelGroup"` and `type="submodel"` instead of forcing every row to `type="model"`. Nested groups expand to their member models. Submodel and group positions come from geometry centroids, and the six snowmen order left to right by that X: Bassist, Keyboardist, Lead, Harmony, Guitarist, Drummer. Drummer hand mapping, Demucs, and Whisper are unchanged. PR #250 was not merged.

Evidence: `tests/test_native_layer_targets.py` plus the existing bed and spatial tests, 12 passed. xLights 2026.19 headless rendered `evidence/beta_completion/layer_blend_clip/layer-blend.xsq` to a 40-frame FSEQ (sha256 `de63bf7ff5826c86aa7cdab1f40ab5fedb4f1e380f4fc30c63a112ea2608dd50`). Snowman Band (modelGroup) lit the lead singer, Singing Face 1/Mouth (submodel) lit only the mouth nodes, and the untargeted eyes stayed at 0. SDL/ALSA had no device; the FSEQ was still written. This is not a full-song render and not owner approval.

## Unified native timing integration checkpoint
Commit `3e23a0d213dbbe024f4e4331eae1b7aea1110ea7` integrates the Infinity native timing-row recognition into the unified validator, scopes legacy phoneme indexes and ordering per timing track, and rejects non-finite timing values. PR #250 remains unmerged. Tests not executed in this checkpoint; next add regression coverage for independent tracks, native rows and NaN/Infinity, then run focused CI and verify a real native export. No device, video or release approval claimed.
