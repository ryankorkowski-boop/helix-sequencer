# Infinite Symphony integration verification gate

Integration base: codex/band-sampler-timed-corrections-20261013 at 94ddc56d1fc69be27b8070de47686fba490a9701.

## Confirmed evidence (2026-10-13)
- Workflow 38478710482 succeeded on 2ece65d67ec5d32f48b2ceb4c731bc537a23aee9.
- Artifact 11856511591, Helix-Six-Song-Technical-180s, exists (52,624,513 bytes); video contents not independently decoded.
- tools/render_six_layout_band_comparison.py consumes six layout MP4s and a band MP4. It does not produce six independent Helix sequences.

## Required release gates
- Inspect all pending PRs and full correction SHAs before merging.
- Verify montage excerpt provenance, duration, segment count and synchronization.
- Verify independent XSQ exports and native xLights loading for all six layouts.
- Verify two animated stages, 88 note-to-rung mappings and distinct musical group responses.
- Verify full LightsOutTheme source exists and is legally redistributable before packaging.
- Verify actual Windows and Android launch/render tests, not merely build success.
- Audit MIT license and music account-specific rights before distribution.
- Publish only artifact links and codec/duration metrics obtained from actual files.

Status: integration preparation only; none of the release gates above has been marked passed.
