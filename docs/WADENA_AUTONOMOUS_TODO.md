# Wadena Digital Twin + Acoustic Manifold Roadmap

> Living execution plan for turning the Helix preview into a 3-D, electrically truthful reconstruction of the Christmas in Wadena display.

## Phase A — Reconnaissance
- [x] Inspect repository architecture and existing preview/sequencing entry points
- [x] Inspect current `core/birdsong_engine.py`
- [x] Inspect current xLights layout representation
- [x] Verify layout contains Single Color Red/Green/White models
- [ ] Inspect all existing XSQs for single-color model conventions
- [ ] Inspect failed Actions run and document root cause

## Phase B — Truth Extraction
- [ ] Build machine-readable 256-channel truth inventory from available layout/XSQ data
- [x] Add conservative xLights truth extractor
- [x] Inventory major model names, colors, channels, groups and world-coordinate landmarks
- [x] Analyze supplied professional LMS
- [x] Separate electrical truth from inferred physical geometry

## Phase C — Wadena Visual Evidence
- [x] Establish Wadena location/show identity from public sources
- [x] Obtain and inspect supplied MP4 directly
- [x] Measure video/audio duration, FPS, frame count and resolution
- [x] Extract embedded audio for analysis
- [x] Produce coarse visual-state measurements
- [x] Produce visual transition candidates
- [x] Produce audio onset candidates
- [x] Perform frame-level local refinement around major visual transitions
- [x] Record evidence vs inference and the 230.5 s video / 246.93 s LMS clock mismatch
- [ ] Complete video-to-LMS event alignment only if multiple independent synchronization anchors support it
- [ ] Do not duration-stretch video to LMS

## Phase D — 3-D Physical Model
- [x] Establish canonical XYZ coordinate system
- [x] Add physical geometry primitives
- [x] Model R/G/W as coincident shared AC paths
- [x] Model boulevard/perimeter spiral tree
- [x] Model large downward apex spiral
- [x] Model distributed cone/traffic-cone yard trees
- [x] Upgrade mini trees to tapered spiral geometry
- [x] Model multi-string mega tree
- [x] Model mega-tree ring/circle geometry
- [ ] Bind all primitives to actual Wadena truth coordinates
- [x] Build deterministic landmark neighbor graph

## Phase E — Preview Renderer
- [x] Add conservative model-name → physical-path mapper
- [x] Add preview wrapper preserving electrical truth
- [ ] Bind all truth models to physical geometry
- [ ] Add temporal spatial effect propagation
- [ ] Add AC R/G/W visual mixing without changing electrical truth
- [x] Add renderer-neutral AC R/G/W color quantization
- [ ] Add mega-tree ring rendering
- [x] Add spiral-tree rendering through Wadena wrapper
- [ ] Add front/wide/close camera presets
- [ ] Add geometry/channel diagnostics

## Phase F — Acoustic Manifold
- [x] Add music-first acoustic state representation
- [x] Extract normalized energy/onset/pitch/spectral state primitives
- [ ] Build phrase/trajectory representation
- [x] Derive musical pressure/tension controls
- [x] Map acoustic state to renderer-independent spatial intent
- [x] Add renderer-neutral visual color-to-AC intent
- [x] Preserve deterministic primitive output
- [ ] Replace species-driven Birdsong semantics in active sequencing path

## Phase G — Integration
- [ ] Keep professional XSQ/LMS timing authoritative
- [x] Add Wadena physical geometry as preview-only transformation
- [ ] Feed physical geometry from complete channel truth
- [ ] Integrate manifold intent through existing effect engine
- [ ] Add layered fallbacks
- [x] Keep preview geometry failures isolated from sequence generation

## Phase H — Validation
- [x] Geometry unit tests
- [ ] Channel/truth tests
- [x] R/G/W separation/color tests
- [x] Mega-tree ring geometry tests
- [x] Acoustic manifold tests
- [x] Determinism tests
- [x] Wadena preview mapper tests
- [x] Wadena landmark graph tests
- [ ] Video calibration fixture tests
- [ ] Spatial propagation tests
- [ ] Failsafe tests
- [ ] Regression tests for existing sequence generation
- [ ] CI verification of all new tests

## Phase I — Proof Render
- [ ] Run professional Wadena/LMS-derived proof
- [ ] Generate Wadena preview MP4
- [ ] Inspect spiral-tree appearance
- [ ] Inspect mini-tree density
- [ ] Inspect mega-tree string density
- [ ] Inspect ring effects
- [ ] Inspect spatial choreography
- [ ] Compare baseline vs spatial-intent render
- [ ] Iterate until visually convincing

## Phase J — CI / Artifacts
- [x] Extend Helix Beta CI with Wadena geometry/acoustic/color/mapper tests
- [x] Extend available-audio winner workflow with Wadena-geometry comparison render
- [ ] Add calibration fixture to CI
- [ ] Upload/verify Wadena-specific diagnostics
- [ ] Verify workflow from clean checkout
- [x] Document mapped landmarks and video evidence

## Phase K — Acoustic/Spatial Calibration from Direct Video
- [x] Establish 11 coarse visual transition regions: ~8, 32, 38, 58, 80, 98, 110, 154, 162, 220, 226 s
- [x] Refine transition timing locally at 0.1 s resolution
- [x] Record strongest refined transition candidates: ~7.7, 31.7, 36.8, 59.9, 79.4, 97.2, 108.1, 154.4, 163.1, 218.7, 225.9 s
- [ ] Inspect each candidate window at individual-frame resolution for physical landmarks
- [ ] Label propagation direction and participating roles
- [ ] Measure lead/lag from audio onset to visible state change
- [ ] Convert high-confidence observations into renderer-independent gesture fixtures
- [ ] Use fixtures to tune launch/travel/decay rather than inventing choreography

## Current Research Notes

- Direct MP4 evidence is now available and supersedes the previous YouTube-access limitation for frame/timing calibration.
- The recording is approximately 230.514 s video / 230.644 s audio, 7,186 frames at ~31.174 fps, 720×1568 portrait.
- The final portion contains Android recorder/UI material; it should not be treated as display choreography.
- Direct frame analysis shows long-lived infrastructure layers, large grouped visual-state changes, deliberate low-activity/reset states, and persistent hero/perimeter structure.
- Representative large visual transition regions occur around 37–38 s, 56–60 s, 78–85 s, and 154–162 s.
- The 56–60 s region is especially useful for studying multi-region color-field changes; it supports treating color as a compositional layer over spatial intent.
- The 79–82 s region is useful for calibrating intentional negative space/reset behavior.
- The professional Nutrocker LMS remains approximately 246.93 s with a 0.05 s grid. No global duration warp is justified against the 230.5 s video.
- `core/wadena_spatial_graph.py` provides deterministic named physical topology.
- `core/wadena_spatial_intent.py` currently provides renderer-independent landmark intents, but temporal propagation should be separated from static spatial ordering before integration.
- Librosa onset strength is a spectral-flux novelty measure and is appropriate for the first audio/visual correlation pass; it should not be treated as a perfect musical-event detector.

## Execution Rule

Continue through the roadmap autonomously. When a task fails, diagnose and repair it, then continue. Never claim a render/test passed unless it actually ran and produced the artifact. Distinguish direct frame evidence, LMS electrical evidence, public-source evidence, and inference.
