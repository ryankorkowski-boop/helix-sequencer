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

## Current V3 drummer contract — independent component lighting

This supersedes the nine-component/four-tom V3 claims retained below as history.

- Eight hit targets: KICK, SNARE, HI_HAT, TOM_HIGH, TOM_MID, TOM_FLOOR, CYMBAL_LEFT, CYMBAL_RIGHT.
- HIGH is image-right, MID image-left, FLOOR lower-left. The extra lower-right drum is unused.
- Snare/toms/cymbals include the corresponding existing arm/stick pixels; kick has no arm/stick; hi-hat includes the foot/pedal and no arm/stick.
- Inactive artwork stays at fixed 28% idle brightness. Simultaneous hits take a max-union; shared arms do not compound brightness.
- Source remains \`fixtures/band_geometry/source/drummerbg.png\`; no substitute drummer.

### Running implementation checklist
- [x] Replace misregistered primitive lighting with source-normalized physical surfaces/actuators.
- [x] Export integrated eight public hit targets plus \`_SURFACE\` geometry submodels.
- [x] Render actual xmodel node ranges and reject missing/empty/out-of-range geometry.
- [x] Remove global brightness changes and painted yellow blobs.
- [x] Use max-union simultaneous hits and exclude other instrument surfaces from actuator contributions.
- [x] Derive PNG review layers from the same exported nodes.
- [x] Share one deterministic event oracle between WAV and XSQ; 68 events over 20 seconds.
- [x] Fix the former starter-model/manifest expected failure and archive that legacy contract.
- [x] GitHub Actions verification of the reconstructed branch: run `37416429803` passed regeneration, oracle checks, 37 focused tests, rendering and artifact upload.
- [ ] User visual approval of the reconstructed candidate.
- [ ] xLights import/playback confirmation.
- [ ] Real-song drum detection/guitar rejection evaluation; unchanged by this visual fix.

See \`docs/DRUMMER_INDEPENDENT_LIGHTING_HANDOFF.md\` for reproduction and limitations.

## Historical drummer / band state — superseded for V3

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

## Historical nine-component contract — superseded for V3
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

### 2026-10-06 — Reconstruct independent V3 component lighting
**Goal:** restore the tested independent-lighting design from the saved candidate artifacts and handoff after the original local patch could not be recovered.
**Changed:** V3 pose geometry, xmodel exporter/static asset, node-driven PNG layer builder, canonical preview renderer, shared fixture oracle/WAV/XSQ exporters, focused tests, ground-truth workflow, runtime hi-hat description, geometry manifest, and this ledger.
**Preserved:** canonical source image, eight public XSQ target names, HIGH-right/MID-left/FLOOR-left orientation, deterministic sequencing contract, extra-drum exclusion, and production drum detector.
**New:** source-aligned surfaces/actuators, integrated hit nodes, dense xmodel grid, portable background path, fixed 28% idle brightness, xmodel-node-driven max-union rendering, hi-hat foot/no-arm behavior, and exact WAV/XSQ oracle agreement.
**Evidence:** GitHub Actions run `37416429803` passed canonical regeneration, exact 68-event WAV/XSQ agreement, 37 focused tests with 3 existing deprecation warnings, and a 20-second H.264/AAC render at 24 fps. All eight isolated decoded states were inspected after encoding; the kick/snare shared-cell regression was corrected by exclusive instrument-surface ownership. User approval and native xLights import remain open.
**Limitations/deferred:** static reference arms illuminate but are not re-posed; xLights native import and real-song detector quality remain separate gates.
**Regression risks:** public hit targets now include actuator nodes; geometry-only checks must use \`_SURFACE\` submodels.

### 2026-10-06 — Resolve legacy starter expected failure
**Goal:** make the archived starter xmodel/manifest contract internally valid without confusing it with the active V3 runtime.
**Changed:** starter HEAD and DRUMKIT_ALL unions, geometry manifest active/archived split, strict xmodel and manifest tests.
**Preserved:** all existing starter node ranges and all five active performer identities other than replacing the obsolete starter drummer identity with V3.
**New:** starter contract is archived and fully testable; active manifest resolves the V3 runtime.
**Evidence pending:** focused CI on the publication branch.


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


## Publication status
- [x] User explicitly authorized publication.
- [x] GitHub write access restored.
- [ ] Publish and validate \`fix/drummer-independent-illumination\`.
