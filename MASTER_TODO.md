# HELIX MASTER TODO & AGENT HANDOFF LEDGER

> Canonical project roadmap and cross-agent handoff layer.

## Current mission
Build Helix into a reliable AI-assisted xLights auto-sequencer while preserving deterministic sequencing, verified artifacts, and cumulative behavior.

**Current priority:** finish drummer/band logic and prove it with real-song XSQ + MP4 artifacts.

## Drummer / band current state
- [x] Canonical nine-component drummer contract documented.
- [x] Runtime drummer state model changed to nine integrated hit components.
- [x] Structure catalog changed to nine drummer sequencing components.
- [x] XML exporter no longer emits the legacy `line0="1-4"` placeholder for drummer components.
- [x] Pose geometry spec now defines nine component composites with embedded contacting-stick geometry.
- [~] xLights model exporter still needs to emit the new component composites as the nine canonical sequencing submodels.
- [x] Drum detector uses HPSS/percussive onset analysis plus spectral features and a second positive-spectral-flux candidate detector.
- [x] Classification now exposes independent drum-family evidence and can preserve compatible simultaneous hits instead of forcing one winner.
- [x] Optional `htdemucs_6s` separation produces vocals/drums/bass/guitar/piano/other with source-audio SHA-256 caching and deterministic local fallback.
- [x] Production drummer XSQ injection now consumes the stem-analysis path and prefers the isolated drums stem.
- [x] Per-event source/stem provenance, family scores, and detector-agreement evidence are available in drum diagnostics.
- [~] Real-song direct-mix vs Demucs-drums validation workflow is implemented and awaiting/collecting CI artifact evidence.
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
**audio → hash-validated stem cache → optional htdemucs_6s → isolated drums stem → HPSS/percussive isolation → onset + spectral-flux candidates → independent drum-family evidence → compatible multi-hit selection → ambiguity handling → drummer mapper → XSQ**

When the Demucs executable/model is available, the production drummer path now uses real neural six-stem separation. When it is unavailable or separation fails, Helix keeps the deterministic local HPSS/frequency-mask fallback. Real-song quality claims still require the direct-mix-vs-stem diagnostics and rendered MP4 verification gate below.

## Ground-truth regression oracle
A prior drummer render was explicitly identified by the user as having the **correct drummer logic** and must be preserved as the behavioral reference while the implementation is upgraded.

- Known-good commit: `b27e8d77a63027ed32bcf6851dcff3925472c155`.
- Prior successful artifact lineage: **Helix Full Current 256 + Drummer**; published workflow run `35486153096` was previously identified as the MP4-producing run.
- The repository's dedicated ground-truth workflow at that point exercised the real V3 drummer submodels and generated deterministic audio/XSQ/preview artifacts.
- Important historical contract: that older workflow used **8 V3 submodels** (kick, snare, hi-hat, left/right cymbal, left/right tom, drumkit-all). It is a regression oracle for behavior, not a reason to revert the current physical nine-component design.
- Current nine-component geometry remains authoritative for the new implementation: four tom zones and contacting-stick geometry integrated into the hit component.

**Rule:** do not discard or rewrite the behavior that made the prior render correct. New detection/mapping logic must be compared against the prior oracle before being accepted.

## Verification gate
**audio → detected events → mapped components → XSQ → full-song MP4 with real audio → compare against prior correct drummer render → human visual review**

Do not mark complete from unit tests alone.

## Change Ledger

### 2026-10-01 — Derwin-inspired six-stem production audio path
**Agent:** ChatGPT/GitHub
**Branch:** `codex/derwin-audio-intelligence-v1`
**PR:** #124

**Changed:**
- Switched optional Demucs model to `htdemucs_6s` and preserved guitar/piano stems.
- Added SHA-256 stem-cache manifests so expensive separation can be reused safely.
- Routed the real drummer injector through `build_stem_analysis()` instead of direct full-mix detection.
- Added spectral-flux candidate detection beside the existing HPSS/librosa onset detector.
- Added independent per-family scores, compatible simultaneous-hit selection, source provenance, and detector-agreement evidence.
- Fixed the diagnostics tool to read actual `DrumEvent` labels/features instead of reclassifying a nonexistent field.
- Suppressed raw ambiguous `drum_bus` placements when typed evidence exists and removed duplicate bus/distribution scheduling.
- Added a real-song diagnostic workflow comparing direct mix against the isolated Demucs drums stem.
- Updated the full current drummer workflow to install Demucs, use the hash-keyed stem cache, and render from the production stem-aware injector.

**Verification in progress:** real `Helix Audiolights.mp3` class balance, drum-bus fraction, detector agreement, XSQ injection, and MP4 timing.

### 2026-09-30 — Ground-truth regression oracle locked
**Agent:** ChatGPT/GitHub
**Branch:** `feature/restructure-core`

**Recorded:**
- Prior known-good drummer behavior is anchored to commit `b27e8d77a63027ed32bcf6851dcff3925472c155`.
- The historical 8-submodel V3 workflow is retained as a behavioral regression reference while the physical model evolves to nine components.

### 2026-09-30 — Confidence-gated drum classification
**Agent:** ChatGPT/GitHub
**Branch:** `feature/restructure-core`
**Commit:** `b8e7f8fa5ab5044c774b3ca482711b47b89fb61e`

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
