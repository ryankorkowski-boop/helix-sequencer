# Viral Christmas Light Show Pattern Notes

Legal scope: these notes capture broad public-domain choreography ideas and engineering habits observed across popular synchronized holiday light show coverage. They do not copy timing maps, prop layouts, song-specific cues, vendor sequences, or identifiable show designs.

## Source Set

- Carson Williams / "Wizards in Winter" coverage: early viral 16,000-light, 88-channel Light-O-Rama style show.
- Richard Holdman / "Amazing Grace" coverage: very large LED display, long planning cycle, strong whole-house emotional phrasing.
- Tom BetGeorge / Star Wars and musical-instrument display coverage: giant instrument props, real-note visual play, narrative set pieces.
- Cadger family / Skrillex dubstep coverage: drop-heavy EDM vocabulary and intensive per-minute programming.
- xLights and learning resources: 20/40 fps sequence expectations, dense pixel workflows, timing tracks, grouped props, whole-house and matrix separation.

## Recurring Choreography Grammar

1. Whole-house downbeat identity
   - Popular shows establish a readable "house as one instrument" moment early.
   - Strong beats often trigger all-house flashes, roofline punches, or symmetric red/white/gold hits.
   - Helix integration: keep downbeat flashes rare but high priority; use them as punctuation, not wallpaper.

2. Build, blackout, drop
   - EDM and rock displays often reduce visual activity before a drop, then explode into wide coverage.
   - The most legible version is: rising motion, short visual breath, hard drop burst, then dense follow-through.
   - Helix integration: showcase/max route profiles lower drop/build thresholds and shorten min gaps; future work should add explicit pre-drop negative space.

3. Real-note props
   - High-attention shows use piano/guitar/drum props that visibly play musical material.
   - The pattern works because the audience can infer cause and effect: note appears, prop responds.
   - Helix integration: preserve and expand existing player piano and spatial keyboard lanes, then layer audio-reactive catalog accents around them.

4. Section-scale scene changes
   - Memorable shows do not only blink on beats; they change visual language between verse, build, chorus, bridge, and outro.
   - Verse tends to be constrained; chorus widens; finale uses maximum coverage.
   - Helix integration: connect MIR section profiles to audio-reactive route profiles so route density evolves through the song.

5. Prop-family specialization
   - Rooflines and arches carry sweeps.
   - Megatrees and matrices carry large texture and image-like movement.
   - Stars/snowflakes carry sparkle and treble detail.
   - Canes and notes carry rhythm/keyboard motifs.
   - Helix integration: current target hints already encode these families; profile route shaping now changes how often each family fires.

6. Alternation beats constant fullness
   - The best shows avoid every prop doing the same thing for the whole song.
   - They rotate attention between house-wide hits, local call/response, and texture fills.
   - Helix integration: keep conflict checks and min gaps. Even "max" should be dense but structured.

7. Symmetry with occasional asymmetry
   - Symmetry reads instantly from the street; asymmetry creates movement.
   - Common habit: symmetrical hit on the one, directional chase after it.
   - Helix integration: use spatial neighbor graph and route order for post-hit motion.

8. Technical density at digital scale
   - Human-authored shows are limited by programming time per minute.
   - Helix can exceed that by stacking deterministic timing tracks, MIR features, stem cues, piano notes, route catalogs, pixel overlays, and audit-safe placement.
   - Helix integration: add more machine-generated micro-cues, but retain power/audit safeguards and conflict-aware routing.

## Safe Integration Done Now

- Added audio-reactive route profiles:
  - `off`: disables route generation pressure.
  - `subtle`: favors shimmer, quiet texture, and light accents.
  - `balanced`: current default behavior.
  - `showcase`: more drop, bass, build, sweep, sparkle, and energy wave cues.
  - `max`: most technical density profile, still bounded by max actions and conflict checks.
- Connected engine profile selection to route generation, not only placement intensity.
- Kept explicit intensity override separate, so operators can still fine-tune safely.

## Recommended Next Steps

1. Add section-adaptive profiles: subtle verse, balanced prechorus, showcase chorus, max finale.
2. Add pre-drop negative-space detector: brief dim/hold before high-confidence drops.
3. Add instrument-prop expansion: map detected piano/guitar/drum motifs to visual "real-note" lanes.
4. Add finale composer: last 8-16 bars get structured escalation, not random density.
5. Add power-aware "max" mode: dense on pixels/matrices while protecting AC/dumb circuits.
6. Add side-by-side render reports: compare subtle/balanced/showcase/max counts and quality gates.
