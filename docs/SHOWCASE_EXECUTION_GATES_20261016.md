# Showcase execution gates — 2026-10-16

Working branch: `codex/showcase-quality-gates-20261016`; review PR #168. Base: `codex/72h-completion-20261015`. No public release merge authorized.

## Completed code (not yet verified by CI)
- [x] MP4 probe and complete-decode validator (`tools/validate_showcase_mp4.py`).
- [x] Six-pilot manifest validator (`tools/validate_showcase_batch.py`).
- [x] Consolidated compatibility entrypoint (`tools/validate_showcase_manifest.py`).
- [x] Regression tests added for MP4 and pilot manifest failure cases.
- [ ] Execute tests in CI and record run URL, commit SHA, failures and environment.
- [ ] Audit validators for edge cases, path traversal and duration/stream consistency.

## Source audio and sequencing
- [ ] Inventory all authorized Drive recordings and nested folders; retain SHA256, size, duration, arrangement identity, original filename.
- [ ] Score 30–42-second passages for drums, pitched parts, guitar, bass, vocal activity and musical transitions.
- [ ] Record excerpt timestamps and actual source-audio fingerprints.
- [ ] Verify snowman identity and six-performer band contracts (never silently substitute humans or placeholders).
- [ ] Preserve 16-channel CTB16PC physical contracts and native xLights/LOR outputs.
- [ ] Audit semantic lyric cues RED, BRIGHT, DIM, DARK, SHIMMER, FLICKER, negation, confidence and sentiment; implement only after establishing existing behavior.
- [ ] Measure instrument independence, cymbal retriggers, drum contacts, bass/guitar separation, mallet timing and singer phonemes.
- [ ] Confirm front-on 2D/3D parity and xLights-native model import.

## Showcase review production
- [ ] Produce six distinct real-audio pilot MP4s: percussion snowmen, Christmas mallets, rock guitar, vocal snowmen, integrated 3D and six-layout comparison.
- [ ] Validate all six with real FFmpeg decode, source matching and manual visual review.
- [ ] Scale only after pilot gates: 12 standalone bands, 8 band-in-layout, 10 six-layout comparisons, 10 lyric videos.
- [ ] Publish review-only manifest, screenshots, validation receipts, video index and downloadable ZIPs.
- [ ] User explicitly approves review videos before integrating public EXE/APK.

## Separate future work
- [ ] Issue #154 Universal Sequence Library remains planning-only and approval-blocked. Its pilot and mass publication require separate authorization.
- [ ] Do not merge #150, #168 or release builds without the relevant user approvals.
- [ ] Do not claim videos, physical controller testing or native import testing without real artifacts and evidence.

## Benchmark criteria
Compare only publicly shared or authorized free sequences and commercial demonstrations. Assess timing, phrase design, controlled darkness, independent prop groups, mega trees, arches, singing faces, submodels, intentional color design, spatial motion and import portability. Do not reproduce paid vendor arrangements.
