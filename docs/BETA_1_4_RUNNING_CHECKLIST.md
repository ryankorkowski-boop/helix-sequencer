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
- [x] Production plan now states the physical `component` and striking `hand` of every drum cue. Before, `core/snowman_band.py` read them from a list that never carries them, so every cue said `None` and each renderer re-derived the staging.
- [x] Fixed front view shows the whole kit. The lead and harmony singers used to hide the ride/crash and floor-tom sides (no parallax in the orthographic approval camera). `models/band_sightline.py` slides both flanks outward as rigid units, widens the stage deck with them and fits the camera; `tests/test_band_sightline.py` documents the defect and the repair.
- [x] First band MP4 on real audio (CUSTOM Helix renderer, not native xLights): `Helix_Beta14_SixMember_Band_PhonemeHook_1080p30.mp4`, 1920x1080, H.264 High, AAC, 30 fps, 34.88 s, soundtrack correlation 0.9989 at zero lag with `fixtures/audio/Phoneme_Test_Hook.mp3`. Receipt and contact sheet: `evidence/beta_completion/band_review_20261119/`. Owner review pending.
- [~] Ride detection: a `ride` event stream exists in the mapper and co-hit detector; not yet measured on real songs.
- [ ] Native xLights render of the nine-cue drummer on real audio (evidence MP4). The patched native preview exporter is not available in this sandbox; stock xLights 2026.19 can render FSEQ headlessly but cannot record its house preview.

## 3. Tests

| Tree | Python | Result |
|---|---|---|
| integration before merge | 3.12 | 19 failed, 1071 passed, 1 error |
| 216 lineage before merge | 3.12 | 21 failed, 2243 passed, 25 errors |
| unified (before ride) | 3.12 pinned | 1 failed, 2571 passed, 6 skipped |
| unified with physical ride | 3.12 pinned | 0 failed, 2573 passed, 6 skipped |
| unified with physical ride | 3.11 (`requirements-dev.txt` only) | 0 failed, 2573 passed, 6 skipped |
| `cebf299f` on GitHub Actions (run 44576199699) | 3.11 and 3.12 | full suite passed on both |
| + sightline, plan staging, spec resources | 3.12 pinned | 0 failed, 2580 passed, 6 skipped |

Existing CI ran focused subsets only, which hid the full-suite failures.
Tests changed for documented contract reasons (not weakened): nine-vs-eight drummer targets, stem guard, promotion flags, Android recovery index alignment, GUI catalog.

## 4. Not done yet (do not treat as delivered)

- [x] Version strings bumped to Beta 1.4 (`1.4.0-beta`, Android versionCode 10); packaging workflow renamed `beta-v1.4-packages.yml`.
- [x] CI on `cebf299f`: full suite green on 3.11 and 3.12; Infinity layout, nine-panel validation and Android variant compile green; Android debug APK built (`Helix-Android-Beta-v1.4.apk`, SHA-256 `536a6da7...25ca`, artifact 14555349736, expires 2026-12-03).
- [~] CI failures found and fixed in the next push (re-verify): Drummer Ground Truth (`No module named 'tools'`, job-level `PYTHONPATH`), Native snowman geometry evidence (runner had no `ffmpeg`), Windows portable (see below).
- [~] Windows portable EXE BUILT but FAILED its real-workflow smoke: the frozen worker had no Whisper `mel_filters.npz`, so every sequencing run died at transcription. `windows_portable.spec` now collects Whisper, Demucs and librosa resources (+ regression test). Not yet re-run.
- [~] CI workflow hygiene: `helix-infinity-layout.yml` installs its requirements. The Bells workflow (PR #250 branch) still lacks `ffprobe`.
- [ ] Nine preloaded layouts (3x3) in Android and Windows. Current catalog is a union of both lineages, not the required nine; coro singing-face house, singing trees/matrices, 3D digital matrix, piano keyboard and Infinity (PR #250) are missing or provisional.
- [ ] Infinity showcase (>=10,000 elements) with `Bells of Mathmas.mp3`: prior run sequenced 10,240 models but its MP4 was a custom non-native preview and the job failed at a missing `ffprobe`.
- [ ] Multi-singer pipeline verification on real audio (separation, independent VAD, no false harmony).
- [~] MP4 deliverables (1920x1080, H.264, AAC, 30 fps, real audio): band hook clip produced (custom renderer, see section 2). Still missing: full-length band song, singers, nine-panel, 16-panel exemplar, Infinity/Bells, and any native xLights preview recording.
- [ ] 16-panel batch (issue #216): decoded-audio dedup of the 91 Drive files (84 unique by byte hash so far), one exemplar for owner approval, resumable queue.
- [ ] Android: API 30 and API 36 emulator runs on the unified tree (this sandbox has no KVM; use `android-offline.yml`, which runs both API levels on GitHub runners via `workflow_dispatch`); band-stage flashing dots; API 30 out-of-memory; variant playback. Owner device report "tapping a layout closes the app" is unresolved.
- [~] Windows: EXE builds in CI; packaged palette smoke must pass after the resource fix, then run the remaining real workflows.
- [ ] Performance before/after measurements.
- [ ] Manuals and docs for Beta 1.4.
- [ ] Drive delivery folder "Helix Sequencer — Beta Version 1.4" is EMPTY.

## 5. Next actions (in order)

1. Confirm the three CI fixes on the new head (Drummer Ground Truth, Native snowman geometry, Windows portable smoke).
2. Dispatch `android-offline.yml` on the integration branch (API 30 and 36 emulators); read the device-proof artifacts.
3. Upload the band MP4, receipt and the tested APK/EXE with SHA-256 sums to the Drive delivery folder.
4. Nine-layout 3x3 catalog (`config/gui_options.json`), then nine-panel render.
5. Full-length band song; Infinity/Bells (fix `ffprobe` on the PR #250 branch); 16-panel exemplar for owner approval.
6. Performance measurements, manuals, final report.

Rebuild the band MP4: `python -m tools.prepare_phoneme_show --audio fixtures/audio/Phoneme_Test_Hook.mp3 --output <show>` then
`python -m tools.render_owner_band_review <show> fixtures/audio/phoneme_vocal_separation <Drum1.mp4> <out.mp4> --expected-sha256 19e90c27...1938 --dimensional-drummer --fps 30`.
`Drum1.mp4` (SHA-256 `f014db45...45b3`) is `Helix_Drummer_DRY_TEST.mp4` inside Actions artifact 11520003337.

## 6. Environment notes for whoever resumes

- Python 3.12 with `requirements.txt` pins (numpy 2.2.6, librosa 0.10.2.post1, numba 0.61.2) plus `requirements-dev.txt` and `requirements-band-preview.txt`. Unpinned librosa/numba cause false failures.
- Full suite: `python -m pytest -q -p no:cacheprovider --continue-on-collection-errors` (about 7 minutes on 2 CPUs).
- Native render: xLights 2026.19 AppImage, extracted, headless under Xvfb.
- Production sequencing needs Demucs `htdemucs` and Whisper; `HELIX_VIVID=0`, `HELIX_MUSICAL_BED=1`.
- Regenerate drummer assets: `python -m tools.build_drummer_v3_assets --overwrite`.

## 7. Current outstanding acceptance gates — 2026-11-20 (supersedes older status above)

- [x] Dedicated synthetic nine-cue drummer CI 44691270749 succeeded; native real-song drummer still open.
- [x] Drive band diagnostic MP4 and receipt plus review gate document present; not native, not approved. Folder https://drive.google.com/drive/folders/1tcW6pfQ3CmyDPWMsYbvJrzaBTJsz_1lT
- [~] Nonfinite effect contract validation b21acf7, malformed template failure 0a5efbe, stale generated layer cleanup 0678577 and regression e3cfa69; CI verification pending. Manual layers preserved by intended contract.
- [ ] P0: full Python 3.11/3.12 suites and focused CI on latest head; verify Windows frozen dependency and native snowman geometry fixes.
- [ ] P0: native XSQ/FSEQ real-audio proof with valid palettes, brightness, timing, group/submodel composition and compatible layering; never promote custom preview to native.
- [ ] P0: canonical six snowmen, nine independently illuminated drum cues and correct hand/foot movement, restrained keyboard and credible bass/guitar; validated independent leads/harmonies and ten phonemes, silence and false-harmony suppression. Apply to singing faces/trees too.
- [ ] P1: audit engine reachability, decide/integrate Birdsong post-run adapter, vary engines and effect families musically; spatial adjacency, traveling chases, counterpoint, brightness envelopes, contrast, rests, section transitions and sustained phrases. Preserve AC color/channel mapping.
- [ ] P1: nine preloaded layouts on Android and Windows matching owner-approved panel order: 16 AC, 256 AC with arches/mega tree, RGB house, coro faces, canonical band, singing pixel trees/matrices, 3D digital grid, keyboard-responsive groups, Infinity. Preserve original 256-channel layout and 16-strip LED tree (owner specs pending).
- [ ] P1: recognizable Infinity >=10,000 props, groups, layers, 3D spirals, double helices, tunnels and matrices using Bells of Mathmas; reject dots/dashes and all-white flashing. Native evidence and visual review required.
- [ ] P1: genuine native-evidence nine-panel and 16-panel real-audio exemplar with owner pass/fail gate before batch; 1920x1080 H264/AAC 30fps, full decode, sync, brightness/framing; no blank panels. Batch issue 216: decoded-content dedup, verified audio hashes, one full-length 16-panel MP4 per unique recording, resumable queue.
- [ ] P0: Android API30/API36 offline acceptance, eliminate crashes/OOM/flashing dots, nine-layout catalog, all eight variants selectable/playable/exportable, scrollable instructions and persistent settings. Windows EXE packaged parity and smoke, legal/donate/instructions.
- [ ] P1: profile CPU/RAM, caching, audio chunking and bounded rendering before/after; document results.
- [ ] P1: update Beta 1.4 manuals, install/export instructions and troubleshooting, checksums and verified direct Drive links for tested APK/EXE and approval MP4s.
- [ ] Final: reconcile MASTER_TODO, handoff/status/manifest, owner explicit visual and release approval. No merge or publishing without approval.

## November 20 continuation — regression checkpoint

- [x] Inspected run 44687388477: both focused jobs passed; both full jobs failed. Python 3.12: 2634 passed, 1 failed, 6 skipped; stale 68-event expectation after ride addition.
- [x] Current source already expects 69 events and nine isolated cues. Commit `3e4ff9b41e692b3a318142e944a409a77c188192` strengthens coverage and soundtrack bounds; no production behavior changed.
- [ ] Confirm fresh full-suite CI on corrected source. Do not rerun old SHA as proof. Device and native visual acceptance remain open.
