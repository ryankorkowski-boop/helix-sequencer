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

## Change Ledger — main-path xLights contract

### 2026-11-04 — Failed audio or a missing sequence exits non-zero
**Branch:** `cursor/main-path-xsq-fixes-41d8`

**Goal:** A per-audio generation error, or a run that does not write a new `.xsq`, must fail the process and be visible in the run manifest and the per-audio report (issue #114).

**Changed:** `core/effect_engine.py`, `core/effect_engine_beat_grid.py`, `core/sequence_builder.py`, `tests/test_sequence_generation_failures.py`, `tests/test_sequence_builder_orchestrator_promotion.py`

**Preserved:** Successful runs still finalize `success: true`. Orchestrator promotion and BeatGrid flag stripping are unchanged. The birdsong post-hook can still fail without failing the sequence.

**New behavior:** `effect_engine.main_for` records each audio failure (exception text plus traceback) in `*.report.json` and raises `SequenceGenerationError`. `run_profile` finalizes the manifest as failed and exits 1 when that exception escapes, when the engine raises `SystemExit`, or when no new `.xsq` appears under the output root.

**Tests:** `tests/test_sequence_generation_failures.py` and the orchestrator promotion tests.

**Limitations:** The underlying Lights Out render exception from the original workflow run was not reproduced here. This commit fixes the success contract, not a specific effect-engine crash.

**Deferred:** Overlap with open PRs #206/#207, which also edit `sequence_builder.py` (duplicate helper removal and effective engine args). Those edits are left in place on their branches. #188 is untouched.

**Regression risks:** Callers that treated a logged `FAILED:` line as a successful process exit now get a non-zero exit. Tests that mock the engine must write an `.xsq` if they expect success.

### 2026-11-04 — Sequence duration follows the audio
**Branch:** `cursor/main-path-xsq-fixes-41d8`

**Goal:** `<head><sequenceDuration>` matches the audio length, and effect rows and timing marks do not extend past that end.

**Changed:** `xlights/xml_io.py`, `xlights/xsq_writer.py`, `core/effect_engine.py` (`run_variant`, immediately before the `.xsq` write), `tests/test_sequence_duration.py`

**Preserved:** `replace_audio_references` still only swaps the media filename. Effect placement still uses the analyzed `song_length_ms`. A non-positive duration raises instead of writing a zero-length sequence.

**New behavior:** `apply_sequence_duration` writes the duration in seconds (3 decimal places, matching the template) and clips or drops `Effect` rows, including timing-track marks, at the audio end. `run_variant` calls it with `audio.dur_s` from `xsq_writer.analyze`.

**Tests:** `tests/test_sequence_duration.py` loads `template.xsq` (132.039 s) and applies a generated 30.000 s WAV. A second case clips a crossing effect and drops a timing mark that starts at the boundary.

**Limitations:** Not opened in xLights. Duration comes from the analyzer's sample count (`len(y) / sr`), which matches the WAV header used in the test. MP3 frame padding was not compared against an xLights media import.

**Deferred:** Showcase generation (`GENERATE_SHOWCASE`) rewrites a second file and does not call this helper itself.

**Regression risks:** Template effects that used to survive past a shorter song are now clipped or removed on write.

### 2026-11-04 — Effects store ref and palette indexes
**Branch:** `cursor/main-path-xsq-fixes-41d8`

**Goal:** Placed effects carry `ref` and `palette` indexes into `EffectDB` and `ColorPalettes`, the way `template.xsq` and xLights store them, instead of inline `settings` / palette strings.

**Changed:** `xlights/xml_io.py`, `xlights/xsq_writer.py`, `core/effect_engine.py`, `helix_intent/xsq_template_writer.py`, `tests/test_effect_db_roundtrip.py`, `tests/test_xsq_template_writer.py`

**Preserved:** Reading still accepts an inline `settings`/`data` string or an inline palette string when no index is present. An existing EffectDB or ColorPalettes row is reused when the text matches. Callers that do not pass the document root still write the legacy attributes.

**New behavior:** `add_effect(..., root=)` and the orchestrator template writer intern settings and palette text, then write `ref` and `palette` indexes. Readers resolve those indexes back to the stored strings. A round-trip check reports any Effect whose index does not resolve.

**Tests:** `tests/test_effect_db_roundtrip.py` proves every Effect `ref` and `palette` resolves after write and reparse, including a newly appended EffectDB row. The template-writer test now checks the resolved strings.

**Limitations:** Not opened in xLights. EffectDB child order is the index, matching xLights. Timing-mark rows that only carry a `label` are not required to have a `ref`.

**Deferred:** None for this storage format.

**Regression risks:** Code that read the `settings` attribute off a newly written Effect now has to resolve `ref`. The main path and the template writer were updated.

### 2026-11-04 — Submodel rows nest under the parent model
**Branch:** `cursor/main-path-xsq-fixes-41d8`

**Goal:** Submodel effects are `<SubModelEffectLayer name="...">` inside the parent model `Element`. Only models and model groups are top-level sequencer rows.

**Changed:** `xlights/layout_sync.py`, `xlights/xml_io.py`, `xlights/xsq_writer.py`, `tests/test_layout_submodels.py`

**Preserved:** Model groups stay top-level `type="model"` rows, which is how `template.xsq` and the xLights sequencer store groups. Submodel names remain addressable as `Parent/Sub` in `xsq.elements` so effect placement can still target them. Aliases still resolve.

**New behavior:** Layout sync no longer emits `Parent/Sub` as its own `Element`. An existing top-level submodel row is folded into the parent's `SubModelEffectLayer`, and its effect layers move with it. `SubModelEffectLayer` is not treated as an ordinary effect layer. Confirmed against xLights' saved shape (`Element` → `EffectLayer` and `SubModelEffectLayer` → `EffectLayer` → `Effect`), including the `fixtotime` sequence script's grouping. Not re-saved from the xLights GUI in this environment.

**Tests:** `tests/test_layout_submodels.py` builds a layout with a group, a model, and two submodels, folds a legacy `Arch/Left` row, and reloads the file.

**Limitations:** Nested submodels of submodels are indexed if present, but the layout parser only emits one `Parent/Sub` level. Display rows for submodels are omitted; xLights expands those from the layout model.

**Deferred:** None.

**Regression risks:** Tools that expected a top-level element named `Parent/Sub` will now find that node nested. `xsq.elements["Parent/Sub"]` still points at the nested layer.

### 2026-11-04 — Absolute start channels for every xLights address form
**Branch:** `cursor/main-path-xsq-fixes-41d8`

**Goal:** `>Model:N`, `@Model:N`, `#universe:N`, `#ip:universe:N`, and `!Controller:N` resolve to an absolute start and end channel, with the controller when the networks file can name one. Chains, submodels, and circular references have explicit results.

**Changed:** `core/start_channels.py`, `core/model_parser.py`, `core/controller_parser.py`, `tests/test_start_channels.py`

**Preserved:** A plain integer start channel is still absolute and 1-based. `parse_layout` does not raise; it stores `start_channel_error` on the model. Models with a blank `StartChannel` chain after the previous root model, which is xLights' default when nothing else is set. Helixville4's 105 models all have integer starts, and parsing them reports no resolution errors.

**New behavior:** `layout_channel_count` is the highest resolved end channel. It no longer sums every model's span on top of that end, which was the overestimate. Unresolvable or circular references raise `StartChannelError` from `layout_channel_count` and from `resolve_model_channels(..., strict=True)`. Universe tables come from controller order in `xlights_networks.xml`. A legacy E1.31 row still treats `BaudRate` as the universe number. Submodel channel bounds follow `line` / `subBuffer` node numbers and the parent's channels per node.

**Deviation from xLights:** xLights refuses `>` when the referenced model has no controller. Helix still computes the channel so layouts that never assigned controllers keep working, and fills `controller_name` when a networks span contains the channel.

**Tests:** `tests/test_start_channels.py` covers each format, a three-model chain, submodels, a legacy BaudRate universe, circular and missing references, and the highest-end channel count.

**Limitations:** Individual per-string start channels (`Individual Start Channels`) are not resolved. Controller ports and smart receivers are not modeled; controller spans are the networks file's channel sizes in document order.

**Deferred:** Per-string `StringN` start channels.

**Regression risks:** `layout_channel_count` can now raise on a broken reference, and it can return a smaller number than the old sum. Callers that used the inflated sum to size a preview controller will size to the real last channel instead.

### 2026-11-04 — Custom-model grids use real node numbers
**Branch:** `cursor/main-path-xsq-fixes-41d8`

**Goal:** `CustomModel` and `CustomModelCompressed` define the node count and the pixel map. Submodel `line` ranges select those node numbers. A custom model with no grid is a layout-health error instead of a width-times-height straight line.

**Changed:** `core/custom_model_grid.py`, `core/model_parser.py`, `helix_layout/layout_health.py`, `tests/test_custom_model_grid.py`

**Preserved:** xLights reads `CustomModelCompressed` when it is non-empty, otherwise `CustomModel`. Layers are `|`, rows `;`, cells `,`. Compressed entries are `node,row,col` or `node,row,col,layer` with 0-based indexes. Values `<= 0` and blank cells are empty. Duplicate node numbers keep the first cell. Image models that use the `CustomModel` class but are not `DisplayAs="Custom"` still use the previous pixel map.

**New behavior:** Node count is the number of distinct node numbers. The pixel map is sorted by node number and placed at cell centers inside the model's world bounds (`WorldPos` through `X2`/`Y2`/`Z2`), with row 0 at the top. Submodel ranges look up `PixelPoint.index` (node number minus 1) instead of a compact list position. A custom model with no positive nodes sets `custom_grid_missing`, `total_pixels=0`, and an empty pixel map. Layout health lists those models. Submodels of a gridless parent do not inherit a fake channel span.

**Helixville4:** All 24 `DisplayAs="Custom"` models in `helixville4/xlights_rgbeffects.xml` have `CustomWidth`/`CustomHeight` 12 and submodel `line0` ranges, and neither `CustomModel` nor `CustomModelCompressed`. They were not regenerated. `tools/build_helpers/helixia.py` writes a similar 12 by 12 placeholder with no grid, but for different names, and `build_helixia_layout` copies the committed file. `models/helixia_props.py` is structure-only and sets `layout_generation` false. `helixville4_full_band.py`, `helixville4_finished_band.py`, and `helixville4_floor_piano.py` do emit `CustomModel` strings, for other model names and sizes (their tests require `CustomWidth` not equal to 12). None of those generators owns the wiring for these 24 models. A real node map from the prop, or from a generator that already knows the node coordinates, is required. Inventing a grid was not done.

**Tests:** `tests/test_custom_model_grid.py` covers both encodings, compressed-over-plain, layers, duplicate nodes, world bounds, submodel node numbers, a missing-grid health error, and the 24 helixville4 models.

**Limitations:** Not loaded in xLights. Per-string `StringN` channel starts inside a custom model are not applied. Multiple buffer coordinates for one node number collapse to the first cell.

**Deferred:** Authoring grids for the 24 helixville4 custom models once a real wiring source exists.

**Regression risks:** Custom models that previously reported `width * height` pixels now report the real node count, or zero when the grid is missing. Sequencing that targeted those fake pixels will see an empty map.

## Next actions
1. Preserve the prior known-good drummer behavior as the regression baseline.
2. Reconcile xLights drummer geometry with the nine canonical composites.
3. Add event provenance/debug output.
4. Run detector on the repository's real song and inspect event counts by class/confidence.
5. Generate full-song XSQ.
6. Render full-song MP4 with real audio.
7. Compare rendered component flashes to actual audible drum events and the prior known-good render.
8. Iterate only on measured false positives/false negatives.
