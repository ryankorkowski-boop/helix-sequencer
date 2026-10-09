# Selected concept native shows

## 2026-10-09: approval extended through #62

All 62 concepts now have independent native xLights shows. The original 22
XML/XSQ exports are preserved byte for byte, and their missing downloadable
movies have been regenerated. Concepts 23–42 add perspective and sculptural
structures; 43–62 add held replacement poses, incremental assembly and a domino
state study. The user explicitly approved all through #62 in this session.

The complete current verification is `evidence/approved_concepts_62/verification.json`.
Compact native sources for all 62 are in `showcase/approved_concepts/`.
The delivery includes a ZIP of all native shows and reusable `.xmodel` files,
a ZIP of all 62 movies, and individual MP4s. The release is titled
**Approved concepts 1–62: xLights files and MP4 previews**.

Reproduce all 62 with the existing command below (omit `--ids`); use the
`models/advanced_concepts.py` and `models/stop_motion_concepts.py` modules for
new geometry. Native replacement poses use 600ms holds, with explicit longer
holds in the firefly, bloom and marionette cycles. Each inactive pose is verified
dark against the actual native FSEQ. Perspective layouts use a frontal hero
camera where alignment matters and an oblique view for depth-heavy sculptures.
Point previews do not simulate physical lenticular baffles.

Verified: 62 native renders, 29,760 frames, 2,714 lit models and 347,170 RGB pixels;
all 62 movies fully decode to 480 H.264/yuv420p frames at 20fps / 24 seconds.
127 focused tests pass. Six representative shows were relocated to folders with
spaces and rerendered with every native frame identical. Source art, favorites,
recordings and canonical drummer ranges remain intact.

The previews are silent artwork-guided planning studies. They project native
xLights channel values onto the exact exported coordinates. Physical installation,
angle-dependent occlusion and full-song drummer transcription remain separate.

The section below records the earlier 22-concept delivery.

The user requested the roughly 20 visually approved concepts, including the two
band stages and two pontoons. This batch implements all 22 saved entries from
`showcase/concepts/2026_10_08/concepts.json`. The remembered whale has no saved
entry or source artwork in this workspace or the searched relevant branches;
it remains unresolved. No invented whale is described as the approved design.

Each layout is an independent xLights show. The complete generated delivery is
`outputs/Approved_Concepts_XLights/<id>_<name>/`. Each folder contains:

- `xlights_rgbeffects.xml` and empty `xlights_networks.xml`;
- a 24-second Animation XSQ and its native rendered FSEQ;
- every reusable Custom model in `models/`, with submodels;
- model/channel inventory, manifest and exact preview coordinates;
- copied reference art and required drummer assets, where applicable;
- a `media/` folder explaining that the study is silent;
- a direct H.264/yuv420p MP4, sampled stills and native verification.

Select the corresponding show folder in xLights 2026.18 or newer, open its
`<name>_Showcase.xsq`, render, then play. No output networks/controllers are
configured. Each XML contains the full model geometry and channel map; no
manual XML swap or another layout's sequence is required.

The checked-in native source folders under `showcase/approved_concepts/` contain
the XML, XSQ, manifest, inventory and required runtime assets. Separate reusable
model exports, copied reference artwork, FSEQ, video and samples are generated
by the reproduction command. XML already embeds all custom model data, so those
additional model exports are not needed to open the checked-in native shows.

Reproduce from the repository root, with a working display for Linux xLights:

```bash
DISPLAY=:101 XL_NO_GPU_COMPUTE=1 python -m tools.build_approved_concepts \
  --output outputs/Approved_Concepts_XLights \
  --xlights /path/to/xLights/AppRun --workers 2
python -m pytest -q tests/test_approved_concepts.py
```

The generator rerenders its dedicated delivery folders. Never point `--output`
at an existing production show. `--ids 15 16 21 22` selects just both stages and
both pontoons. One active geometry implementation remains in the focused
`models/approved_concepts.py` module; source art and older pipelines are intact.

All contours and sparse meshes use native Custom grids. The movie projects the
actual native FSEQ values onto the identical exported node coordinates, using
a fixed auto-fit camera. It is a geometry projection, not an xLights GUI screen
recording. The studies use native On attack/decay and sector/depth chases; they
contain no unsupported Ramp effect, soundtrack or fabricated music transcript.
The layouts interpret the source light structures, rather than converting
scenic stonework, people, water, car paint or beams into LED nodes. Car and
church proportions are stylized planning geometry; accurate surveyed meshes,
power/controller wiring, rigging and marine implementation remain separate.

Both stage layouts include `HX_SNOWMAN_DRUMMER_V3`, preserving its canonical
96×72 grid, node order and all 40 original submodel ranges. They add a dim body
helper and an eight-instrument demonstration with separate neutral/wood helpers
where supplied by the source. This is placement/native connectivity work;
musical correctness and drummer acceptance remain open. No source drum events
are moved between different songs.

Verification checks native frame/channel dimensions, every model receiving
lighting, all bindings and portable asset references, controller absence,
complete MP4 decoding, 480 frames at 20fps and 24-second duration. Focused tests
also reconstruct every compressed custom grid back into the exported XYZ
points and verify disjoint channel ranges and preserved drummer targets.
`evidence/approved_concepts/verification.json` records the final concise native
proof, original-art/favorite/source hashes and limitations. `MASTER_TODO.md`
is the handoff authority.
