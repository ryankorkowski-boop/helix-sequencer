# Helix dual-mode sequencing and MP4 delivery

## GUI choice

Open `gui_launcher.py` and choose **Sequencer Mode**:

**xLights** (default)
- Upload/select an audio song, your existing `template.xsq` and
  **the matching** `xlights_rgbeffects.xml` (or .xbkp) layout.
- Helix generates editable `.xsq` sequences exactly as before.
- It also copies the exact layout bytes into the output show directory,
  using the expected filename `xlights_rgbeffects.xml`. If present in the
  source show folder, it also copies `xlights_networks.xml`.
- If the destination already contains a *different* layout or network
  configuration, the run fails instead of silently pairing incompatible
  controller settings. Use separate output folders for different displays.
- The `helix_show_context.json` manifest records exact layout hashes and
  names of the generated XSQ files. Audio/video/shader resources may still
  need to be bundled or relinked. Verify the show in xLights before use.

**Light-O-Rama** (legacy LMS compatibility)
- Choose a **real existing .lms** file exported/saved from the user's LOR
  show. It provides the actual channel names, Unit IDs, circuit numbers,
  colors and track references. No xLights XML or xLights install is required.
- Helix builds a local synthetic XML/XSQ sequencing workspace under
  `.helix_lor_workspace/` and runs the same Helix music analysis and the
  existing `--ac-lights-only` sequencing engine.
- After strict filtering/validation, it writes a **new legacy .lms** file,
  retaining the supplied physical unit/circuit/channel identity; the source
  file remains unchanged. On/fade/shimmer/twinkle are translated to LMS
  channel events in centiseconds. Any competing overlapping source effects
  have a documented deterministic winner.
- A copy named `helix_lor_source_layout.lms` accompanies each exported
  LMS as the original channel/controller reference, and an
  `.lms_validation.json` report records the export details.
- **Modern S5/S6 .loredit** files are not supported for direct input or
  output. S5/S6 LOR software can upgrade older LMS files through its own
  supported conversion/import workflow, but native import with a real LMS
  remains an outstanding verification task.
- An LMS does not normally contain the actual physical prop geometry.
  Helix's preview uses a clearly identified **virtual channel grid**, not
  a claim that your house's positions were reconstructed.

## MP4 previews in both modes

The checkbox **Generate MP4 preview with every sequence** is enabled by
default for both modes. A sample is **30 seconds** initially; change
`Preview seconds` (1–600) for a longer or shorter clip. The editable
sequence always includes the full music duration.

The MP4 is generated from the same internal xLights-style sequence data,
*after* AC safety filtering for LOR mode and palette updates for xLights
mode. A `.preview_provenance.json` states explicitly that the video is
Helix's **simulated model-level rendering**, not a pixel-perfect native
xLights FSEQ render or a certified LOR hardware preview.

LOR mode emits `.lms` + `.mp4` + source channel configuration +
validation/provenance reports. The engine's intermediate editable
`.xsq` also remains available for debugging if required.

xLights mode emits `.xsq` + `.mp4` + matching
`xlights_rgbeffects.xml` + available `xlights_networks.xml` +
show-context/provenance reports.

When advanced native xLights rendering is available in the future, an
FSEQ-backed per-pixel MP4 can supersede the simulated video, but will
require a compatible xLights installation. This iteration does not
silently represent approximations as exact native rendering.

## CLI

In addition to normal engine arguments after `--`, wrapper-only flags:

- `--helix-lor-source-lms /path/to/physical_channels.lms`: enable direct
  LOR mode. Helix imports channels and writes legacy LMS results.
- `--helix-preview-mp4`: request an MP4 for each generated variant.
- `--helix-preview-seconds 30`: limit preview duration to first 30s.

Normal xLights CLI behavior remains unchanged when neither flag is used,
except that an explicit selected xLights layout is copied beside newly
generated sequence files. The GUI enables MP4 previews by default.

## Safeguards and compatibility

- All actual Unit ID/Circuit metadata comes from the user-supplied LMS.
- No model/channel assignment is fabricated from colors or geometry.
- Unsupported device types are not silently re-addressed as LOR.
- Original user-supplied LMS, layout XML and template XSQ are never edited.
- Legacy LMS output uses centisecond timing; exact LOR S5/S6 device
  compatibility requires a live import test in the user's LOR software.
- New strict CI checks verify XML round trips, the virtual channel
  layout, duplicate address refusals, and xLights folder packaging.
- A successful XML test does **not** establish native LOR compatibility.

Official references:
- xLights show folder: https://manual.xlights.org/xlights/chapters/chapter-four-set-up/directories
- xLights import requirements: https://manual.xlights.org/xlights/chapters/chapter-five-menus/import
- LOR S5/S6 vs legacy sequence: https://www.lightorama.com/downloads/6.6.8/help/sequencer_file_menu.htm
