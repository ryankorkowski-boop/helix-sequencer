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


### 2026-11-16 — Animated Android sequencing progress (in progress)
**Goal:** Introduce a modern lightweight decorative light-show progress display without changing sequencing output.
**Changed files/modules:** Android SequencingLightShowView.java and MainActivity.java.
**Intentionally preserved behavior:** Existing six-stage Android workflow, audio processing, variant generation, exports, drummer behavior, and deterministic effect selection.
**New behavior:** While a job is running, display chasing LED arches and a swirling RGB mega tree. The bar inside the decorative view only shows measured preview percentage; other stages are indeterminate in the existing progress bar. View animation stops when not running or detached.
**Tests/evidence:** Source-level implementation only; Android compilation, emulator smoke test, performance measurement, and actual APK review have NOT been run.
**Limitations:** Windows EXE GUI is unchanged. No settings UI for scene selection yet. The decorative show is not an authoritative audio-synchronized render or band preview. A pending-job state may need further lifecycle validation.
**Deferred work:** Android and Windows design parity, scene preferences, battery/reduced-motion settings, preview/variant UX overhaul, packaging and visual tests.
**Regression risks:** Android UI lifecycle and frame invalidation; verify cancellation, activity recreation, memory usage, and API 30/36 before release.


### 2026-11-16 — Preserve help, legal, and donation navigation during GUI refresh
**Goal:** Keep user-requested Instructions, Legal, and Donate actions accessible as the Android UI changes.
**Changed files:** android/app/src/main/java/org/helixsequencer/android/MainActivity.java.
**Preserved behavior:** Existing Instructions button opens InfoActivity, legal footer opens its legal page, and SupportLinks.add still supplies both Donate to xLights and Donate to Helix links. InfoActivity retains its separate scroll positions and recreation handling.
**New behavior:** Dedicated Legal button beside Instructions in the horizontally scrollable workflow navigation. Decorative animation pauses when activity is backgrounded and resumes for an active job.
**Tests/evidence:** Source inspection confirms existing SupportLinks and InfoActivity wiring. Android build, instrumentation tests, and device screenshot have not run.
**Limitations/deferred:** Windows UI parity and APK packaging remain outstanding. Verify navigation and background/resume behavior on emulator and real devices.
**Regression risks:** Extra tab width on narrow phones; horizontal navigation must remain scrollable. Preserve donation URL configuration and legal wording exactly.


### 2026-11-16 — Desktop GUI animated progress and support navigation
**Goal:** Bring animated arches and swirling RGB mega tree to the Windows Tkinter launcher while preserving legal, donation and instructions access.
**Changed files/modules:** gui_lightshow.py, gui_launcher.py.
**Preserved behavior:** Existing sequence command, engine switches, layout choices, logs, and legal/third-party license links.
**New behavior:** Dark-themed ttk appearance, animated decorative show during sequence builds with selectable Combined/Arches/Mega tree modes, Instructions viewer, Donate to Helix and Donate to xLights buttons reading existing config/support_links.json.
**Tests/evidence:** Source-level changes committed; no Windows EXE build, UI screenshot, integration test, or runtime validation performed.
**Limitations:** Desktop Instructions falls back to README guidance when the Android bundled instructions asset is missing. Progress animation is decorative and not synchronized to audio or measured progress.
**Deferred work:** Fix any desktop runtime/UI issues found by smoke tests, confirm packaged assets and support links, test Windows and Android builds and their navigation; implement complete multi-panel responsive UI.
**Regression risks:** Tkinter worker thread currently performs some UI updates, an existing issue; validate thread safety. Desktop screen space and packaging asset paths require checks.


### 2026-11-16 — GUI smoke validation infrastructure and desktop thread-safety repair
**Goal:** Establish repeatable checks for the modernized Android/Windows interfaces and prevent Tk worker-thread UI access.
**Changed files/modules:** gui_launcher.py, tests/test_gui_modernization_smoke.py, .github/workflows/gui-modernization-smoke.yml.
**Preserved behavior:** Existing CLI command arguments, sequencing engine settings, support links, legal controls, instructions and decorative light-show scenes.
**New behavior:** Worker stdout and completion status are passed through a queue polled by the Tk main loop. GitHub Actions workflow requests headless Python syntax/navigation checks and Android debug compilation using installed Gradle.
**Tests/evidence:** Smoke test and CI workflow committed, but no successful run or APK/EXE build has been verified in this session.
**Limitations:** Desktop runner's other helper methods may still contain preexisting Tk threading issues; no Android instrumentation/emulator playback or native xLights video verification. Android project lacks a Gradle wrapper, so workflow uses setup-gradle.
**Deferred work:** Inspect CI results, repair failures, run Android API 30/36 and Windows GUI tests, package builds, visually review navigation and performance, then complete full UI redesign.
**Regression risks:** Tk event queue polling during window destruction; packaging dependencies; Android SDK/Chaquopy availability in CI.


### 2026-11-16 — CI failure triage: Android SDK setup
**Goal:** Unblock actual Android GUI compilation in CI.
**Changed files:** .github/workflows/gui-modernization-smoke.yml.
**Preserved behavior:** Android source, desktop GUI, donation/legal/instructions, sequencing engines and animations unchanged.
**New behavior:** Android job uses runner's preinstalled Android SDK rather than android-actions/setup-android@v3 attempting obsolete sdkmanager package 'tools'.
**Tests/evidence:** Initial GUI modernization workflow run 43898738834: desktop-headless SUCCESS; android-compile FAILURE during SDK setup before Gradle compilation. Log shows 'Failed to find package tools'. Corrected workflow committed; rerun result pending.
**Limitations:** Android compile and APK runtime remain unverified; CI may uncover further Gradle/SDK/plugin issues.
**Deferred work:** Inspect new CI run, repair any Gradle compile errors, package APK/EXE, run emulator and Windows smoke tests.
**Regression risks:** Runner Android SDK paths/version drift; installed Gradle compatibility.


### 2026-11-16 — Android Gradle compatibility repair
**Goal:** Advance Android compilation beyond toolchain initialization.
**Changed files:** .github/workflows/gui-modernization-smoke.yml.
**Preserved behavior:** All app code, animation, donate/legal/instructions, engine and export logic.
**New behavior:** CI provisions Gradle 8.11.1, the minimum version required by the configured Android Gradle plugin.
**Tests/evidence:** Workflow run 43902284172 desktop-headless SUCCESS, Android compile FAILURE at Gradle plugin version check: minimum 8.11.1 vs configured 8.10.2. New run pending.
**Limitations/deferred:** No compiled APK yet; continue diagnosing remaining Android build failures and then device validation.
**Regression risks:** Compatibility of Gradle 8.11.1 with the project's other build plugins.


### 2026-11-16 — Android CI Python 3.10 staging prerequisite
**Goal:** Allow Android's preBuild stageHelix task to launch its required interpreter.
**Changed files:** .github/workflows/gui-modernization-smoke.yml.
**Preserved behavior:** Android engine staging, Chaquopy 3.10, GUI, legal/instructions/donate, sequencing logic.
**New behavior:** CI provisions Python 3.10 before running Gradle.
**Tests/evidence:** GUI run 43902637436: desktop-headless SUCCESS; Android Gradle 8.11.1 starts, then :app:stageHelix fails because python3.10 is absent. Correction committed; result pending.
**Limitations/deferred:** Android APK still not compiled; next failures may involve Python wheel build, Chaquopy dependencies or Java compilation.
**Regression risks:** Runner PATH resolution for python3.10, dependency compatibility.


### 2026-11-16 — Successful Android compile and review artifact packaging
**Goal:** Preserve a downloadable debug APK and build a Windows GUI review executable for validation.
**Changed files/modules:** .github/workflows/gui-modernization-smoke.yml.
**Preserved behavior:** Android and Windows source code, sequencing engines, donation links, Instructions and Legal controls unchanged.
**New behavior:** CI uploads Android debug APK for seven days and attempts a Windows PyInstaller GUI review EXE in a separate windows-latest job.
**Tests/evidence:** GUI modernization workflow 43913514506 completed SUCCESS, with android-compile and desktop-headless both SUCCESS. New artifact and Windows packaging jobs not yet verified.
**Limitations:** Windows onefile GUI review executable may lack bundled data/assets and may not execute full sequencing; do not present it as release-ready. Android APK compilation is not emulator or hardware validation.
**Deferred work:** Check Windows packaging and artifact outputs, test launch, support navigation, actual sequencing, APK installation on API 30/36, and package complete production assets.
**Regression risks:** PyInstaller hidden imports and asset paths, missing runtime Python dependencies, Android test install/runtime differences.


### 2026-11-16 — Owner delivery instruction: Beta Version 1.4 to Google Drive
**Goal:** After both Android and Windows builds are functional and validated, upload them to the existing Helix Google Drive delivery area, labeled Beta Version 1.4.
**Changed files/modules:** MASTER_TODO.md (delivery and approval requirements only).
**Preserved behavior:** Existing code, engine, artifacts and prior beta release remain untouched; no merge or public release.
**New behavior:** Delivery naming requirement recorded: Helix Sequencer Beta Version 1.4, separate APK and EXE, with readme/build evidence; use a single ZIP if appropriate to established Drive release conventions.
**Tests/evidence:** GUI workflow 43923131470 SUCCESS (desktop-headless, android-compile, windows-package). GitHub artifacts: helix-gui-android-debug and helix-gui-windows-review. These are review artifacts, not verified full production builds.
**Limitations:** Android build.gradle still declares versionName 1.3.0-beta; Windows review EXE is a bare PyInstaller GUI package and may lack dependencies/assets. No Android hardware or Windows runtime smoke testing. Do not mislabel these as final Beta 1.4.
**Deferred work:** Finish functional packaging, update internal Android/Windows version metadata to 1.4, verify both applications, identify established Drive release folder, upload binaries/readme, verify uploaded file IDs and links, then request owner approval before merge/public beta release.
**Regression risks:** Mismatched displayed version versus filename, missing packaged engine files, incomplete EXE, unverified Android functionality and premature distribution.


### 2026-11-16 — Beta 1.4 internal version alignment
**Goal:** Match user-visible Android and Windows version metadata to the owner's Beta Version 1.4 delivery requirement.
**Changed files/modules:** core/helix_version.py; android/app/build.gradle.
**Preserved behavior:** Sequencing logic, layout controls, exports, donation/legal/instructions, and existing signing safeguards.
**New behavior:** Desktop/CLI TITLE, DISPLAY and VERSION identify Beta 1.4 (1.4.0-beta); Android versionName 1.4.0-beta, versionCode 10, and app label Helix Beta 1.4.
**Tests/evidence:** Source changes committed; new CI rebuild and runtime inspection pending. Prior workflow 43923131470 compiled both platform review artifacts before these metadata changes.
**Limitations:** Version metadata does not make an app production ready. Windows onefile review package may not include engine assets; Android and Windows runtime tests pending.
**Deferred work:** Verify fresh artifacts, packaging and runtime; upload tested Beta 1.4 files and README to Drive, confirm links, hold public release/merge pending owner approval.
**Regression risks:** Version code change impacts Android update compatibility; other hardcoded 1.3 labels may remain.
