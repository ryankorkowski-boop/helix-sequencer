# Helix unified beta completion — live handoff
Updated: 2026-11-17. Branch: codex/unified-beta-integration-20261117.

## Verified discovery
- Default baseline is feature/restructure-core. AGENTS.md and MASTER_TODO.md read.
- PRs #241–#248 form a stacked audit chain; #248 is based on feat/orchestration-final-xsq-reconcile-20261117, not the default branch. No automatic merge or cherry-pick is authorized without validating dependency chain.
- PR #208 layout bench exists but is not mergeable against default in current PR metadata; #217 full-song 16-panel branch targets a different base.
- Existing MASTER_TODO describes four tom zones, conflicting with owner's latest exactly-three-tom kit requirement. Preserve known-good drummer oracle b27e8d77a63027ed32bcf6851dcff3925472c155 and do not blindly rewrite.
- Native real-song xLights, Android APK, Windows EXE, and nine-panel MP4 are NOT verified by this session.

## Current work
BETA-001 baseline reconciliation: IN PROGRESS. BETA-002 engine activation and orchestrator audit: NOT STARTED. BETA-003 canonical band/drums: BLOCKED on reference comparison. BETA-004 independent lead/harmony: NOT STARTED. BETA-005 Android eight-variant/preview/export: NOT STARTED. BETA-006 Windows parity/build: NOT STARTED. BETA-007 nine-panel real-audio native video: NOT STARTED. BETA-008 acceptance evidence: NOT STARTED.

## What failed / blockers
Required status and artifact manifest files absent from baseline; initialized on this branch. Current default ledger is inconsistent with latest three-tom requirement. No CI or native render has been run in this session. Branch integration conflicts have not yet been resolved.

## Exact next actions
1. Fetch PR #241 through #248 diff and compare dependency ancestry against this branch; inspect relevant engine invocation paths and existing tests.
2. Inspect #208 layout-bench files, #217 renderer, band/drummer branches, and the latest accepted ground truth before selecting small integration patches.
3. Update the feature execution-path matrix with measured call/consumer evidence.
4. Run focused tests, record exact commands and logs; only then attempt real-song xLights native render and platform builds in a capable runner.
5. Update this handoff and both JSON manifests after every milestone.

## Must not change
No main/default branch edits, no merges/releases/uploads without owner approval. Do not overwrite approved band assets. Preserve deterministic sequencing, 256-channel AC behavior, original drummer oracle, and locked 3x3 panel order. Do not treat diagnostic sidecars as native verification.
