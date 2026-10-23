# Final release execution handoff — 2026-10-23

Release status: **IN PROGRESS**. No merge of PR #188 or public beta publication
is authorized until release gates pass and the owner approves a fresh canonical
band movie. Post-beta roadmap work remains deferred. See MASTER_TODO.md first.

## Current source

Branch: `codex/eight-hour-recovery-20261019`. Verified starting HEAD:
`8c61452713bd06273e94e8607a828c8341ada9f3`. PR:
https://github.com/ryankorkowski-boop/helix-sequencer/pull/188 (open, draft).
The commit containing this file is an implementation checkpoint, not evidence
that its renderer/platform builds have completed.

| Task | Status | Evidence / cause / exact next action |
|---|---|---|
| True branch/PR state | COMPLETE | Remote fetched; PR #188 open/unmerged at starting SHA. No older ZIP used. |
| Original owner audio | COMPLETE | `fixtures/audio/Phoneme_Test_Hook.mp3`, 802902 bytes; SHA256 `19e90c273d0d747938f24b36586b50818c104cddffbefe4a4128927374301938`. Recovered original Library upload and verified exact bytes; full decoded duration 34.8799791667s. |
| Reliable ingestion | IN PROGRESS | `tools/phoneme_source.py`: retained fixture default, optional HTTPS/auth override, exact hash, bounded download, redacted diagnostics, source receipt before DSP install. Workflow no longer requires audio/show URLs or prepared show ZIP. Run committed workflow and inspect completed result. |
| Analysis bottleneck | IN PROGRESS | Existing one-variant/no-orchestrator defaults preserved. Reuse magnitude/power STFT for default onset mel and centroid; vectorized argmax pitch. Exact numerical/onset/beat equivalence across 22050/44100/48000 Hz passes. `tools/benchmark_audio_analysis.py` compares trusted baseline SHA to candidate on full recording. |
| Production singing-face binding | IN PROGRESS | Found generated `lead_singer_full` / `helixville4_harmony_singer_full` style hints were being treated as imported faceInfo names. Generated hints bind only one unambiguous real definition on the same target. Explicit face selections remain strict (b418efe retained). Native lead now appears in lead cycle. Test explicit/ambiguous/other-target refusal and generated binding. |
| Full-song XSQ | IN PROGRESS | First real current-source production run completed in 73.49s with 1861 effects and 34.88s header. Six existing Review3DScene-derived models, no xylophone. First run omitted opt-in lyric sync; corrected builder rerun is required. Generated show uses current source, no external ZIP. |
| Genuine native render | IN PROGRESS | Pinned xLights 2026.18 AppImage hash verified `62affb88b9a9b03cf5164974ac69bcefe35c559719d157b3364e4d4a5ab4214b`. Actual native headless FSEQ: 74643 channels, 697 frames, 6854540 nonzero samples. Native GUI exported 248x442; strict HD gate correctly rejected it. Local openbox lacked theme search path; retry with extracted theme data in XDG_DATA_DIRS, then inspect real-canvas resize and full decode. No accepted full-resolution MP4 yet. |
| Canonical appearance | BLOCKED | Existing native geometry recovered; no new placeholder design authored. It remains an unapproved candidate. Need owner comparison with approved references and actual rendered frames; code labels do not prove approval. |
| Independent backing vocals | BLOCKED | Source is mixed stereo; classifier estimates are not independent vocal ground truth. `vocal_lane_diagnostic.json` keeps this false. Obtain isolated lead/backing source or defensible separated/validated vocal lanes; never manufacture events. Existing E14 native producer independently fails because its retained backing lane is empty. |
| Instrument musical acceptance | NOT STARTED | Current production show is diagnostic; native FSEQ activity and effect counts do not prove instrument identity, shoulder/contact continuity, independence or string/key accuracy. Preserve original algorithms; review source-timed per-role evidence. |
| Windows latest starting SHA | IN PROGRESS | Run39924409615 reported success at starting SHA; inspect binary/start/clean-host evidence before distribution. New changes require a new build. |
| Android API30/API36 | IN PROGRESS | Run39924409507 was in emulator instrumentation at inspection; Gradle build already succeeded, installation not yet verified. Read completed run, signing/install reports and device evidence. |
| Full Python3.11/3.12 CI | IN PROGRESS | Earlier starting-SHA push Beta CI39924402290 passed; PR jobs were still running. Do not claim all completed. New checkpoint needs fresh completed CI. |
| Licensing | COMPLETE | No license/legal policy changed in this checkpoint; retain noncommercial/homeowner and paid commercial vendor requirements. Existing compliance run39924409519 reported success at starting SHA. |
| Merge/publication | BLOCKED | All release gates plus owner MP4 approval required; no merge or publication performed. |

## Commands and evidence

```
python -m tools.phoneme_source phoneme-work/input
python -m tools.prepare_phoneme_show --audio phoneme-work/input/Phoneme_Test_Hook.mp3 --output phoneme-work/show
HELIX_NATIVE_PREVIEW_WIDTH=1280 HELIX_NATIVE_PREVIEW_HEIGHT=720 xvfb-run -a -s '-screen 0 2560x1440x24' python -m tools.native_preview phoneme-work/show --xsq phoneme-work/show/Phoneme_Test_Hook_Helix.xsq --audio phoneme-work/show/media/Phoneme_Test_Hook.mp3 --xlights /absolute/path/to/xLights
python -m tools.finalize_phoneme_review phoneme-work/show
python -m tools.benchmark_audio_analysis fixtures/audio/Phoneme_Test_Hook.mp3 --baseline-ref 8c61452713bd06273e94e8607a828c8341ada9f3 --report benchmark.json
```

38 focused source/DSP/face/compiler/snowman/discovery/routing tests passed in
5.09s on Python3.12 locally. Full regression is not inferred. The new workflow
uploads the complete show, source, sequence logs, native logs, diagnostic report,
checksums and actual MP4 even if later acceptance blocks release. It resolves
`native_preview.mp4` from the renderer receipt rather than guessing a root path.

Historical failures verified:
- https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39924402434 — old Phoneme workflow failed before install because automatic push supplied no manual URLs.
- https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39921342070 — source qualification rejected original E14 empty backing lane before compile. Do not rerender unchanged E14 expecting two singers.

Remaining work is explicit above; queued, unverified or diagnostic work is never
marked complete. Update this file and MASTER_TODO.md with every next safe change.

## Verified local follow-up before first checkpoint

- Corrected full-song production rerun: **44.30s**, **1893 effects**; actual
  parent singer rows contain **22 lead Faces effects and 11 harmony Faces
  effects**. The prior zero-face export is repaired. Whisper is unavailable
  locally; cues are broad source-energy/classifier estimates, not verified
  lyrics/phonemes or independently isolated backing vocals.
- DSP full-source benchmark: warmed median 0.542879s baseline versus
  0.449600s candidate (1.20747x throughput; 17.18% elapsed-time reduction).
  All measured features and onset/beat/pitch clocks match exactly; original
  source bytes unchanged. Scope is initial analyze(), not whole engine.
  Receipt: `evidence/phoneme_recovery_20261023/audio_analysis_benchmark.json`.
- Generated shows record source commit, dirty-worktree flag and relevant
  module hashes. An uncommitted local run must not be described as the clean
  committed source. Workflow checkout will render the committed revision.

## Native export root cause confirmed and next repair

The unmodified AppImage did render an actual MP4 but **failed acceptance**:
248x602, black image at8s, even after real X11 canvas resize to1280x720. Exact
pinned `xLightsMain.cpp` reads cached getWidth/getHeight immediately after
SetSize; its saved3D camera is initialized before mode selection. Both defects
are already repaired by `tools/patch_xlights_native_export.py`. Do not repeat
unpatched exports or substitute an upscaled/black movie.

The Phoneme workflow now restores/builds the **existing source-patched pinned
renderer**, reinstalls cached wxWidgets libraries, checks ldd, saves the build
before export and uses HELIX_PATCHED_XLIGHTS. Automatic production uses the PR
trigger so it can read the existing PR-scope native build cache. Native runtime
and compiler logs are included even if downstream acceptance fails.

Additional verification:98 native-preview/cast/artifact/patch/sequence-builder
checks passed,1 native-only integration skipped,10 subtests passed (4.23s).
Checkpoint3776d2a95bfce693239caccaa81d895daa35c382 is pushed. Its original
unpatched renderer workflow is superseded by this next targeted fix. Current
jobs and build/install results remain unverified until completed.


## 2026-10-23 — Verified retained native renderer recovery branch

IN PROGRESS: recover the actual compiled patched xLights bundle from successful
producer39511779105 (aa00b873, codex/native-build-reuse-20261020), artifact12308760631.
The patch is byte-identical to the current source; artifact label uses GitHub
hashFiles' hash-of-hash18596d7e while renderer.json uses direct SHA256db2802bb.
Recover only tools/native_renderer_bundle.py and its tests from that historical
implementation; do not merge the old branch.8 bundle cases and8 subtests pass.
New isolated branch codex/phoneme-renderer-recovery-20261023 uses the same current
Helix sequencing source286307e plus this workflow/helper. It verifies successful
producer/repository/source identity, pinned upstream/patch/archive/binary hashes,
restores wxWidgets and checks runtime libraries before regenerating the complete
Phoneme recording. No old movie reused. Native output/visual/independent-vocal
acceptance remains pending. No primary render is interrupted; no public release.
