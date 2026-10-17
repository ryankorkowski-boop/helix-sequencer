# Helix showcase and advertisement — autonomous completion checklist
Updated 2026-10-17. Branch: `codex/showcase-pilot-recovery-20261017`, PR #172.

**Release gate:** Do not merge, publish, or label desktop/Android binaries approved before the owner reviews authentic native xLights musical videos. Existing 2026-10-10 videos are historical references, not evidence of current code.

## P0 — unblock and verify current implementation
- [x] Commit note timing, MIDI pitch and normalized velocity validation; routed-string finite energy checks.
- [x] Commit independent string/key regressions and native instrument-visibility audit.
- [x] Include relevant source and test paths in showcase recovery CI triggers.
- [ ] Confirm latest workflow results and identify cancellation cause from GitHub run metadata/logs; **cancelled != failed tests**. Earlier native-proof run 39018601628 and Helix CI run 39018601636 were cancelled. Newer run statuses must be checked afresh.
- [ ] Run focused pytest for note/string, keyboard orientation, hi-hat foot and channel ownership on actual checkout; fix failures.
- [ ] Run full CI and smoke suites on both supported Python versions; record exact SHA, counts and failures.
- [ ] Verify independent singer visemes, drummer physical contacts, hi-hat foot, mallet strikes, guitar/bass note/string ownership, and front-on 2D/3D parity against decoded native frames.
- [ ] Audit source-note accuracy and uncertainty; no fabricated note, phrase or vendor-quality claims.

## P1 — restore authentic native video production
- [ ] Restore or provision actual xLights 2026.18-compatible native rendering environment. Prior scratch workspace `/workspace/scratch/1971fd9f91ad` is not accessible in this session.
- [ ] Resolve original audio and source digest for each selected song; preserve SHA256 and edit boundaries.
- [ ] Select high-quality 30–42 second source excerpts (Fractal Crown, Frosted Axes, Glitterquake Parade are candidates, not owner-approved).
- [ ] Rebuild from **latest checked commit**: seven-performer editable XSQ, xLights layout/models, rendered FSEQ, and native MP4.
- [ ] Inspect `pose_provenance.json` instrument-visibility counts and independently validate actual note/string channels, animation contacts, cymbal decay and vocal phonemes.
- [ ] Verify source-audio synchronization, camera, 1080p decoding, source SHA256 and channel/sample parity. Record concrete tool versions and commands.
- [ ] Produce genuine whole-band, musician close-up, embedded-stage and six-layout comparison MP4s with manifests and accessible URLs.
- [ ] Ask owner to approve **new** videos and song selections; do not substitute earlier review renders.

## P2 — advertisement delivery (blocked by P1)
- [ ] Select best source-verified moments of authentic solo, drumming, keyboard, mallets, vocals, and ensemble transitions.
- [ ] Edit short launch cut and longer feature showcase exclusively from validated native footage and original music.
- [ ] Add factual feature captions; distinguish supported RGB pixels from reduced AC16 capability and avoid unverified marketing claims.
- [ ] Export final MP4s, preview thumbnails, provenance/attribution, audio sync QC and reproducible project manifest.
- [ ] Provide review links for explicit owner approval. **Current state: no newly validated final advertisement MP4.**

## P3 — match/exceed community and paid vendor sequence expectations
- [ ] Gather legal preview/reference set of five professional vendor and five community sequences with licensing/quality limits.
- [ ] Conduct blind musicality and choreography ratings with `tools/sequence_quality_benchmark.py`; record actual reviewer evidence.
- [ ] Improve phrase-aware choreography, synchronized individual instruments, color hierarchy, build/release/finale and usable prop groups based on measured gaps.
- [ ] Verify multi-layout variants (small, traditional, mega-tree, band, advanced 3D, AC16), independent xmodels, import/remap and compatibility.
- [ ] Validate full-song editable XSQ, native FSEQ, and supported LOR LMS export with real import tests; no blanket compatibility promise.
- [ ] Run owner review and small external usability trial before any parity/superiority claim.

## P4 — release (owner approval required)
- [ ] After explicit approval only: integrate approved branch and confirm desktop Windows EXE/Android APK builds.
- [ ] Verify release archives, install/playback, third-party import, licensing and publication links.
- [ ] Publish approved deliverables, documentation and honest limitations.

## Progress / execution log
- 2026-10-17: This checklist created to consolidate scattered status updates in `docs/RUNNING_SHOWCASE_IMPLEMENTATION_CHECKLIST_20261017.md` and `MASTER_TODO.md`.
- Pending: verify fresh CI run results and resume actual native video production. No new MP4, no approval, no release.
