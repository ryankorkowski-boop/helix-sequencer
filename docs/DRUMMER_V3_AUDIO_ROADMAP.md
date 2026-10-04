# Drummer V3 Audio + Visual Roadmap

## Goal
Produce a musically convincing Drummer V3 performance driven by real audio, using the canonical V3 visual asset rather than a placeholder renderer.

## Phase 1 — Audio foundation
- [x] Require isolated drum/percussive evidence before creating any drum event.
- [x] Keep full-mix features confirmation-only.
- [ ] Add multi-resolution onset detection and transient-shape features.
- [ ] Add harmonic/percussive separation quality scoring.
- [ ] Add instrument-confusion rejection for guitar, piano, vocal, and synth transients.
- [ ] Add per-class adaptive thresholds for kick, snare, hats, cymbals, and toms.
- [ ] Add phrase-aware fill detection and density control.

## Phase 2 — Musical performance
- [ ] Build groove/beat-strength context without allowing the beat grid to manufacture hits.
- [ ] Infer kick/snare relationships and common backbeat patterns.
- [ ] Detect hat subdivisions and cymbal phrase boundaries.
- [ ] Detect tom fills from low/mid-band trajectories and phrase context.
- [ ] Humanize timing and velocity with deterministic seeds.
- [ ] Prevent impossible simultaneous/overdense patterns.

## Phase 3 — Canonical visual integration
- [x] Lock performer identity to `HX_SNOWMAN_DRUMMER_V3`.
- [x] Lock tom inventory to HIGH/MID/FLOOR only.
- [ ] Make the render compositor use `fixtures/band_geometry/source/drummerbg.png` as the visual source.
- [ ] Drive the approved V3 PNG layers/pose frames directly from typed performance events.
- [ ] Add an automated pixel/asset provenance check so a placeholder renderer cannot pass.

## Phase 4 — Validation
- [ ] Guitar-only transient fixture => zero drum events.
- [ ] Drum-only fixture => expected typed events.
- [ ] Mixed real-audio fixture => compare event timing against reference annotations.
- [ ] Verify all three toms and no fourth tom.
- [ ] Render a dedicated MP4 and inspect the first 10 seconds before full-song rendering.
- [ ] Require visual approval before calling a drummer build release-ready.

## Phase 5 — Production
- [ ] Run real-audio 256-channel + Drummer V3 workflow.
- [ ] Publish XSQ, dedicated drummer MP4, full render, and analysis metadata.
- [ ] Preserve deterministic analysis seed and configuration with every artifact.

## Definition of done
A build is not considered successful merely because tests or workflow jobs pass. The drummer must (1) use the canonical V3 visual asset, (2) avoid obvious non-drum transients such as guitar notes, (3) produce musically coherent typed events, and (4) survive direct MP4 visual/audio review.
