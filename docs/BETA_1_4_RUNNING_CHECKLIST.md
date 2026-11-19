# Helix Sequencer Beta 1.4 — Running Checklist and Handoff

Single source of truth for the autonomous Beta 1.4 completion session.
Updated after every milestone. If the session stops, resume from "Next actions".

- Session: 2026-11-19 (UTC). Release approved: NO. Nothing merged to `feature/restructure-core`.
- Working branch: `integration/unified-beta-completion-20261117`
- Legend: [x] done and verified · [~] implemented, verification incomplete · [ ] not started · [!] blocked

## 1. Code integration

- [x] Found that the 864-commit "216 lineage" (`codex/drummer-truths-integration-20261115`, merge base 2026-10-18) had never been integrated; merged it (43 conflicts resolved by hand).
- [x] `core/effect_engine.py`, `core/sequence_builder.py`: both sides kept. `core/audio_intelligence.py`: one stem policy (Demucs required when `require_neural_stems`; otherwise opt-in via `HELIX_USE_DEMUCS`; SHA-verified HPSS cache is labelled `local_hpss_diagnostic`).
- [x] Drummer family resolved onto the traced-polygon toolchain (chosen by full-suite comparison: 125 vs 46 failures).
- [x] Android bridge: restored `--helix-quick-clip`, `--helix-lor-source-lms`, `--helix-no-pitched-props`, `--helix-spatial-accent` (the UI sent them; the bridge dropped them).
- [x] Desktop GUI unified (xLights/LOR modes, export selector, quick clip, phone remote, arches/mega-tree processing animation, "Review variants" dialog). GUI start-up smoke passes under Xvfb from source (not from a frozen EXE).
- [x] `windows_portable.spec`: removed a duplicate `hiddenimports=` keyword that was a SyntaxError on every Windows build; regression test added.
- [~] Birdsong post-run adapter from the 216 lineage is not wired (`--enable-birdsong` maps to `--birdsong`); decide whether to restore.

## 2. Drummer (owner P0)

- [x] Nine cues: Kick, Snare, Hi-hat, Ride, Left crash, Right crash, Left tom, Right tom, Floor tom.
- [x] Snare alternates hands every strike; crashes alternate sides and use the hand on that side.
- [x] Physical ride target. The owner artwork has no ride, so pose spec v8 authors a gold ride on a boom from the left crash stand (left-hand strike). The source PNG file is unchanged; the ride is painted in memory and into the generated idle art/xmodel. Owner should confirm the placement.
- [~] Ride detection: a `ride` event stream exists in the mapper and co-hit detector; not yet measured on real songs.
- [ ] Native xLights render of the nine-cue drummer on real audio (evidence MP4).

## 3. Tests

| Tree | Python | Result |
|---|---|---|
| integration before merge | 3.12 | 19 failed, 1071 passed, 1 error |
| 216 lineage before merge | 3.12 | 21 failed, 2243 passed, 25 errors |
| unified (before ride) | 3.12 pinned | 1 failed, 2571 passed, 6 skipped |
| unified with physical ride | 3.12 pinned | 0 failed, 2573 passed, 6 skipped |
| unified with physical ride | 3.11 (`requirements-dev.txt` only) | 0 failed, 2573 passed, 6 skipped |

Existing CI ran focused subsets only, which hid the full-suite failures.
Tests changed for documented contract reasons (not weakened): nine-vs-eight drummer targets, stem guard, promotion flags, Android recovery index alignment, GUI catalog.

## 4. Not done yet (do not treat as delivered)

- [x] Version strings bumped to Beta 1.4 (`1.4.0-beta`, Android versionCode 10); packaging workflow renamed `beta-v1.4-packages.yml`.
- [~] CI: full-suite job (3.11 and 3.12) added to `helix-unified-beta-integration.yml`; `helix-infinity-layout.yml` now installs its requirements. Awaiting first CI run. The Bells workflow (PR #250 branch) still lacks `ffprobe`.
- [ ] Nine preloaded layouts (3x3) in Android and Windows. Current catalog is a union of both lineages, not the required nine; coro singing-face house, singing trees/matrices, 3D digital matrix, piano keyboard and Infinity (PR #250) are missing or provisional.
- [ ] Infinity showcase (>=10,000 elements) with `Bells of Mathmas.mp3`: prior run sequenced 10,240 models but its MP4 was a custom non-native preview and the job failed at a missing `ffprobe`.
- [ ] Multi-singer pipeline verification on real audio (separation, independent VAD, no false harmony).
- [ ] MP4 deliverables (1920x1080, H.264, AAC, 30 fps, real audio): band, singers, nine-panel, 16-panel exemplar, Infinity/Bells. NONE produced this session.
- [ ] 16-panel batch (issue #216): decoded-audio dedup of the 91 Drive files (84 unique by byte hash so far), one exemplar for owner approval, resumable queue.
- [ ] Android: API 30 and API 36 emulator runs on the unified tree; band-stage flashing dots; API 30 out-of-memory; variant playback. Owner device report "tapping a layout closes the app" is unresolved.
- [ ] Windows: build the portable EXE from the unified tree and run real workflows.
- [ ] Performance before/after measurements.
- [ ] Manuals and docs for Beta 1.4.
- [ ] Drive delivery folder "Helix Sequencer — Beta Version 1.4" is EMPTY.

## 5. Next actions (in order)

1. Push this branch; open a draft PR; let CI run.
2. Version bump and CI workflow fixes.
3. Native band render on real audio (six snowmen, fixed front camera) to 1080p30 MP4; verify with ffprobe.
4. Nine-layout catalog, then nine-panel native render.
5. Android/Windows candidate workflows; download and test artifacts.
6. Upload verified artifacts with checksums to the Drive delivery folder.

## 6. Environment notes for whoever resumes

- Python 3.12 with `requirements.txt` pins (numpy 2.2.6, librosa 0.10.2.post1, numba 0.61.2) plus `requirements-dev.txt` and `requirements-band-preview.txt`. Unpinned librosa/numba cause false failures.
- Full suite: `python -m pytest -q -p no:cacheprovider --continue-on-collection-errors` (about 7 minutes on 2 CPUs).
- Native render: xLights 2026.19 AppImage, extracted, headless under Xvfb.
- Production sequencing needs Demucs `htdemucs` and Whisper; `HELIX_VIVID=0`, `HELIX_MUSICAL_BED=1`.
- Regenerate drummer assets: `python -m tools.build_drummer_v3_assets --overwrite`.
