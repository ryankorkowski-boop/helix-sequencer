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
or with multiple eligible models starting on the same channel. It also excludes
AC circuits whose addresses are occupied by a declared RGB model and reports
the conflict in the validation JSON (for example original RGB node 164 overlaps
AC addresses 165 and 166). Do not assume those omitted circuits have been
remapped. The original layout and template files are never changed.

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


## Genuine per-pixel MP4 (from native xLights FSEQ)

The Helix GUI now provides the following separate tools:

- **xLights render to FSEQ...** — choose the original XSQ, installed xLights
  executable, show folder, and an output folder. This runs native xLights
  headless. The persistent FSEQ is only accepted if xLights returns success
  and writes a new nonempty sequence. The show folder must contain the
  xlights_rgbeffects.xml layout matching the XSQ.
- **FSEQ to pixel MP4...** — choose that FSEQ. The preview reads each
  channel's actual values from xLights (not fabricated XSQ effect simulations)
  and displays individual nodes. When using the selected xLights layout,
  spatial pixel positions are approximate based on model geometry.
  For exact pixel positions use a verified CSV map in the standalone CLI.

Requires Pillow, imageio, and imageio-ffmpeg. FSEQ v1 and v2 dense/sparse
channels are supported; v2 zlib supported and v2 zstd requires an optional
Python zstandard package. The video uses actual channel frames and supports
audio muxing when an audio file is selected in the GUI.

`python -m tools.validate_native_xlights music.xsq --xlights-exe PATH_TO_XLIGHTS --show-dir SHOW_FOLDER --output-dir OUTPUT_FOLDER`

`python -m tools.fseq_pixel_preview OUTPUT_FOLDER/music.fseq --layout SHOW_FOLDER/xlights_rgbeffects.xml --output music.mp4 --audio song.wav`

For a calibrated real-pixel coordinate map, use a CSV with headings
channel,x,y,kind. Channel is **1-based**; kind is rgb, red, green or white.
The RGB kind consumes 3 sequential channel values, and AC kinds use one.
Feed this with the --pixel-map option instead of --layout.

**No native xLights render was performed solely by adding this software.**
The xLights program must be installed and run on the user's workstation.
This tool does not claim full physical/3D geometry fidelity from an inferred
layout. With an exact pixel map, color and pixel positions are both explicit.

## Legacy LMS export (older Light-O-Rama software)

The GUI button **Export legacy LOR LMS...** converts a validated AC-only XSQ
to an editable legacy LMS XML file. A CSV mapping with all controller_unit and
controller_circuit fields must first be completed by the user and verified
against real equipment. This is NOT S5/S6 LOREDIT and not ready for live
hardware playback without manual checks.

`python -m tools.legacy_lms_export music.xsq --channel-map music.ac_channel_map.csv --output music.lms`

The exporter:
- refuses missing/duplicate Unit ID/Circuit information (unit decimal 1–255
  or 0x-prefixed hex; circuit 1–16);
- refuses non-On effects, fades, unmapped models and non-flat intensity;
- combines overlapping intervals and converts xLights milliseconds to
  LOR centiseconds with floor/ceiling rounding;
- writes legacy XML with channel definitions, fully-on intensity events,
  timing grid and track/channel references;
- emits a separate .lms_validation.json with explicit unverified import and
  hardware status.

See the historical LMS structure described by the Light-O-Rama community:
https://github.com/fractal13/light-o-rama-auto-sequencer
and official LOR sequence version distinctions:
https://www.lightorama.com/downloads/6.6.8/help/concept_sequences.htm
