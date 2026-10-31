# Snowman band and helix singing faces

The requested six-member band has the unchanged canonical finished drummer,
upright bass, guitar, male/female singers and a new keyboardist. Five members
have original volumetric snowman geometry; the accepted drummer remains its
original planar artwork/grid, placed on a raised rear riser in the 3D stage.
Stationary replacement arms and seven mouth shapes animate through native
xLights submodels. Strings, frets and individual keys respond to the recording.

The alternate stage pairs the same drummer/performance with four original
singing props: tree, bulb, pumpkin and snowman. Interwoven rails follow the
silhouettes at varying depths and brighten with detected singing. This applies
Helix geometry to familiar coro singing-face categories. It does not import
exact vendor wiring or claim measured popularity. Boscoyo's current
[Singing Decor collection](https://boscoyostudio.com/collections/singing-decor)
lists ChromaBulb, Christmas Tree and ChromaSnowman families; the collection
was read on 2026-10-09. HolidayCoro's direct tree page returned 403 in this
environment, so no downloaded HolidayCoro geometry is claimed.

## Runs and signal path

The working prior-upload choice is Wire Tree; the optional preference question
received no answer before useful work proceeded. The five new tracks are
Who Knew (Grinch's Redemption), 49, Candy Cane Chaos, Phoneme Test Hook and
Festivus. Every new track gets both stages, for 11 full-song performances.

Each source recording is hash-verified and separated once with externally
installed Demucs `htdemucs_6s` (drums, bass, guitar, piano, vocals, other). Bass,
guitar and piano use measured separated-stem spectral-flux onsets; measured
dominant spectral pitches select string/fret/key lights. These are pitch
proxies, not verified polyphonic notes. Separation can leak other instruments.

The same source-bound ADTOF Frame RNN used by the latest drummer research
supplies polyphonic drum families. `tools/integrate_drummer_v3_into_xsq.py`
uses the unchanged V3 scheduler, physical target mapper, alternating snare
hands, shared-actuator union and cymbal shimmer. The native adapter retains
every visible placement before song-end clipping and 50 ms native quantization.
Unknown tom identities abstain; no other song's kit calibration or event file
is applied. All 40 original node ranges and the 96×72 dense grid are preserved.
Source-colored idle helpers illuminate the artwork without its gray backdrop.

Whisper `small.en` via stable-ts recognizes vocals with word timestamps.
Three sources contain embedded lyrics; these are retained and separately
forced-aligned for comparison. The performed text uses detected words so
unsupplied repetitions can be represented. CMU dictionary pronunciations (with explicit rules for sung ba/da-style syllables) map
to the repository's REST/AH/EE/OH/MBP/FV/L contract; out-of-dictionary words
use its existing grapheme fallback. Phones are allocated within detected
word boundaries, not individually acoustically aligned. Ordinary lyrics below
0.25 word confidence do not trigger a mouth. The explicit phoneme exercise
retains all recognized practice syllables and their original probabilities;
lexical confidence is unsuitable for rejecting intentionally sung nonwords. This is an inferred first performance, requiring
listening review rather than a claim of perfect lip synchronization.

Both singers and the four alternate faces share the recognized vocal line.
Their roles are authored ensemble choreography; this does not identify or
separate male/female singers from a mix. Lyric, word and phoneme timing tracks
are editable in the XSQ. A separate standard xLights viseme track (three layers: phrases, words,
phonemes) and reusable
`Helix_Seven_Mouths` NodeRange face definition support the native Faces effect;
ten standard viseme names alias the seven physical mouth shapes. The existing
lyric-trigger lexicon provides stage
accent cues. Debug JSON includes source/stem hashes, timings, probabilities,
pronunciation methods, rejected drum candidates and musical-review status.

## Native shows and previews

`outputs/Snowman_Ensemble/shows/<song-id>_<band-or-faces>/` contains an
independent 3D xLights show, native model exports, Media XSQ, rendered FSEQ,
original relative media, static orbit/zoom geometry review HTML and full MP4.
Use xLights 2026.18 or newer, select the folder as the show directory, and
open `Snowman_Band.xsq` or `Helix_Singing_Faces.xsq`. Render All before play.
No physical output controllers are configured. Geometry is a planning model,
not a controller, power or fabrication plan. Arm/mouth motion means switching
stationary light poses, not moving physical hardware.

Movies are 1280×720, H.264/yuv420p, 20 fps with original-source AAC audio. The
projector uses actual native FSEQ values on the identical exported XYZ nodes;
these are neither generated art slideshows nor recordings of the xLights GUI.
Displayed lyrics are recognized text and may contain errors. The HTML is a
static geometry review; the MP4 and native sequence contain the performance.

## Reproduction

Install the exact external CPU inference versions recorded in
`evidence/snowman_ensemble/runtime.json`. ADTOF code/weights are external and
are not redistributed. Their evaluation licensing and unresolved musical
acceptance remain as documented in `DRUMMER_TRANSCRIPTION_REASSESSMENT.md`.
ffmpeg/ffprobe and pinned xLights 2026.18 are required for delivery checks.
Retain network proxy/CA settings when installing/downloading models.

Prepare `outputs/Snowman_Ensemble/sources.json` with IDs 00–05, source paths,
original hashes, durations, titles, embedded lyrics and `previous` flags.

```bash
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 python -m tools.analyze_snowman_ensemble outputs/Snowman_Ensemble
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python -m tools.align_snowman_lyrics outputs/Snowman_Ensemble
DISPLAY=:101 XL_NO_GPU_COMPUTE=1 python -m tools.probe_snowman_ensemble outputs/Snowman_Ensemble --xlights /path/to/AppRun
DISPLAY=:101 XL_NO_GPU_COMPUTE=1 python -m tools.build_snowman_ensemble outputs/Snowman_Ensemble --xlights /path/to/AppRun
DISPLAY=:101 XL_NO_GPU_COMPUTE=1 python -m tools.add_snowman_face_definitions outputs/Snowman_Ensemble --xlights /path/to/AppRun
python -m tools.package_snowman_ensemble outputs/Snowman_Ensemble outputs/Snowman_Ensemble_Delivery
```

The focused tests cover canonical preservation, contiguous channels, 3D depth,
fixed/mouth isolation, pronounced words/50 ms allocation and source-only
instrument activity. Native proof checks every mouth node/frame and exclusive
active/rest arm holds against the source-derived schedules. Every movie is
fully decoded and its soundtrack compared at zero offset to the original.
All 11 native shows and full-song movies are complete: 33,726 native frames and
105 lit models. Every mouth/arm schedule matches native output; all five paired
drummer performances match every channel/frame. Metadata rerenders preserve
every performance frame. Minimum original-vs-AAC soundtrack correlation is
0.9992747792. 48 focused tests pass. Both delivery ZIPs pass CRC, and a relocated
show rerenders identically. See [all download links](SNOWMAN_ENSEMBLE_DOWNLOAD_LINKS.md)
and `evidence/snowman_ensemble/verification.json`. One embedded-reference
segment in 49 failed alignment; detected-word performances remain separate
from reference alignment and are not claimed as reviewed ground truth.

The older `test_band_demo_manifest_includes_vocal_face_export` fails on the
unchanged inherited demo path because non-drummer runtime states are empty.
This focused native performance path does not use or promote that demo compiler.
No whole-repository green-test, physical controller, local laptop audio device or
human musical acceptance claim is made. `MASTER_TODO.md` remains the handoff.
