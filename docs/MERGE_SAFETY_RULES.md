# Merge Safety Rules

## Required Test Gates Before Merge

- Run `PYTHONPATH=. python -m pytest`.
- Confirm Helixia layout XML parses with `core.model_parser.parse_layout`.
- Confirm generated XML changes are intentional and reviewed.
- Confirm CI runs the same pytest gate or a documented deterministic subset.

## Branch Safety Policy

- Work only on feature branches.
- Never edit `main` directly.
- Do not merge branches as part of stabilization work.
- Keep commits small and scoped.
- Use commit messages in `type(scope): description` format.

## Stale Branch Policy

Unsafe/stale branches:

- `feature/helixville3-spotlog-birdsong`
- `beta/orchestrator`
- `codex/nextlevel`
- `codex/shader-layering-lab`
- `codex/legallearning`

These branches must not be merged without rebasing/revalidating against current stabilization state and reviewing generated artifact churn.

## Generated Artifact Handling

- Do not modify generated artifacts unless the generator or regression test requires it.
- Review generated XML diffs separately from source changes.
- Prefer temp-directory validation when checking determinism.
- Do not commit environment-specific absolute path churn.

## XML Regeneration Rules

- Regenerate XML only from the authoritative generator.
- Parser-valid XML is required before any merge.
- Byte-identical regeneration is preferred for stabilization changes.
- Any intentional XML diff must be explained in the PR.

## Backup Artifact Policy

- Do not edit generated backup XML snapshots.
- Do not delete backups during stabilization.
- Archive legacy variants instead of deleting them when cleanup is required.

## Prohibited Merges

- Branches with failing pytest.
- Branches that modify backup XML snapshots.
- Branches that introduce unseeded randomness into generated outputs.
- Branches with unexplained generated XML churn.
- Branches that redesign protected core systems during stabilization.
