# Truths-backed drummer and vocal integration — 2026-11-15

Status: **partial implementation, not owner acceptance**. This record describes
verified inputs and the narrow scheduler repair. It does not assert a repaired
native xLights MP4 exists.

## Source-of-truth videos

Authenticated owner Drive folder: [Truths](https://drive.google.com/drive/folders/1SUtLHdk1nncBrQssmBpYHUeE327Q1VJj).
The following original stored MP4s were downloaded, probed and sampled; hashes
are of the downloaded original bytes, not edited reference images.

| File | Duration | SHA-256 | Review role |
| --- | ---: | --- | --- |
| [Aaadrummergroundtruth.mp4](https://drive.google.com/file/d/1cPHct6XEhZM_-9x9lkCP-7tN_DfIKo7b/view) | 20.000 s | `e324abb3e73da098ccd7253b5a154d40d4d8ada63b099fcbd6cd504c69678458` | Canonical drummer appearance, instrument and stick contact illumination |
| [Aaadrummertruth.mp4](https://drive.google.com/file/d/1qDjj8JJ3Z-rZfFUntidsnPkq5DRqOsMm/view) | 38.317 s | `d4b144629a325ed32729b7ca7e6779fb5c561df84c67d8218d94a9d1f8062c4d` | Source-driven kick/snare/cymbal and drum-light response |
| [Bbb Vocalstruth.mp4](https://drive.google.com/file/d/1FN29mXUxy5dDJ0VIn6Wy7K-4llFHzGAs/view) | 34.900 s | `2485eb68a2f3dd0866bf55818212f38645d85bb391b21c56cd453ee2e4d625d4` | Multi-view stage and singer shape reference |
| [Bbb vocals.mp4](https://drive.google.com/file/d/1PPPz4TbYIS0Z9D6zRHScfnQoom38ltxX/view) | 34.900 s | `190705c655adcd417fa69e94920516f6235571beb2fc1de01660feb55a177d0e` | Readable pair of singer mouths, **explicitly labeled ORIGINAL – TIMING FAIL** |

All four contain H.264 video and AAC audio. The drummer references are
960×540 at 60 fps. The vocal references are 2560×1440 and 1280×720,
respectively, both at 20 fps. Frame sampling was a visual review, **not**
frame-perfect acoustic/phoneme ground-truth certification.

## Canonical constraints

- Exactly three toms: High, Mid and Floor. Preserve the original V3
  artwork, instrument positions and all eight sequenced component IDs.
- One drum event lights its physical target and contacting stick geometry.
  Sticks and arms are derived animation geometry, not extra sequencing channels.
- Preserve independently classified tom hits, even when another tom lands in
  the same 24 ms debounce window or at the same timestamp. Different tom
  targets must not damp one another as rapid duplicates.
- Unclassified toms and generic drum_bus are rejected; do not fabricate tom
  fills to make a showcase appear more active.
- A genuine simultaneous multi-instrument strike may exceed the normal
  four-event clutter cap; staggered noisy bursts retain the cap.
- Preserve individually audible kick, snare, cymbal and hi-hat strikes.
  Validate left/right cymbal alternation and shoulder-constrained arms in
  native frames against the selected videos.

## Vocal guidance

Reference video appearance is **not** proof of singer identity or timing.
In particular, the readable close-up is labeled TIMING FAIL. Reuse the useful
open/closed shape geometry and readable framing only where correct, not its
unverified clocks. Independent lead and purple harmony mouth channels require
source-qualified stems or independently verified acoustic identity; no mouth
activity during source silence. The full-length Helix Motion pilot is
instrumental: it is not a valid demonstration of singing. Use a separate
source-matched vocal sample to judge words and mouth timing.

## Implementation and verification

This feature branch changes only `mapping/drum_mapper.py` to debounce
classified toms by **physical target** instead of the generic `tom` family,
and exempts exact-onset distinct physical drum groups from the clutter limit.
`tests/test_three_tom_truth_integration.py` adds five small guard tests.

This does **not** repair or certify source detection, pose meshes, string
instrument behavior, vocal separation, phoneme accuracy, or the nine-panel
composition. Remaining work: run all focused tests and Python 3.11/3.12
regression in CI; render source-accurate native XSQ/FSEQ with all three toms
visibly hit; check original audio sync and complete decode; visually compare
contact geometry against the Truths videos; independently validate vocals
with verified source tracks; then render and offer a **new nine-panel MP4**.
Owner approval remains required for every new pilot.

## Release gates

Do not merge PR #188, trigger the other 82-song batch, publish beta, or
mark this change as accepted from logic tests or a diagnostic clip alone.
The owner's favorite advanced RGB Resistance panel is a positive reference
for the nine-panel visual composition, not a reason to change drum timing.
