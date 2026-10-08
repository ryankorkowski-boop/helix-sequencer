# Helix Aurora — Ultimate Showcase

Built for the request for every native model, artistic customization, many spiral trees and double helices. The standalone show contains **108 models, 48 groups, 36 spiral trees, 12 double-helix sculptures and 32,277 RGB pixels**. Its 96,929 channels are disjoint; no physical controllers are configured.

## The composition

| Area | Design |
| --- | --- |
| DNA cathedral | A 94-foot cyan/magenta central helix, two 65-foot companion towers, golden illuminated ladder rungs and a north-star crown. |
| Spiral forest | Two graduated groves of 12 native spiral trees each, plus 12 small entrance trees. Different heights, strand counts and turns create depth and rhythm. |
| DNA walk | Paired helix gateposts, six smaller path sculptures and a horizontal orbital DNA halo. Each helix has genuine depth and separately addressable strands/rungs. |
| Orrery pavilions | Sphere moons, nested pink orbit rings, golden wreaths and twelve-ray sunflowers surround differently oriented matrix canvases and jewel-box window frames. |
| Crystal garden | Rotated voxel lanterns, Fibonacci icicle fringes, branching sixfold snowflakes and suspended firefly constellations. |
| Ribbon promenade | Scalloped arches, mirrored candy reeds, opposing horizon rails and a flowing infinity ribbon. |
| Native tree gallery | 180° and 360° cones plus flat and ribbon variants alongside the spiral grove. |
| Welcome/technology alcoves | Original image crest and native label, amber AC marquee, moving heads, floods, utility DMX, skull and kinetic 2D/3D servo sculptures. |

Dimensions are scalable design feet. The overall design is approximately 376 feet wide; this is a large showcase composition, not a surveyed installation or wiring plan.

## Native coverage

Coverage follows the creatable native factory in [pinned xLights source](https://github.com/xLightsSequencer/xLights/tree/6ceddc6b25a24d82754d4f9af28e18ee70b51f81): **Arches, Candy Canes, Channel Block, Circle, Cube, Custom, DmxMovingHead, DmxMovingHeadAdv, DmxFloodlight, DmxFloodArea, DmxGeneral, DmxSkull, DmxServo, DmxServo3d, Image, Label, Window Frame, Wreath, Sphere, Single Line, Poly Line, MultiPoint, Tree, Matrix, Spinner, Star and Icicles**. Model groups are exported separately. Tree and matrix orientations are included as variants; obsolete DMX aliases are not counted as additional families. Snowflakes use the actual native Custom family.

DNA models expose `STRAND_A`, `STRAND_B`, `RUNGS`, `RUNGS_EVEN`, `RUNGS_ODD` and `TOP`. The custom grid preserves unique node identities without collapsing rung/strand points. Zones, native families, all spirals, east/west spirals, all DNA and the three principal DNA parts have sequencing groups. Control fixtures have a separate group and receive no RGB demo effects.

## Open the show

Download and extract **Helix_Aurora_Ultimate_Showcase.zip**. Select the extracted `Helix_Aurora` folder as a new show directory in **xLights 2026.18 or newer**. Keep `assets/` next to the XML. Open Layout in 3D with the Default preview; right-click and choose **Restore Default ViewPoint**, or load **Aurora overview**, to frame the garden. Open `Helix_Aurora_Showcase.xsq` for its 24-second lighting study. It needs no audio.

The same bundle contains the MP4, two still views, an offline interactive `Helix_Aurora_3D.html`, inventory, manifest, 12 reusable DNA `.xmodel` exports, native FSEQ and verification evidence. The browser viewer supports orbit, front/site-plan views, filtering and individual model inspection; it depicts RGB sculptures. Inspect DMX/servo/AC/Image/Label fixtures in xLights.

The checked-in [`showcase/Helix_Aurora`](../showcase/Helix_Aurora) folder is a permanent importable show with original assets and model exports. Videos, native frame data and large review artifacts are generated separately.

## Verification and practical limits

- Actual xLights **2026.18** loads all **108** model definitions, recognizes all **27** families and preserves every absolute start channel. GUI automation also confirms no configured output controllers.
- Native headless rendering produces **480 frames at 50 ms**, spanning 24 seconds. At the 20-second reference frame, all **97 RGB models / 32,277 pixels** have the intended colours, with a maximum accepted channel rounding error of 3. The native FSEQ drives the MP4 lighting.
- Custom sparse-grid geometry is identical in XML and the review. Stock-model review coordinates illustrate the authored geometry using native dimensional conventions. The MP4 is a geometry compositor driven by native channel values; it is not a screen recording of xLights. DMX beams, servo motion, image/label drawing, camera perspective and some stock wiring paths differ in the native display.
- Native checking caught and fixed two silent failures: `Controller="No Controller"` reallocating channels alphabetically, and incorrectly nested DNA submodel effect layers rendering black. Native raw radii/heights, cane reversal, icicle direction and a star boundary pixel were also corrected against the engine.
- **43 layout tests pass.** A broader initial audit found five existing placeholder-drummer expectation failures in `test_helixia_props.py` and `test_helixia_xlights_band_specs.py`; the same five failures reproduce on unchanged baseline `3cbd736`. They were not repaired by bringing obsolete arms/models back.
- Existing root/Helixia layouts, builders, drummer logic and approved drummer assets remain unchanged. The former unsafe append-to-root showcase builder/workflow are archived, superseded only for this standalone showcase.
- Controller selection, ports, power injection, support structures, sight lines and site scaling need installation design. Artistic approval remains with the user. Drummer musical/hi-hat approval remains an independent open task.

## Reproduce

```bash
python -m pip install numpy pillow pytest zstandard
python -m tools.build_ultimate_showcase_layout --no-video --no-zip
```

Render the XSQ using xLights 2026.18 (Linux example; install ffmpeg and xvfb):

```bash
SHOW_DIR="$PWD/outputs/ultimate_showcase/Helix_Aurora"
XL_NO_GPU_COMPUTE=1 xvfb-run -a /path/to/xLights/AppRun \
  --headless -q -s "$SHOW_DIR" -od "$SHOW_DIR" \
  "$SHOW_DIR/Helix_Aurora_Showcase.xsq"
python -m tools.build_ultimate_showcase_layout \
  --native-fseq "$SHOW_DIR/Helix_Aurora_Showcase.fseq" --no-zip
python -m tools.audit_ultimate_showcase_native "$SHOW_DIR"
python -m tools.build_ultimate_showcase_layout --package-only
```

Without a native FSEQ the CLI can make a clearly labelled geometry lighting study using the same authored fades. Native validation and deliverable generation are automated by [Helix Ultimate Showcase Preview](../.github/workflows/helix-ultimate-showcase-preview.yml). It pins the upstream AppImage by SHA256, tests layouts, renders native data, checks every RGB pixel and uploads a clean ZIP without xLights backups/caches.

The running checklist and preserved/deferred work are in [`MASTER_TODO.md`](../MASTER_TODO.md).
