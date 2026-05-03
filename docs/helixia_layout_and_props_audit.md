# Helixia Layout And Props Audit

Date: 2026-05-03
Branch audited: `feature/restructure-core`
Props branch compared: `feature/helixia-props`

## Summary

Helixia currently exists as a planning/specification system, not as a completed xLights RGB effects layout.

- `helixville4/helixia_manifest.json` exists.
- `helixville4/HELIXIA_LAYOUT_NOTES.txt` exists.
- `helixville4/xlights_rgbeffects.xml` does not exist.
- `helixville4/xlights_rgbeffects.xbkp` does not exist.
- The layout builder writes a manifest and notes only.
- The props system defines structure-only prop catalogs, not layout XML, animation, sequencing, or export files.

This is consistent with the current guardrails in `docs/HELIXIA_CREATIVE_DIRECTION.md` and `docs/HELIXIA_PROPS_SPEC.md`, but it means Helixia is not yet a renderable xLights layout.

## Current Helixia Layout State

Files:

- `tools/build_helixia_layout.py`
- `tools/build_helpers/helixia.py`
- `helixville4/helixia_manifest.json`
- `helixville4/HELIXIA_LAYOUT_NOTES.txt`
- `tests/test_helixia_layout.py`
- `docs/HELIXIA_CREATIVE_DIRECTION.md`

Implemented:

- 3x4 village planning grid.
- 12 house lots.
- 11 special lots.
- Fibonacci tree lot concept.
- Native model coverage planning for 13 xLights-style model categories.
- Cost tiers, style IDs, preferences, and model-type coverage.
- Tests verifying manifest generation, required special lots, Fibonacci constraints, native model coverage, and house personality/cost metadata.

Not implemented:

- Actual `xlights_rgbeffects.xml` generation.
- Actual xLights model elements.
- DisplayElements / modelGroups XML output.
- Coordinates translated into xLights preview coordinates.
- Model dimensions, string/channel metadata, pixel counts, controller/network assignment, or XBKP generation.
- Real Helixia stage models for snowman band / cactus / tube man.
- Real prop placeholders in XML.
- Center anchors, districts, semantic model groups, or sequencing target groups.

## Current Props State

Files:

- `models/helixia_props.py`
- `tests/test_helixia_props.py`
- `docs/HELIXIA_PROPS_SPEC.md`

Implemented:

- Structure-only snowman band definitions:
  - `HX_SNOWMAN_BASSIST`
  - `HX_SNOWMAN_GUITARIST`
  - `HX_SNOWMAN_DRUMMER`
  - `HX_SNOWMAN_SINGER`
  - `HX_SNOWMAN_SINGER_FEMALE`
- Body and instrument model definitions per snowman member.
- Body submodels: arms, head, torso.
- Instrument submodels for bass, guitar, drums, and microphones.
- Aggregate snowman group definitions.
- Cactus / tube man / DJ booth structure.
- JSON-ready snowman export catalog.
- Tests enforcing structure-only boundaries.

Not implemented:

- Floor piano structure from the spec.
- Crip-walking reindeer structure from the spec.
- Standalone xLights model export files.
- Prop geometry, dimensions, node maps, or custom model strings.
- Integration of prop catalog into the Helixia layout manifest.
- Integration of prop catalog into generated xLights XML.
- Any animation hooks beyond naming concepts.

## Props Branch Audit

Branch: `feature/helixia-props`

Findings:

- `feature/helixia-props` is an ancestor of `feature/restructure-core`.
- It is 12 commits behind `feature/restructure-core`.
- It has no unique commits ahead of the current branch.
- Helixia-specific files are identical between the current branch and `feature/helixia-props`.
- Therefore, the props branch does not contain a newer or alternate props implementation to recover.

Practical implication:

- Keep working from `feature/restructure-core`.
- Do not merge `feature/helixia-props` into current; it would add nothing Helixia-specific and would risk dropping recent audio/quality work if mishandled.

## Existing RGB Effects Layout Health Baseline

These are not Helixia v4, but they are useful references for what a completed layout should avoid.

`allmodels/xlights_rgbeffects.xml`

- Models: 384
- Groups: 69
- Root models: 368
- Submodels: 16
- Empty groups: 1
- Orphan root models: 1
- Singing face models without submodels: 3
- Complex props without recommended submodels: 32
- Render-cost risks: 2

`helixville/xlights_rgbeffects.xml`

- Same broad profile as `allmodels`.
- Usable as a source/reference layout, but not a clean Helixia target.

`helixville2/xlights_rgbeffects.xml`

- Models: 347
- Groups: 63
- Submodels: 0
- Cleaner group/orphan status.
- Still missing singing-face submodels and complex-prop submodels.

`helixville3/xlights_rgbeffects.xml`

- Models: 377
- Groups: 66
- Submodels: 16
- Cleaner group/orphan status.
- Still missing singing-face submodels and complex-prop submodels.

## Completion Steps For Helixia RGB Effects Layout

1. Freeze scope for Helixia v1.
   - Decide whether v1 is a planning manifest only, a generated xLights layout, or a hybrid.
   - Recommended: v1 should produce `helixville4/xlights_rgbeffects.xml`, `xlights_keybindings.xml`, and `helixia_manifest.json`.

2. Add a Helixia XML writer module.
   - Keep it separate from the manifest builder.
   - Suggested file: `tools/build_helpers/helixia_xlights.py`.
   - It should translate manifest lots into deterministic xLights model XML.

3. Define model templates by semantic type.
   - Lines, windows, candy canes, trees, arches, matrices, stars, spinners, circles, spheres, icicles, DMX placeholders, and custom placeholders.
   - Keep templates simple and valid before making them pretty.

4. Convert world coordinates to preview coordinates.
   - Use a single projection rule for 3D-to-2D.
   - Preserve `world_x_ft`, `world_y_ft`, `world_z_ft` in manifest metadata.
   - Write xLights-friendly coordinates into XML.

5. Generate lot-level model groups.
   - `HELIXIA_ALL`
   - `HELIXIA_HOUSES`
   - `HELIXIA_STAGE`
   - one group per house lot
   - one group per special lot
   - one group per model family

6. Add stage placeholders.
   - `HX_STAGE_SNOWMAN_BAND`
   - `HX_STAGE_CACTUS_TUBE_DJ`
   - `HX_FLOOR_PIANO`
   - `HX_REINDEER_DANCE`
   - These can start as low-detail custom/line placeholders.

7. Integrate props catalog structurally.
   - Import prop definitions from `models/helixia_props.py`.
   - Add them to manifest and XML groups without adding behavior.
   - Keep sequencing/audio boundaries intact.

8. Add submodels for complex props.
   - Singing faces need mouth/eye/face submodels.
   - Stage props need body/head/arms/instrument sections.
   - Matrices and mega props need regions.

9. Add layout health gates.
   - Fail tests if Helixia XML is missing.
   - Fail tests on duplicate model names.
   - Fail tests on empty core groups.
   - Fail tests if all required prop groups are missing.
   - Warn, not fail, for render-cost risks initially.

10. Add visual preview verification.
   - Render a simple preview image or MP4 from the generated XML.
   - Confirm model count, group count, nonblank preview, and readable 2D placement.

11. Add XBKP/keybinding copy support.
   - Mirror the pattern used by Helixville builders.
   - Use source backups instead of destructive writes.

12. Promote `helixville4` as a first-class layout target.
   - Add README command.
   - Add sequence-builder smoke test using `--layout-file helixville4/xlights_rgbeffects.xml`.

## Completion Steps For Props System

1. Add missing prop structures from the spec.
   - `HX_FLOOR_PIANO_BASE`
   - `HX_FLOOR_PIANO_KEYS`
   - `HX_REINDEER_DANCE`

2. Add prop dimensions and layout hints.
   - Width, height, depth, default world position, and preferred model type.
   - Keep these as metadata only.

3. Add export catalog for all props, not just snowman band.
   - Suggested catalog ID: `HELIXIA_PROPS_V1`.
   - Include snowman band, cactus/tube man, floor piano, and reindeer.

4. Add group consistency rules.
   - Every prop must belong to one individual group.
   - Every stage prop must belong to `HELIXIA_STAGE`.
   - Every exportable prop must have at least one model.

5. Add submodel completeness tests.
   - Drummer: kick, snare, tom, cymbals, hi-hat, sticks.
   - Singers: microphone, stand, head, torso, arms, future mouth placeholders.
   - Floor piano: individual key groups.
   - Reindeer: body and leg segments.

6. Add optional xLights export adapter.
   - Keep it separate from `models/helixia_props.py`.
   - It can create XML fragments, but the props module itself should stay structure-only.

7. Integrate with Helixia XML builder.
   - The layout builder decides placement.
   - The props catalog supplies model/submodel/group structure.

8. Add legal distinctness checklist.
   - Confirm prop names, geometry, and silhouette are not vendor-identical.
   - Keep compatibility without cloning.

## Recommended Order

1. Add missing floor piano and reindeer prop structures.
2. Add all-props export catalog and tests.
3. Add Helixia XML writer with only simple native model placeholders.
4. Generate `helixville4/xlights_rgbeffects.xml`.
5. Add groups and health gates.
6. Integrate prop catalog into generated XML.
7. Add preview verification.
8. Iterate on aesthetics and model density.

This order keeps the system modular: props first, XML writer second, visual verification third, sequencing integration last.
