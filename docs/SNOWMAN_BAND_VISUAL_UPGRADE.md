# Refined snowman performance previews

Read `MASTER_TODO.md` for the current handoff and review status.

The new preview rig replaces the sparse point projection with smooth three-dimensional snowmen and instruments. It includes an upright bass with four strings, bridge, fingerboard and endpin; a six-string electric guitar with frets and pickups; a correctly grouped 37-key keyboard; two distinct singer characters; and a raised drummer with a snare, three toms, kick, hi-hat and two cymbals. An alternative stage pairs the drummer with four original singing-face sculptures and interwoven helix rails.

These are character-performance review videos. They are **not new native xLights exports or recordings of native playback**. The existing native shows, model node order, source artwork, recordings and all prior movies remain untouched. Mesh GLBs are static geometry references, not xLights models or playable animations.

## Source and performance behavior

The original FSEQ binds the movie frame count, and its corresponding tagged XSQ supplies strike windows, intensity and the persisted snare-hand schedule. Idle artwork colors are not interpreted as hits. Cymbal surface decay follows the source duration with an approximate visual fade; it never extends an arm's strike hold and does not claim reproduction of the native shimmer raster. Both views of a song use identical decoded drum curves and hand schedules. The new drummer mesh interprets the polished V3 arm/three-tom contract in 3D. Searches of current/main and relevant band/drummer branches found procedural member artwork definitions and instrument specifications, but no separate complete band-member concept PNG collection or a different approved drummer image. **This does not claim recovery of the user's preferred drummer revision.** The original PNG/XMODEL files are preserved.

Existing lyric lines and seven mouth shapes are reused. Bass pitch uses probabilistic YIN; guitar and keyboard use constant-Q spectral candidates with overtone rejection. Measured separated-stem attacks drive picking and key gestures, while notes drive finger/string/key positions. These are inferred performance cues rather than a verified musical score. The keyboard folds pitches into its displayed register. A quiet piano stem produces no artificial keyboard solo.

The male and female characters have separate mouth/gesture controls. Conservative phrase-level voice embeddings test whether a stable second voice profile can be routed independently. None of the six mixes passes the current confidence gate. Their uncertain vocals therefore remain on the lead character; the harmony mouth rests. There is **no claim of acoustic gender classification, singer identity recognition or separation of overlapping duet vocals**. Reliable separate singer tracks or verified phrase assignments would permit independent lip sync; the current previews do not manufacture such assignments.

## Reproduction and checks

```sh
python -m pip install -r requirements-band-preview.txt
python -m tools.analyze_band_upgrade
python -m tools.render_band_upgrade --width 1920 --height 1080
python -m pytest tests/test_band_performance_scene.py tests/test_keyboard_geometry.py tests/test_drummer_review_schedule.py -q
```

The focused path uses external Demucs stems already generated for the original six recordings, SpeechBrain ECAPA embeddings, librosa, SciPy, NumPy, scikit-learn, Pillow, trimesh and ModernGL/EGL. The installed SpeechBrain model revision is `0f99f2d0ebe89ac095bcc5903c4dd8f72b367286`. Model weights and source stems are not bundled. The analysis CLI expects the existing model cache at `/workspace/runtime/speaker_ecapa` and original ensemble outputs; it is a reproduction entry point for this environment rather than a portable end-user installer.

Each movie proof records original audio/lyric hashes, decoded drummer/hand hashes, frame count, full decoding and original-versus-encoded zero-offset soundtrack correlation. Geometry tests check finite nonsingular transforms and meshes, a GLB round trip, proper raised black-key groups, instrument string tuning and the full three-tom kit. All 21 pinned original source inputs must remain byte-identical. Final review/download evidence is stored alongside the archive and performance proofs.

Limitations include stem leakage, inferred notes, uncertain vocal profiles, possible visual intersections during gestures and lack of a physical lighting/controller test. Artistic acceptance remains pending user review.
