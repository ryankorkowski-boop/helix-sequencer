# Beta 1.4 — autonomous output-quality repair handoff
Updated: 2026-11-21. Integration branch: `integration/unified-beta-completion-20261117`.
This file is a running checklist, not a claim of product completion. No merge or release authorized.

## Acceptance gates
- [x] Existing classified drum mapper inspected: nine physical targets, snare-hand and crash-side logic already exist.
- [x] Existing vocal adapter and synthetic XSQ emitter inspected; seven canonical phonemes currently supported, not ten.
- [x] Existing production handoff and owner rejections reviewed; previous approval videos remain FAIL.
- [ ] Verify latest integration SHA with Python 3.11/3.12 focused and full CI; record actual run IDs.
- [ ] Integrate **actual** drum events and canonical drummer geometry in native xLights model and FSEQ; independently check all nine targets.
- [ ] Ensure singing-face mappings correspond to real xLights face definitions/submodels (not merely synthetic XML metadata).
- [ ] Verify independently qualified lead/harmony stems; reject mixed vocal bus as proof of independent singers.
- [ ] Native short real-audio pilot: validate editable XSQ, layout XML, native FSEQ, frames, source-clock sync, contrast and motion diversity.
- [ ] Only then render full-song 16-panel, 12-layout and six-snowman band MP4s; decode and request owner approval.
- [ ] Android eight-variant on-device/API30 acceptance, Windows EXE runtime, manuals and release gate.

## Output optimization queue (ordered by expected impact)
1. [ ] Make orchestration's final intent placements drive production XSQ rather than a shadow-only report. Compare generated effects against actual native channel activity.
2. [ ] Add objective FSEQ frame quality metrics: white dominance, saturation, dead panels, simultaneous activation and repeated patterns; fail closed for gross regressions. Calibrate thresholds against actual owner-approved examples.
3. [ ] Enforce prop-role/section contrast and rest budgets while retaining original AC channel/color mapping.
4. [ ] Reuse SHA-bound audio/stem/section plans; invalidate only changed layout/panel native renders.
5. [ ] Repair synthetic test contracts and exercise native exports in CI. Keep diagnostics separate from approval media.

## 2026-11-21 implementation checkpoint
- [x] Added bounded RGB sample evaluator (core/native_rgb_quality.py), commit 6cd8d4e; no full-resolution frame retention.
- [x] Added white/blank/frozen/vivid regression tests (tests/test_native_rgb_quality.py), commit 35d492a.
- [x] Added CLI to decode sampled frames from actual MP4 and write a JSON receipt (tools/check_mp4_visual_quality.py), commit 48e1601.
- [x] Add dedicated Python 3.11/3.12 output-quality regression workflow, commit 204d693; trigger is configured, execution not yet confirmed.
- [ ] Inspect CI run result for latest integration SHA; repair failures before claiming pass.
- [ ] Wire CLI into native approval workflows; no production acceptance pass is claimed yet.
- [ ] Calibrate thresholds against actual owner-approved visuals; bright white intentional scenes may otherwise be flagged.
- [ ] Repair any tests that fail after latest phoneme/drum commits.

Example after native MP4 exists: `python -m tools.check_mp4_visual_quality path/to/native.mp4 --report path/to/visual_quality.json` (exit 2 on rejected output).


## Evidence known before this handoff
- MASTER_TODO reports 55 focused local Python 3.12 regressions passing on an earlier checkpoint; this does not verify the most recent commits.
- Nov 21 source reports a real 34.88s Phoneme Test Hook with four checked stems; mixed E14 vocals do not qualify as separate lead/harmony.
- Prior bounded Infinity native FSEQ technically succeeded, but owner visual approval is absent.
- Latest recent commits: face adapter 275e8405, tests 842b4a99, XSQ emitter 16d4c75, test 6d19f71, drum preview ef50d4e1, test 50f80cd, vocal compiler f5720c1, test c887060.
- The earlier visual failures remain rejected. No fresh native owner-approved MP4 exists in the evidence reviewed.

## Resume instructions
Read this checklist, MASTER_TODO.md, docs/BETA_COMPLETION_LIVE_HANDOFF.md and evidence/beta_completion/latest_status.json. Inspect current branch HEAD, run focused tests, fix any failing tests, then follow the P0 native visual gate. Update this file after each verified milestone. Never mark an artifact approved without explicit owner review.
