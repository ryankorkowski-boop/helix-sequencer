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

## Additional PR inspection (2026-11-17)
- #235 identifies a production promotion contract mismatch: RunConfig's promotion default did not emit sequence_builder's required flag. Its patch defaults promotion off and requires explicit opt-in. Must test before integration.
- #241 activation audit is stacked on feature/music-section-recurrence-20261116, not directly on default. It reports flags separately from verified engine output.
- #245 explicitly records synthetic section seed provenance and sidecar counts without claiming native render proof.
- #248 includes unrelated Demucs checkpoint workflow changes in its PR diff; do not blindly cherry-pick whole diff. Review per-file ancestry and isolate audit changes.
- #188 diff is exceptionally large (~12 MB) and #205 is based on its branch. Avoid wholesale integration; select tested narrow modules.
- No tests or rendering were executed by this connector session. Exact next action: inspect #235 focused test and implementation files and decide whether to cherry-pick its small isolated contract repair after running tests on an available checkout.

## Session continuation — 2026-11-17
- Created `docs/BETA_ENGINE_EXECUTION_MATRIX.md` at commit `fc65639c517fe4b9dd2b30db6463f3e33663cf81` on the existing unified integration branch. Reused existing handoff rather than creating a competing branch.
- Inspected actual patches: #235 changes `RunConfig.promote_orchestrated_template` default to false and emits explicit promotion flag when enabled; #230 preserves independent same-onset tom events using physical target keys; #248 rejects stale orchestration sidecars in XSQ reconciliation. None is verified as integrated on this branch.
- Next action: inspect integration branch `core/run_spine.py`, compare PR #235, selectively apply the contract fix with tests; inspect #230 three-tom tests before changing geometry. Then trace end-to-end changed XSQ and native FSEQ.
- No test, render, APK, EXE or nine-panel MP4 was produced in this continuation. All corresponding acceptance gates remain open.
