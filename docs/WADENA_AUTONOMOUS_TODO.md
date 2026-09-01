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

- [x] Add conservative Wadena model-name → physical-path mapper
- [x] Add renderer wrapper that preserves the existing renderer/electrical truth
- [ ] Bind all truth models to physical geometry
- [ ] Add spatial effect propagation
- [ ] Add AC R/G/W visual mixing without changing electrical truth
- [x] Add renderer-neutral AC R/G/W color quantization primitive
- [ ] Add mega-tree ring rendering
- [x] Add spiral-tree rendering through Wadena preview wrapper
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
- [x] Add Wadena physical geometry as a preview-only transformation layer
- [ ] Feed physical geometry from complete channel truth
- [ ] Integrate manifold intent through existing effect engine
- [ ] Add layered fallbacks
- [x] Keep preview geometry failures isolated from sequence generation

## Phase H — Validation

- [x] Geometry unit tests added
- [ ] Channel/truth tests
- [x] R/G/W separation/color tests added
- [x] Mega-tree ring geometry tests
- [x] Acoustic manifold tests added
- [x] Determinism tests added
- [x] Wadena preview mapper tests added
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
- [ ] Iterate until visually convincing

## Phase J — CI / Artifacts

- [x] Extend Helix Beta CI with Wadena geometry/acoustic/color/mapper tests
- [x] Extend available-audio winner workflow to produce a Wadena-geometry comparison render
- [ ] Upload/verify Wadena-specific diagnostics
- [ ] Verify workflow from clean checkout
- [ ] Document artifacts and remaining uncertainties

## Current Research Notes

- Public sources identify the display at 414 3rd St SW, Wadena, MN and describe thousands of lights synchronized to music on 88.1 FM.
- Recent public descriptions mention a spectacular LED tree; this remains a technology-specific exception rather than changing the traditional AC model.
- The supplied professional LMS is XML/LOR sequence data and should be treated as timing/electrical evidence, not physical geometry by itself.
- The repository layout contains numerous `Single Color Red`, `Single Color Green`, `Single Color Intensity`, and related models. Do not convert AC strands to RGB merely for rendering.
- The existing renderer already has a normalized spatial scene abstraction. Wadena geometry is being layered onto that renderer rather than replacing it.
- Wadena preview mapping is intentionally conservative: known tree families are transformed, while unknown models retain their existing xLights geometry.

## Execution Rule

Continue through the roadmap autonomously. When a task fails, diagnose and repair it, then continue. Never claim a render/test passed unless it actually ran and produced the artifact.
