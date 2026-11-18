# Helix production execution-path reconciliation (evidence-limited)
Updated 2026-11-17. Integration branch: codex/unified-beta-integration-20261117.

| Feature | Observed entry / candidate path | Downstream evidence | Android | Windows | Native xLights | Status / next verification |
|---|---|---|---|---|---|---|
| Orchestrator promotion | `core/run_spine.py` RunConfig.to_engine_args; PR #235 adds explicit `--promote-orchestrated-template` opt-in | PR #248 reconciles changed XSQ candidates with sidecar tags | Unverified | Unverified | Changed XSQ tags are not FSEQ proof | IN PROGRESS: test promotion flag contract and compare final XSQ effects |
| Engine activation audit | PRs #241–#248; `core/orchestration_xsq_reconciliation.py` | PR #248 rejects stale sidecars and distinguishes changed XSQ candidates | Unverified | Unverified | Unverified | IN PROGRESS: inspect stacked ancestry, exercise real run |
| Three-tom event scheduling | `mapping/drum_mapper.py`, PR #230 `schedule_drum_events` | Physical target key preserves independent simultaneous tom hits | Unverified | Unverified | Unverified | IN PROGRESS: test three toms and compare b27e8d77 oracle |
| Eight-variant review | PR #231 Android MainActivity/PreviewActivity/EngineService; desktop gui_launcher.py | PR includes tests/test_variant_review_media.py | Unverified | Unverified | Unverified | NOT STARTED: inspect implementation and execute device tests |
| GUI progress | PR #233 | No session build or visual evidence | Unverified | Unverified | N/A | NOT STARTED |
| Nine-panel layout bench | PR #208 `tools/layout_bench` | Reported synthetic layout generation; not nine-panel real-song approval | N/A | N/A | Unverified in this session | NOT STARTED: map nine locked panels and validate native render |
| Independent vocal streams | PR #214 and other branches, untraced | No independent harmony real-audio evidence in session | Unverified | Unverified | Unverified | NOT STARTED |

## Important integration constraints
- Existing default ledger documents four toms; owner's current requirement is exactly three. Nine cues must be reconciled with the actual physical kit, including ride and left/right crashes; do not equate nine legacy composites with nine approved cues.
- PR #235 is a narrow flag-contract candidate, not yet merged or tested here. Promotion must remain opt-in until verified against production behavior.
- PR #248 is stacked and includes unrelated workflow changes. Do not wholesale cherry-pick.
- This is a source/PR patch inspection matrix, **not** a dynamic execution proof. All platform and native output cells remain unverified.

## Exact next commands on a capable checkout
`git fetch origin --prune`
`git switch codex/unified-beta-integration-20261117`
`git status --short`
`git diff origin/feature/restructure-core...HEAD --stat`
`python -m pytest -q tests/test_orchestrator_promotion_contract.py tests/test_three_tom_truth_integration.py tests/test_orchestration_xsq_reconciliation.py` (only after relevant PR test files are selectively integrated; do not imply these tests already exist on the integration branch).
