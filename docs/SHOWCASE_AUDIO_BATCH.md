# Five uploaded songs on the six showcase layouts

The audio batch runs active Helix Prime v27.3 on the user's five exact MP3
recordings and the six existing artistic layouts. The default produces thirty
full-song XSQs, native xLights FSEQs and 1280×720, 20fps MP4s with original song
audio. The existing drummer and permanent layouts are unchanged.

## Run and review

```sh
DISPLAY=:99 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
python -m tools.run_showcase_audio_batch \
  --audio-dir evidence/showcase_audio/source \
  --xlights /absolute/path/to/xLights-2026.18/squashfs-root/AppRun \
  --workers 2

python -m tools.package_showcase_audio_batch
```

Use an X server, or `xvfb-run -a`, for native rendering. The pinned AppImage
SHA256 is `62affb88b9a9b03cf5164974ac69bcefe35c559719d157b3364e4d4a5ab4214b`.
`--track Frostbitten_Fingerboard --flavor neon_circuit` selects a single pilot.
`--finish-existing` resumes rendering from the saved batch manifest without
repeating audio analysis. Completed output reuse verifies sequence, media,
FSEQ and MP4 hashes; native render stamps also bind the layout XML.

Open `outputs/showcase_audio/index.html` for all full-song MP4s, XSQs,
twenty-four-second six-layout comparison reels and five import packages.
The complete offline review ZIP includes all thirty videos/native shows and
a gallery with working relative links.
Each package contains six separate shows: set one directory as a new xLights
show, open its XSQ and keep the media/assets beside it. Render locally before
connecting output hardware. Native FSEQs remain in the complete local output.
Each comparison shows the same song interval simultaneously in all six
layouts, centred on a bright native frame in the middle70% of the first
layout. Selection is recorded; no lighting is changed for the excerpt.
Full previews retain the entire uploaded recording.

## What is preserved and corrected

- One SHA-bound, process-local cache per song reuses audio, harmonic, stem
  and multiband analysis. Configuration changes fail closed; per-layout
  mutable section profiles are copied. Layout routing and placements are
  recomputed for every show. No unverified serialized analysis is loaded.
- Clean templates contain no twenty-four-second demo choreography. The
  fixed thirty-second orchestration bridge seed is not used. Prime detects
  song features and generates its existing audio-driven placements.
- Legacy Ramp cues do not name a native xLights effect. The adapter converts
  them to native On envelopes, preserving explicit endpoints or supplying an
  onset-aligned100→0 attack/decay. Single Strand is canonicalized to
  SingleStrand. Unknown effect names fail closed against the native catalog.
  A pinned native probe checks the formerly dark Ramp interval, its decay and
  preservation of the existing On/SingleStrand intervals.
- The native adapter sets Media type and full-song duration rounded up to
  fifty-millisecond frames. It converts legacy inline settings/palettes and
  flat model/submodel rows into native EffectDB/ColorPalettes references
  and direct SubModelEffectLayer children, preserving placement times.
- Explicit family routes cover both sides. Prime's signed numeric-name
  discovery still omits some paired RGB motifs. Only an otherwise unrouted
  negative-side artistic motif can share its existing sibling's complete
  audio-driven choreography, with its own authored palette. This is logged
  under `mirrored_rgb_motifs`. Independently sequenced targets, instruments,
  controls and servos never acquire these copies. No drum identity or onset
  is inferred from this artistic symmetry.
- Geometry, native channels, assets and authored model/submodel colours
  remain unchanged. Mixed generated-show groups contain only RGB targets;
  control/image/label fixtures retain their layout representation but do
  not receive RGB music effects. Pictures/Text choices receive native content
  sources instead of silently rendering black.
- Videos project actual native channel values through a cached geometry
  view; they do not generate independent lighting from playback time. Exact
  native dots remain full resolution; soft halos use a half-resolution blur
  to reduce processing cost. A grid-aligned crop removes empty screen margins
  during compositing; all six layouts match the prior full-screen compositor
  byte-for-byte in both halo modes. Custom grid coordinates match the export;
  stock model review geometry remains illustrative.

## Evidence and limits

`batch_manifest.json` records source hashes, analyzed waveform durations,
per-song reuse counts, native export decisions and each preview's proof.
Every `verification.json` records full native frame count, model coverage,
control isolation, animation, first/last active times, video/audio streams,
duration and file hashes. `soundtrack_verification.json` compares decoded
original audio to each unique AAC stream; matching streams can reuse that
comparison across layouts. Early, middle and ending frames are decoded from
the actual MP4s, not just rendered independently.

The dedicated workflow checks relevant regressions and one full uploaded
Frostbitten/Neon native pilot. The complete thirty-show local run provides
the broader batch evidence; the workflow does not claim thirty remote runs.
An existing legacy vocal-validator fixture fails its unrelated current
Element requirement; record this separately rather than claiming an entirely
green repository test suite.

Prime uses its existing local fallback separation and sequencing rules.
This task does not tune or certify its inferred instrumentation, nor the
physical drummer. Engine scores, channel coverage and CI establish technical
execution; musical and artistic acceptance require the user's preview review.
