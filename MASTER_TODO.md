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

## Competitive optimization track (started 2026-11-16)
See `docs/HELIX_COMPETITIVE_OPTIMIZATION_ROADMAP.md` for full plan.

- [x] Roadmap document created on feature/competitive-optimization-roadmap-20261116.
- [x] Slice 1: Sequence plan contract (`core/sequence_plan.py`) added and fail-soft wired into full_show_orchestrator.
- [ ] Slice 2: Prop role map.
- [ ] Slice 3: Density and restraint rules.
- [ ] Slice 4: Section identity scoring.
- [ ] Slice 5: Palette discipline.
- [ ] Deeper integration into sequence_builder (advisory first).
- [ ] Tests and quality report hooks.

## Drummer / band current state
- [x] Canonical three-tom / eight-component drummer contract documented (`docs/DRUMMER_THREE_TOM_GROUND_TRUTH.md`, `docs/DRUMMER_COMPONENT_CONTRACT.md`).
- [x] Runtime and structure catalog use the eight sequenced components (Kick, Snare, Hi-hat, High/Mid/Floor Toms, Left/Right Cymbals).
- [x] XML exporter no longer emits the legacy `line0="1-4"` placeholder for drummer components.
- [x] Sticks and arms are visual/contact geometry only; they are never independent sequencing targets.
- [~] xLights model exporter still needs to emit the eight canonical sequencing submodels.
- [~] Drum detector uses HPSS/percussive onset analysis plus spectral features.
- [x] Classification now rejects high harmonic-contamination candidates when unsupported and suppresses ambiguous low-margin classifications into `drum_bus`.
- [ ] Add per-event source/stem provenance to rendered XSQ debug metadata.
- [ ] Validate detector against real-song audio and quantify false positives.
- [ ] Generate real-song XSQ.
- [ ] Render full-song MP4 with audio.
- [ ] Human visual review of rendered drummer timing.

## Canonical drummer components
1. `HX_SNOWMAN_DRUMMER_KICK`
2. `HX_SNOWMAN_DRUMMER_SNARE`
3. `HX_SNOWMAN_DRUMMER_HI_HAT`
4. `HX_SNOWMAN_DRUMMER_TOM_HIGH`
5. `HX_SNOWMAN_DRUMMER_TOM_MID`
6. `HX_SNOWMAN_DRUMMER_TOM_FLOOR`
7. `HX_SNOWMAN_DRUMMER_CYMBAL_LEFT`
8. `HX_SNOWMAN_DRUMMER_CYMBAL_RIGHT`

**Physical rule:** There is no fourth tom. Contacting stick geometry is part of the hit component visually; there are no independent stick or arm sequencing channels. Kick has no stick. Left and right cymbals alternate on ordinary fills/crashes. Simultaneous events must be preserved.

## Detection architecture
**audio → HPSS/percussive isolation → onset candidates → spectral/transient features → confidence-gated drum classification → eight-component mapper → XSQ**

## Ground-truth regression oracle
A prior drummer render was explicitly identified by the user as having the **correct drummer logic** and must be preserved as the behavioral reference while the implementation is upgraded.

- Known-good commit: `b27e8d77a63027ed32bcf6851dcff3925472c155`.
- Prior successful artifact lineage: **Helix Full Current 256 + Drummer**; published workflow run `35486153096` was previously identified as the MP4-producing run.
- The repository's dedicated ground-truth workflow at that point exercised the real V3 drummer submodels and generated deterministic audio/XSQ/preview artifacts.
- Authoritative physical kit is the three-tom contract: High, Mid, and Floor toms only. Historical four-tom language is superseded.

**Rule:** do not discard or rewrite the behavior that made the prior render correct. New detection/mapping logic must be compared against the prior oracle before being accepted. Never emit `TOM_4` or independent stick sequencing targets.

## Verification gate
**audio → detected events → mapped components → XSQ → full-song MP4 with real audio → compare against prior correct drummer render → human visual review**

Do not mark complete from unit tests alone.

## Change Ledger

### 2026-11-16 — Competitive optimization roadmap and Slice 1 sequence plan
**Agent:** Grok
**Branch:** feature/competitive-optimization-roadmap-20261116

**Recorded:**
- Added `docs/HELIX_COMPETITIVE_OPTIMIZATION_ROADMAP.md` consolidating competitive differentiators and implementation slices.
- Added minimal `core/sequence_plan.py` (SectionPlan / SequencePlan + build_minimal_plan).
- Fail-soft wired sequence_plan into `full_show_orchestrator.apply_full_show_enhancements` so reports include the plan.
- Updated this ledger with the new track and checklist.

**Intentionally preserved:** No change to default sequence generation output.

### 2026-11-15 — Align MASTER_TODO with three-tom canonical contract
**Agent:** Grok
**Branch:** main

**Recorded:**
- Removed stale nine-component / four-tom language from the drummer sections.
- Aligned the current-state checklist, component list, detection architecture, and ground-truth notes with `docs/DRUMMER_THREE_TOM_GROUND_TRUTH.md` and `docs/DRUMMER_COMPONENT_CONTRACT.md`.
- Confirmed eight sequenced components only (Kick, Snare, Hi-hat, High/Mid/Floor Toms, Left/Right Cymbals). Sticks remain visual geometry only.

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
- The historical V3 workflow is retained as a behavioral regression reference. Physical naming must follow the three-tom contract.

### 2026-09-30 — Confidence-gated drum classification
**Agent:** ChatGPT/GitHub
**Branch:** `feature/restructure-core`
**Commit:** `b8e7f8fa5ab5044c774b3ca482711b47b89fb61c`

**Changed:** `audio/drum_classification.py`
- Added harmonic-contamination gating using the existing percussive/harmonic ratio.
- Added a minimum score-margin requirement between the best and runner-up drum classes.
- Ambiguous or weak events now become `drum_bus` instead of being confidently misclassified.

**Preserved:** existing kick/snare/tom/hat/cymbal feature scoring and event schema.

**Not yet verified:** real-song false-positive rate, XSQ output, and MP4 behavior.

### 2026-09-30 — Drummer geometry notes (superseded four-tom language)
**Agent:** ChatGPT/GitHub
**Branch:** `feature/restructure-core`

**Changed:** `fixtures/band_geometry/drummer_v3_pose_spec.json`
- Historical note only. Four-tom / nine-component language is superseded by the three-tom ground-truth and component-contract documents.
- Contacting sticks remain embedded visual geometry, not independent sequencing targets.

## Next actions
1. Preserve the prior known-good drummer behavior as the regression baseline.
2. Reconcile xLights drummer geometry with the eight canonical components (three toms only).
3. Continue competitive optimization: implement prop role map (Slice 2) and deepen sequence_plan usage.
4. Add event provenance/debug output.
5. Run detector on the repository's real song and inspect event counts by class/confidence.
6. Generate full-song XSQ.
7. Render full-song MP4 with real audio.
8. Compare rendered component flashes to actual audible drum events and the prior known-good render.
9. Iterate only on measured false positives/false negatives.
