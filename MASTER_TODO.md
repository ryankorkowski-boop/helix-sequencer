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

### 2026-11-26 — Resolve physical targets and rank optional accents in live placement
**Goal:** Let existing producers share the Composition Governor's placement policy while preserving Faces and kit timing.
**Changed files/modules:** Composition Governor, placement accounting, physical layout groups and submodels, XSQ alias sync, BeatGrid, Snowman Band handoffs, and pinned native verification.
**Intentionally preserved behavior:** Default timing, legacy orchestration opt-out, model effect compatibility, named specialist inputs, manual windows in smart-layer mode, independent analysis sidecars, and opt-in drummer placement.
**New behavior:** Resolve layout aliases and nested groups to root/node coverage. Guard shared layers and manual windows during admission and polish. Rank optional cues by proximity to instrument onsets, beats and section transitions, then section energy and stable proposal fields. Budget and cooldown accounting use the accepted placement time for ranked cues. Explicit BeatGrid chooses the nearest admissible point in the section when one exists. Native verification decodes the FSEQ to confirm active frames.
**Tests/evidence:** [Engine compatibility measurements and verification gates](docs/UNIFIED_ORCHESTRATION.md#physical-ownership-and-ranked-accent-follow-up). Serialized XSQ checks cover performer anchors, disjoint nodes, shared manual content and proposal-order determinism. The full-song comparison retained 8,711 effects versus 8,715 on #260, with focal clarity 60.9 versus 58.7 and zero budget overages. The cache bypass comparison reproduced all nine XSQ and specialist artifacts byte for byte on the three-variant synthetic fixture. Broad suite comparison found the same 18 failures and one collection error on both revisions.
**Limitations:** Unsupported submodel geometry reserves the entire parent. Unresolved and cyclic groups are rejected with diagnostics. Native kit diagnostic uses the shipped five-hit-target layout and compares serialized detector anchors with the nine-component list above. The dedicated drummer docs specify a conflicting eight-component kit.
**Deferred work:** Nine-component native kit playback against the historical oracle, original-source Faces and nine-panel review, and release gates. The prior owner pilot stopped at the missing private Drive locator and no independent vocal annotation has been verified.
**Regression risks:** Shared node rules can displace or reject overlapping group cues. Ranked accents can redistribute focal motion with similar total density. Capability depends on xLights node-range definitions and explicit face definitions in the layout.

### 2026-11-26 — Repair native smoke staging
**Goal:** Let the pinned xLights smoke reach native rendering.
**Changed files/modules:** Native compatibility workflow and evidence tool.
**Intentionally preserved behavior:** CLI output-root protection, pinned renderer, exact-head checkout, and fresh FSEQ requirement.
**New behavior:** Generate into a separate output directory, then stage the resulting XSQ in the disposable native show. Bind audio, layout, and template hashes to the evidence.
**Tests/evidence:** Reproduced the output-root overlap error from PR #260 run 45770486080 on commit `e007e12`.
**Limitations:** Successful native output still requires independent execution of the gate.
**Deferred work:** Native drummer oracle and independently annotated Faces playback.
**Regression risks:** The staged media name must match the reference emitted by Helix.

### 2026-11-26 — Apply explicit BeatGrid in live placement and add exact-head native smoke
**Goal:** Make explicit quantization affect generated XSQ timing rather than rewriting analysis metadata; add repeatable native import/FSEQ evidence.
**Changed files/modules:** BeatGrid helpers, effect engine and wrapper, focused/CLI regressions, native smoke workflow and evidence tool, and the orchestration architecture record.
**Intentionally preserved behavior:** Default and no-grid timing, manual template content, source-clock analysis sidecars, performer onset anchors, and opt-in kit routing.
**New behavior:** Explicit grid starts are decided before admission, with section, duration, layer, cooldown and existing composition constraints retained. The native gate renders a synthetic fixture with checksum-pinned xLights and records exact-commit hashes.
**Tests/evidence:** Added boundary, anchor and FSEQ-header tests and a CLI regression comparing generated XSQ timing with the override disabled and enabled. Native evidence requires a successful workflow run; it is not inferred from structural checks.
**Limitations:** The smoke is not a performer fidelity or hardware test. Explicit start snapping can increase collisions; those are rejected or resolved by the existing placement policy without shifting starts. Reports count admitted attempts, not unique retained effects.
**Deferred work:** Native review against the drummer oracle and independently annotated Faces for the original source, nested physical ownership, accent arbitration, and profiling.
**Regression risks:** Requested strict grids can cause dense cues to compete for one start. The default path is unchanged and no release flag is widened.

### 2026-11-25 — Verify unified orchestration against baseline exports
**Goal:** Compare sequencing quality and preservation over the full song, an opt-in drummer excerpt and a clean-room layout.
**Changed files/modules:** [Unified orchestration architecture, engine map and verification record](docs/UNIFIED_ORCHESTRATION.md).
**Intentionally preserved behavior:** The master roadmap's known-good drummer oracle and outstanding native and beta release gates.
**New behavior:** Recorded playback previews, placement evidence, deterministic output and exact detector-onset comparisons. Full-song role consistency improved from 86.5 to 87.6 and show heuristic from 72.7 to 73.7. The runtime score moved from 96.2 to 95.9. The opt-in excerpt retained 169 exact detector-onset and model matches. The governed real-audio XSQs had zero final budget overages.
**Tests/evidence:** 926 passed, 25 failed, 5 skipped, 1 xfailed and 1 collection error on the sparse checkout. Baseline had the same failure identifiers plus the now-fixed Snowman Band test. Actual XSQ and Helix preview MP4 comparisons were produced. Clean-room repeated XSQs were byte-identical.
**Limitations:** Native xLights REST probe returned connection refused. FSEQ, device packaging and real vocal articulation remain unverified. Preview and runtime heuristics are supporting evidence for choreography, with specific mixed results recorded in the comparison.
**Deferred work:** Native xLights and prior drummer-oracle review, larger fixture and group ownership coverage, platform packaging and annotated vocal acceptance.
**Regression risks:** Additional admitted cross-layer effects can increase visual density. The clean-room clutter heuristic increased while its other scores improved. Keep the band kit path gated pending native visual review.


### 2026-11-25 — Preserve validated layering and kit timing through polish
**Goal:** Keep the exported placements inside the governor's compatibility and budget rules after the final quality pass.
**Changed files/modules:** Effect engine, orchestration balance reporting, polish, and audit/polish regression coverage.
**Intentionally preserved behavior:** Manual template windows, per-layer timeline validation, and legacy audit/polish behavior for the opt-out path.
**New behavior:** In governed runs, audit scores the admitted layers. Polish keeps approved overlaps and rejects proposed timing changes that move anchored cues, switch budget windows, or break layer, prop or manual-content constraints. The report includes final start offsets.
**Tests/evidence:** 19 focused audit, balance, shared context, and CLI tests passed. Before this correction the full-song artifact showed 26 over-budget windows after polish, and an excerpt showed only 138 exact drum target/onset matches.
**Limitations:** Explicit beat-grid overrides remain a separate output postprocess. The final visual comparison and broader regression totals are tracked in the verification entry.
**Deferred work:** Native import and visual playback against the known drummer oracle, platform packages, and physical controller review.
**Regression risks:** Preserving accepted overlap can raise active layer count relative to prior audit flattening. The placement and polish paths enforce the configured concurrent layer limit.


### 2026-11-25 — Give late audio-reactive cues room in the accent budget
**Goal:** Preserve contributions from the catalog-driven audio-reactive pass after pixel and multiband choreography.
**Changed files/modules:** Live budget policy, effect scheduling call site, balance tests and a clean-room CLI integration test.
**Intentionally preserved behavior:** Section limits, quiet gaps, primary ownership, and existing engine switches.
**New behavior:** Hold one overlay slot in eligible windows with a scheduled reactive cue. Release any unused slot after the producer runs. Surface reserved and used counts.
**Tests/evidence:** 15 focused balance, routing and CLI tests passed. The CLI test covers byte-identical XSQ output on repeated inputs, opt-out, manifests, and structural validation. The full test run completed with 925 passed, 25 failed, 5 skipped, 1 xfailed and 1 collection error. The baseline on the same sparse checkout had 915 passed and one additional failure in Snowman Band.
**Limitations:** Existing audit and polish timing changes can move admitted overlays between windows. The evidence exposed this as a follow-up requirement before enforcing final budget guarantees.
**Deferred work:** Carry the policy through the last timing pass and repeat rendered verification.
**Regression risks:** Reserving capacity changes competing accent placements. The real-audio excerpt retained nine audio-reactive effects, compared with zero in the first governor trial.


### 2026-11-25 — Close bounded intent feedback and verify serialized output
**Goal:** Connect the existing readability evaluator and correction loop to the real-audio director and surface XSQ validation in runtime diagnostics.
**Changed files/modules:** Director, canonical timeline, autonomous render validation, effect engine, and context/quality tests.
**Intentionally preserved behavior:** Seeded bridge API and pass list, original user files, and live audit/polish pipeline.
**New behavior:** Correct at most once when the intent simulator produces concrete issues. Keep the candidate only if it removes issues without creating others. Validate generated effect bounds and palette references after writing XSQ and report those findings alongside the live decisions.
**Tests/evidence:** 28 focused context, correction, output palette, bridge, and band tests passed.
**Limitations:** The simulator grades intents before placement. XSQ probing checks structure and palette references, not pixel output or native import. Explicit custom beat-grid postprocessing happens later.
**Deferred work:** Recheck visual and timing results against native FSEQ and signed Windows/Android packages.
**Regression risks:** A readable plan does not guarantee playable native effect settings. Keep native verification distinct in artifact reports.


### 2026-11-25 — Restore band cues and admit dedicated drum hits
**Goal:** Route existing drummer analysis to valid physical kit components and protect anchored performer timing.
**Changed files/modules:** Snowman Band cue adapter, orchestration balance attribution, effect engine runner, and Snowman Band tests.
**Intentionally preserved behavior:** Legacy drum mapper keys, fallback choreography on non-kit layouts, existing Hardkor vocabulary, and dedicated drummer workflows.
**New behavior:** Join legacy drum cue tags with mapper-produced components. The opt-in `--orchestrate-band-performers` sends supported kit hits to live placement; their starts and Faces effect starts are held through placement retries.
**Tests/evidence:** 30 focused band, balance, Birdsong and Hardkor tests passed. The parent branch reproduces the band cue `KeyError('composite_submodels')`.
**Limitations:** Existing mapper and fixture geometry contain legacy drum component names. Only explicit model matches or the legacy named tom/cymbal components are used. Native performer rendering remains open.
**Deferred work:** Verify full nine-component native geometry, mouth and face playback, and the prior drummer MP4 oracle on the target platform.
**Regression risks:** Restoring the band payload can expose previously bypassed face routes. The new physical drummer placements remain opt-in.


### 2026-11-25 — Govern live effect placement
**Goal:** Hold competing effects to a common ownership, priority and density policy before XSQ serialization.
**Changed files/modules:** Composition governor, orchestration balance, live placement in effect engine, and balance tests.
**Intentionally preserved behavior:** Existing effect, palette and layer compatibility rules, explicit template promotion, and fallbacks on layouts without dedicated models.
**New behavior:** Every live placement records a proposal decision. Only successful placements consume section budgets on the actual start time. Measured quiet windows and the director's low-density passages tighten overlay capacity. Owned specialist and primary placements take precedence over accent effects on the same layer.
**Tests/evidence:** 22 focused tests passed. The three-model CLI smoke emitted 12 placed effects in an early run of this policy. The unmodified Helixville4 baseline emitted 986 effects from a 36-second real-audio excerpt with quality score 92.9.
**Limitations:** Output report reflects live placement before any explicitly requested beat-grid postprocessing. Model ownership is inferred from names. Structural and render validation are separate gates.
**Deferred work:** Make specialist timing verifiable, repair existing Snowman Band contract failure, and compare current final artifacts.
**Regression risks:** Tight budgets and role assignments can suppress accents on unusually named layouts. The CLI can select previous admission policy with `--no-unified-orchestration`.


### 2026-11-25 — Share analyzed timing with existing planners
**Goal:** Carry live musical timing and available features into the canonical director and specialist planners.
**Changed files/modules:** Canonical timeline, director, effect engine, and musical-context tests.
**Intentionally preserved behavior:** Existing analytics and feature switches, seeded bridge/template promotion, and specialist planner inputs and ordering.
**New behavior:** Snapshot live milliseconds, beat subdivisions, local tempo, sections, notes, vocals, percussion, quiet windows and dynamic marks. Convert units at the intent graph boundary. Chronoflow, Band Sync, and Snowman Band consume this snapshot.
**Tests/evidence:** 11 context, Band Sync and bridge tests passed. Snowman Band exposed a separately tracked drum-mapping contract failure.
**Limitations:** Additional stereo/piano-roll analysis and specialized phoneme generation remain with their current producers. The live governor is pending.
**Deferred work:** Live decision policy, correction, diagnostics, and render comparisons.
**Regression risks:** Future consumers should keep beat and note timestamps in milliseconds until the intent boundary.


### 2026-11-25 — Unified orchestration discovery
**Branch:** `feature/unified-intelligence-orchestration`

**Goal:** Trace the live renderer and establish a baseline for shared timing and cooperative placement.
**Changed files/modules:** Added [architecture and engine inventory](docs/UNIFIED_ORCHESTRATION.md).
**Intentionally preserved behavior:** Runtime unchanged.
**New behavior:** Recorded the seeded director sidecar and live export paths, duplicated work, timing boundaries and placement hazards.
**Tests/evidence:** 34 focused baseline tests passed. Clean-room CLI run emitted an eight-effect XSQ with quality score 81.0.
**Limitations:** No installed native xLights renderer. Native import and FSEQ evidence remain open.
**Deferred work:** Complete real-audio comparison, wire analyzed context and governor, and review visual output.
**Regression risks:** Changes to placement accounting can affect dense chords, intended layers, and section-boundary effects.


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
