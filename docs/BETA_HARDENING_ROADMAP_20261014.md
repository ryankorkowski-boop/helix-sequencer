# Helix Beta v1.0 — executable completion roadmap

Status: NOT RELEASE READY. This branch stacks on PR #147; do not merge until verified.

## Gate 1: engine hardening
- [x] Guard recording-calibrated kick recovery against undersized windows and silent references (PR #148).
- [x] Add focused regressions for these cases.
- [x] Run the four focused regression tests on an isolated local copy of the two GitHub files: 4 passed after the minimum-duration correction (SciPy 1.17.0, NumPy 2.3.5, pytest 9.0.2). This is not a full repository or GitHub Actions run.
- [x] Focused regressions are included in clean c56a097 full CI: 1,525 passed/5 missing-fixture skips on Python3.11/3.12, run38689830938.
- [x] Full Python 3.11/3.12 GitHub CI regression audit succeeded for commit 15e2155e (run 38620436019, all four jobs success). Exact test counts not extracted from job logs.
- [ ] Review 137 uncertain tom events against isolated source/audio evidence; abstain rather than fabricate labels.

## Gate 2: musical and band acceptance
- [ ] Validate two independent singer stems against the opening duet; do not infer separation from mixed vocals.
- [ ] Inspect source-bound kick, keyboard, xylophone, synth, bass and guitar passages at issue #144 timestamps.
- [ ] Verify two six-performer stages and exact 3,603-frame sampler exports without distributing uncleared audio.

## Gate 3: native output
- [x] Native xLights2026.18 proof on c56a097 passes keys, both native bands/drummers and4,800CTB16PC intensities; run38689830974.
- [ ] Re-run six-layout comparison and giant layout import and check native channel allocations.
- [ ] Record physical controller/LOR verification as blocked until hardware/vendor software is available.

## Gate 4: app integration
- [x] Windows and Android workflows succeeded on commit 15e2155e (runs 38620436215 and 38620436180, API30/API36 jobs passed); artifact hashes and on-device verification still pending.
- [ ] Rebuild Windows and Android from the ultimate release SHA after remaining changes.
- [x] c56a097 Windows38689830954passes packaged GUI/engine, xLights/LOR and native preview; ZIP/checksum/CRC verified.
- [x] c56a097 Android38689830986passes API30/API36, MP3/WAV, full237.47s/3,562-frame preview, recovery and reinstall;0ms measured audio offset on both.
- [ ] Treat Samsung hardware and production signing as separate gates.

## Gate 5: media rights and release
- [ ] Obtain full original LightsOutTheme file and verify identity/hash.
- [ ] Audit each Suno track by creation account, subscription period, download and redistribution rights; keep accounts separate.
- [ ] Package only authorized full-song videos/audio/layouts; publish an omissions ledger for others.
- [x] Build and independently verify same-SHA beta review installers ZIP, nested checksums/CRCs, guides and source receipts: d3a3d37, workflow38697129438/artifact11954249825.
- [ ] Final approved release installers and authorized full-song showcase ZIP, checksums, file sizes and extraction remain open; the review delivery does not close these acceptance gates.
- [ ] Resolve contributor/asset relicensing authority and acceptance before final public release.

## Evidence policy

Final October15 software receipt: evidence/72h_completion/validation_receipt.json
and MASTER_TODO.md. Earlier pending log entries are historical, superseded for
these software checks. The six-layout source cues pass native rendering; the
requested real-audio comparison/full-song showcase movies and their track rights
remain separate open gates. Final approved release packaging is still outstanding.
Each checkbox requires a concrete source SHA and artifact or test receipt. Synthetic fixture results are not evidence of original-song recognition. Do not mark a missing audio/hardware/legal gate green. Preserve default branch and historical MIT/third-party notices.

## Running implementation log

- 2026-10-14 — Started persistent evidence-gated checklist on this branch. PR #148 includes two kick-recovery protections and two regression cases. Neither a successful CI receipt nor full-suite test receipt has been obtained; these remain unchecked.
- 2026-10-14 — Native CI workflow edit attempted but blocked by the write safety gate; no workflow change claimed. Next action: run focused tests on exact HEAD using a permitted execution environment, then full CI, and update this ledger with concrete run links and failures.

**Checklist maintenance rule:** Append each implementation commit, exact test outcome, and remaining blocker to this file as work progresses. Never mark a gate complete from a plan, attempted tool call, or prior-source test receipt.

- 2026-10-14 — Local focused execution: initial 3 passed / 1 failed; tiny 0.1ms review window did not abstain because filter context padded it. Added explicit minimum 60ms attack/decay review duration and adjusted regression. Re-execution: 4 passed in 3.14 seconds on isolated copies of the two GitHub files. Source commits 3f01e877 and 0bbff6d0. Full checkout/CI still pending.

- 2026-10-14 — GitHub Actions detected on checklist commit 6b870085: Helix CI run 38620251217, Helix Beta CI 38620251177, Android 38620251324, Windows 38620251302, compliance 38620251183 and birdsong 38620251198. All were queued/pending when queried; no success or artifact claim. Native proof workflow not observed in this commit's PR-triggered run listing. Exact repository checkout from local container was blocked by DNS/network, so do not misrepresent isolated test copy as a clean checkout.

- 2026-10-14 — Exact commit 15e2155e GitHub Actions all green: Helix CI 38620436019 (3.11/3.12 regression and lint), Android 38620436180 (API30/API36), Windows 38620436215, Beta smoke 38620436106, birdsong 38620435989, compliance 38620436164. Prior commit 6b870085 jobs had seven cancellations and five successes, superseded by these completed runs. Native xLights proof still unverified on this branch. The newer checklist-only commit itself does not alter application source.

- 2026-10-15 — User requested fresh 180-second band/stage MP4 using audio from Android local file `Helix_Band_With_Singers_Same_Sampler-1.mp4` (October 13, 2026, 1280×720, 20fps, H.264/AAC, 109MB). Only screenshot metadata supplied, not media bytes. Prior original sampler SHA256 recorded in docs/BETA_FINAL_COMPLETION_20261014.md, but no playable source audio or requested MP4 accessible in this execution container. Workflow `.github/workflows/beta-completion-native.yml` has a `workflow_dispatch` trigger but automatic push is scoped to the earlier completion branch and its proof is a synthetic/native diagnostic, not a newly rendered 180-second band movie. Thus latest-code movie/audio identity cannot be confirmed and no new MP4 or bundle is claimed. Await actual MP4 or WAV upload (or accessible rendered artifact) and an executable render pipeline before marking complete.

- 2026-10-15 — Continued in codex/72h-completion-20261015 from183057f. Integrated PR149 physical contracts, implemented the opt-in actual-source-addressed CTB16PC XSQ/LMS exporter, and connected hardening/engine changes to native verification plus fresh platform builds. Full localPython3.12 suite:1515passed,5missing-2.wav skips,36warnings,209.69s; focused49passed. Native local attempt failed GTK socket initialization, so native pass remains pending Actions. Read MASTER_TODO.md and docs/REPO_AUDIT_20261015.md for current scope and remaining external gates.

- 2026-10-15 — Continued implementation verified on d3a3d37: both PR150review
  defects repaired with actual LMS/native regressions; full Python3.11/3.12each
  1560passed/5missing-fixture skips; native38697129459and Windows38697129450pass;
  Android38697129307API30/API36full-song decode passes3562frames/237.47s/0ms offset.
  Combined installer38697129438/artifact11954249825delivered and independently
  hash/CRC/source checked. This supersedes pending software gates only. See
  MASTER_TODO.md and evidence/72h_completion/installer_delivery_receipt.json for
  exact artifacts/hashes and the remaining musical, rights, physical and release gates.
