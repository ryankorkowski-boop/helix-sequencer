# Uploaded Dry Drum Test and cymbal shimmer

- [x] Verify exact uploaded WAV and retain its source hash.
- [x] Run actual original-mix and separated-input pretrained transcription.
- [x] Inspect isolated stems and original-source bands; record hat-stem body leakage without inventing labels.
- [x] Export complete 38.32 s drummer-only XSQ/MP4 and event report/CSV; verify decoded frames and original soundtrack.
- [x] Add cymbal surface shimmer/decay with short original strike poses; all 1,022 Helix musical events unchanged.
- [x] Four focused lighting regressions and the complete relevant local suite.
- [ ] Push and verify remote workflow/artifacts, including uploaded audio.
- [ ] User review of dry-test MP4; false-hi-hat behavior is unresolved and must not be called fixed.

See `DRUMMER_DRY_TEST_AND_CYMBALS.md` and `MASTER_TODO.md`.

# Current visual polish after positive #219 feedback

The user finds the transcription candidate pretty decent. Preserve its events; possible hi-hat excess remains uncertain. Current work supersedes the old raised-idle/actuator-exclusion visual behavior.

- [x] Exact previous/new event audit and analysis comparison: unchanged.
- [x] Remove resting raised arms/sticks; keep dim body and clean native background.
- [x] Complete native/preview strike overlays; alternating snare hand metadata.
- [x] Full snare shell lights behind the transparent kick.
- [x]116 tests plus61 final focused checks; decoded real-song frames, full and25s MP4 with source audio verified.
- [x] Push cd16a03; CI #220 success and uploaded report/assets/frame evidence verified.
- [ ] User approval of the updated preview; native xLights playback remains unverified.

See `docs/DRUMMER_VISUAL_POLISH.md` and `MASTER_TODO.md`.

# Drummer recovery — 2026-10-07

## Reopened after user rejection of #218 / 73bb80b

- [x] Record explicit rejection; preserve approved physical implementation.
- [x] Research independent automatic sequencing/transcription methods and limitations.
- [x] Compare pretrained multilabel transcription on identical mix and separated drums.
- [x] Inspect disputed song windows with source/stem/activation evidence.
- [x] Implement the strongest measured method with reproducible provenance.
- [x] Generate event report, isolated XSQ and actual-song comparison MP4s.
- [x] Run relevant checks, commit 474dec70, push and verify uploaded #219 artifacts.
- [ ] Obtain explicit human musical approval; remains open.

## Prior recovery candidate — rejected musically

User rejected #217. Earlier musical-acceptance claims in MASTER_TODO.md are superseded.

- [x] Verify branch starts at 3e860542; preserve approved visual assets/compositor.
- [x] Read b27e8d77 in detached worktree and reproduce historical events from identical audio.
- [x] Recover rejected #217 MP4, XSQ, and report; reproduce its 405 events locally.
- [x] Trace all 1,164 current candidates including rejection reasons and both spectra.
- [x] Inspect independent waveform, spectrogram, onset trace and band energy in five real-song windows.
- [x] Complete single-stage ablations and document history boundaries.
- [x] Port useful historical audio behavior; keep bus non-emitting and tom identity evidence-based.
- [x] Detector tests, historical comparison, independent sparse audio anchors.
- [x] Full song event JSON/CSV, drummer-only XSQ, real-song MP4, decoded-frame review.
- [x] Visual contracts and complete relevant local checks.
- [x] Prior #218 CI, commit and push completed; user rejected its musical performance.
- [ ] Human review of sparse annotations and explicit user MP4 approval.

No claim of listening: the available tools expose audio files and signal inspection, but no auditory perception tool. Sparse labels must carry their inspection provenance and remain pending human review. Synthetic precision and count agreement are not musical acceptance.

Detailed reference, artifacts, known risks and reproduction: `DRUMMER_FINAL_FIX_HANDOFF.md`. Musical acceptance remains open.
