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

### 2026-11-13 — Beta 1.3 workflow audit and targeted repairs

- Goal. Exercise the current customer engine and showcase candidate on the same real-audio excerpt and repair verified workflow failures on a feature branch.
- Changes. Adapted the Snowman Band consumer to the current drum mapper's single-submodel event. Routed the frozen Windows Run and Helixville builder actions through the packaged console worker. Propagated song failures to the run manifest after the batch attempt and corrected the misleading orchestration-promotion log. Restored Android band visibility and the media-duration/tail boundary checks from the showcase branch. Added targeted checks to the Windows packaging job.
- Preserved. Explicit orchestration-template promotion, processing of later songs in a batch, existing effect selection, palette fix, and original drum detection, source data and asset geometry.
- Evidence. On a 32-second Tinsel Sawtooth excerpt, the Beta 1.3 run produced zero band cues after a missing-key exception. The repair produced 784 planning cues, including 253 drum cues. The same run generated a 32-second decodable simulation. An invalid WAV produced a failing manifest and exit code 1. With Band performers off, the Android host bridge removed 10 performer models and 5 now-empty groups from its private layout copy. The hardKor excerpt XSQ now declares 32.000 seconds in place of 132.039 and has zero lighting or timing intervals past the soundtrack. The local focused regression set passed 44 tests. The broader local suite returned 934 passes, 18 failures and one collection error. The Windows executable needs a new packaged GUI run.
- Open. The Beta 1.3 Android host bridge generated XSQ in LOR mode and failed because it had no source-address LMS export. PR #217 exported an LMS with the input Unit/Circuit addresses and colors on the audit fixture. Its native showcase path still needs integration with the apps. Independent vocal attribution, lexical timing, canonical performer motion, native approval jobs, complete regression and physical device/controller verification remain open.
- Regression risks. An overall batch failure can still leave successful earlier/later song files for recovery. A band-plan cue count does not establish mapped native performer motion. Keep native acceptance and packaged behavior tied to the exact tested commit.

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
