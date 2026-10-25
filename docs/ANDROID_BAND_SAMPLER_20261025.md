# Android instructions, band switch and alternate sampler follow-up

Branch: codex/eight-hour-recovery-20261019; PR188 remains unmerged.
Starting HEAD:6c78bdc1644c25f841c8a14fc709a69ad2c19c03.
Read MASTER_TODO.md first. Implementation commit is the checkpoint containing
this file; subsequent completion receipts must distinguish code and docs changes.

## Implemented / device verification pending

- Replace the manual TabHost/raw-pixel help UI with a single density/inset-aware
  reader and two buttons. Keep scroll positions and selected page across tab
  changes/recreation. Device tests assert actual content, scroll and recreation.
- Persistent Band performers switch in Layout. For xLights layouts containing
  recognized band performers, off filters performers/groups/template rows in the
  private job copy; other props and their addresses remain unchanged. On preserves
  input bytes. The switch is disabled in LOR, where addressed circuits are retained.
- Band-off engine/MP4 proof is added to the real-audio Android smoke and independent
  media decode. Enabled/default behavior and existing 237s smoke remain covered.
- Build a separate Helix Review APK (org.helixsequencer.android.review), code8,
  alongside regular debug/release outputs. Co-install/launch and baseline marker
  preservation are tested only on disposable emulators. The existing owner's app
  is not uninstalled or migrated; Review needs its own input/settings selection.
- A differently signed base-package APK still cannot update the installed beta.
  The Review package is the intentional parallel-install route for this review.

## New sampler / actual analysis completed

Six16s high-RMS/positive-flux excerpts: North Pole Overdrive; Lethal Christmas Logic;
Let It Glow; Ghost In The Grid; Jingle Wobble; Christmas in the Ether.
Original Starred catalog IDs remain in showcase/starred_music_catalog.json.
Exact source hashes/sample positions are in evidence/review_sampler_20261025.
No original audio files were changed; edit fades20ms, no gain normalization.
AudioSHA25696f22339369a4f8894816bd3a621d9a5b49a95d8c95260ecb182539962acd75b.
96.000s PCM16 stereo/44100Hz. This is a new sampler, distinct from the Phoneme
Test Hook and earlier256s Starred sampler. Actual pinned UVR/Silero inference
completed:35.03s lead/4.67s backing estimates, not singer-identity proof.

The user explicitly requested preview-layout comparisons in this follow-up.
Produce12 fresh native individual previews and synchronized6/12 comparisons on
this source, clearly marked review candidates. Do not fabricate the strict
pilot_acceptance.json or mark unresolved final release gates approved.
The native cast/planar source drummer remains the retained source-family candidate;
this follow-up does not claim exact canonical visual restoration.

## Reproduce from repository root

```bash
python -m tools.build_review_sampler SOURCE_SELECTION.json NEW_SAMPLER
python -m tools.offline_vocal_candidates NEW_SAMPLER/Helix_Starred_New_Review.wav NEW_VOCALS --models PINNED_LOCAL_WEIGHTS --expected-sha256 96f22339369a4f8894816bd3a621d9a5b49a95d8c95260ecb182539962acd75b
python -m tools.prepare_phoneme_show --audio NEW_SAMPLER/Helix_Starred_New_Review.wav --output NEW_SHOW --expected-sha256 96f22339369a4f8894816bd3a621d9a5b49a95d8c95260ecb182539962acd75b --vocal-fixture NEW_VOCALS --title 'Starred Six-Song Review'
python -m tools.build_approval_collection NEW_SHOW NEW_LAYOUTS --audio-name Helix_Starred_New_Review.wav --expected-sha256 96f22339369a4f8894816bd3a621d9a5b49a95d8c95260ecb182539962acd75b --vocal-fixture NEW_VOCALS
# Run with an owned Xvfb/openbox session and verified pinned xLights2026.18:
python -m tools.render_approval_collection NEW_LAYOUTS NEW_OUTPUT --xlights PINNED_XLIGHTS --audio-name Helix_Starred_New_Review.wav --expected-sha256 96f22339369a4f8894816bd3a621d9a5b49a95d8c95260ecb182539962acd75b --bundle-name Helix_Starred_Preview_Layouts --source-commit SOURCE_COMMIT
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 NUMBA_NUM_THREADS=2 python -m pytest tests/test_review_sampler.py tests/test_band_visibility.py tests/test_approval_collection.py tests/test_approval_label_atomic.py tests/test_review_archive_staging_guard.py tests/test_sampler_comparison_duration.py tests/test_phoneme_vocal_export.py tests/test_vocal_diagnostic.py tests/test_android_recovery.py tests/test_android_offline.py -q
```

Local checks:41 passed; additional guidance/branding/signing/source suite18 passed
with overlap. Device and native completion/results/artifact URLs are still pending.
Next: finish actual native generation/inspection and API30/API36 Android tests,
repair any failures, then preserve the final APK/videos/receipts and update this
handoff with exact links and limitations. Never substitute output creation for
visual acceptance or co-installation for an in-place historical update.
