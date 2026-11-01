## UploadedDrum1reference

Reference identity is now located: seeDrum1_Reference.json. The upload is exact archivedV3drytest f014db45; full decode, actualframes and drysoundtrack correlation.99708 verified. The choice between this exact image-based drummer within3Dscene and fully volumetricgeometry is pending owner response; original no-planar requirement has not silently changed. Continue from existing36smusic checkpoint. PinnedofficialxLightsAppImage downloaded, checksum verified and resources extracted at /workspace/checkpoints/xlights-runtime/squashfs-root. Patchedbinary still needs compatible monolithicwx runtime; no new native render claimed.

# Published recovery checkpoint

Published compositor/evidence implementation: `9a800a1abad26d2daf203ad34caf9779249ae581`; remote recovery branch head matched. All five compressed production files round-trip to their recorded SHA256. No qualifying final MP4 exists; delivery remains blocked. PR188 unmerged and no release published.

# 1 November real-audio comparison recovery

Delivery is BLOCKED, not complete. No file named HELIX_REAL_AUDIO_12_LAYOUT_COMPARISON_APPROVAL.mp4 was made. Current required original fully modeled3D drummer source was not located. The canonical exporter, original restore9e9dcc3 and actual retained native pilot use planar V3 artwork. The procedural model explicitly says new interpretation. Do not use either as the requested original3D asset. Owner answered that they are not certain where the asset is. Independent acoustic singer qualification also remains open.

The new36s sampler is actual owner-library music; SHA256 b889df23d4960b393bfa5b6f84f2f72de245bdd176032bf16346d8680e960a3d. Source hashes/Drive IDs/ranges are in Sampler_Provenance.json. Engine completed at source09677d4:5155effects,5section/shared-sync frames,69drum/17bass/250guitar/631keyboard cues. These counts do not establish acoustic truth. Whisper unavailable; no lexical timing claim.

Focused34tests pass in27.93s, including an actual test-only subsecond12-color FFmpeg composition/decode/panel-order/audio check. No synthetic audio was used. Those test fixtures are not native display footage and are not delivered or named as approval media. Initial6missing-imageio import failures resolved by installing imageio/imageio-ffmpeg; assertions unchanged.

Compositor fix:4columns x3rows,480x360cells=1920x1080,30fps,H264/AAC,one soundtrack,explicit literal labels. Existing historical layout names remain historical; requested12-layout mapping is unfinished and must not be relabeled as complete. Original engine, drummer, AC addresses/colors and gates unchanged.

Latest available native render checkpoint is a historical rejected diagnostic: run41219733511/artifact13050724353, /workspace/checkpoints/native/phoneme-work/show/native-preview-dakzsdzu/preview.mp4. The actual2s frame was inspected. Motion.425fails the unchanged.65gate; independent vocal/reference gate also fails. Exact-source renderer artifact13050955075 is retained at /workspace/checkpoints/renderer; it needs pinned2026.18 resources and compatible wxWidgets/shared libraries. Its binary alone does not make a runnable local native environment. Do not promote the historical pilot.

Restore production checkpoint without reanalysis:
```bash
cd /workspace/helix-sequencer
mkdir -p /workspace/checkpoints/production36
python - <<'PY'
from pathlib import Path
import gzip,shutil
for source in Path('evidence/beta_completion/comparison_20261101/production').glob('*.gz'):
    target=Path('/workspace/checkpoints/production36')/source.name[:-3]
    with gzip.open(source,'rb') as src,target.open('wb') as dst:
        shutil.copyfileobj(src,dst,1024*1024)
PY
```

If audio scratch is lost, fetch the two observed Drive IDs with the connected Drive plugin, verify their exact recorded SHA256, update only local_path in a copy of source_selection.json, then recreate the exact36s waveform:
```bash
python -m tools.build_review_sampler /workspace/checkpoints/source_selection.json /workspace/checkpoints/sampler36 --seconds-per-song 18
```
This input contains explicit source-clock intervals, not a newly qualified lexical or section-based selection. The waveform must hash to b889df23d4960b393bfa5b6f84f2f72de245bdd176032bf16346d8680e960a3d. No gain normalization;20msedge fades only.

Exact fresh engine command (after restoring input.xsq from the retained native artifact):
```bash
python main.py --profile master -- --template /workspace/checkpoints/native/phoneme-work/show/input.xsq --audio /workspace/checkpoints/sampler36/Helix_Starred_New_Review.wav --layout-file xlights_rgbeffects.xml --output-dir /workspace/checkpoints/production36-rerun --single --variants 1 --no-prompt --no-save-settings --no-workspace-history --no-learning-memory --palette-mode warm --sync-lyrics-heads
```

Next executable source-dependent action: obtain the approved original fully modeled3D drummer source or known-good commit, integrate its existing event interface without substitution, qualify two singer clocks on this exact audio, finish supported12-layout mapping, render, compose and verify. A passing mux/compositor test does not establish that these gates are satisfied. PR188 and release remain unmerged/unpublished.
