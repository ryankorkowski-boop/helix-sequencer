HELIX FOR WINDOWS - PORTABLE BETA
=================================

QUICK START (Windows 10/11, 64-bit)
1. Download Helix-Windows-Portable.zip from the GitHub Release.
2. Right-click the ZIP and choose Extract All. DO NOT run the EXE inside the ZIP.
3. Open the extracted "Helix" folder and double-click Helix.exe.
4. Choose your audio file (WAV, MP3, FLAC, or supported other audio).
5. Choose the included template and layout, or Browse to your own xLights
   template.xsq and xlights_rgbeffects.xml / .xbkp.
6. Choose an output folder, then click Run Sequence Build.
7. Open the resulting .xsq file in xLights to inspect/edit your show.

The initial presets and template are examples. Use YOUR OWN matching template,
layout, audio, and model configuration for production-quality sequences.

WHAT IS INCLUDED
- Helix.exe (the graphical control panel)
- HelixCLI.exe (internal sequencing worker; Helix.exe starts this automatically)
- _internal/ (Python 3.12 runtime, xLights logic, native libraries and FFmpeg)
- template.xsq and xlights_rgbeffects.xml example files
- allmodels/ and helixville/ layout presets where available
- outputs/ directory plus licensing documents

INSTALLATION REQUIREMENTS
- No Python installation, pip, git, PowerShell commands, or manual FFmpeg install.
- xLights is NOT needed to launch Helix. It is used to open or edit XSQs.
- Extract the WHOLE "Helix" folder; do not move Helix.exe by itself.
- Place the extracted folder somewhere writable (Downloads, Desktop, or Documents)
  rather than under Program Files, because presets and outputs are written there.
- To keep files between versions, back up your outputs and custom show files.

IMPORTANT BETA LIMITS
- This build intentionally does not bundle optional Whisper/PyTorch lyric
  transcription (large neural model dependencies); normal sequencing remains
  available, and model downloads are not required for the included features.
- The standalone build does not guarantee that an arbitrary generated XSQ will
  be visually correct or import successfully into every xLights version.
- MP4 preview output depends on the selected existing Helix sequencing and
  rendering path; the GUI is primarily an XSQ sequencing control panel.
- Windows SmartScreen may warn about an unsigned EXE. Verify it came from the
  official GitHub release and compare the published SHA-256 if available.
- The supplied GUI does not need network access for its basic local workflow,
  but optional features and external resources may require connectivity.

TROUBLESHOOTING
- "Cannot find HelixCLI.exe": Re-extract the full ZIP; don't move one EXE alone.
- "Missing template/layout": Browse to your show files or re-extract the ZIP.
- No generated XSQ: Check the on-screen Run Log and selected Output Folder.
- Permissions error: Move the extracted folder to a writable location, or
  select a writable custom output folder.
- Antivirus flags: Do not disable protection automatically. Verify the source,
  signature (if present), and file hash; report false positives with evidence.

Source, bug reports and releases:
https://github.com/ryankorkowski-boop/helix-sequencer

All sequencing core logic is the same code as the source repository revision
used for this package. Licensed dependencies and notices accompany the ZIP.

INTEGRATED GUI REVIEW - 2026-10-12
Choose xLights for XSQ and matching layout/audio exports. Choose Light-O-Rama
for legacy LMS using Unit/Circuit wiring from your existing LMS. Modern S5/S6
.loredit import/export and hardware playback validation are not included.
Musical neon palettes apply only to missing RGB palette references; original
explicit colors remain intact. AC/mixed/unknown targets receive neutral swatches.
RGW AC On only exports no RGB choreography. The optional quality gate can fail
a build on measured quality; it is not an artistic approval.
Default short MP4 is an XSQ simulation. Render in installed xLights and Preview
rendered FSEQ use actual channel bytes (stock model geometry is approximate).
Optional Whisper/PyTorch transcription and full 3D band rendering require the
source runtime; the portable package does not promise those optional capabilities.

For a new custom layout, supply an optional model-role mapping JSON using the
existing --model-overrides-file contract. House-specific defaults may otherwise
leave unfamiliar added props untargeted. Mapping assigns real layout models to
Helix roles; it does not create substitute effects.
