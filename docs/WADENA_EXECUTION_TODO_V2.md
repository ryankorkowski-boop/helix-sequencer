# Wadena Execution Roadmap v3 — Autonomous Control Document

> Evidence-first execution plan for the Wadena digital twin, acoustic manifold, spatial choreography and electrically truthful XSQ generation. This is the **living control document**. Execute unchecked items autonomously in priority order; repair failures and continue. Never mark an item complete without a real artifact, test result, inspected source, or reproducible command output.

## Operating contract

1. Prefer implementation over discussion.
2. Never guess electrical channels, model identities, coordinates, timing offsets, or video timestamps.
3. Direct frame/audio evidence outranks public descriptions for appearance and timing.
4. LMS/xLights source outranks visual inference for electrical truth.
5. Preserve independent R/G/W AC channels; RGB is a visualization concept only.
6. Never stretch the 230.5 s recording to 246.93 s without multiple independent synchronization anchors.
7. Unknown evidence becomes explicit `unknown`/`uncertain`, never a guessed value.
8. Every generated proof must carry commit SHA, source inputs, commands and artifact hashes.
9. A synthetic proof channel such as `WADENA_PROOF_*` is never allowed to masquerade as physical channel truth.
10. After each implementation slice: run focused tests → run relevant full tests → generate proof artifact → update this roadmap → continue.

## Priority queue

### P0 — Evidence + electrical safety gate
- [x] Obtain and inspect playable Wadena MP4.
- [x] Measure video/audio duration, FPS, frame count and resolution.
- [x] Extract embedded audio.
- [x] Analyze supplied professional LMS: duration, 0.05 s grid, named-channel/effect inventory.
- [x] Build conservative Wadena landmark/channel evidence map.
- [x] Make AC binding explicit and fail-safe: unknown landmarks are dropped, not guessed.
- [x] Add validator-compatible Wadena XSQ emitter.
- [x] Add deterministic temporal-propagation MP4 proof.
- [x] Add CI workflow that renders and validates MP4 + XSQ proof artifacts.
- [ ] Verify latest CI workflow from a clean checkout.
- [ ] Record successful run ID, commit SHA and artifact hash.

### P1 — Machine-readable evidence fixture
- [ ] Create `data/wadena_video_calibration.json` containing only observed frame/audio evidence.
- [ ] Schema fields: `source`, `time_window`, `frame_range`, `region`, `observation_type`, `roles`, `direction`, `magnitude`, `confidence`, `notes`.
- [ ] Explicitly distinguish `observed`, `inferred`, `uncertain` and `not_visible`.
- [ ] Encode the known ~7.7, 31.7, 36.8, 59.9, 79.4, 97.2, 108.1, 154.4, 163.1, 218.7 s candidate windows.
- [ ] Add deterministic schema/fixture tests.
- [ ] Add calibration fixture to CI.
- [ ] Generate a diagnostic CSV/JSON artifact in CI.

### P2 — Audio/video synchronization
- [ ] Compare video-derived transition envelope with extracted-audio onset/energy envelope.
- [ ] Search multiple independent anchors rather than fitting one global offset.
- [ ] Determine whether recording and LMS represent the same performance/edit before alignment.
- [ ] If defensible, record alignment as piecewise interval(s) with confidence and uncertainty bounds.
- [ ] If not defensible, formally declare the video an independent choreography fixture.
- [ ] Never duration-warp the recording merely to match LMS length.

### P3 — Choreography grammar
- [ ] Label high-confidence gestures: left→right, right→left, center→out, out→center, bottom→top, impact propagation, field change, hero reveal, punctuation and reset.
- [ ] Inspect candidate windows at individual-frame resolution.
- [ ] Measure sequential vs simultaneous participation.
- [ ] Estimate launch/travel/dwell/decay and overlap.
- [ ] Separate persistent infrastructure from phrase-driven events.
- [ ] Classify hero/support/punctuation/impact/perimeter participation.
- [ ] Encode reusable renderer-independent gesture fixtures.

### P4 — Temporal spatial compiler
- [x] Deterministic landmark topology exists.
- [x] Explicit launch/travel/decay propagation exists.
- [x] Temporal renderer and AC-safe event adapter exist.
- [ ] Validate propagation parameters against observed choreography fixtures.
- [ ] Add role-aware participation weights.
- [ ] Add explicit quiet/reset intent.
- [ ] Add overlapping gesture composition.
- [ ] Add fail-safe behavior for missing/invalid routes.
- [ ] Keep static spatial ordering separate from temporal propagation.

### P5 — Music-first Birdsong replacement
- [ ] Remove species/confidence semantics from active music sequencing.
- [ ] Preserve F0, RMS/energy, onset, spectral centroid, bandwidth, flux and tension/pressure primitives.
- [ ] Build phrase/trajectory objects.
- [ ] Convert acoustic trajectories into spatial gesture intents.
- [ ] Add conservative instrument priors only when confidence is adequate.
- [ ] Provide pitch-unknown and instrument-unknown fallbacks.
- [ ] Prove deterministic output for identical audio/configuration.

### P6 — Existing effect-engine integration
- [ ] Feed spatial intent into `sequence_builder → effect_engine → xsq_writer` rather than bypassing the engine.
- [ ] Preserve existing effect-selection contracts.
- [ ] Quantize visual color intent to available AC R/G/W channels only at the final stage.
- [ ] Add channel-truth regression tests.
- [ ] Add fallback to legacy sequencing when spatial intent is unavailable.
- [ ] Compare baseline vs spatial-intent output for identical electrical constraints.

### P7 — Physical digital twin
- [ ] Bind every verified truth model to physical coordinates.
- [ ] Map every major family to a physical primitive or explicit fallback.
- [ ] Finish/verify mega-tree ring rendering.
- [ ] Verify spiral orientation/density.
- [ ] Verify mini-tree density/spacing.
- [ ] Add front/wide/close camera presets.
- [ ] Add optional geometry/channel/landmark diagnostic overlays.
- [ ] Render a clean Wadena scene independent of sequencing.

### P8 — LMS calibration
- [ ] Inventory all available channels/models/colors from actual source files.
- [ ] Preserve 0.05 s timing authority when LMS is used.
- [ ] Quantify persistent vocabulary: snowflakes, beat sticks, candy canes, perimeter/roof/wreath.
- [ ] Quantify copied timing blocks and controlled offsets.
- [ ] Treat mega-tree activity as sectional unless evidence says otherwise.
- [ ] Calibrate density/persistence/effect vocabulary without inventing geometry.

### P9 — End-to-end proof
- [ ] Generate baseline XSQ from existing engine.
- [ ] Generate spatial-intent XSQ from identical input.
- [ ] Validate both electrically and structurally.
- [ ] Render both through Wadena overlay/digital twin.
- [ ] Generate side-by-side/sequential comparison MP4.
- [ ] Generate machine-readable diagnostic report.
- [ ] Inspect hero, perimeter, spiral, impact, reset and color-field behavior.
- [ ] Iterate using measurable differences.

### P10 — Release/CI gate
- [ ] Full test suite passes from clean checkout.
- [ ] Focused Wadena tests pass.
- [ ] Calibration tests pass.
- [ ] Electrical-truth regression passes.
- [ ] Proof MP4 is nonempty and decodable.
- [ ] Proof XSQ passes structural validation.
- [ ] Artifacts uploaded with reproducible metadata.
- [ ] Final report records exact SHA, commands, durations and hashes.

## Evidence ledger

| Evidence | Authority | Status | Rule |
|---|---|---|---|
| Supplied Wadena MP4 | direct frame/audio | available | timing/appearance evidence |
| Supplied professional LMS | electrical/timing source | available | channel/effect truth |
| Wadena landmark map | extracted source + documented inference | available | only verified bindings may drive AC |
| Public Wadena descriptions | secondary | available | context only |
| YouTube footage | secondary visual | not frame-addressable | never fabricate timestamps |

## Current verified implementation

The repository already contains deterministic Wadena spatial topology, temporal propagation, AC-safe event compilation, explicit XSQ emission, and a CI proof workflow. The XSQ emitter intentionally requires caller-supplied landmark/channel bindings and does not infer electrical channels. fileciteturn265file0

The current landmark map records real LMS channel names and physical landmark coordinates separately from choreography roles, including perimeter, hero, punctuation, impact, foreground rhythm, candy-cane and mega-tree families. fileciteturn266file0

## Autonomous next action

**Do not redesign architecture until the evidence/CI gate is green.** First verify the latest Wadena proof workflow from clean checkout. If it fails, diagnose and repair. If it passes, immediately implement P1 (`wadena_video_calibration.json` + schema tests + CI artifact), then proceed to P2 synchronization.
