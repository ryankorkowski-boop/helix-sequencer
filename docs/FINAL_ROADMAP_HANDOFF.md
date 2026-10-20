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
| DRM01 [ ] | Original V3 drummer source review / workflow download | [39400549476](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39400549476) failed | Inspect exact failed download and preserve source ID/hash |
| AUD01 [ ] | Production analysis/effects integration and performance | Prior recovery ledger retained | Inspect current tests, entrypoints, redundant variants/decodes, Shader/Meteors assets; implement measured fixes |
| PERF01 [ ] | Six-snowman musical and visual performance | Native review absent; separate 3D workflow success does not establish native acceptance | Review fresh genuine native footage incl. drummer, guitar, bass, universal keys, two singers |
| EXP01 [ ] | Native editable XSQ, layout persistence, AC/RGB, dual XSQ/LMS | Prior focused CI passed; native imports/hardware not established | Run focused integration tests and inspect generated native files; document LOR import limits |
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
