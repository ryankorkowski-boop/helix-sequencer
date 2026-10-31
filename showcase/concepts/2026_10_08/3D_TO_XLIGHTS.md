# From a 3D idea to an xLights layout

**Feasible, with different amounts of work depending on the geometry.** The current Helix repository already creates importable 3D pixel layouts. A detailed car, church or boat would extend the shape authoring and light-placement work; this concept round has not built or validated those new examples.

## What is already demonstrated

The original saved Helix Aurora show contains 108 native model definitions across 27 creatable xLights families, including 97 RGB models / 32,277 pixels. Its recorded xLights 2026.18 GUI import and native 480-frame lighting render are documented in `docs/ULTIMATE_SHOWCASE.md` and `showcase/Helix_Aurora/native_verification.json`. The six later flavors have their own native proofs in `docs/SHOWCASE_FLAVORS.md`. This is existing evidence, not a claim of a newly run test here.

The active builder in `models/ultimate_showcase.py` supports:

- Native **Tree, Arches, Circle, Matrix, Sphere, Spinner, Star** and other model families for conventional props.
- Native **Poly Line / MultiPoint** with 3D point data for contours and spatial paths.
- Native **Custom** models with a sparse 3D node grid, separate X/Y/Z dimensions and world transforms.
- Unique node numbering and named submodels, including double-helix strands and ladder rungs.
- Collision checks that refuse coincident custom nodes, shared geometry for the export and preview, and channel allocation checks.

`tests/test_ultimate_showcase.py::test_custom_xyz_roundtrip_and_unique_occupied_cells` reconstructs exported XYZ positions and checks them against the intended snapped nodes. Geometry is quantized onto a sparse grid; the implementation records its maximum snap error. The permanent Aurora also includes twelve reusable DNA `.xmodel` files and an offline 3D viewer.

## What a 3D mesh does and does not provide

A textured mesh can describe a car or building and serve as scene/reference geometry. Addressable light models still need explicit pixel positions, node order, physical string boundaries and channels. Exporting a decorative mesh or loading an OBJ backdrop does not by itself turn that surface into a working pixel model.

For an accurate Impala, church or pontoon, the practical route is to use a dimensioned source model or measured reference, choose the light-bearing contours/surfaces, sample the intended LEDs along them, and export those points as native line/custom models. Body paint, stone, glass, water reflections and cinematic glow in the concepts do not become emitted pixels. Dense matrix surfaces and stage DMX fixtures also require their own model/control treatment.

No general-purpose arbitrary-mesh-to-wired-layout importer has been demonstrated by this concept request. The existing procedural XYZ export is real; a robust mesh-sampling workflow would be additional implementation.

## Relative effort for the proposed directions

| Direction | Digital layout effort | Main work beyond the existing exporter |
| --- | --- | --- |
| Extreme traditional display | Lower | Arrange many native props, preserve readable zones and sensible channel groups |
| Spatial helix garden | Moderate | Author supports/tiers and world transforms; check depth paths and occlusion |
| Layered abstract installation | Moderate to high | Tune spacing, pixel density and camera-dependent overlap through prototype views |
| Gothic facade / cloister | Moderate with accurate reference | Trace architectural contours; split rose-window, tower and arcade submodels |
| Arena stage | Moderate to high | Combine pixel surfaces, stage structure and fixture-specific DMX behavior |
| Parked Impala show car | Higher | Accurate body geometry, contour sampling, segmented wiring and visibility around the car |
| Pontoon display | Moderate digitally; substantial physical design | Hull/deck/canopy geometry plus marine installation constraints |

These are relative estimates, not elapsed-time promises. Accurate source geometry substantially reduces reconstruction work. A fixed parked car is simpler than lights on rotating wheels; a dockside concept is simpler than a deployed moving boat. Large scenic terraces and suspended props may be easy to represent digitally while demanding major physical construction.

## A useful assessment after concept selection

Build one small, clearly bounded module from the chosen concept before the whole scene: for example a cathedral rose window plus one pointed arch, an Impala grille/hood contour, or a pontoon rail/canopy section. Deliver its native `.xmodel`, node/wiring map, 3D positions, an importable test show and an actual native lighting render. Compare the imported geometry and lit frames to the intended model from more than one view. Record time and manual intervention so the user can judge ease as well as appearance.

Then scale only the selected design. That proof should verify actual exported/native behavior; the image-generation output alone cannot establish geometric fidelity or sequencing correctness. The approved three-tom drummer and all saved layouts remain separate preserved work.
