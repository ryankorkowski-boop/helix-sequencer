# Helix four-performer refinement execution — October 12, 2026

Review build on `codex/band-performance-refinement-20261012`. Primary development is unmerged. The requested branch began at f0aca518, identical to the shoulder reference and 137 commits ahead of the older primary branch. Newer work from 0d855b2, 99bcd7b and 37ffbed was inspected and selectively carried forward, then corrected; no experimental branch merge occurred. Historical reports in BAND_REFINEMENT_REPORT.md describe an earlier build, not current validation.

## Implementation

Drummer: connected shoulder–elbow–wrist contours attached below the scarf, fixed original gold shafts, anticipation/contact/rebound/recovery, travel constraints and independent ringing cymbals. Original artwork, eight instrument surfaces, accepted 289 physical events and unknown tom identities are retained. Quiet head/torso brightness is raised to 1.20 independently of instrument idle 0.40, arm idle 0.58 and strike 1.35. Controls remain configurable from 0 to 2. This changes source-light gain, not source image bytes.

Bass: retained separated-source pitch/onset/duration/velocity events drive plucks. A kick cannot generate a note. Warm segmented strings and localized resonant accents remain visible. New fixed-length 3D joints prevent note-dependent stretching. Fretting uses the selected physical string and its semitone distance from the nut, with short deterministic transitions and stable holds.

Guitar: retained independent string routes, dominant supported contact, smaller picking and wider chord gestures, warm individual strings. New fixed-link elbow/wrist geometry and fretting transitions replace variable-length midpoint arms. Stroke directions alternate artistically; actual recorded up/down directions are not inferred.

Xylophone: compatible dedicated 25-bar MIDI60–84 rig; original keyboard stays separate. Only independently screened pitched-percussion candidates from the other stem drive this rig. Piano events and out-of-range notes abstain. Mallets have fixed shafts and fixed arm segments, literal bar contacts and visible recovery. Acoustic timestamps remain in the audit; contacts are displayed on the nearest 20fps frame with a maximum25ms timing adjustment. These are mallet candidates, not confirmed xylophone transcription.

Existing `tools/render_band_upgrade.py` can select the new path with `--performance-refinement --variants band`. Historical rendering remains available. The generic physical-performer runtime explicitly reports missing approved states rather than exporting fabricated motion. No unrelated sequencing engine was rewritten.

## Real audio and outputs

| Output | Source window |
| --- | --- |
| A synchronized drummer before/after | Complete original Dry Drum Test, 0–38.32s |
| B improved dry test | Complete original Dry Drum Test, 0–38.32s |
| C bass/guitar | 49 (Remastered),115–133s; Who Knew (Grinch's Redemption) (Remastered),101–119s |
| D mallet diagnostic | Festivus (Remastered),26–44s |
| E band montage | Dry test; Wire Tree164–182s; Candy Cane Chaos168–186s; Festivus26–44s; bass/guitar excerpts above |

Dry source SHA256:4cd9ee35b65d359aa44ac4c9e01a256bbcaf3297458340fc512084bae1463913. Input ZIP:ac7c36b1a749aedf09d2de20681163e3ede052d2062466474f228919bdc6b2ec. Originals are unchanged; soundtrack compression is AAC. A/B video frame rounding yields38.333s; the complete38.32s audio is retained. C36s, D18s, E128.35s. Five additional individual18s source studies accompany the five principal deliverables.

## Verification status

Source pass:40 protected tracked geometry/drummer/source files match the starting Git blobs; original production scene/sampler/layout/template/audio files are untouched. Focused motion, source routing, runtime, export and prior shoulder tests pass. Earlier broad collection gaps were missing dependencies, not detector failures; torch, mapping modules and cmudict were restored before rerunning. Receipts are in evidence/band_execution.

Musical pass:10 previously user-reviewed passage/signal anchors remain within14.5ms of accepted dry events. This is sparse independent evidence, not an exhaustive score. All2,160 excerpt frame poses preserve fixed3D link lengths to floating-point precision, with maximum error below9e-16scene units. Source curves preserve held notes over old release tails and restore onsets previously hidden by those tails; these are event-playback corrections. Drum family accuracy, ghost-note precision/recall, bass/guitar note correctness and confirmed mallet identity cannot be measured from prediction caches alone. Original raw six-stem WAVs and exhaustive independent annotations were not recovered.

Video/native pass: fresh complete renders, full decoding, quiet/strike/contact screenshots, original soundtrack and native matrix pixel checks are recorded in the downloadable output_verification.json, montage_audio_verification.json, native_verification.json and review_frames. Current final evidence supersedes interrupted or dim pilots. File hashes, ZIP CRC and playback media are checked before delivery.

## xLights scope

Each corresponding XSQ is a genuine Helix-generated384×216 xLights virtual-matrix Video show. Keep each `xlights/<name>/` folder's XSQ, xlights_rgbeffects.xml, xlights_networks.xml, media/performance.mp4 and media/soundtrack.wav together. Actual xLights2026.18 native rendering and frame-pixel comparison verify this route. Controller outputs are empty. These sequences reproduce the review animation on a matrix; individual stationary bass/guitar/xylophone prop articulation is not implemented. Native physical-performer parity is not claimed.

## Open work

This is a substantial implemented and rendered review build, not completion of every musical-intelligence claim in the mission. Independent raw-stem/label evaluation, confirmed pitched-percussion identity, detailed finger/chord identity, real guitar stroke direction, physical performer model export/controller proof and user artistic approval remain open. The continuous source-art drummer remains a planar prop mounted in the 3D scene. No primary merge is authorized. Continue from MASTER_TODO.md and BAND_EXECUTION_HANDOFF.md.
