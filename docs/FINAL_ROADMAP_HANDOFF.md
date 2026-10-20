# Final roadmap and release handoff

Updated 2026-10-20. Branch: `codex/eight-hour-recovery-20261019`; inspected HEAD: `3077fb3fffbc9b0a16b22ad1850b1d1abc30eb63`; integration PR: #188.
Read `MASTER_TODO.md` and `docs/HELIX_LIVE_IMPLEMENTATION_CHECKLIST.md` for preserved history. This file records the current release gates. No default/release merge or publication authorized.

Status: [ ] not started; [~] in progress; [x] completed and verified; [!] blocked; [-] superseded with explanation. Code presence is not acceptance.

| ID / status | Task and files/subsystems | Commit / evidence | Remaining work and exact next action |
|---|---|---|---|
| REC01 [x] | Reconcile branch and latest Actions | HEAD 3077fb3; latest 20 branch runs queried; no newer HEAD | Continue checking after implementation commits |
| NAT01 [~] | Native startup dialog: tools/native_preview.py, focused tests | Run [39400549536](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39400549536), render job 118554038926: `xLights startup modal persists in X11 tree` | Implemented actual Map State/PID checks and persistent diagnostics; 16 focused tests pass. Commit and track fresh native Actions; real mapped state/MP4 still pending |
| NAT02 [ ] | Native camera/model/playback/export visibility | Same run: 720/720 FSEQ frames active; 128691 channels; 33617814 nonzero samples; mean lit 0.362818; no MP4 exported | After NAT01, run actual native export and inspect images/luminance/motion; keep thresholds |
| BAND01 [ ] | Final-band same-artifact dependency / XSQ editability / audio provenance | [39400549581](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39400549581) failed | Inspect exact job log and consumer workflow; bind to accepted native artifact |
| DRM01 [x] | Original V3 drummer source review / workflow download | Historical run 39400549476 failed gdown public-link retrieval; fresh [39413537064](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39413537064) success at f8a7b68; source authentication, 36s render and decode/sync checks passed | Artifact [12261025120](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39413537064/artifacts/12261025120); owner visual review remains; separate 3D source-art review, not native xLights |
| AUD01 [ ] | Production analysis/effects integration and performance | Prior recovery ledger retained | Inspect current tests, entrypoints, redundant variants/decodes, Shader/Meteors assets; implement measured fixes |
| PERF01 [ ] | Six-snowman musical and visual performance | Native review absent; separate 3D workflow success does not establish native acceptance | Review fresh genuine native footage incl. drummer, guitar, bass, universal keys, two singers |
| EXP01 [~] | Native editable XSQ, layout persistence, AC/RGB, dual XSQ/LMS | Prior focused CI passed; native imports/hardware not established | Run focused integration tests and inspect generated native files; document LOR import limits |
| WIN01 [~] | Windows portable build and end-user validation | [39400549704](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39400549704) success at 3077fb3 | Inspect package/runtime evidence; no physical Windows validation claimed |
| AND01 [~] | Android offline build and end-user validation | [39400549441](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39400549441) success at 3077fb3 | Inspect runtime/storage evidence; physical Android testing remains unperformed |
| LIC01 [~] | Licensing/docs/package consistency | [39400549473](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39400549473) success | Audit remaining terms/documentation; preserve third-party notices |
| SHOW01 [ ] | Fresh native preview and synchronized six-panel comparison | No accepted new native MP4 | Complete NAT02 first; generate distinct layouts using authorized real audio; ads follow owner approval |
| CI01 [x] | Historical current-HEAD core and beta CI | [39400549607](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39400549607) and [39400549680](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39400549680) success at 3077fb3 | Revalidate relevant changed code; do not rerun unchanged successful builds |
| HAND01 [~] | Permanent checklist and master ledger | This change set | Update after every milestone; commit with implementation |

## Last Known Good
3077fb3: core CI, beta CI, Windows/Android packaging, keyboard regression, drum benchmark, license bundle and separate animated 3D band workflows pass. Native MP4 and final-band verification fail. No fully accepted release candidate.

## Failed approaches and pending runs
9eb8012: wmctrl dismissal alone did not establish dialog state. 3077fb3: string presence in X11 tree incorrectly used as visibility proof. Preserve actual window-state evidence next. No active runs found in latest 20 results at start.

## Next Agent Starts Here
1. Fetch current branch; `git status --short`; read this file and MASTER_TODO.md.
2. Finish NAT01 and run `python -m unittest discover -s tests -p 'test_native_preview_resolution.py' -v` plus dialog tests.
3. Commit tested changes and this checklist to development branch; inspect the resulting native workflow run, exact job logs, state diagnostics and frames.
4. Keep native 1920x1080, original-audio identity, luminance and motion gates. Do not promote diagnostic media or claim device/hardware testing.

Decision: **INCOMPLETE — CONTINUE IMPLEMENTATION**.

## Native startup milestone validation
`python -m pytest tests/test_native_preview.py tests/test_native_preview_resolution.py -q`: **25 passed, 1 skipped, 8 subtests passed** (0.94s). Skip requires a real native manifest; this is not native-render evidence. Compileall and diff-check pass.

## Continuation at f8a7b68
- Native startup fix committed: `f8a7b68c43ddbd50061de275a0c7b8188c49dc2c`. Native run [39413537205](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39413537205), render job 118597682419, compiling pinned xLights. Preflight and authentic source acquisition pass. Do not restart for speculative changes.
- Local production-focused suite: 69 passed + 6 subtests (layout/preferences, dual export, styles, native source pose, ownership, orchestration). Additional style/geometry/inventory suite: 37 passed. No native import or hardware validation implied.
- BAND01 consumer implementation prepared in `tools/verify_native_band_artifact.py`, `tests/test_native_band_artifact.py`, `.github/workflows/beta-completion-native.yml`: only successful exact-SHA native producer, exact named unexpired artifact, independent file hashes/6 editable XSQ rows/FSEQ activity/native dimensions/decoded audio correlation and unchanged luma-motion gates. Keeps diagnostic inventory separately; does not label a 36s clip as full-song completion. Pending commit and real producer acceptance.
- AUD01 performance: default already 1 variant and per-run analysis cache exists. `core/sequence_builder.py` still ran unused orchestration sidecar unconditionally; prepared opt-in `--effects-orchestrator`, with promotion flag still enabling orchestration and disable flag taking precedence. Engine argument/output path is unchanged by default. 16 builder/bridge tests passed. Pending milestone commit and CI.
- Combined changed-code/nearby suite: 79 passed, 1 native-manifest-dependent skip, 14 subtests (3.04s). Full collection found 1874 tests plus 3 missing-torch collection errors in this local environment; full local suite not claimed.
- Local native fallback investigation: checksum release AppImage downloaded and isolated Xvfb provisioned. GTK socket creation fails `socket(): Operation not permitted`; local interactive xLights unavailable. Actions remains native execution environment.

## Confirmed native camera startup defect / next native milestone
Pinned xLights 2026.18 source (839c0f590dc454bb7adb8a16c4dd92a70b46156e) inspected: `ModelPreview` constructors start in 2D and camera3d distance -2000. `src-ui-wx/app-shell/TabSequence.cpp::LoadEffectsFile` restores default cameras near line 550, then selects saved XML 3D mode near line 700. A fresh profile therefore restores 2D, leaves 3D camera at -2000, and ignores this show's authored distance -65. `LayoutPanel::Set3d` does not restore the camera. This is a confirmed ordering defect; its quantitative contribution to prior black video still requires native output evidence.
Prepared `tools/patch_xlights_native_export.py`: restore saved default cameras after mode selection and retain genuine native dimension fix. Validated both exact patch sites against actual upstream 2026.18 checkout; 4 transformation regression tests pass. Native workflow now caches a completed build before video acceptance, pins exact upstream SHA, and uses shared push/PR branch concurrency to prevent two simultaneous 30-minute compiles. Previous source had been compiling twice (push 39413528055 and PR 39413537205); the new preflight cancels only older native runs on this same branch. Confirmed camera defect justifies superseding those builds.
V3 download hardened with three bounded attempts and unchanged archive/audio identity; gdown pinned 6.4.2. Current source-access blocker is resolved by successful fresh run 39413537064.
Latest changed-code suite: 55 passed, 1 real-native-manifest skip, 8 subtests in 2.60s. Native/consumer acceptance still pending.

## AC dual export integration milestone (prepared alongside active native build)
New `core/dual_export.py` connects mapped legacy LMS siblings to the normal `run_profile` path with `--helix-dual-channel-map CSV`. GUI Both now requests the explicit CSV and selects the existing AC On-only export path. Preflight checks every eligible model/color/start channel against the real layout, validates Unit/Circuit uniqueness and CTB16PC-compatible circuit limits, and fails before analysis on invalid maps. All conversions stage first and publish exclusively; rollback removes only newly created LMS/sidecars, preserving source XSQ and racing/preexisting files. Portable GUI uses its existing bundled normal CLI (core/tools already collected by windows_portable.spec); native Windows confirmation pending. Android Both is not implemented and RGB-to-LOR export remains unsupported.
Changed: core/sequence_builder.py, core/dual_export.py, gui_launcher.py, three focused tests, docs/DUAL_EXPORT.md and friendly guide. Evidence: **43 tests pass** across new pipeline/GUI behavior, actual generated XSQ/LMS timing and metadata, rollback/race preservation, existing export, GUI integration and builder suites. Real LOR application import/hardware tests remain open.
Full regression started before these GUI edits finished: 1901 passed, 6 skipped, 1 obsolete GUI assertion failed because that test had been loaded before the implementation changed. Re-run the full suite on the finished tree; do not call that mixed-snapshot run a pass.
Licensing audit: root LICENSE/NOTICE/COMMERCIAL_LICENSING.md and GUI policies preserve PolyForm Noncommercial and separate paid written commercial license. First-party MIT search found only intentionally historical MIT text, a regression fixture and archived Lua attribution. Official PolyForm page reviewed; it also permits specified noncommercial organizations, so homeowner-only exclusivity is not claimed. No license terms changed.

### Verified full regression after desktop dual export
`python -m pytest -q`: **1911 passed, 6 skipped, 36 warnings, 14 subtests passed in 213.91s**. Five skips require absent fixed `2.wav` sandbox input; one requires a real native preview manifest. No test failures or exclusions. Compileall and diff-check also pass.
This tested desktop milestone is preserved on temporary integration branch `codex/dual-export-integration-20261020`, based on ff019a9, to avoid restarting the active native build. After native run 39414958884 finishes, fast-forward the recovery branch to the tested descendant (check both refs first). No default/release merge. Native result and packaged Windows runtime for this change are still pending.
