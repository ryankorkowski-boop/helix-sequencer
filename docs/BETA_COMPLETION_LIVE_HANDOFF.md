# Unified Beta Completion — Live Handoff

Updated: 2026-11-17 UTC. Status: IN PROGRESS; no release approval.

## Baseline
Integration branch: `integration/unified-beta-completion-20261117`, created from PR #248 head `bb41f078a92e02ccb1980785efe1c1be741a9d16`. This is a stacked audit branch, NOT the default branch. No merge or publication authorized.
Default branch: `feature/restructure-core`. Read AGENTS.md and MASTER_TODO.md before changes. Preserve accepted drummer reference `b27e8d77a63027ed32bcf6851dcff3925472c155`, but resolve legacy four-tom contract against owner's latest exactly-three-tom requirement. Do not replace canonical six snowmen with humans or introduce xylophonist/mallet cues.

## Completed this session
- Inspected repository rules and default-branch master ledger.
- Identified missing handoff/status/manifest files on default branch.
- Inspected PRs #188, #205, #208, #217, #240 and #248 metadata; #248 is stacked on #247 and has pending CI/native proof.
- Created isolated integration branch from #248 without merging any PR.

## Active task
HBC-001: reconcile branch ancestry, code and evidence. Current status IN PROGRESS. No runtime tests executed in this session.

## Priority task ledger
| ID | Workstream | Priority | Status | Blocker / evidence | Exact next action |
|---|---|---|---|---|---|
| HBC-001 | A | P0 | IN PROGRESS | Stacked PRs, no verified execution-path matrix | Compare branch ancestry and inspect actual CLI/GUI orchestration call sites |
| HBC-002 | A | P0 | NOT STARTED | Engine participation not proven | Instrument real run and compare emitted XSQ and native FSEQ |
| HBC-003 | Band | P0 | BLOCKED | Ledger lists four toms; owner requires three; visual proof pending | Compare known-good drummer source, truths references, cue schema, and nine-cue mapping |
| HBC-004 | Vocals | P0 | NOT STARTED | Independent real harmony unverified | Inspect separation and ten-phoneme output; run real dual-vocal test |
| HBC-005 | B | P0 | NOT STARTED | Android/Windows build and runtime evidence absent | Audit band-stage render, eight variants, exports, API 30 memory |
| HBC-006 | C | P0 | NOT STARTED | Real nine-panel native output absent | Validate locked layouts and real audio, then short native render |
| HBC-007 | All | P0 | NOT STARTED | Release acceptance gates outstanding | Run regression and owner review; do not publish |

## Failures / blockers
- Default branch lacks three requested persistent evidence/handoff files (created on this integration branch).
- Legacy drummer contract conflicts with current three-tom owner directive; do not silently change geometry without oracle comparison.
- PR #248 explicitly says CI and native evidence pending; do not count its instrumentation as native sequencing proof.

## Exact continuation
1. `git fetch --all --prune`
2. `git switch integration/unified-beta-completion-20261117`
3. `git status --short && git log -1 --oneline`
4. `git diff feature/restructure-core...HEAD --stat`
5. Read `AGENTS.md`, `MASTER_TODO.md`, this handoff, and both JSON manifests.
6. Inspect `core/sequence_builder.py` and real CLI/Android/Windows entry points, plus PR #248 regression tests; run targeted tests.
7. Update all four handoff files after each milestone, with branch/commit, files, test logs, failures and next command.

## Protected behavior
No main/default-branch edits, no merges/releases/uploads without owner approval. Preserve deterministic effect timing, original AC channel compatibility, owner-approved drummer visuals, locked 3x3 nine-panel order and actual native xLights validation. Never call an unrendered preview approved.

## 2026-11-17 follow-up — production routing inspection
Read actual `core/sequence_builder.py` (529 lines), `core/effects_orchestration_bridge.py` and `core/engine_activation_audit.py` from integration branch. `_orchestration_enabled` defaults true unless `--no-effects-orchestrator`; `run_effects_orchestration` invoked at lines 407-413; `_promote_orchestrated_template` at lines 142-159 only substitutes `--template` when `--promote-orchestrated-template` is explicit AND report says invoked, XSQ written and path available. Default therefore leaves orchestration sidecar-only. This is a confirmed wiring/activation condition, NOT yet proof that final sequences are unaffected: independent effect-engine behavior still requires testing. `engine_activation_audit.py` computes `promoted_to_renderer` from invocation, sidecar, and flags rather than the effective template argument; audit status should be reconciled with actual renderer input before trusting it. Do not change default promotion blindly; preserve deterministic output and legacy behavior until real-audio regression comparison. Next action: add a targeted test proving effective `--template` propagation and audit truthfulness; run the relevant pytest suite, then a native XSQ/FSEQ comparison with the same audio and layout. No tests executed or video rendered during this follow-up.

## Implementation checkpoint — 2026-11-17
Commits `ee03ead0` and `284288e0` change only promotion audit truthfulness and its focused test. Previously `promoted_to_renderer` could be true when `xsq_written=True` and the flag was set but no `orchestrated_xsq_path` existed, while `_promote_orchestrated_template` would decline promotion. The audit now requires the path to be nonempty. This does not prove file existence or renderer use. Tests NOT executed. Next action: `python -m pytest -q tests/test_engine_activation_audit.py tests/test_sequence_builder.py`; inspect and compare effective template routing in a real audio run. HBC-001 remains IN PROGRESS, HBC-002 not started. No platform/video artifacts created.

## Continuation checkpoint — explicit routing test
Added `tests/test_sequence_builder.py::SequenceBuilderTests::test_orchestration_template_requires_explicit_promotion_and_written_path` (commit `e6c2e4cb`). Confirms expected sidecar-only default, promoted template argument substitution, explicit opt-out and missing-path guard at unit-test level once executed. Current head had no reported GitHub PR-triggered workflow runs or combined commit statuses at time of check. This is NOT a passed test or native render. Run `python -m pytest -q tests/test_sequence_builder.py tests/test_engine_activation_audit.py` in a checkout and compare actual exported XSQ/FSEQ. Do not promote by default until evidence shows no deterministic regressions.

## Input-template prerequisite discovery
Inspected `core/effects_orchestrator_bridge.py` lines 231-260. `_write_orchestrated_xsq` refuses to write a sidecar if no `--template` argument or template file is missing. This is a second gating condition before explicit promotion in `sequence_builder.py`. Next investigation must identify actual app/CLI argument construction for `--template` and whether a generated XSQ can be used as an orchestration input without circularity. No production change made; no tests/native rendering run. Maintain HBC-001 IN PROGRESS. Prior added regression test is unexecuted.

## Launcher investigation and config parity checkpoint
Source audit found Android `helix_mobile.build_args` unconditionally includes `--no-effects-orchestrator` while supplying `--template`, `--audio`, and `--layout-file`. This is a confirmed Android choreography integration opt-out; do not remove without memory/performance proof. Windows portable entry delegates to sequence_builder. Existing `tests/test_sequence_builder_orchestrator_promotion.py` covers fake-engine routing. `core/run_config_v2.RunConfig` default promotion True conflicted with actual serialization (no positive flag); corrected default False (commit `00aa7364`) and explicit True serialization (commit `34876e7e`), added tests (commit `54143fb7`). These are unexecuted. Next: run `python -m pytest -q tests/test_run_config_v2_orchestration.py tests/test_sequence_builder_orchestrator_promotion.py tests/test_engine_activation_audit.py tests/test_sequence_builder.py`; review Android resource budget and compare with opt-in on desktop. HBC-001 in progress; no verified native exports or app builds.

## Ground-truth discovery and CI execution checkpoint — 2026-11-17
Branch-scoped `.github/workflows/helix-unified-beta-integration.yml` added at commit `214d8d5` because pre-existing `unit-tests.yml` and `helix-ci.yml` push branches exclude `integration/**`. GitHub run `44213308493` (https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/44213308493) started Python 3.11/3.12 focused regressions and was IN PROGRESS at inspection; **do not count as passing** until completion. The source audio and owner reference files were located via the connected Google Drive: Truths folder `1SUtLHdk1nncBrQssmBpYHUeE327Q1VJj`, containing `Aaadrummertruth.mp4` id `1qDjj8JJ3Z-rZfFUntidsnPkq5DRqOsMm`, `Aaadrummergroundtruth.mp4` id `1cPHct6XEhZM_-9x9lkCP-7tN_DfIKo7b`, `Bbb Vocalstruth.mp4` id `1FN29mXUxy5dDJ0VIn6Wy7K-4llFHzGAs`, `Bbb vocals.mp4` id `1PPPz4TbYIS0Z9D6zRHScfnQoom38ltxX`; Songs with Lyrics `1JqYbCEn0rywNJhigYEywCEtscxn6kXFc`, `Tinsel Tornado.mp3` id `1Z_WvwVcp2tOytfF63SVgJf1VUCkRpfD4`, `Phoneme Test Hook.mp3` id `1gKAW9-S6TJNuKudC_TCEv2uabx36Aszj`. Files found, not yet independently decoded/visually verified. No raw Drive audio/video copied to GitHub, no app artifacts or MP4 created. Next: inspect run 44213308493 job conclusions/logs; fix failures and rerun if necessary; visually inspect ground truth and compare before drum changes.
