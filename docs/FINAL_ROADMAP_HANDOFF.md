# Final roadmap and release handoff

Updated 2026-10-20 (startup recovery milestone). Status is evidence-based.
Statuses: [ ] not started; [~] in progress; [x] completed and verified; [!] blocked; [-] intentionally retired.


## Current execution checkpoint — tested acceptance integrated without interrupting native build
- Recovery branch now contains the startup/process/REST fix, cached wxWidgets runtime restoration, headless loader diagnostics, and stricter musical-activity/exact-source acceptance. This commit intentionally uses `[skip ci]` to leave the healthy renderer installation/build in run39467730818 intact.
- Tested acceptance source: `1c471c41564fef5df047387513ace640b289dfa4` on `work/native-acceptance-evidence-20261020`; [focused run 39468604731](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39468604731), job118786433373: **24 unittest cases passed (0.039s), 32 pytest cases passed (1.63s), Python compile and workflow YAML parsing passed**.
- Current integration changes the candidate checkpoint documentation only; the runtime/verification code is the tested candidate code. Full current-HEAD native output and release acceptance remain **unverified**.
- Active native run: [39467730818](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39467730818), source branch head `0a2fcebd63314db906c3f112560c24bcc42f307f`, actual PR checkout `0c6f89a`; preflight24+7 passed. Render job118783981953 was still in “Install checksum pinned native xLights” at 17:44 UTC. Do not cancel healthy compilation. No new accepted MP4 exists yet.
- The run above uses the older permissive artifact verifier. Even if its consumer turns green, that is **not** proof of the stricter current verifier, independent backing vocals, or current integration SHA.
- BAND02 implementation is tested: transported XSQ must contain actual timed musical effects for each of six performers; BODY, idle pose banks and MOUTH_rest cannot substitute. The source visibility audit also excludes rest from active mouth counts.
- PROV01 implementation is tested: checkout exact source head, assert actual git HEAD, write source_commit in manifest + PROVENANCE, require consumer --expected-commit. Missing/earlier/mismatched identity fails.
- VOC01 remains unresolved: retained E14 harmony lane is entirely at rest. A current final-band check is expected to refuse acceptance until actual source-backed activity is present. Do not fabricate second vocals or claim inferred identity as verified separation.
- KEY01 remains unresolved: source contact counts show gaps; no untested choreography alteration was introduced.
- Source audit findings and hardware/device limits are retained below. New native media, six-layout/full-song assets, measured real-audio profiling and physical runtime validation are unfinished.

### Exact continuation after the healthy native run completes
1. Fetch the recovery branch and record actual `git rev-parse HEAD`; read AGENTS.md and MASTER_TODO.md. The commit containing this checkpoint is the integrated acceptance milestone; its parent is `0a2fcebd63314db906c3f112560c24bcc42f307f`.
2. Inspect run39467730818, native-runtime-libraries.log, native_headless.log and native_startup_health.json. First establish loaded binary, then genuine active FSEQ, then live GUI/REST after dismissal, then genuine HD MP4. Record exact failure if any.
3. Do not silently use that earlier-source run as current proof. After it finishes, dispatch a fresh producer at the current recovery branch; with authenticated gh:
   `gh workflow run fresh-real-band-mp4.yml --repo ryankorkowski-boop/helix-sequencer --ref codex/eight-hour-recovery-20261019 -f archive_file_id=1XZTghW96Adc27iL4b_7Vi8kBJQzLCM1j -f archive_sha256=604107acea8e57e8e5436b6bcbcb6f584806a4bed3a85679f72295d340c37b10 -f audio_sha256=8905fcaf105faf5016608517cf2d8a798d1809d8e615f1d4f5bca58e0c0b1171`
4. Run its matching consumer:
   `gh workflow run beta-completion-native.yml --repo ryankorkowski-boop/helix-sequencer --ref codex/eight-hour-recovery-20261019`.
   The consumer selects only the exact same SHA and independently checks bytes/audio/video/model activity. Missing harmony must produce an explicit failure, not rest-mouth acceptance.
5. Original audio/source hashes, native size/luma/motion thresholds and default-branch/release hold stay unchanged. For backing activity, inspect voice_roles.json/npz with the original source; independently isolated tracks or evidenced source analysis is required before claiming independent voices.
6. Continue the remaining roadmap below. Update both ledgers with actual run IDs, source SHAs, artifacts and limitations at each milestone.

**Decision remains INCOMPLETE — CONTINUE IMPLEMENTATION.** No fresh native MP4, final-band completion or physical-device approval is claimed.

## Earlier implementation checkpoints (historical; current checkpoint above takes precedence)
## Recovery result at 7f2f568 and cached-runtime follow-up
- Commit: `7f2f5686df0a888b6433e1a30c89f109d1b1c78b`; [native run 39466709677](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39466709677), PR checkout `90b4333`.
- Preflight job 118779879306 **passed**: 23 native-preview tests in 0.026s, 7 source-selection tests, compileall. Includes seven new safe-dismissal/process/REST regression cases. This verifies tests, not real GUI survival.
- Native render job 118780967104 **failed before GUI startup**: `Native headless render exited 127`. [Diagnostic artifact 12285522374](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39466709677/artifacts/12285522374); no accepted MP4.
- New finding from pinned upstream Makefile and reference build logs: wxWidgets shared libraries are built inside cached `wxWidgets-xlights_2026.17c/lib` but installed into `/usr/lib` during a fresh build. Restoring only xlights-src skips that installation on a new runner. The exact failed loader message was hidden inside native_headless.log.
- Follow-up change restores the cached wxWidgets installation (`sudo make -C wxWidgets-xlights_2026.17c install`, then ldconfig) before cache-hit early return; runs ldd and rejects unresolved libraries before sequence/render; uploads native-runtime-libraries.log. It preserves the cached compiled renderer and does not trigger a speculative full recompile.
- Headless failures now include the actual last 4000 log characters in the run manifest/Actions output; one added regression tests exit127 with the missing-library diagnostic. Follow-up preflight execution pending.
- Next: inspect follow-up native preflight (24 expected tests), runtime ldd report, actual headless FSEQ, then post-dismissal health and native MP4. Do not rerun 7f2f568 as proof of follow-up changes.

### Additional source audit (not full implementation acceptance)
- Production `core/effect_engine.py` defaults CLI variants to 1 (line 12789) and uses internal `_SongAnalysisCache` near line 13102. `core/audio_run_cache.py::AudioRunCache` is a separate hash-verified implementation not used by that entrypoint; evaluate consolidation only with real-audio baseline/parity evidence.
- `core/sequence_builder.py` already makes orchestration opt-in; `core/effects_orchestration_bridge.py` is a compatibility re-export, not a second engine. `effects_orchestrator_bridge.build_seed_graph` still seeds five fixed sections and defaults to 30s rather than deriving structure from audio. Do not silently enable this demo-like schedule as musical ground truth.
- Matrix intelligence CLI describes shader planning in reports. A report recommendation is not proof a native Shader effect with packaged resources was exported. Trace actual exported effects/resources before completion claims.
- Desktop license GUI, root LICENSE/NOTICE/README/COMMERCIAL_LICENSING.md and Android InfoActivity Legal content are PolyForm/separate commercial terms; existing MIT mentions describe third-party or earlier grants and must remain. Android InfoActivity exposes Instructions + Legal; full license asset also exists. Full distribution surface audit remains open.
- Desktop layout_preferences saves to user config and reloads only an existing file; Android MainActivity restores URI selections from SharedPreferences and persists granted URI access. Source presence does not establish device behavior.
- Actual native artifact verifier currently accepts any effects per model, so body/rest-only harmony could pass transport. Next acceptance fix must require non-rest mouth and actual NOTE_MIDI/STRING/drum effect lanes, while preserving the distinction from independently proven vocal sources.


## Acceptance candidate checkpoint (subsequently tested and integrated)
- Candidate branch: `work/native-acceptance-evidence-20261020`, based on `0a2fcebd63314db906c3f112560c24bcc42f307f`. Recovery branch's active [native run 39467730818](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39467730818) remains intact.
- Recovery preflight at 0a2fceb: job118783515172 passed **24 native-preview tests in 0.031s plus 7 source-selection tests**. Native job118783981953 still installing renderer; do not cancel healthy work.
- BAND02 [~]: verifier now checks actual transported XSQ lanes for non-rest mouth, NOTE_MIDI, STRING and physical drum-hit effects with positive bounded intervals; BODY/rest-only models cannot establish playing. Reports per-model musical counts and leaves independent-vocal-source verification explicitly false.
- PROV01 [~]: producer/consumer checkout the exact requested PR head SHA; producer asserts git HEAD, writes source_commit to run_manifest.json and PROVENANCE.json; consumer CLI requires --expected-commit and rejects missing/mismatched provenance.
- VOC02 [~]: source visibility audit excludes MOUTH_REST from active_mouth_parts, so 720 resting frames no longer suppress the absent-harmony warning. No vocal events or source audio are fabricated or changed.
- Candidate files: tools/verify_native_band_artifact.py; tests/test_native_band_artifact.py; tools/native_source_pose_band.py; fresh-real-band-mp4.yml; beta-completion-native.yml; native-acceptance-regressions.yml; both ledgers.
- Tests: focused candidate workflow passed at 1c471c4 (24 unittest +32 pytest); integrated at current checkpoint. Cases cover silent performer per role, rest-only harmony, zero/reversed/out-of-range intervals, missing/mismatched/invalid commit provenance, and existing source hashes/media transport.
- Integration updated: tested code is now on recovery with [skip ci] to preserve its healthy active build. After that run completes, dispatch fresh exact-SHA producer and consumer using the current checkpoint instructions above. Do not mark final-band complete if it correctly rejects silent harmony.
- Existing native producer may be compiling on cache miss; completed cache-restore step was near-instant. Do not assert cache hit without logs.
- Source-policy audit: read the current supplied model_effect_policy.py (Library version2) and helix_effect_adapter.py (version1). Both explicitly say standalone integration candidates, with native catalog validation required; direct Shader insertion lacks a packaged shader-resource guarantee. Keep their candidate status and avoid creating a duplicate production selector.



## A. Current repository state
- Branch: `codex/eight-hour-recovery-20261019`; inspected parent HEAD: `746b63f110f9dbbd5a8f2c68826317944a388e27`. The commit containing this checkpoint is the startup-recovery child of that SHA; use `git rev-parse HEAD` after fetching.
- Integration [PR #188](https://github.com/ryankorkowski-boop/helix-sequencer/pull/188): open, draft, base `feature/restructure-core`. No merge/publication authorized.
- Working tree: changes are committed atomically through GitHub Git Data API; no local checkout/runtime available in this session. Do not interpret this as a checked local clean tree.
- At inspected HEAD, core CI 39449667720, beta CI 39449667902, Windows 39449667881, Android 39449667728, license bundle 39449667741 passed.
- Last successful native producer: [39414958884](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39414958884), head lineage `ff019a902d721504e599701b7433f6a3091b8f92`; PR checkout was synthetic merge `175a50b`. Preserve both provenance values.
- Regression: `746b63f` adds unconditional `xdotool windowclose` after cooperative dismissal. Failed run's X11 tree contains only Openbox afterward; export receives connection refusal. Correlation strongly implicates destructive closure; no direct exit trace yet.

## B. Completed and verified
- [x] REC01: fetched actual HEAD, PR metadata, root AGENTS.md (only AGENTS.md found in recursive tree), canonical MASTER_TODO.md, failed job 118721373351 and successful reference job 118602350198.
- [x] REF01: successful native reference confirmed from Actions logs: median luma 24.072 (>=12), bright fraction 0.13098 (>=0.012), motion 0.921 (>=0.65), original-audio verification and native decode steps passed.
- Reference artifact: [12264050159](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39414958884/artifacts/12264050159). Historical evidence only; not acceptance of current changes.
- No new native movie or new test pass is claimed at this checkpoint.

## C. In progress
All rows use branch `codex/eight-hour-recovery-20261019`. Commit/evidence identifies inspected parent or this recovery change, not a presumed passing build.

| Task ID | Status | Description | Files | Commit | Tests | Actions | Artifacts | Blocker | Next action |
|---|---|---|---|---|---|---|---|---|---|
| NAT01 | [~] | Restore safe startup dismissal and process/REST survival | tools/native_preview.py; tests/test_native_preview_resolution.py | Recovery child of 746b63f | 7 added cases plus exact 2-command assertion; execution pending CI | Native push workflow preflight gates render | native_startup_health.json uploaded even on failure | No local runtime | Inspect preflight then native producer on recovery SHA |
| NAT02 | [~] | Genuine 1920x1080 original-audio native movie and strict visual gates | .github/workflows/fresh-real-band-mp4.yml | Recovery child | Existing HD/audio/luma/motion gates unchanged | Last failure 39449667724 | Failed diagnostics 12281386545; no MP4 in failed run | Fresh render required | Inspect successful producer logs and decoded frames |
| BAND01 | [~] | Exact-head artifact verification | tools/verify_native_band_artifact.py; beta-completion-native.yml | Present at 746b63f | Existing verifier tests; fresh consumer required | Last failure 39449667840 | None accepted for recovery SHA | Producer dependency | Check accepted-native-band at same source SHA |
| KEY01 | [ ] | Visible complete keyboard, pitched key activity, natural contact | tools/native_source_pose_band.py; source choreography | 746b63f baseline | CI 39449667850 passed; visual acceptance absent | Native producer pending | Retained source data, not approval | Failed-run audit: left contact 168/474 active frames, right 22/144 | Inspect source contact mapping and fresh decoded native frames |
| VOC01 | [ ] | Independently active backing singer with restrained lyric mouth | vocal/role analysis and native_source_pose_band.py | 746b63f baseline | No vocal ground truth claimed | Failed producer source audit available | Harmony mouth_rest=720/720, active non-rest parts=0 | Actual backing role inactive in retained analysis | Inspect role extraction before changing activity; never fabricate harmony |
| PERF01 | [ ] | Drummer/guitar/bass synchronization and independent snowman performance | source band geometry/choreography | 746b63f baseline | Drum CI 39449667963 passes; musical review still open | Fresh native pending | Historical reference only | Needs actual media review | Review instrument passages including fast kick and solos |
| AUD01 | [ ] | Recover/integrate developed unused intelligence and effects | audio/; core/; music/; effect policies | Prior ledger retained | Prior 79-test subset historical | Core CI passes at parent | None new | Current entrypoint coverage audit incomplete | Trace real sequencing entrypoint to existing analysis, styles, Meteors/Shader assets |
| OPT01 | [ ] | Representative real-audio time and memory profile | core/sequence_builder.py; audio caches | Parent already defaults 1 variant; unused sidecar opt-in implemented earlier | No new baseline/after measurements | None new | None | Local runtime absent | Profile same real source, record wall/RSS and musical output parity |
| EXP01 | [ ] | Independently editable XSQ/FSEQ plus supported dual LMS and AC safety | xlights/; lor exports; model mapping | Parent baseline | File-level checks pending fresh exports | Parent CI historical | Reference XSQ/FSEQ retained | Native import/CTB16PC hardware not established | Validate generated files/timing; document physical limits |
| LAY01 | [ ] | Layout selection persists across desktop/Android runs | layout_preferences.py; GUI/config | Prior settings recovery tested historically | Fresh persistence/runtime evidence needed | Desktop capture 39449667991 passed at parent | No new runtime package | Real-device checks absent | Inspect saved selection and missing-layout behavior |
| WIN01 | [~] | Portable EXE runtime and licensing | packaging/Windows GUI | 746b63f | CI build passed; physical Windows untested | 39449667881 success | Query current run artifacts before use | No Windows device | Review package/startup/export/offline evidence |
| AND01 | [~] | APK runtime, storage, playback, persistence | Android GUI/package | 746b63f | CI build passed; physical Android untested | 39449667728 success | Query current run artifacts before use | No Android device/emulator this session | Collect available CI checks and owner-device feedback |
| LIC01 | [~] | PolyForm Noncommercial and separate paid commercial licensing consistency | LICENSE; NOTICE; GUIs; package metadata | 746b63f | License bundle passed; surface audit incomplete | 39449667741 success | Query artifact before use | Full current distribution audit pending | Audit first-party MIT mentions; retain required third-party notices |
| SHOW01 | [ ] | Six-performer native preview | native workflow | Recovery SHA pending | Strict native checks required | NAT02 dependency | No new MP4 | Native render pending | Complete NAT02 then inspect six performers |
| SHOW02 | [ ] | Six synchronized distinct layouts | showcase pipeline | None newly verified | No acceptance | None new | None | Native core first | Generate same-passage native panels after band acceptance |
| SHOW03 | [ ] | Full-song native demonstration | source/showcase pipeline | None newly verified | 36s reference is not full-song | None new | None | Source analysis/native runtime | Use authorized original full-length source and preserve duration |
| SHOW04 | [ ] | Advertisement, teasers, highlights | promotional pipeline | Historical assets preserved | No fresh approval | None new | None | Core band acceptance first | Produce only after SHOW01; no publication |
| HAND01 | [~] | Continuous handoff and canonical ledger | docs/FINAL_ROADMAP_HANDOFF.md; MASTER_TODO.md | This recovery change | Evidence updated with every milestone | Runs to be recorded after push | GitHub tracked files | None | Append actual SHA, tests, runs and artifacts |

## D. Blocked
- Local execution: exec_command returned exactly `No usable execution environment is available. Wait for an environment to become available before using this tool.` No local tests, rendering, profiling, install or physical checks claimed. GitHub source edits and Actions remain available.
- Native failed job 118721373351 at 746b63f: `Native audio preview unavailable; retain XSQ for xLights: <urlopen error [Errno 111] Connection refused>`. FSEQ was active (720/720 frames, 33,617,814 nonzero samples); the failure occurred after GUI startup handling, before video export.
- Backing voice audit in the same job: harmony had only rest frames (720), all 9 non-rest phoneme tracks zero. Do not mark two-vocal acceptance from performer presence alone.
- Keyboard contact audit: 306/474 left-active and 122/144 right-active frames lacked source-key contact. Source estimators explicitly do not establish musical ground truth.

## E. Remaining roadmap (priority order)
1. Require passing focused preflight, live owned process + REST health, accepted native MP4 on recovery commit.
2. Require exact-SHA consumer acceptance, source hashes/audio synchronization/independent editable rows and genuine FSEQ.
3. Fix and visually verify keyboard presence/contact and independently evidenced backing vocals; preserve six performers and snowman art.
4. Audit real production musical/effect entrypoints, profile actual audio, validate exports and layout persistence.
5. Review Windows/Android/license runtime evidence and identify remaining physical validation.
6. Produce synchronized distinct six-layout and full-song native assets; then advertisement cuts.
7. Owner visual/hardware review and explicit release approval.

## F. GitHub Actions status
| Run | Source SHA | Outcome | Evidence |
|---|---|---|---|
| [39414958884](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39414958884) | ff019a9 (PR checkout 175a50b) | success | Native reference artifact 12264050159 and strict readability pass |
| [39414958924](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39414958924) | Historical ff019a9 lineage; inspect checkout before reuse | Reported successful reference; consumer details not independently re-read yet | Historical only |
| [39449667724](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39449667724) | 746b63f | failure | [12281386545](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39449667724/artifacts/12281386545), diagnostic/source archive, not a successful MP4 |
| [39449667840](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39449667840) | 746b63f | failure | Producer unavailable |
| 39449667720 / 39449667902 | 746b63f | success | Core / beta CI; runtime acceptance separate |
| 39449667881 / 39449667728 | 746b63f | success | Windows / Android builds; physical checks separate |
| Recovery child | Inspect branch HEAD | Pending push and focused preflight | Never rerun failed old SHA as proof of the fix |

## G. Validation evidence and limits
- Exact source diff: 746b63f adds only two windowclose lines to tools/native_preview.py. Recovery removes those lines and adds post-dismissal process/REST checks with persisted JSON.
- Regression suite adds: safe Escape-only fallback, healthy process+endpoint, dead process before request, connection refusal, rejected REST, death during request, production export refuses to proceed after process death. Existing dismissal test now asserts exactly two cooperative commands.
- Required preflight command: `python -m unittest discover -s tests -p test_native_preview_resolution.py -v`. Not executed locally; CI must pass before render.
- Historical metrics above are verified from logs, not a fresh quality claim. Frame review, backing-source accuracy, physical controller/device performance and full-song assets remain open.
- Source audio identity remains SHA256 `8905fcaf105faf5016608517cf2d8a798d1809d8e615f1d4f5bca58e0c0b1171`; archive identity and renderer pin remain unchanged.

## H. Next Agent Starts Here
1. `git fetch origin codex/eight-hour-recovery-20261019 && git switch codex/eight-hour-recovery-20261019 && git pull --ff-only`; inspect `git rev-parse HEAD` and `git status --short`.
2. Read root AGENTS.md, MASTER_TODO.md, then this current checkpoint; older text below is retained history.
3. Run `python -m unittest discover -s tests -p test_native_preview_resolution.py -v`; broader installed-runtime suite: `python -m pytest tests/test_native_preview.py tests/test_native_preview_resolution.py tests/test_native_band_artifact.py -q`.
4. Inspect latest branch fresh-real-band-mp4.yml run. Do not queue duplicates or cancel healthy work. Preflight is a dependency of render.
5. Inspect native_startup_windows.json + native_startup_health.json + native_gui.log, ffprobe, readability and native artifact provenance. Require alive process and responding REST after dialog handling.
6. Inspect beta-completion-native.yml accepted-native-band consumer for exact producer SHA. Record run URLs/artifact IDs and results in this file and MASTER_TODO.md.
7. Continue KEY01/VOC01 while rendering; start with source audit counts above. Preserve estimator uncertainty and never invent backing-vocal events.
8. Keep release hold until all actual acceptance requirements are evidenced.

## I. Last Known Good
| Subsystem | Last evidence | Limits |
|---|---|---|
| Native startup / native MP4 / visibility | ff019a9 producer 39414958884 | PR checkout 175a50b; earlier footage only |
| Core and beta CI | 746b63f runs 39449667720 / 39449667902 | CI cannot establish artistic quality |
| Windows and Android packaging | 746b63f runs 39449667881 / 39449667728 | No physical-device validation claimed |
| License bundle | 746b63f run 39449667741 | All GUI/distribution surfaces still require audit |
| Keyboard focused regression / drum benchmark | 746b63f runs 39449667850 / 39449667963 | Contact/real-song ground truth remains open |
| Backing vocal acceptance / six-panel full-song showcase | No completed current evidence | Must continue implementation |

## J. Final release decision
**INCOMPLETE — CONTINUE IMPLEMENTATION**

No release/default merge, publication, public music distribution, physical-device success or fresh MP4 acceptance is implied by this milestone.

---

# Retained earlier handoff (historical; current checkpoint above takes precedence)

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
