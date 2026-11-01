# Current recovery checkpoint — actual MP4 delivered, owner review pending

This section supersedes all blocked/running recovery instructions below. Do not rerun analysis or separation for unchanged inputs.

Delivered file: `/workspace/deliverables/HELIX_REAL_AUDIO_12_LAYOUT_COMPARISON_APPROVAL.mp4`; 18,530,685 bytes; SHA256 `0a2a0763b4952984b1d5a0d8481b08348ab212e702c3d64a4af29b6c5b1bb198`. Drive copy: https://drive.google.com/file/d/1uNEshOt-FvjRhp3nRK5O73nc8kefoDup/view?usp=drivesdk . Download-back identity and full playback verified. Final code commit and module hashes are recorded in `render-source-snapshot.json`; this was rendered from those final worktree bytes before their commit, not from unchanged `60fb74e`.

Valid current render checkpoint: `/workspace/checkpoints/comparison-hook/layouts/01` through `/12`, each with matching native XSQ, layout, FSEQ, run manifest and successful actual preview. Solid band: `comparison-hook/panels/02_Canonical_3D_Snowman_Band.mp4` and JSON. Graded panels: `comparison-hook/graded-panels/01.mp4` through `/12.mp4`. Full final file and delivery checks: `final-playback-verification.json`, `delivery-download-verification.json`. Preserve both the original candidate and final metadata-only remux; encoded video/audio stream hashes match. Never promote earlier failed36s diagnostic panels.

Recover without reanalysis:

```bash
cd /workspace/helix-sequencer
git fetch origin codex/eight-hour-recovery-20261019
git switch codex/eight-hour-recovery-20261019
python - <<'PY'
from pathlib import Path
import gzip, shutil
target = Path('/workspace/checkpoints/production-hook')
target.mkdir(parents=True, exist_ok=True)
for source in Path('evidence/beta_completion/comparison_20261101/production-hook').glob('*.gz'):
    with gzip.open(source, 'rb') as src, (target/source.name[:-3]).open('wb') as dst:
        shutil.copyfileobj(src, dst, 1024*1024)
PY
```

Original soundtrack is tracked at `fixtures/audio/Phoneme_Test_Hook.mp3`, SHA256 `19e90c273d0d747938f24b36586b50818c104cddffbefe4a4128927374301938`. Cached source-bound vocal clocks are `fixtures/audio/phoneme_vocal_separation`. Production staging is `/workspace/checkpoints/source-hook` (media/audio, sequence/plan and run_manifest); fresh run outputs `/workspace/checkpoints/production-hook`. Do not reuse the older36s sampler staging for this34.88s recording.

Exact optional regeneration commands for requested changes:

```bash
python -m tools.build_current_comparison /workspace/checkpoints/source-hook fixtures/audio/phoneme_vocal_separation /workspace/checkpoints/comparison-hook/layouts
python -m tools.render_owner_band_review /workspace/checkpoints/source-hook fixtures/audio/phoneme_vocal_separation /workspace/checkpoints/drum1-reference/Drum1.mp4 /workspace/checkpoints/comparison-hook/panels/02_Canonical_3D_Snowman_Band.mp4 --expected-sha256 19e90c273d0d747938f24b36586b50818c104cddffbefe4a4128927374301938 --dimensional-drummer --width 960 --height 540
```

The native renderer runs in the retained `helix-native-20261101` Ubuntu24 container with workspace mounted unchanged. Verified xLights binary SHA256 `09dfeae588e9659dfd41cbd6115bf77b9cf4871fcea2bd02190dcbdc3a7ac844`, upstream `839c0f590dc454bb7adb8a16c4dd92a70b46156e`, patch `93bedae81caefda745034651994a16b2d127079a5af784013109becfb428566b`. Compatible wx artifact13069713422/run41272538723 SHA256 `46ac60296a4cb797295e5a09ea31df275eca6704471a117d8da10ccbfaf3ec93`; extracted `/workspace/checkpoints/native-wx`. Runtime wrapper uses pinned resources in `/workspace/checkpoints/xlights-runtime/squashfs-root` and verified binary. Do not mix incompatible host GTK/AppImage libraries.

```bash
env -u DOCKER_HOST -u DOCKER_CONTEXT -u DOCKER_TLS -u DOCKER_TLS_VERIFY -u DOCKER_CERT_PATH docker --host=unix:///var/run/docker.sock exec -e HELIX_NATIVE_PREVIEW_WIDTH=960 -e HELIX_NATIVE_PREVIEW_HEIGHT=540 -e OMP_NUM_THREADS=2 -e OPENBLAS_NUM_THREADS=2 -e LP_NUM_THREADS=2 -w /workspace/helix-sequencer helix-native-20261101 xvfb-run -a -s '-screen 0 1600x1000x24' sh -c 'openbox >/workspace/checkpoints/comparison-hook/openbox-recovery.log 2>&1 & exec python3 -m tools.render_current_native_views /workspace/checkpoints/comparison-hook/layouts --xlights /workspace/checkpoints/xlights-runtime/run-patched.sh'
python -m tools.finish_current_comparison /workspace/checkpoints/comparison-hook fixtures/audio/Phoneme_Test_Hook.mp3 --source-commit "$(git rev-parse HEAD)"
python -m tools.verify_current_comparison /workspace/checkpoints/comparison-hook/HELIX_REAL_AUDIO_12_LAYOUT_COMPARISON_REVIEW_CANDIDATE.mp4 fixtures/audio/Phoneme_Test_Hook.mp3 /workspace/checkpoints/comparison-hook/final-playback-verification.json
```

Owned native previews resume only when hashes of actual current layout/XSQ/audio and MP4 match. Each active render process needs its own Xvfb and port; optional `--port49913` (with a space: `--port 49913`) is available for disjoint view sets. Final rename/remux must use the required filename, then repeat full decode and compare video/audio encoded stream SHA256 before replacing a delivered version. Upload actual MP4 bytes and download them back before claiming a changed delivery.

Remaining: owner artistic acceptance; independent singer/word/source-instrument proof, physical qualification and full current-source CI. No merge or release. The owner explicitly authorized matching-front dimensional construction; no missing approved mesh question remains pending. The following prior phase records remain historical failure evidence.

## UploadedDrum1reference (historical)

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
