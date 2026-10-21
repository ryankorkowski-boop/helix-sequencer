# Helix GUI preview and sample-library acceptance contract (2026-10-21)

Status: SPECIFIED, NOT IMPLEMENTED. User screenshots: signed 112 MB release APK fails installation while debug installs; Android preview at 00:29/00:30 is obscured by oversized black diagnostic panels.

## Release blockers
- Capture Android package manager INSTALL_FAILED_* reason and signing certificate fingerprints for installed debug and release builds; inspect applicationId, versionCode, ABI/minSdk, integrity and build variant. Never label release verified based on debug installation.
- Relocate timing/sequence/debug diagnostics to a collapsed, non-modal inspector outside the preview surface. Preview must occupy the available viewport; portrait and landscape screenshots must show no obstruction. Missing timing label is a diagnostic, not a modal alert.

## Quick Clip
- Same setting in Windows and Android: Quick Clip off = full song; on = exactly 10 seconds (or remaining duration for shorter input).
- Select highest-activity contiguous 10-second region deterministically from actual analyzed audio; respect song duration, avoid silent sections; save start/end in run manifest.
- Render authentic XSQ with independent editable model tracks, original excerpt audio, and native MP4 when rendering available. Do not splice fabricated activity or reuse stale preview.
- Preserve the user's layout, style, stage, and hardware settings when toggling Quick Clip. Regression tests cover 3s, 10s, 11s, long audio, silence and repeated runs.

## Styles
Expose existing engines first (ClassicChristmas, BeatDrive, CinematicSweep, PartyMode, SpatialHelix); map GUI labels to validated engine IDs. Add further styles only with implementation and distinct-effect evidence. Neon is not the only option. Style changes must yield distinguishable model effects and respect AC constraints.

## Sample layout library
Six real, independently loadable xLights layouts, from 1 Classic LOR 64/128/256 AC, 2 Traditional Christmas Plus, 3 Hybrid AC+RGB, 4 Modern Pixel Show, 5 3D Spectacular, to 6 Ultimate Helix Showcase. Include arches, rooflines, candy canes, spinners, trees, singing faces; high-end layouts add multi-tree spatial groupings, helix ladder keyboard rungs, spirals, moiré, forced perspective, and band stages. Validate xLights import, model IDs, channel collisions, and actual rendered output. Default fresh demonstration to layout 6; remember user-imported layout and never overwrite it with a demo preset.

## Stage library
Separate selectable stages: canonical 3D snowman band; pixel-count-faithful snowman representation; rock concert stage; LOR AC channel-limited export; generic singing faces; dual stage. Reuse ONE canonical musical performance logic across representations. Keep lead and backing vocal phonemes independent and active when detected; canonical band identity and approved drummer geometry must not regress. Do not introduce unwanted xylophonist into the canonical approved band.

## Acceptance evidence
- Signed release APK installed and launched on device (package manager output, checksum, version, signing identity).
- Unobscured Android portrait and landscape preview screenshots.
- Quick Clip 10-second verified media, native XSQ and audio.
- Six real layout files and separate stage asset inventory with paths, model counts and import validation.
- Distinct verified effects/style sample renders and Windows/Android parity.
- Maintain checklist and report every incomplete item honestly.
