# Execution handoff

Branch:codex/band-performance-refinement-20261012. Canonical ledger:MASTER_TODO.md. Checklist:docs/BAND_EXECUTION_CHECKLIST.md.

Restore the exact29,719,264-byte band input ZIP specified in evidence/band_instrument_review/remote_render_request.json, safely extract at repository root, then run with Python3.12, ffmpeg, numpy/scipy/Pillow/librosa/soundfile/trimesh/moderngl/zstandard/pytest/PyYAML. Wider tests also need CPU torch and cmudict.

```bash
python -m tools.rebuild_band_logic_review
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 LP_NUM_THREADS=2 python -m tools.render_refined_helix_band --dry
for job in 0 1 2 3 4 5; do
  OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 LP_NUM_THREADS=2 python -m tools.render_refined_helix_band --job "$job"
done
python -m tools.package_refined_band --montages --exports
python -m tools.audit_refined_band_native --binary /absolute/path/xLights/AppRun --display 131
python -m tools.audit_refined_band_output
python -m tools.audit_refined_band_soundtrack
python -m tools.complete_refined_band_delivery
```

Production renderer entry point:

```bash
python -m tools.render_band_upgrade --ids 00 --variants band --start 164 --seconds 18 --performance-refinement
```

Brightness defaults:body1.20/kit0.40/arms0.58/strike1.35. CLI --idle-brightness and --strike-brightness. Preserve independent body and surface masks. Do not promote background grid pixels to idle illumination.

Render band movies atomically; exception cleanup terminates and waits for encoders before removing temporary files. An interrupted initial guitar encoder exposed why this is necessary. Exclude pilots and .rendering.mp4 files from exports.

Workflow .github/workflows/render-band-refinement-review.yml reruns tests, rendering, native/pixel/audio verification and publishes a separate codex-band-refinement-20261012-v2 prerelease. It does not merge primary. Final hashes may differ across Mesa/ffmpeg versions; compare source timing, geometry, native pixels and actual decoded output.

Open: obtain raw separated WAVs and independent labels before tuning family thresholds or claiming accuracy improvements; validate mallet identity; develop native physical-prop states and controller parity separately. Further detailed fingers/chords, real stroke directions and user artistic review remain outstanding. Original protected assets must continue to match evidence/band_execution/preservation.json.
