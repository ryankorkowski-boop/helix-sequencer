# Helix Beta v1.0 — executable completion roadmap

Status: NOT RELEASE READY. This branch stacks on PR #147; do not merge until verified.

## Gate 1: engine hardening
- [x] Guard recording-calibrated kick recovery against undersized windows and silent references (PR #148).
- [x] Add focused regressions for these cases.
- [x] Run the four focused regression tests on an isolated local copy of the two GitHub files: 4 passed after the minimum-duration correction (SciPy 1.17.0, NumPy 2.3.5, pytest 9.0.2). This is not a full repository or GitHub Actions run.
- [ ] Re-run focused tests on a clean checkout of the exact final branch HEAD in CI.
- [ ] Run the full Python 3.11/3.12 suite and record SHA, test counts and logs.
- [ ] Review 137 uncertain tom events against isolated source/audio evidence; abstain rather than fabricate labels.

## Gate 2: musical and band acceptance
- [ ] Validate two independent singer stems against the opening duet; do not infer separation from mixed vocals.
- [ ] Inspect source-bound kick, keyboard, xylophone, synth, bass and guitar passages at issue #144 timestamps.
- [ ] Verify two six-performer stages and exact 3,603-frame sampler exports without distributing uncleared audio.

## Gate 3: native output
- [ ] Run native xLights 2026.18 output proof on the exact source revision, including all 88 keys and both drummers.
- [ ] Re-run six-layout comparison and giant layout import and check native channel allocations.
- [ ] Record physical controller/LOR verification as blocked until hardware/vendor software is available.

## Gate 4: app integration
- [ ] Rebuild Windows and Android from the same final source SHA.
- [ ] Verify desktop GUI startup, xLights/LOR mode, packaged dependencies and MP4 preview.
- [ ] Verify Android API30/API36, MP3/WAV, full-length preview, recovery and reinstall.
- [ ] Treat Samsung hardware and production signing as separate gates.

## Gate 5: media rights and release
- [ ] Obtain full original LightsOutTheme file and verify identity/hash.
- [ ] Audit each Suno track by creation account, subscription period, download and redistribution rights; keep accounts separate.
- [ ] Package only authorized full-song videos/audio/layouts; publish an omissions ledger for others.
- [ ] Rebuild and verify installers ZIP and showcase ZIP, checksums, file sizes and extraction.
- [ ] Resolve contributor/asset relicensing authority and acceptance before final public release.

## Evidence policy
Each checkbox requires a concrete source SHA and artifact or test receipt. Synthetic fixture results are not evidence of original-song recognition. Do not mark a missing audio/hardware/legal gate green. Preserve default branch and historical MIT/third-party notices.

## Running implementation log

- 2026-10-14 — Started persistent evidence-gated checklist on this branch. PR #148 includes two kick-recovery protections and two regression cases. Neither a successful CI receipt nor full-suite test receipt has been obtained; these remain unchecked.
- 2026-10-14 — Native CI workflow edit attempted but blocked by the write safety gate; no workflow change claimed. Next action: run focused tests on exact HEAD using a permitted execution environment, then full CI, and update this ledger with concrete run links and failures.

**Checklist maintenance rule:** Append each implementation commit, exact test outcome, and remaining blocker to this file as work progresses. Never mark a gate complete from a plan, attempted tool call, or prior-source test receipt.

- 2026-10-14 — Local focused execution: initial 3 passed / 1 failed; tiny 0.1ms review window did not abstain because filter context padded it. Added explicit minimum 60ms attack/decay review duration and adjusted regression. Re-execution: 4 passed in 3.14 seconds on isolated copies of the two GitHub files. Source commits 3f01e877 and 0bbff6d0. Full checkout/CI still pending.

- 2026-10-14 — GitHub Actions detected on checklist commit 6b870085: Helix CI run 38620251217, Helix Beta CI 38620251177, Android 38620251324, Windows 38620251302, compliance 38620251183 and birdsong 38620251198. All were queued/pending when queried; no success or artifact claim. Native proof workflow not observed in this commit's PR-triggered run listing. Exact repository checkout from local container was blocked by DNS/network, so do not misrepresent isolated test copy as a clean checkout.
