# Helix RGW AC On-only mode and musical RGB color

## GUI output choices

Open gui_launcher.py, select audio, a matching real xLights layout and template,
then choose one of three output modes:

- Original xLights colors: preserve the existing engine/template behavior.
- Neon musical color: match coherent color themes to detected musical verses,
  builds, choruses and bridges, refreshing long phrases every ~12 seconds.
  Existing musical timing, target choices and effect names are preserved.
- RGW AC - On effects only (Light-O-Rama): use strictly the distinct
  Single Color Red, Single Color Green and Single Color White circuits.

An optional RGB chorus chase checkbox layers an On-only left-to-right accent
across three or more actual RGB models, aligned to detected chorus/drop onsets.
It never runs for AC-only output, and skips accents colliding with a model's
existing effects. This is an additive spatial accent, not a full replacement
for native xLights spatial effect rendering.

Optional Strict showcase quality gate rejects empty or monochrome neon runs
and one-palette dominance above 80%. Normal mode writes advisory quality
reports without blocking the sequence build.

## AC controller safety

The generated file is an xLights XSQ, NOT a native Light-O-Rama LMS file.
The export writes flat, full-brightness On effects to eligible physical
single-color models only. A white intensity palette drives those circuits;
the physical red/green/white bulbs determine actual color.

Unknown Single Color Intensity models, RGB pixels, matrices and unmapped
group targets are excluded, not guessed as AC. Known groups expand to
eligible AC member circuits. Overlapping On events are coalesced.

Before export the tool rejects a layout without explicit AC color models
or with multiple eligible models starting on the same channel. The original
layout and template files are never changed.

Each output includes:
- an XSQ with only On effects on supported single-color models;
- a .ac_channel_map.csv containing xLights StartChannel and physical color;
- a .ac_validation.json with dropped effects, short pulses, and warnings.

Raw engine XSQs are saved under a hidden .helix_source_sequences audit folder,
while the normal visible XSQ output path becomes AC-only.

**An xLights StartChannel is not automatically a LOR Unit ID/circuit.**
Controller Unit and Circuit columns in the CSV are deliberately left blank.
The output requires operator verification of the real AC controller network,
electrical wiring, unit addresses, and AC string circuit mapping.

## Convert and verify for Light-O-Rama

1. Configure an accurate AC layout in xLights (one eligible model per actual
   physical color circuit), selecting real controller/network assignments.
2. Build with RGW AC On-only, open the resulting XSQ in that xLights show,
   and inspect all effects and channel mapping.
3. Compare the channel CSV with the LOR unit/circuit assignments and fill
   missing controller fields manually and verify them.
4. Use xLights Render and Export Model to export for LOR where supported,
   then inspect the result in Light-O-Rama Sequencer before physical playback.
   This is NOT a guarantee of automatic complete-show LMS conversion.
5. Validate on real controllers with appropriate loads and safety limits.

xLights export instructions:
https://manual.xlights.org/xlights/chapters/chapter-four-sequencer/models

## CLI

Normal sequencing supports the wrapper flag --helix-ac-on-only after the
-- separator. This flag is removed before the existing audio engine runs.

Standalone format conversion:
python -m tools.ac_on_export input.xsq --layout layout.xml --output output.xsq

Optional genuine xLights headless render check:
python -m tools.validate_native_xlights output.xsq --show-dir SHOW_DIR --xlights-exe PATH_TO_XLIGHTS

Native validation only passes if the real xLights process returns success
and writes a nonempty FSEQ. This is not a physical LOR hardware test.
Supported headless mode:
https://github.com/xLightsSequencer/xLights/blob/master/AGENTS.md

## Guarantees and known limitations

The engine retains all music timing/effect placement decisions. For RGB,
musically coherent phrase palettes improve color variety, but do not invent
new movement or perform per-pixel effect rendering. Existing preview code
is a model-level approximation; native xLights renders are authoritative.
This export does not alter original xlights_rgbeffects.xml or template.xsq.

The new strict targeted CI workflow covers AC and RGB export behaviors;
repository-wide tests may remain non-blocking due to unrelated failures.
