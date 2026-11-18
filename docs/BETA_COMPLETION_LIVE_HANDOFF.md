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
