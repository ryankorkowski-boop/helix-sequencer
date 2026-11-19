# HELIX INFINITY UNIVERSE — Bells of Mathmas build / live handoff

## Owner request (2026-11-18)
Build layout number nine as the extreme 3D showcase and render the current master Helix logic against the original **Bells of Mathmas.mp3**. Do not substitute synthetic audio, procedural placeholder animation, or a legacy-only sequence. Do not merge or release without explicit owner acceptance.

## Verified input
Drive source: https://drive.google.com/file/d/1Zjyz9b-V0SdJ-p9K2FN6ryUR2H88DELG/view
SHA256: `beb2a064595a64d4924847ccd68ca0f2897d5de3ae5064e6e2023a68b7b8ce8a`
Duration: 156.000 seconds; MP3, 3,620,694 bytes. Source recording is fetched in Actions (not copied into the public Git history).

## Work implemented
- `tools/build_infinity_showcase_layout.py` generates a deterministic real `xrgb` xLights layout.
- Extreme tier: 2,048 distinct addressable models, 14 prop families (including spiral trees, double helixes, tunnels and 8x8x8 volumetric grids), and over 2,000 overlapping model groups for rhythm, melody, harmony, spatial zones and layered choreography.
- Each physical model owns its own consecutive 3-channel RGB range; the generator checks for channel overlap, duplicate names and dangling group references.
- 128/512-prop tiers provide bounded previews, not a replacement for the full 2,048-model layout.
- `tests/test_infinity_showcase_layout.py` checks deterministic generation, 3D geometry, groups and channel mapping.
- `.github/workflows/helix-infinity-bells.yml` downloads hash-verified real audio, builds both layout tiers, runs the current master `main.py` on the 512-prop tier with a real 42-second Bells excerpt, refuses to label untouched-template output a render, and requests a 1920x1080 H.264/AAC preview only when actual Infinity effects are present.

## Acceptance checklist (do not mark complete without evidence)
- [ ] GitHub layout unit tests confirmed passing on branch.
- [ ] Full 2048-prop XML and manifest in workflow artifacts.
- [ ] Audio hash confirmed inside render job.
- [ ] Current master engine created XSQ with >=20 active Infinity model effect rows.
- [ ] xLights-native XSQ load and FSEQ export verified.
- [ ] HQ MP4 exists and FFmpeg audio/video decode passes.
- [ ] Full 156-second extreme tier run with bounded-memory measurements.
- [ ] Android and Windows 1.4 preloaded layout and manual updates.
- [ ] Integrate panel #9 into nine-panel benchmark without changing other panels.
- [ ] Owner approves downloaded MP4. No merge/release before approval.

**Truthfulness:** The repository workflow HQ preview is not equivalent to native xLights rendering. Do not claim native validation until xLights actually loads, renders and exports this sequence. The early 512 tier is a scale-constrained real-engine pilot; it is not the full extreme-tier acceptance render.

## Current evidence after first true Helix run
- 2048-prop layout generation: 2,077 groups, 158,016 pixels, 474,048 channels. Three generator tests passed in GitHub Actions.
- GitHub run 44439984298: Bells file hash verified; master v27.3 sequenced 42 seconds and emitted 6,322 effects, 513 active Infinity model/group rows. The prior structure validator stopped only because it did not recognize native xLights timing rows. Corrected validator and regression cases are in this branch; rerun required.
- Snowman band planner reported KeyError('composite_submodels'), not claimed fixed by showcase work. Future dedicated band review needed.
