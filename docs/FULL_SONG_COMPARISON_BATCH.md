# Full-song native 16-panel comparisons

Use this runner on an isolated checkout with Helix's Python dependencies, FFmpeg and ffprobe, and the verified xLights native renderer. The existing native preview runtime uses xLights 2026.18 and an isolated X11 display on Linux. The renderer must support the explicit export dimensions. Give parallel workers separate displays and disjoint panel numbers, and use a dedicated output directory per source SHA-256.

Obtain the original audio bytes through authenticated Drive access. SHA-256 the downloaded bytes, keep one work directory per exact hash, and retain distinct hashes even when filenames match. Record duplicates, calibration exclusions and retrieval failures in the private inventory. Keep private Drive IDs and credentials out of public repository files and logs.

```bash
export HELIX_NATIVE_PREVIEW_WIDTH=640 HELIX_NATIVE_PREVIEW_HEIGHT=360
python -m tools.render_full_song_comparison /private/input/song.mp3 /private/work/source-hash \
  --expected-sha256 "$VERIFIED_SOURCE_SHA256" --instrumental --xlights /path/to/xLights
```

Use `--instrumental` for an identified instrumental recording. Use `--vocal-fixture /private/fixture` for a vocal recording. The fixture must belong to the original audio and pass the applicable vocal-confidence checks. A successful audio/video render does not establish singer identity. Generate layouts first with `--prepare-only` when running disjoint panel groups. Use `--render-panels 1 2 3` on a worker to render a selected group, then rerun the full command to validate checkpoints and compose.

`comparison_manifest.json` binds the full MP4 to source, engine commit, renderer and per-panel native layout, XSQ, FSEQ and video hashes. `panel_activity.json` records decoded visible and moving frames without the captions. The final MP4 is published locally only after the media and panel checks succeed. Keep failed layout folders and candidate files as diagnostics. A partially prepared layout folder can be moved aside before rerunning. A changed recording or source commit should get a fresh directory.

Upload the verified MP4 individually to the designated Drive folder. Read the uploaded bytes back and compare them to the manifest before counting the song. Keep the video and its receipt together in the private batch index. Owner review is separate from technical verification.
