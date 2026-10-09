# Android review movies

Read `MASTER_TODO.md` first. The user accepted the layout/package work and asked for MP4 previews while back on Android. Laptop launch is deferred, with no new local playback claim. Drummer acceptance remains separate.

The movie source is the verified `outputs/Helix_Portable_Shows/` delivery. The renderer requires each XSQ, layout, FSEQ and original soundtrack to match its recorded native verification hash. It does not regenerate or modify sequences, native effects, audio analysis, model geometry or production shows.

Run from the repository root:

```sh
python -m tools.render_portable_xlights_previews \
  --root outputs/Helix_Portable_Shows \
  --output outputs/Helix_Android_Previews \
  --workers 2
```

Python requires NumPy, Pillow and zstandard; ffmpeg/ffprobe must be installed. Existing proof-matched movies are reused, making interrupted batches resumable. Changed native inputs fail before encoding.

The output contains 30 complete song movies across the six flavors and seven silent 24-second studies. Aurora retains only its actual study. Each full movie is 960×540 at 20fps, H.264 with yuv420p pixels and AAC audio; the MP4 index precedes its media for streaming. Five 24-second same-song comparisons show all six flavors together. Every movie is completely decoded for corruption checks; stream duration, frame count and expected audio are validated. Full-song AAC audio is correlated against the preserved original recording, and comparison excerpts are checked at their actual source offset.

`PREVIEWS.json` records source/output hashes and validation results. Three decoded frames per full movie/study support visual review. `index.html` is a relative-link gallery. Movie-only downloads are created beside the output directory: one ZIP per song, one study ZIP and `Helix_All_MP4_Previews.zip`. ZIP CRC and movie inventories are verified.

Lighting values come from actual native xLights FSEQs projected onto their matching geometry; these videos are not xLights screen recordings. Custom-node coordinates match the exported geometry, while stock review paths remain illustrative. Lower resolution is intentional for phone viewing. Original recordings and show files remain unchanged. No physical output is enabled, no newer concept is built and no drummer approval is inferred.
