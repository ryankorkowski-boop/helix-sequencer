# Wadena Digital Twin + Acoustic Manifold Roadmap

> Living execution plan for turning the Helix preview into a 3-D, electrically truthful reconstruction of the Christmas in Wadena display.

## Phase A — Reconnaissance

- [x] Inspect repository architecture and existing preview/sequencing entry points
- [x] Inspect current `core/birdsong_engine.py`
- [x] Inspect current xLights layout representation
- [x] Verify that the layout already contains Single Color Red/Green/White models
- [ ] Inspect all existing XSQs for single-color model conventions
- [ ] Inspect failed Actions run and document root cause

## Phase B — Truth Extraction

- [ ] Build a machine-readable 256-channel truth inventory from available layout/XSQ data
- [x] Add conservative xLights truth extractor (`tools/extract_wadena_truth.py`)
- [ ] Inventory model names, colors, channels, groups and world coordinates using extractor output
- [ ] Analyze the supplied professional LMS where available
- [x] Separate electrical truth from inferred physical geometry in the extractor design

## Phase C — Wadena Visual Evidence

- [x] Establish Wadena location/show identity from public sources
- [ ] Inspect supplied YouTube reference
- [ ] Collect additional multi-angle public footage where accessible
- [ ] Record confirmed/inferred geometry observations with confidence levels
- [ ] Document GP sequencing vocabulary observed in footage

## Phase D — 3-D Physical Model

- [x] Establish canonical XYZ coordinate system in geometry primitives
- [x] Add initial physical-element geometry primitives
- [x] Model R/G/W as coincident shared paths on AC geometry
- [x] Model boulevard/perimeter spiral tree primitive
- [x] Model large downward apex spiral
- [x] Model distributed cone/traffic-cone yard-tree primitive
- [x] Upgrade mini trees from vertical placeholders to tapered spiral geometry
- [x] Model multi-string mega tree primitive
- [x] Model mega-tree ring/circle geometry
- [ ] Bind primitives to actual Wadena truth coordinates
- [ ] Build neighbor graph

## Phase E — Preview Renderer

- [ ] Bind existing truth models to physical geometry
- [ ] Add spatial effect propagation
- [ ] Add AC R/G/W visual mixing without changing electrical truth
- [x] Add renderer-neutral AC R/G/W color quantization primitive
- [ ] Add mega-tree ring rendering
- [ ] Add spiral-tree rendering
- [ ] Add useful front/wide/close camera presets
- [ ] Add optional geometry/channel diagnostics

## Phase F — Acoustic Manifold

- [x] Add music-first acoustic state representation
- [x] Extract normalized energy/onset/pitch/spectral state primitives
- [ ] Build phrase/trajectory representation
- [x] Derive musical pressure/tension controls
- [x] Map acoustic state to renderer-independent spatial intent
- [x] Add renderer-neutral visual color-to-AC intent primitive
- [x] Preserve deterministic output at the primitive level
- [ ] Replace species-driven Birdsong semantics in the active sequencing path

## Phase G — Integration

- [ ] Keep professional XSQ/LMS timing authoritative
- [ ] Feed physical geometry from existing channel truth
- [ ] Integrate manifold intent through existing effect engine
- [ ] Add layered fallbacks
- [ ] Ensure preview failures never invalidate sequence generation

## Phase H — Validation

- [x] Geometry unit tests added
- [ ] Channel/truth tests
- [x] R/G/W separation/color tests added
- [x] Mega-tree ring geometry tests
- [x] Acoustic manifold tests added
- [x] Determinism tests added
- [ ] Failsafe tests
- [ ] Regression tests for existing sequence generation
- [ ] CI verification of all new tests

## Phase I — Proof Render

- [ ] Run professional Wadena/LMS-derived proof
- [ ] Generate preview MP4
- [ ] Inspect spiral-tree appearance
- [ ] Inspect mini-tree density
- [ ] Inspect mega-tree string density
- [ ] Inspect ring effects
- [ ] Inspect spatial choreography
- [ ] Iterate until visually convincing

## Phase J — CI / Artifacts

- [x] Extend Helix Beta CI with Wadena geometry/acoustic/color tests
- [ ] Add/update Wadena proof workflow
- [ ] Upload XSQ/MP4/diagnostics
- [ ] Verify workflow from clean checkout
- [ ] Document artifacts and remaining uncertainties

## Current Research Notes

- Public sources identify the display at 414 3rd St SW, Wadena, MN and describe thousands of lights synchronized to music on 88.1 FM. citeturn0search0turn0search7
- Recent public descriptions mention a spectacular LED tree; this remains a technology-specific exception rather than changing the traditional AC model. citeturn0search3
- The supplied professional LMS is XML/LOR sequence data and should be treated as timing/electrical evidence, not physical geometry by itself.
- The repository layout contains numerous `Single Color Red`, `Single Color Green`, `Single Color Intensity`, and related models. Do not convert AC strands to RGB merely for rendering.
- The current Birdsong engine is still species-oriented; the new acoustic manifold is intentionally separate until integration is tested.
- The preview renderer already has a normalized spatial scene abstraction; the next integration should adapt Wadena physical geometry into that existing path rather than replace the renderer wholesale. fileciteturn76file0turn76file2

## Execution Rule

Continue through the roadmap autonomously. When a task fails, diagnose and repair it, then continue. Never claim a render/test passed unless it actually ran and produced the artifact.
