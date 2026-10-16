# Native audio preview (Phase 2)

`tools/native_preview.py` extends the pinned native headless path. xLights
renders FSEQ, a fresh xLights GUI loads that exact sequence/FSEQ and exports
House Preview, and ffmpeg copies the native video packets while encoding the
selected original audio as AAC. No Python renderer supplies preview frames.
This is an explicit post-run command; existing profiles are unchanged.

Prepare a run/show directory containing `run_manifest.json`,
`xlights_rgbeffects.xml`, the generated XSQ and all referenced assets. Resolve
relative media paths against that show folder; XSQ-directory-only external
assets should use absolute references. Keep the show configuration complete,
including any controller/network files required to resolve its channels.
Do not run concurrently with generation or other manifest writers.

```bash
python -m tools.native_preview path/to/run \
  --xsq path/to/run/generated.xsq --audio path/to/original.wav \
  --xlights /path/to/xLights
```

On Linux the official GUI build needs a display even for native headless
rendering. `xvfb-run -a` can wrap the command on a headless machine. The adapter
owns its new process, uses automation port 49914 (or `--port 49913`), refuses
an occupied port, and terminates only its own process. It never enables light
output, switches an existing session, saves the source sequence, or edits
effects, palettes, timing, models or profiles.

Each attempt has a fresh `native-preview-*` evidence directory inside the run:
staged XSQ/FSEQ, native channel report, native render/GUI logs, silent native
video and verified `preview.mp4`. Input files and previous attempts are kept.
The run manifest receives `native_preview`, including source hashes, xLights
version, output hash, raw ffprobe stream evidence and verification status.
Unrelated run fields, including quality, are preserved by an atomic write.

If xLights, ffmpeg or ffprobe is missing, or native export/mux/verification
fails, the command exits 2, records `status: fallback`, leaves `mp4: null` and
adds a clear warning to the manifest. The fallback is the usable XSQ for
manual work in xLights. A silent or stale MP4 is never reported as success.
Incomplete diagnostic evidence may remain for debugging.

Audio starts at sequence time zero. The sequence duration controls the clip:
longer audio is trimmed to that duration; shorter audio or a nonzero start
timestamp is rejected. Audio and video streams must start within 30 ms of
zero and last within 100 ms of the sequence duration. Both streams are
decoded after muxing. This does not support arbitrary clip offsets, external
video references or multiple audio tracks. AAC is an encoded copy of the
original source, not a byte-identical audio stream. Native video is copied.

## Reproducible evidence

```bash
python -m tools.prepare_native_preview_benchmark test_runs/native_audio_preview
xvfb-run -a python -m tools.native_preview test_runs/native_audio_preview \
  --xsq test_runs/native_audio_preview/benchmark.xsq \
  --audio test_runs/native_audio_preview/original.wav \
  --xlights /path/to/xLights
HELIX_NATIVE_PREVIEW_MANIFEST=test_runs/native_audio_preview/run_manifest.json \
  python -m pytest -q tests/test_native_preview.py
```

The original four-second synthetic benchmark reuses Phase 1's effects and
four channels, with larger dots/visible coordinates only. Original tones at
0, 1 and 2.5 seconds provide audio markers. Tests use real ffprobe, decode
audio/video, check native light/rest windows, assert 4 channels/80 frames/78
nonzero channel samples, and reject a wrong soundtrack in a separate mux
unit fixture. Without the native artifact environment variable that one
integration test skips explicitly; native CI sets it and requires success.

Native CI pins official Linux xLights 2026.18 and verifies its SHA256. Native
export uses the configured House Preview dimensions; this build produced
248 by 442 at 20 fps locally. The benchmark is technical output evidence,
not a real-song band showcase, visual quality approval, an improvement in
Phase 1 quality metrics, or physical-controller validation. The latter
reviews remain pending. GUI `renderAll` timed out locally; the supported
path renders headlessly first and loads the resulting FSEQ for export.
