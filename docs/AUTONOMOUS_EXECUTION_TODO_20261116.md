# Helix autonomous execution checklist — 2026-11-16

**Scope:** Draft PR #232, branch `codex/arbitration-ci-repair-20261116`. No merges, public release, or owner approval implied.
**Evidence:** https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/43880078404

## Completed and evidence-backed
- [x] Read AGENTS.md and MASTER_TODO.md before changing implementation.
- [x] Repair escaped newline in orchestration bridge (Python compile failure).
- [x] Repair Flow exporter invocation from repository root.
- [x] Replace dictionary comparison during tied remote-preview candidate ranking with explicit deterministic key.
- [x] Repair optional `composite_submodels` lookup in snowman drum cue planning without inventing targets.
- [x] Add regression tests for legacy and empty drum marks.
- [x] Include those tests in Python 3.11/3.12 beta smoke CI (execution pending after this commit).
- [x] Verify CI, Beta CI, Birdsong, Flow Quality, Flow Review, Compliance and Remote MP4 workflow success on previous head `6b9cd925`.
- [x] Confirm remote workflow produced downloadable artifact `helix-remote-review-preview-mp4` (artifact ID 14231739526; 5,493,838 bytes) with `REMOTE_REVIEW_v28.9_LightsOutTheme.first_20s,v28.9.mp4`.
- [x] Inspect successful remote workflow logs; no `Snowman band planning skipped` warning detected.
- [x] Verify latest head `aa544018` passed Helix CI, Beta CI, Birdsong CI, Flow Quality, Flow Review, Compliance, and remote MP4 preview workflows.

## Active verification
- [x] Verify Python 3.11 and 3.12 beta smoke CI on head `aa544018`, including new band tests: 162 passed each; workflow 43882085814.
- [ ] Download and visually inspect the MP4 for native xLights compatibility, correct six-member snowman geometry, drummer kit lighting, realistic limbs and independent vocal timing. A passing workflow is not visual acceptance.
- [ ] Inspect rendered MP4 metadata, frame decode, audio sync, blank frames and brightness, then compare to owner Truths examples. GitHub workflow artifact exists but its binary frames have not been visually inspected.

## Next implementation (separate focused changes)
- [ ] Trace missing drum lighting, exactly three toms, independent cymbals and anatomical drummer motion against owner Truths.
- [ ] Reconcile band asset schema and missing snowman models on Android and Windows; test eight variants, per-variant playback, export, persistence and memory limits.
- [ ] Validate independently sourced lead and harmony vocals with phoneme/word timing; reject false harmony detections and silence animation.
- [ ] Integrate non-destructive engine arbitration with musical transitions, chases, piano routes and Birdsong spatial effects, with baseline XSQ comparisons.
- [ ] Render native xLights nine-panel comparison with band center, and obtain explicit owner acceptance before any release/merge.

## Handoff rules
Use MASTER_TODO.md as canonical ledger. Every change records goal, files, preserved/new behavior, evidence, limitations, deferred work and regression risk. Work on feature branches. Do not merge PR #188 or publish beta without owner approval.
