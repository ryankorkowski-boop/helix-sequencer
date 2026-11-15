# HELIX MASTER TODO & AGENT HANDOFF LEDGER

> Canonical project roadmap and cross-agent handoff layer.

## Current mission
Build Helix into a reliable AI-assisted xLights auto-sequencer while preserving deterministic sequencing, verified artifacts, and cumulative behavior.

## Beta roadmap baseline status

This repo is currently in the beta-safety phase described by `ROADMAP_BETA_TODO.md`.

- [x] Phase 0 guidance is in place: beta roadmap, safety baseline, and support/data-use policy are documented.
- [x] Core beta docs are linked from the README and are available under `docs/`.
- [x] Agent task index is aligned with the roadmap and points to the current next tasks.
- [x] Sample beta tester feedback checklist exists and is documented for testers.
- [ ] Continue with Phase 0/1 execution in the exact order called out by the roadmap before moving into engine-facing refactors.
- [ ] Keep this ledger updated as each beta phase completes.

## Current priority
The current repo priority is the beta-readiness sequence defined in `ROADMAP_BETA_TODO.md`:

1. Add/maintain `TASKS.md` pointing to the beta roadmap.
2. Maintain `docs/SUPPORT_MATRIX.md` and `docs/BETA_POLICY.md`.
3. Normalize dependencies and CI with `requirements-dev.txt`.
4. Add repo-safe smoke fixtures and structural validation.
5. Add run manifest/output safety behavior.
6. Add GUI beta mode + dry-check behavior.
7. Add beta tester docs and issue templates.
8. Add Windows packaging smoke coverage.
9. Only then begin engine facade/extraction work.

## Drummer / band current state
- [x] Canonical nine-component drummer contract documented.
- [x] Runtime drummer state model changed to nine integrated hit components.
- [x] Structure catalog changed to nine drummer sequencing components.
- [x] XML exporter no longer emits the legacy `line0="1-4"` placeholder for drummer components.
- [x] Pose geometry spec now defines nine component composites with embedded contacting-stick geometry.
- [~] xLights model exporter still needs to emit the new component composites as the nine canonical sequencing submodels.
- [~] Drum detector uses HPSS/percussive onset analysis plus spectral features.
- [x] Classification now rejects high harmonic-contamination candidates when unsupported and suppresses ambiguous low-margin classifications into `drum_bus`.
- [ ] Add per-event source/stem provenance to rendered XSQ debug metadata.
- [ ] Validate detector against real-song audio and quantify false positives.
- [ ] Generate real-song XSQ.
- [ ] Render full-song MP4 with audio.
- [ ] Human visual review of rendered drummer timing.

## Canonical drummer components
1. `HX_SNOWMAN_DRUMMER_KICK` = KICK + KICK_RIM
2. `HX_SNOWMAN_DRUMMER_SNARE` = SNARE + SNARE_RIM + SNARE_CONTACT_STICK
3. `HX_SNOWMAN_DRUMMER_TOM_1` = TOM_1 + TOM_1_CONTACT_STICK
4. `HX_SNOWMAN_DRUMMER_TOM_2` = TOM_2 + TOM_2_CONTACT_STICK
5. `HX_SNOWMAN_DRUMMER_TOM_3` = TOM_3 + TOM_3_CONTACT_STICK
6. `HX_SNOWMAN_DRUMMER_TOM_4` = TOM_4 + TOM_4_CONTACT_STICK
7. `HX_SNOWMAN_DRUMMER_HI_HAT` = HI_HAT + HIHAT_CONTACT_STICK
8. `HX_SNOWMAN_DRUMMER_CYMBAL_LEFT` = CYMBAL_LEFT + CYMBAL_LEFT_CONTACT_STICK
9. `HX_SNOWMAN_DRUMMER_CYMBAL_RIGHT` = CYMBAL_RIGHT + CYMBAL_RIGHT_CONTACT_STICK

**Physical rule:** the contacting stick is part of the corresponding hit component. There are no independent stick sequencing channels. Kick has no stick.

## Detection architecture
**audio → HPSS/percussive isolation → onset candidates → spectral/transient features → confidence-gated drum classification → nine-component mapper → XSQ**

## Ground-truth regression oracle
A prior drummer render was explicitly identified by the user as having the **correct drummer logic** and must be preserved as the behavioral reference while the implementation is upgraded.

- Known-good commit: `b27e8d77a63027ed32bcf6851dcff3925472c155`.
- Prior successful artifact lineage: **Helix Full Current 256 + Drummer**; published workflow run `35486153096` was previously identified as the MP4-producing run.
- The repository's dedicated ground-truth workflow at that point exercised the real V3 drummer submodels and generated deterministic audio/XSQ/preview artifacts.
- Current nine-component geometry remains authoritative for the new implementation: four tom zones and contacting-stick geometry integrated into the hit component.

**Rule:** do not discard or rewrite the behavior that made the prior render correct. New detection/mapping logic must be compared against the prior oracle before being accepted.

## Verification gate
**audio → detected events → mapped components → XSQ → full-song MP4 with real audio → compare against prior correct drummer render → human visual review**

Do not mark complete from unit tests alone.

## Change Ledger

### 2026-11-14 — Optimization PR 2 of 8 · audio decode reuse and analysis cache

#### Goal and files

Reuse each decoded waveform within a run and persist eligible analysis results without changing the pitch or drummer pipelines. Branch `codex/optimization-02-audio-analysis` builds on PR #225.

- `core/audio_intelligence.py` reuses decoded mono PCM for mix separation, stem timing and summaries, background-vocal analysis, and bass pitch extraction. Both HPSS passes stay in the mix note path by owner decision.
- `audio/drum_detection.py` lets the existing file entry point take the samples already decoded by the caller. Its classifier, event mapping, logging, and fallback are unchanged.
- `core/audio_analysis_cache.py` keys local results by audio SHA-256, input filename, analysis configuration, cache version, and DSP runtime versions. Writes replace complete JSON records atomically. A hit verifies all four legacy stem checksums and restores typed events. The caller's source path and layout metadata are derived at read time. Cache misses isolate the local stem computation from other recordings with the same filename.
- `tests/test_audio.py` checks one decode per input, typed cold/warm equality, input and setting invalidation, corrupt records, missing stems, and fresh caller paths.

#### Verification and preserved behavior

Both HPSS passes, the PCM16 stem round trip, pitch and vocal thresholds, event and target selection, and drummer event math are preserved. Master uses the shared stem decoder and its existing sequencing analysis. The full-result cache applies to the separate `analyze_audio_file` entry point.

- `python -m pytest tests/test_core_sandbox.py tests/test_audio.py tests/test_palette_not_white.py tests/test_drummer_v3_xsq_integration.py tests/test_sequence_plan.py -q` returned 29 passed and one pre-existing XML truth-value warning. PR 1 documents the pre-existing `assign_hand` collection error.
- Serialized analysis results, including stem and drum events, matched the PR 1 base byte-for-byte on cold and cached runs of the 12-second drum fixture and 15.024-second Tinsel Sawtooth excerpt. Their sorted JSON SHA-256 values are `0fb6f4820b47a53c53afe7f589f361cf2a575adbfe17fcfaccc6f18157e3ae97` and `2931e3875f984a456a96b9be92f60890b6f972942eec05f913f10ad7c2ad0602` using the benchmark's fixed paths.
- Generated master XSQs matched byte-for-byte for both inputs with the PR 1 CLI flags and fixed filenames. The drummer fixture reported 2,053 placements and SHA-256 `01ae2f5c8f8b14a2d99af68fc6443fa97b529e7fc62ee2df63da35c8157b6757`. The song excerpt reported 4,144 placements and SHA-256 `8f3aafbb48b689caaae5a3808a760d5f458c1466d281a3f58d056c9f9882347a`.

#### Before and after timings

Single-process measurements used the PR 1 environment. The cold call decodes the input and runs DSP. The repeat uses the same path, content, and settings.

| Input | Base cold | PR 2 cold | Base repeat | PR 2 cache hit |
| --- | ---: | ---: | ---: | ---: |
| Drummer fixture | 10.179 s | 10.276 s | 7.697 s | 0.023 s |
| Tinsel Sawtooth excerpt | 12.377 s | 15.870 s | 14.101 s | 0.025 s |

Both inputs went from two mix and ten stem decodes to one mix and four stem decodes on cold calls, and zero decodes on hits. A fresh process also returned identical cached output and bypassed the decoder for both inputs. In these samples the Tinsel cold run was slower, with most of the difference in stem analysis and pitch DSP. The repeat-call gains apply to eligible direct audio analysis. Master CLI wall time on the Tinsel excerpt was 19.41 s before and 18.95 s after, with 16.93 s inside the instrumented variant after this change.

#### Limitations and regression risks

The full-result cache is limited to local fallback stems with lyrics disabled and default song-part detection. Moises, Demucs, live transcription, and caller-supplied parts keep their existing analysis flow. Stem files continue to use legacy output names. Colliding names can invalidate a cache hit, and each cacheable analysis computes from its own staged sidecars. Decoded drums, vocals, and bass remain live through the stem pass. Full-song peak memory, Android execution, and Windows execution remain unmeasured. Bump the cache version when analysis semantics or the payload format change. The attempted xLights render was blocked by Xvfb listener initialization, so native playback and the historical drummer MP4 remain outside this verification.

#### Follow-up optimization assessment

- Share immutable master-path analysis across candidates and layouts once its input dependencies are explicit. The Tinsel excerpt spent 5.62 s in audio/polyphony and 9.72 s in timing/planning before this PR. Profiling isolated 7.30 s in stem analysis, including separation and drum/vocal DSP, during the instrumented run.
- Remove exact duplicate DSP in a focused follow-up. `_summarize_stem_file` currently calculates the same STFT magnitude twice. `_extract_note_candidates` recomputes the maximum of the same pitch matrix for every frame. Verify full-song XSQ and analysis parity and measure peak RSS.
- Profile report serialization and effect placement on a dense RGB layout. The profiled legacy layout serialized two reports and called `add_model` more than 4,700 times. Preserve palette indexes, overlap precedence, and RNG calls when optimizing these paths.
- Keep history-dependent generation ordered. `scan_workspace_preferences` reads XSQs written earlier in the same output directory, and learning state can change after a song. Parallel work requires independent inputs and deterministic promotion.
- Gate visual changes using native FSEQ samples and audio-aligned MP4 review. Track section-level prop activity and blackouts, near-white RGB frames, onset alignment, and canonical drummer targets. The current `grade_preview` derives its grades from intent counts and overlays, so it cannot measure these pixel-level failures.

### 2026-11-14 — Optimization PR 1 of 8 · baseline and safety net

#### Goal and files

Set up reproducible regression tests and measure the current sequencing and audio-analysis stages. The feature branch is `codex/optimization-01-baseline`, based on `1b1ff83c`.

- `.gitignore`, `README_CURRENT.md`, `tests/test_core_sandbox.py`, and `tests/snapshots/*.json` make the five sandbox tests runnable in a fresh checkout. The tests generate the existing 12-second synthetic drum fixture and require both snapshots.
- `core/stage_timer.py`, `core/effect_engine.py`, and `core/audio_intelligence.py` record elapsed time with `perf_counter`. Completed variants log their numbered stages and completed analyses log seven stages via the supplied callback or the module's INFO logger.

#### Preserved behavior and verification

Effect selection, model targets, event timing, RNG seeds, stem processing, and drummer source and mapping are unchanged. Timing samples appear in logs only.

- `python -m pytest tests/test_core_sandbox.py tests/test_audio.py tests/test_palette_not_white.py tests/test_drummer_v3_xsq_integration.py -q` returned 25 passed on Python 3.12.14. The base checkout returned 20 passed and five skipped because `2.wav` was unavailable. The five sandbox tests also passed with librosa 0.10.2.post1. The base full-suite collection separately reproduces the `assign_hand` import error in `tests/test_drum_mapping.py`.
- The master CLI generated byte-identical XSQs with 2,053 reported placements using the same layout, template, audio, and output filename before and after. Their SHA-256 is `01ae2f5c8f8b14a2d99af68fc6443fa97b529e7fc62ee2df63da35c8157b6757`. Use the same output filename for subsequent comparisons because it seeds timing labels.
- Sorted JSON from `analyze_audio_file(..., enable_lyrics=False).to_dict()` also matched byte-for-byte with the same audio and stem-cache paths. SHA-256 is `e4bf0cb305a0bc30c8b55b1807b20862aa609b6f92f6107fbccd4b056b196d25`.

#### Fixed-input timings

The WAV generated by `python -m tools.generate_drummer_ground_truth --wav <wav> --events <json>` had SHA-256 `9e5040b4f890508c1beebfcdd6a9c3a1ce4841682247a8d393efe8c508b211bb`. The benchmark used Python 3.12.14, NumPy 2.5.4, SciPy 1.18.1, librosa 1.0.1, Numba 0.68.1, and one BLAS thread.

```sh
python main.py --profile master -- --template template.xsq --audio <wav> \
  --layout-file xlights_rgbeffects.xml --output-dir <scratch> --variants 1 \
  --no-prompt --no-save-settings --no-polish --no-birdsong --no-matrix-intelligence \
  --no-workspace-history --no-learning-memory --no-effects-orchestrator
```

The pre-instrumentation CLI took 23.94 s and the instrumented repeat took 13.13 s end-to-end. The instrumented `run_variant` took 11.497 s, including 3.578 s for audio and polyphony, 6.486 s for timing and planning, and 0.762 s for placement. Direct audio analysis took 16.240 s before instrumentation and 17.210 s with timers, including 4.499 s for stems and lyrics and 3.200 s for pitch and notes. These single-run measurements include variable process, cache, and host overhead. Use the stage timings as the baseline for follow-up benchmarks.

#### Limitations, deferred work, and risks

The comparison covers one synthetic input, the repository layout, and generated XSQ and analysis data. Full-song visual verification and comparison against the historical drummer MP4 were outside this baseline. Snapshot precision could expose DSP differences on dependency or platform changes. Timer summaries are emitted on successful runs and expand progress logs.

#### Ordered optimization checklist

- [x] PR 1 · Track the sandbox fixtures, instrument the stages, and verify generated output against the base.
- [x] PR 2 · Reuse decoded stems and add a cache for deterministic local analysis. The owner approved retaining both HPSS passes after the skip probe changed 116 note events to 119 on the drum fixture and 687 to 731 on the Tinsel Sawtooth excerpt. Both direct analysis and master XSQ parity are verified.
- [ ] PR 3 · Replace the lyric interval scan and verify placement parity.
- [ ] PR 4 · Add opt-in workers and verify identical output across worker counts.
- [ ] PR 5 · Narrow error handlers and preserve their fallbacks.
- [ ] PR 6 · Consolidate smoke jobs and capture existing lint results before enforcing new violations on Python 3.11 and 3.12.
- [ ] PR 7 · Validate asset references, clean up tracked files, and split runtime and build dependencies.
- [ ] PR 8 · Extract variant stages after PRs 1 and 2 merge and reproduce the filename-controlled XSQ comparison.

### 2026-11-13 — Beta 1.3 packages the palette fix for Windows and Android
**Agent:** Cursor cloud agent
**Branch:** `cursor/beta-1-3-release-1aae`

**Goal:** Ship the white-output fix from pull request #218 in the Windows portable zip and Android APK testers install, labeled Beta 1.3.

**Changed files/modules:**
- Merged #218 (`core/effect_engine.py`, `tests/test_palette_not_white.py`).
- `core/helix_version.py`, desktop title/About, CLI `--version`, Android `versionName` `1.3.0-beta` / versionCode 9, and the Windows version resource.
- Restored the November Drive packaging shape: `windows_portable.spec` one-folder zip and the Chaquopy `android/` debug project, with `.github/workflows/beta-v1.3-packages.yml`.
- `tools/palette_smoke.py` generates a synthetic sequence and fails if effects still resolve to a white-only palette.

**Intentionally preserved behavior:** Effect choice, timing, and model targeting from the merged default branch. A template palette that already enables a chromatic color is left unchanged. Release signing still requires the owner's keystore; the handoff APK stays the debug build testers already install. Layouts that are not on this branch were dropped from the Android sample list.

**New behavior:** User-visible version is Beta 1.3. Packaged effects point at section palette rows instead of a white-only palette 0.

**Tests/evidence:** `tests/test_palette_not_white.py` and `tests/test_helix_version.py`. Full suite: 916 passed, 19 failed, 5 skipped, 1 xfailed, 1 collection error in `tests/test_drum_mapping.py`. The 19 failures are the pre-existing band, drummer, preview-mux, and xsq-validation tests. A local synthetic-tone sequence wrote 2128 named effects, none on a white-only palette, across palette indexes 3–8. Packaged Windows and Android evidence is produced by `.github/workflows/beta-v1.3-packages.yml`.

**Limitations:** The historical `windows-portable.yml` and `android-offline.yml` files are not on this branch, so the new workflow rebuilds that package shape without the emulator matrix or release keystore. The cloud agent token cannot call `workflow_dispatch` (Actions permission denied), so the workflow also starts on a push that changes the packaging files. Run 43430925127 failed in the workflow, not the engine: the smoke command passed a bare `--` that argparse rejected, and `android-actions/setup-android@v3` asked sdkmanager for the removed `tools` package. Android code that depended on `core.band_visibility`, `core.output_provenance`, and later-only CLI flags is skipped when those modules are absent. The separate palette-variety pull request is not included.

**Deferred work:** Production Android signing (`HELIX_ANDROID_KEYSTORE`, `HELIX_ANDROID_STORE_PASSWORD`, `HELIX_ANDROID_KEY_ALIAS`, `HELIX_ANDROID_KEY_PASSWORD`) and the API 30/36 emulator matrix from `android-offline.yml`.

**Regression risks:** Desktop About/title text moved the layout-preset row down one. Android LOR runs use AC-safe effects without the later source-LMS binder.

### 2026-11-13 — Default sequences no longer collapse to a white-only palette
**Agent:** Cursor cloud agent
**Branch:** `cursor/rich-palettes-f36b`

**Goal:** Master-profile output should use multiple hues, change color with the song section, and reserve white for accent effects.

**Changed files/modules:**
- `core/effect_engine.py` replaces a white-only template palette (including palette index `0`) before effects are written, on both `add_model` and the all-models showcase path.
- The polish pass no longer copies a white-only template palette back onto effects near section boundaries.
- `tests/test_palette_not_white.py` fails if that path returns palette `0` or any white-only palette again.

**Intentionally preserved behavior:** A template palette that already enables a chromatic color is left unchanged. Effect choice, timing, and model targeting are unchanged. `palette_mode=template` still starts from the template palette.

**New behavior:** When the resolved palette enables only near-white, Helix appends a ColorPalettes row of section hues and sets the effect palette to that index. xLights ignores an inline palette string and falls back to palette 0, so an index is required. Twinkle, Shimmer, Strobe, Snowflake, and Sparkle also check a white accent. Other effects do not.

**Tests/evidence:** `tests/test_palette_not_white.py` (4 passed) plus `tests/test_palette_discipline.py` (8 passed). Full suite: 914 passed, 19 failed, 5 skipped, 1 xfailed, 1 collection error in `tests/test_drum_mapping.py`. The 19 failures are pre-existing band, drummer, preview-mux, and xsq-validation tests. Imageio is installed in this environment, so the previously cited 24 imageio failures are not all present. Before the change, real xLights 2026.19 FSEQ renders averaged 91.1% near-white lit RGB pixel-frames across 22 layout/song pairs. After the index fix the same metric is 0.040% (highest pair 0.169% on wow_spinners / north_pole_overdrive). AC layouts have no multi-pixel RGB nodes, so they stay out of that metric; their visible color is still the model color times intensity. An isolated probe rendered palette index 0 red and an inline blue string red as well, confirming xLights discards the inline string.

**Limitations:** Color still follows song sections already detected by Helix. A song that stays in one section keeps one hue family, with the lead color rotating per effect. Single-channel AC props are not recolored by this change.

**Deferred work:** None for this item. V01-NPO-ALL16 and V06-CLF-WOW12 were re-rendered from the new FSEQ files.

**Regression risks:** Sequences whose template palette 0 was intentionally white-only will now gain color. That is the requested change. The sequence gains extra ColorPalette rows.

### 2026-10-02 — Beta tester feedback checklist documented
**Agent:** GitHub Copilot
**Branch:** `feature/restructure-core`

**Recorded:**
- Added a repo-safe beta tester feedback checklist document for single-run evidence collection.
- Linked the checklist from the root README so testers can find it from the main entrypoint.
- Kept the checklist focused on privacy-safe, local-only evidence collection without requiring private asset disclosure.

**Limitations:**
- This is a documentation gate only; it does not claim xLights import success or visual quality.
- The beta roadmap still requires run manifest, GUI, and packaging safety work before broader beta claims.

### 2026-10-02 — Beta roadmap baseline alignment
**Agent:** GitHub Copilot
**Branch:** `feature/restructure-core`

**Recorded:**
- Restored the task index to the beta-roadmap-first workflow required by `ROADMAP_BETA_TODO.md`.
- Added a repo-level beta baseline status note to this ledger so the project continues in the intended order.
- Preserved the active drummer work while making the higher-priority beta safety work explicit.

**Limitations:**
- This does not replace the deeper engineering work required for drum detection or xLights import validation.
- Beta-safety milestones must still be executed in order before engine refactor work begins.

### 2026-09-30 — Ground-truth regression oracle locked
**Agent:** ChatGPT/GitHub
**Branch:** `feature/restructure-core`

**Recorded:**
- Prior known-good drummer behavior is anchored to commit `b27e8d77a63027ed32bcf6851dcff3925472c155`.
- The historical 8-submodel V3 workflow is retained as a behavioral regression reference while the physical model evolves to nine components.

### 2026-09-30 — Confidence-gated drum classification
**Agent:** ChatGPT/GitHub
**Branch:** `feature/restructure-core`
**Commit:** `b8e7f8fa5ab5044c774b3ca482711b47b89fb61c`

**Changed:** `audio/drum_classification.py`
- Added harmonic-contamination gating using the existing percussive/harmonic ratio.
- Added a minimum score-margin requirement between the best and runner-up drum classes.
- Ambiguous or weak events now become `drum_bus` instead of being confidently misclassified.

**Preserved:** existing kick/snare/tom/hat/cymbal feature scoring and six-stream event schema.

**Not yet verified:** real-song false-positive rate, XSQ output, and MP4 behavior.

### 2026-09-30 — Nine-component drummer geometry spec
**Agent:** ChatGPT/GitHub
**Branch:** `feature/restructure-core`

**Changed:** `fixtures/band_geometry/drummer_v3_pose_spec.json`
- Four distinct tom zones and nine canonical hit composites.
- Contacting sticks are embedded in snare/tom/hi-hat/cymbal components.

**Known limitation:** xmodel exporter still needs to make the nine composites the canonical sequencing submodels.

## Next actions
1. Preserve the prior known-good drummer behavior as the regression baseline.
2. Reconcile xLights drummer geometry with the nine canonical composites.
3. Add event provenance/debug output.
4. Run detector on the repository's real song and inspect event counts by class/confidence.
5. Generate full-song XSQ.
6. Render full-song MP4 with real audio.
7. Compare rendered component flashes to actual audible drum events and the prior known-good render.
8. Iterate only on measured false positives/false negatives.
