# Drummer shoulder revision and dry-source hit review

[Download/play the38.32-second MP4](https://raw.githubusercontent.com/ryankorkowski-boop/helix-sequencer/ea7a5e17447914feba9acf1fec652bcee6df22c9/drummer_shoulder_revision/Drummer_Dry_Test_Natural_Shoulders.mp4)

[Encoded hit review](https://raw.githubusercontent.com/ryankorkowski-boop/helix-sequencer/ea7a5e17447914feba9acf1fec652bcee6df22c9/drummer_shoulder_revision/encoded_hit_review.jpg) · [Before/after shoulder poses](https://raw.githubusercontent.com/ryankorkowski-boop/helix-sequencer/ea7a5e17447914feba9acf1fec652bcee6df22c9/drummer_shoulder_revision/shoulder_comparison.jpg)

Both arm roots now sit outward and below the scarf on the upper torso. The original source arm artwork is reposed with fixed wrists and stick contact points. Small shoulder contours connect the roots to the body. The shared compositor, generated source-art pose layers and96×72 projected xmodel arm nodes are updated together. Future renderers loading the canonical assets pick up these shoulders; older published movies stay unchanged.

The original Dry Drum Test is38.32seconds. Its source PNG/audio/transcription cache, eight surface masks, three-tom kit, seven stick contacts and289 accepted strike/hand schedules are preserved. The exact original dry-test XSQ/report were recovered from artifact11527580859; cached analyses are source-hash bound.

## Coverage results

Every delivered score pulse was checked in actual decoded MP4 frames, rather than only in an event manifest:

-2299 frames decode completely at1920×1080/60fps, H.264/yuv420p with original-source AAC.
-312/312 scored cues have a visible encoded response; all289 accepted physical poses are active in the corresponding frame.
-309 cached family detections are retained. Twenty without a resolved physical position get a labelled torso flash. Three additional source-only positive-novelty candidates also flash the torso.
-All185 independently measured source-novelty candidates have a visible scored response within28.74ms of the novelty timestamp. This is a measured coverage bound, not independently annotated drum timing ground truth.
-Source soundtrack zero-lag correlation0.9973257645; no excerpt or offset changes.
-38 focused geometry, projection, independent-lighting, hit coverage and stage tests pass.

Short contact sparks and the counter make repeated/overlapping scores visible even during a sustained pose or cymbal ring. Unresolved tom positions are not assigned a fabricated high/mid/floor stroke. A torso pulse indicates that a source attack was scored while its physical placement remains uncertain. Source-only candidates remain untyped. These checks do not establish exhaustive detection of every audible ghost note or correctness of every model family label.

Evidence: `evidence/drummer_shoulder_revision/verification.json` contains every encoded response and independent attack match; `scores.json` contains source identities and positions; `preservation.json` records unchanged inputs/surfaces/contacts; `visual_review.json` records encoded frame inspection; `publication.json` records the complete public download hash check. Earlier render evidence remains historical, and its exact-geometry preservation is explicitly superseded for future renders by this user-requested revision.

## Reproduce

From the repository root with its preview dependencies and ffmpeg installed:

```bash
python -m tools.render_drummer_shoulder_preview \
  --audio evidence/drummer/dry_drum_test.wav \
  --xsq evidence/drummer_shoulder_revision/Helix_Drummer_DRY_TEST_ONLY.xsq \
  --report evidence/drummer_shoulder_revision/dry_test_accepted_report.json \
  --raw evidence/drummer/dry_drum_test_adtof.json \
  --output outputs/Drummer_Shoulder_Revision/Drummer_Dry_Test_Natural_Shoulders.mp4
python -m tools.audit_drummer_shoulder_preview \
  --video outputs/Drummer_Shoulder_Revision/Drummer_Dry_Test_Natural_Shoulders.mp4 \
  --audio evidence/drummer/dry_drum_test.wav \
  --xsq evidence/drummer_shoulder_revision/Helix_Drummer_DRY_TEST_ONLY.xsq \
  --output outputs/Drummer_Shoulder_Revision/decoded
```

To rebuild canonical assets: `python tools/build_drummer_v3_assets.py --overwrite`.

This is the approved source-art performance review. Updated native projected assets are supplied; new native xLights playback/controller proof and regeneration of older band movies are deferred.

Movie SHA256: `816adc99bbcba755e975f182e55c22ba51a916e9085d43e99b7b896b20801a3c`, bytes6061359.
