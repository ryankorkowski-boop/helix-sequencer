# Helix musical band response — October 13, 2026

The new preview path keeps both keyboardist and xylophonist and preserves the
approved guitar performance. Four 78.2-second samplers use different stages and
different audio arrangements. Each starts with eight seconds of the original
Dry Drum Test, includes three guitar-forward musical passages, and ends with
Wire Tree's 196.0–224.2-second last full chorus. Musical passage selection uses
retained guitar and vocal activity, not independently verified solo notation.

## What changed

- Ringing pitched attacks use the original source screening instead of a second
  restrictive filter. Bell, marimba and xylophone-like cues share a dedicated
  49-bar MIDI48–96 rig, separate from piano. No octave folding or beat-driven
  filler notes. Source-wide accepted attacks: Wire Tree 23→66, Who Knew 33→58,
  49 23→52, Candy Cane Chaos 18→31, Festivus 35→82. These are estimates of
  ringing instruments, not verified instrument transcription.
- Keyboard hands move toward supported notes before their display frame and
  reach the depressed key surface on that frame. Bass plucks have a shorter
  130ms release and smaller displacement. Fixed links remain connected.
- The original source-art drummer has an optional shaded sleeve/mitten profile,
  a visible shaft grip/butt, and wrist-led rebound. Original drum identity,
  strike contacts, source art and fixed stick/link lengths remain unchanged.
- Singers keep a stable assigned lead throughout a recording. Repeated lyrics
  no longer cause arbitrary singer swaps or a fabricated duet. Explicit
  start/end/role overrides support real exchanges and shared phrases. Mouths
  retain recognized phonemes, close over measured silence and use vocal energy
  for jaw amplitude. The initial per-song casting is a provisional isolated
  voice-register estimate; singing pitch does not prove gender or separate
  simultaneous voices. Listening review and manual casting remain necessary.

## Reproduce

Restore the existing, SHA256-bound source/audio/note/phoneme caches using the
input restoration in `.github/workflows/render-band-refinement-review.yml`.
Run `python -m tools.rebuild_band_logic_review`, then:

```bash
LIBGL_ALWAYS_SOFTWARE=1 EGL_PLATFORM=surfaceless LP_NUM_THREADS=2 \
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 \
python -m tools.render_musical_band_samplers \
  --casting evidence/musical_band_response/singer_casting.json
```

Use `--pilot` for two seconds of each passage, or `--version 1` through `4` for
one complete movie. A source hash mismatch or out-of-bounds clip fails loudly.
Ten-millisecond fades remove edit clicks without changing timeline lengths.
Movies use 1280×720, 20fps, H.264/AAC, and fast-start MP4.

## Verification and preservation (initial batch)

At initial batch completion, 57 focused regressions passed. The guitar's source events and all guitar curves
are identical to the approved implementation, and all guitar instance matrices
match across 1,876 sampled source frames from five songs. At that stage, seven protected
engine/scene/drummer source files retained their original bytes. No desktop GUI,
Android code, original audio/layout, or master sequencing algorithm changed in
that first batch. The later direct-engine failure guard is documented below.
Encoded movie audit checks complete decoding, frame counts, duration, waveform
agreement, visible decoded frames, and literal mallet contacts. Evidence lives
in `evidence/musical_band_response/`; rendering output in
`outputs/Musical_Band_20261013/`. Artistic/musical listening accuracy and physical
controller playback are not claimed by the automated checks.

## Pixels and discrete lighting channels

These movies show continuous animated geometry. Reproducing them directly uses
a video display or RGB pixel matrix. The existing five-performer AC plan is 66
discrete channels: guitar14, bass14, male singer12, female singer13, drummer13.
That plan switches wired zones/poses and does not include keyboard or mallets.
There is no verified seven-member physical export or channel count yet. A
physical band can retain discrete LOR/xLights channels if its actual poses and
wiring are mapped; it cannot reproduce continuous mesh articulation with the
unchanged 66-channel plan. Native virtual-matrix packaging remains available
through `tools/export_refined_band_matrix.py` and should not be described as a
physical-performer export.

The new rendering path is opt-in. Existing engine, desktop/Android applications
and historical preview paths remain preserved on their own branches.

## Final October13 follow-up

Both singers and the mallet player now use neutral beanies/faces, with color
identities and stable source lanes. All four samplers are refreshed with the
original faint H/internal credit and the final protected keyboard contact
anchors. A later real key-mesh audit caught overlapping anticipation; the fix
keeps actual source change frames and uses one held-note lane for key depression
and hand position. Original guitar transition behavior remains unchanged.
The latest focused suite passes65 tests; see evidence/final_20261013/.
The only subsequent master-engine change is a five-line failure guard, not
sequencing/detector scoring. The fresh branded GUI source is on its isolated
local branch; its publication/build was rejected by automatic approval review.
Today’s full status, legal limitations, channel distinction and market estimates
are in HELIX_COMPLETION_AND_MARKET_20261013.md.
