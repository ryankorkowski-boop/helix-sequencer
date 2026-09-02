# Wadena Execution Roadmap v2

> Autonomous execution plan after obtaining the actual MP4 recording. This roadmap is deliberately evidence-first: direct frame/audio observations are separated from inference, and no test/render is marked complete until an artifact exists.

## 0. Evidence baseline — COMPLETE

- [x] Obtain playable MP4 rather than relying on YouTube access.
- [x] Measure video/audio duration, frame count, FPS and resolution.
- [x] Extract embedded audio for analysis.
- [x] Produce coarse visual-state measurements.
- [x] Produce visual transition candidates.
- [x] Produce audio onset candidates.
- [x] Record the 230.5 s video vs 246.93 s LMS clock mismatch.
- [x] Refuse duration-only time stretching as an alignment method.

## 1. Build the visual calibration fixture — NEXT

- [ ] Sample candidate transition windows at frame-level resolution (not only 0.5/2 s).
- [ ] Compute left/center/right activity centroid and transition magnitude for each window.
- [ ] Classify visible changes as field, propagation, pulse, reset, hero, punctuation, or uncertain.
- [ ] Attach confidence to every observation.
- [ ] Create `data/wadena_video_calibration.json` containing observations only; no guessed channel IDs.
- [ ] Create tests proving calibration data is deterministic and schema-valid.

## 2. Establish audio ↔ video synchronization

- [ ] Compare video-audio onset envelope against visual transition envelope.
- [ ] Detect stable musical section boundaries and repeated motifs.
- [ ] Search for multiple independent audio/visual anchors.
- [ ] Determine whether the recording is cropped, edited, or a different Nutcracker/Nutrocker performance before aligning to LMS.
- [ ] If a defensible offset/segment mapping exists, record it as an interval with confidence rather than a forced global warp.
- [ ] If no defensible mapping exists, keep the video as an independent choreography reference fixture.

## 3. Extract choreography grammar

- [ ] Label recurring spatial gestures: left→right, right→left, center→out, out→center, vertical/bottom→top, impact propagation, quiet/reset.
- [ ] Detect persistent infrastructure fields separately from transient phrase events.
- [ ] Measure whether propagation is sequential, overlapping, or simultaneous.
- [ ] Estimate gesture duration, dwell, overlap and decay.
- [ ] Identify hero-element participation vs support-element participation.
- [ ] Identify color-state changes that span multiple physical regions.
- [ ] Encode a compact reusable gesture vocabulary in renderer-independent terms.

## 4. Fix/strengthen the spatial intent compiler

- [ ] Review `core/wadena_spatial_intent.py` against observed gesture timing.
- [ ] Separate spatial ordering from temporal wave propagation.
- [ ] Add explicit propagation profile: launch → travel → decay.
- [ ] Preserve deterministic landmark routes from `core/wadena_spatial_graph.py`.
- [ ] Add role-aware participation: hero / infrastructure / impact / punctuation / perimeter.
- [ ] Add quiet/reset intent that can intentionally reduce activity.
- [ ] Add tests for route ordering, temporal propagation, strength clamping and invalid-landmark fail-safe behavior.

## 5. Replace species semantics in Birdsong

- [ ] Remove species/confidence semantics from the active music-first path.
- [ ] Preserve useful acoustic primitives: F0, RMS/energy, onset, spectral centroid/bandwidth/flux, phrase/tension.
- [ ] Convert acoustic state into trajectory/gesture descriptors.
- [ ] Add instrument-aware priors only where evidence is reliable.
- [ ] Keep graceful fallbacks when pitch or instrument inference is uncertain.
- [ ] Ensure deterministic output from identical audio + configuration.

## 6. Integrate without breaking electrical truth

- [ ] Keep `sequence_builder → effect_engine → xsq_writer` authoritative for electrical output.
- [ ] Feed spatial intent into existing effect selection rather than bypassing it.
- [ ] Preserve independent R/G/W AC channels.
- [ ] Never synthesize RGB values as electrical truth.
- [ ] Quantize visual color intent to available AC color channels only at the final rendering stage.
- [ ] Add channel-truth regression tests.
- [ ] Add fail-safe fallback to existing behavior when spatial intent is unavailable.

## 7. Complete Wadena physical digital twin

- [ ] Bind all known truth models to physical coordinates.
- [ ] Map every major model family to a physical primitive or explicit fallback.
- [ ] Finish mega-tree ring rendering.
- [ ] Verify spiral-tree path orientation and density.
- [ ] Verify mini-tree density and spacing.
- [ ] Add front/wide/close camera presets.
- [ ] Add optional model/channel/landmark diagnostic overlays.

## 8. Calibration against the supplied professional LMS

- [ ] Inventory all 256 channels and model/color conventions.
- [ ] Preserve the LMS 0.05 s timing grid when using it as timing authority.
- [ ] Compare persistent vocabulary layers: snowflakes, beat sticks, candy canes, perimeter/roof/wreath.
- [ ] Treat mega-tree activity as sectional rather than always-on hero behavior.
- [ ] Measure copied/coherent timing blocks and controlled offsets.
- [ ] Use LMS evidence to calibrate density, persistence, offsets and effect vocabulary—not to invent physical geometry unsupported by evidence.

## 9. Proof sequence

- [ ] Generate a baseline existing-engine XSQ.
- [ ] Generate the same input with spatial-intent enabled.
- [ ] Verify identical electrical constraints/channel validity.
- [ ] Render both through the Wadena physical overlay.
- [ ] Produce side-by-side or sequential MP4 proof.
- [ ] Produce a machine-readable diagnostic report.
- [ ] Inspect hero, perimeter, spiral, impact, reset and color-field behavior.
- [ ] Iterate based on measurable differences.

## 10. CI and artifacts

- [ ] Add calibration-fixture tests to Helix CI.
- [ ] Add spatial-propagation tests to Helix CI.
- [ ] Add electrical-truth regression tests.
- [ ] Add Wadena diagnostic artifact upload.
- [ ] Add a proof-render workflow using available audio/assets.
- [ ] Verify clean-checkout execution.
- [ ] Record exact commit SHA, test command, render command and artifact hash for every proof.

## Research guardrails

1. **Direct frame evidence outranks public descriptions for timing/appearance.**
2. **LMS data outranks visual inference for electrical/channel truth.**
3. **Never infer a channel from a visually ambiguous frame.**
4. **Never stretch the 230.5 s recording to 246.93 s without multiple synchronization anchors.**
5. **No fabricated video timestamps.**
6. **No species classification in the music-first Birdsong metaphor.**
7. **No RGB abstraction may overwrite the physical R/G/W AC model.**
8. **Every completed checkbox requires a real test, generated file, or inspected artifact.**
9. **If evidence is insufficient, encode uncertainty instead of guessing.**

## Current highest-priority execution order

`visual calibration fixture → audio/video alignment → choreography grammar → temporal spatial propagation → Birdsong replacement → effect-engine integration → Wadena proof render → CI artifact gate`
