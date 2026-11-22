# Beta 1.4 — autonomous output-quality repair handoff
Updated: 2026-11-21. Integration branch: `integration/unified-beta-completion-20261117`.
This file is a running checklist, not a claim of product completion. No merge or release authorized.

## Acceptance gates
- [x] Existing classified drum mapper inspected: nine physical targets, snare-hand and crash-side logic already exist.
- [x] Existing vocal adapter and synthetic XSQ emitter inspected; seven canonical phonemes currently supported, not ten.
- [x] Existing production handoff and owner rejections reviewed; previous approval videos remain FAIL.
- [ ] Verify latest integration SHA with Python 3.11/3.12 **full** CI; focused regressions already PASSED on integration commit 48e1601 (run 44964385167), full suites still running.
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
- [x] Add end-to-end MP4 encode/decode/receipt CI smoke, commit c66ad512; verifies real H.264 frames rather than just Python syntax.
- [x] Dedicated output-quality regression CI PASSED for Python 3.11 and 3.12, including decoded MP4 smoke: run 44964518308 (commit c66ad512).
- [ ] Inspect full-suite integration CI results (run 44964385167); repair any failures.
- [x] Wire decoded MP4 quality receipt into real Helix Motion 16-panel native pilot workflow (commit 4c43604a); run 44964923524 pending, receipt not yet produced.
- [ ] Extend receipt coverage to all native approval workflows and calibrate thresholds.
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


## 2026-11-21 · Real owner Drive audio execution checkpoint
- [x] Verified Google Drive original `Helix Motion.mp3` (file ID `12gRu8SUf-8GVCQdJnrIROnTY6XumOUzZ`), MIME audio/mpeg, owner-readable; native workflow has a pinned original SHA256.
- [x] Verified new `The Test Is On.mp3` (file ID `18zI7nKAQ0JHG-cPMppPJWeNP_Qo3aXce`; 30s) and `Rhythmic Awe.mp3` (file ID `11J89FUSbbH1QuP_joaTlgKdFVUdqRuqH`; 253.44s) in Google Drive, matching existing repository source manifest identities pending exact in-run hash checks.
- [x] Triggered original-drive-audio Helix Motion 16-panel native pilot by updating its workflow to collect decoded MP4 quality receipt, commit `4c43604a`; Actions run [44964923524](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/44964923524) was PENDING at first check. No success/MP4 claimed.
- [x] Triggered Rhythmic Awe full-song Demucs qualification workflow with explicit stereo 48kHz and source-clock preflight, commit `3ecf9579`; Actions run [44964935413](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/44964935413) was QUEUED at first check. No independent vocal pair claimed.
- [x] Verified new output-quality CI smoke including real MP4 encode/decode PASSED: [44964518308](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/44964518308) (commit `c66ad512`).
- [ ] Inspect both current Actions runs, download actual artifacts after completion, verify source SHA, native XSQ/FSEQ, audio sync, frame quality, and output decoding; provide real playable MP4 only if produced.
- [ ] If either run fails, use the logs to make a targeted repair and launch another run. Preserve diagnostic distinction, do not count failed or queued jobs as completed videos.

## 2026-11-22 · Live execution update
- [x] Confirmed native-proof job PASS in [44964385102](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/44964385102); accepted-native-band job still awaiting successful producer, not an acceptance pass.
- [x] Confirmed Python 3.11/3.12 focused regression jobs PASS in [44964385167](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/44964385167); full suites remain in progress.
- [x] Confirmed original Rhythmic Awe file fetched, SHA verified, MP3 duration/stereo format validated, Demucs syntax check passed in [44964935413](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/44964935413); Demucs separation running, four-stem receipt pending.
- [ ] Helix Motion 16-panel native [44964923524](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/44964923524) remains PENDING with no allocated job. Do not assert rendering has started.
- [ ] Once completed, inspect jobs and retrieve genuine MP4/FSEQ/XSQ artifacts. In-progress job logs currently unavailable from GitHub API; wait for job completion before using logs for targeted repair.

## 2026-11-22 · Source logic to native render repair
- [x] Added `tools/verify_render_logic_provenance.py` (0c09a3f) to parse authoritative panel XSQ and reject absent effects, missing mapped instrument provenance, and missing detected drum provenance. Source SHA and analysis SHA retained in receipt. This is an XSQ input gate, **not** native FSEQ proof.
- [x] Wired provenance verifier into every `render_panel()` call before xLights invocation (d7a8cbf), emitting `RENDER_LOGIC_PROVENANCE.json` per panel.
- [x] Added tests for present/missing source-tagged musician effects and missing drum source tags (fb3d486), wired into Python 3.11/3.12 output quality CI (c4b9054); [run 44965389808](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/44965389808) queued on first check, pass not claimed.
- [x] [Rhythmic Awe Demucs source qualification run 44964935413](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/44964935413) completed SUCCESS with 111,308,994-byte stems artifact `owner-rhythmic-awe-demucs-stems-3ecf957946710f4edea89d1d7ce539f24fca1bf0`. This confirms workflow completion, not independent lead/harmony vocal identity.
- [ ] Inspect [Helix Motion native 16-panel run 44964923524](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/44964923524) and superseding run 44965365205; the first was in progress, the second pending. Do not confuse earlier run with new provenance gate.
- [ ] Validate source effect *coverage*, not only existence: compare cue counts and timings per drum/instrument to XSQ and then verify FSEQ activity per model, using native renderer receipts. Reject silent or disconnected effects.
- [ ] Wire this evidence to six-snowman and 12-layout native producers; preserve AC 16/64/256 behavior and don't silently promote orchestrator sidecars as native effects.

## 2026-11-22 · One universal music pipeline, arbitrary panel count
- [x] Confirmed `tools/render_full_song_comparison.prepare` already calls `tools.build_current_comparison.build` with `models.full_song_layouts.build`; 16 panels share the 9/12 layout source-plan and native XSQ emitter, not a separate sequencing algorithm.
- [x] Moved source-event-to-authoritative-XSQ verification into the common `tools.build_current_comparison.build` loop (commit be42dfb). Every layout now emits `RENDER_LOGIC_PROVENANCE.json` and fails on missing instrument/drum provenance, regardless of batch count. The 16-panel render additionally rechecks on resumed native panel jobs.
- [x] Added regression guarding shared builder invocation and shared verification gate (d9000ae); [output-quality CI 44965603728](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/44965603728) queued at first check. Previous provenance-gate CI [44965389808](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/44965389808) PASSED.
- [ ] Important: do not equate one source-tagged effect with *all* logic reaching render. Build per-role cue counts/timestamps/target coverage, confirm source-driven vocal modes, and measure native FSEQ model activity.
- [ ] Keep HPSS, Demucs, beat/chord/section, orchestration, instrument and vocal logic independent of panel count; allow AC/RGB capability-specific effect mapping only. Never force band geometry onto non-band layouts.
- [ ] Verify 9/12/16 all use same music-plan SHA for identical source audio, and prove native FSEQ carries those event lanes before owner acceptance.

## 2026-11-22 · Per-component source coverage
- [x] Shared 9/12/16 pipeline output-quality CI [44965603728](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/44965603728) PASSED for Python 3.11 and 3.12.
- [x] Upgraded shared XSQ provenance gate to check source-tagged effect counts separately for every instrument model and every detected drummer component, not only the presence of one tagged effect (fd6d533).
- [x] Added partial-loss regression: two mapped musician cues with only one native source effect must fail (f89b1ab).
- [ ] Confirm updated CI [44965743388](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/44965743388) passes; subsequent test commit may supersede the run.
- [ ] Extend proof to exact event timestamps and qualified vocal clocks, then independently inspect xLights FSEQ channels and actual decoded MP4; source XSQ event counts alone are not full render verification.

## 2026-11-22 · Regression failure repair
- [x] Investigated failed Python 3.11/3.12 quality runs 44965750104 and 44965743388 using job logs. Failure: new fixture placed musician source effect on parent `GUITAR`, while real production writes submodel `GUITAR/STRING_0`; 3 regression assertions failed, 15 passed.
- [x] Corrected fixture to use actual native submodel effect lane, commit 95f81fa; [rerun 44965816121](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/44965816121) queued. No pass claimed yet.
- [ ] Verify current CI and then perform real XSQ/FSEQ provenance comparison on owner audio; never count a fixture pass as proof of actual native pixels.

## 2026-11-22 · Native XSQ source clock retention
- [x] Confirmed repaired shared-pipeline source-coverage regression run [44965816121](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/44965816121) SUCCESS for Python 3.11 and 3.12.
- [x] Added source clock validation for every tagged native musician/drum effect: required sourceStartMs, nonnegative onset, onset within declared sequence duration when available, and valid sourceEndMs where present (ca63e77). Musical note duration and shortened gesture duration remain separate by design.
- [x] Added regression for invalid source onset, plus source clock fields in test fixtures (2e90652). Await new CI; no claim of success until completed.
- [ ] Native Helix Motion pilot [44964923524](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/44964923524) in progress, currently building authentic patched xLights; no approval MP4 artifact at last check. Superseding provenance-gated pilot 44965365205 pending.
- [ ] Next: check native FSEQ activity per prop and effect clock, compare decoded MP4 to musical activity, ensure 9/12/16 native parity.
