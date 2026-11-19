# Intricate snowman band samplers

Six newly modeled, volumetric musical stages contain the six-member snowman
ensemble: Borealis Knot Cathedral, Prismatic Orrery, Woven Aurora Vault,
Cymatic Geode Garden, Infinity Observatory and Quasicrystal Theatre. Each
stage has layered curves and facets, a visible cymatic floor, architecture,
source-driven lighting chases and a slow camera dolly. These are rendered
geometric performances, not static concept-art slides.

Five songs are sampled for 42 seconds in every stage: Wire Tree, Who Knew,
49, Candy Cane Chaos and Festivus. Three additional windows cover Who Knew's
opening vocables and later guitar activity, plus Festivus's early mallet part.
Selections maximize joint guitar/keyboard activity while retaining vocals and
bass. 49 and Festivus are the stronger separated guitar/keyboard examples;
Who Knew's principal vocal excerpt has little guitar and is not made to
strum from unrelated music. No claim that every song contains every instrument.

The drummer uses the exact source art, masks, target geometry and poses from
the recovered dry-test artifact 11527580859, source revision
`3cbd736bedf0feadaba69c8a526b2d246ec07b7d`. All 19 source/pose/compositor checks
match that revision byte for byte. The planar physical light prop is mounted
in the three-dimensional stage. This replaces the previous new mesh
interpretation; it does not mirror or remodel the accepted kit. Original
song-specific tagged XSQ strike windows and alternating snare hands remain
unchanged. Cymbal lighting decay never prolongs a stick pose.

Both singer characters have separate mouth/gesture lanes: authored phrase
exchange, shared refrains and shared wordless backing sounds. This is a duet
arrangement, **not gender classification or separation of recorded singers**.
Recognized quiet oh/ooh/ah tokens use sustained rounded/open mouths.
Periodicity and recording-calibrated spectral vowel color fill sustained
voiced gaps; these are uncertain acoustic viseme estimates, not invented
lyric words. Credible embedded lyric alignments correct recognition errors;
failed forced segments are rejected. A second original-mix recognition pass
uses Festivus's title as context. Earlier lyric files remain unchanged. The on-screen
“Wordless vocal” cue distinguishes an acoustic gap from lexical lyrics.
Within-word phoneme boundaries are still allocated rather than independently
forced-aligned. Vocal-stem silence closes the mouths.

Keyboard cues combine the piano stem with selected narrow-band, decaying
pitched attacks from the other stem. Broadband attacks and strong vocal
leakage are rejected. These are xylophone/bell-like articulation estimates,
not a guaranteed instrument label. Hands now target the actual raised black
or white key positions, including depth and height. Bass left-hand height is
monotonic in absolute measured pitch: lower toward the sky, higher toward the
ground. Uncertain pitches hold the last measured position. Guitar picking
follows measured guitar-stem attacks, with real tuning/fret constraints.

These MP4s are 3D performance review visualizations, **not new native xLights
exports or recordings of native playback**. Original native shows, audio,
artwork and earlier MP4s remain preserved. New stage native exports, physical
installation engineering, verified scores, acoustic word-level correction and
reliable overlapping-singer separation remain deferred.

Rerender the published previews after restoring the SHA-pinned input ZIP from
`evidence/intricate_band_samplers/remote_render_request.json` into the repository root:

```bash
python -m tools.render_intricate_band_samplers
```

Regenerating the analysis additionally requires the original six-stem Demucs
cache, the earlier instrument curves and lyric/reference alignment files, and
the separately installed Whisper/analysis dependencies. The render input ZIP
contains the finished curves and lyric results, not those raw separated stems.
With those analysis inputs present, run `python -m tools.recognize_sampler_lyrics`
and then `python -m tools.analyze_band_samplers`.

Analysis, dry-source preservation, decoded pilot inspection, focused tests and
final movie/ZIP/audio proofs are tracked in `evidence/intricate_band_samplers/`
and `MASTER_TODO.md`. Downloads: [single sampler ZIP](https://github.com/ryankorkowski-boop/helix-sequencer/releases/download/intricate-band-samplers-2026-10-10/Snowman_Band_Intricate_42s_Samplers.zip) and [all individual MP4 links](INTRICATE_BAND_DOWNLOADS.md).
