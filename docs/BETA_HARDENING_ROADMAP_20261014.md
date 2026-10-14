# Helix Beta v1.0 — executable completion roadmap

Status: NOT RELEASE READY. This branch stacks on PR #147; do not merge until verified.

## Gate 1: engine hardening
- [x] Guard recording-calibrated kick recovery against undersized windows and silent references (PR #148).
- [x] Add focused regressions for these cases.
- [ ] Run `python -m pytest -q tests/test_rapid_kick_recovery.py` on the exact branch HEAD.
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
