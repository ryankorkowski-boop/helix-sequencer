# Beta 1.4 live handoff

Updated: 2026-11-26

Branch: `integration/beta14-recovered-logic-20261126`
Pull request: https://github.com/ryankorkowski-boop/helix-sequencer/pull/264
Not merged. Not a public release. Visual quality is not approved.

## What was already on this branch

ChatGPT's recovered engine is the production engine. It already contains Demucs/RoFormer review wiring, short-note spatial routing, the palette fix, birdsong, and Beta 1.4 version `1.4.0-beta` (versionCode 10). `feature/restructure-core` is a different history. Its package run was cancelled so it is not presented as this build.

## What failed on the current applications

- Android API 30 and API 36 compiled the APK, then instrumented tests failed. The instructions page no longer started with "Your first Helix show". Sequencing exited because Demucs was required and is not on the phone.
- Windows Portable GUI built `HelixCLI.exe`, then `tools/portable_worker_smoke.py` timed out at 600 seconds inside Demucs on an 8-second excerpt.

## What this commit changes

- `HELIX_REQUIRE_NEURAL_STEMS=0` selects labeled diagnostic HPSS. It does not claim Demucs or RoFormer output. Desktop production still requires Demucs when that variable is unset.
- Android sets the variable before `run_profile`. The portable smoke sets it for the packaged worker so the EXE test can finish without downloading weights.
- Whisper runs only when the stem source is Demucs or Moises.
- The instructions asset again starts with "Your first Helix show" and names Beta 1.4 on the next line.

## Local evidence

`tests/test_neural_stems_required.py`: 5 passed.
A 3-second local run with the variable set wrote `source,v27.3.xsq` (874 effects placed, diagnostic stem label in the log). Preview encoding stopped here because `imageio` is not installed in this sandbox. That is not an APK or EXE artifact.

## Still not delivered

No new Android APK or Windows zip exists for this commit until GitHub Actions finishes. Do not use the earlier failed artifacts or the cancelled `feature/restructure-core` package as Beta 1.4.
