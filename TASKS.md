# Helix Agent Task Index

This is the short starting point for humans, Codex-style coding agents, and autonomous repo agents.

## First read

1. `ROADMAP_BETA_TODO.md` — canonical beta-version roadmap and autonomous TODO.
2. `docs/SUPPORT_MATRIX.md` — supported beta platforms, inputs, and boundaries.
3. `docs/BETA_POLICY.md` — data-use, safety, and asset-handling policy.
4. `AGENTS.md` — repo-wide agent rules.
5. `README.md` — active entrypoints and current repo structure.

## Current repo status

Recently completed:

- Phase 0 docs baseline exists: task index, support matrix, and beta policy.
- Phase 1 dependency/CI/bootstrap slice exists:
  - `requirements-dev.txt`
  - `.github/workflows/helix-ci.yml`
  - `scripts/bootstrap_windows.ps1`
  - `scripts/bootstrap_unix.sh`
  - `scripts/run_smoke.ps1`
  - `scripts/run_smoke.sh`

Known blocker:

- The newer targeted `Helix Beta CI` gate is green on the Phase 1 PR, but the older broad `Helix CI` full-suite pytest job is tracked separately in issue #72 and still needs exact failure triage.

## Current next recommended task

Proceed with the next beta-readiness slice from `ROADMAP_BETA_TODO.md`:

1. Add a clean-room beta demo fixture under `tests/fixtures/beta_demo/` using only synthetic/repo-safe assets.
2. Add structural smoke checks proving generated XML/XSQ output is parseable, non-empty, ordered, and free of obvious invalid serialized values.
3. Add run-manifest and no-overwrite support without changing sequencing behavior.
4. Keep this as a small PR before adding GUI beta-mode behavior.

## Agent operating checklist

Before editing:

- [ ] Work on a feature branch; do not edit `main` directly.
- [ ] Read the roadmap phase you are implementing.
- [ ] Confirm the change is the smallest useful slice.
- [ ] Do not commit private tester files, songs, layouts, templates, screenshots, or generated outputs.

Before opening a PR:

- [ ] Update roadmap checkboxes if acceptance criteria changed.
- [ ] Add or update docs when behavior changes.
- [ ] Include test output, manual reproduction steps, or a clear reason tests were not run.
- [ ] Record notable technical decisions in `docs/DECISIONS.md` when they affect future agents.

## Current beta priorities

1. Restore or triage the broad full-suite `Helix CI` failure in issue #72.
2. Clean-room smoke fixture.
3. Run manifest and no-overwrite guarantees.
4. GUI beta mode and dry-check behavior.
5. Beta README, feedback form, and issue templates.
6. Windows packaging smoke.
7. Engine facade and typed config/result containment.
8. Legacy/open-PR cleanup only after the beta path is stable.

## Non-goals for near-term agents

- Do not perform a major rewrite of `core/effect_engine.py` yet.
- Do not train on user/tester sequences or layouts.
- Do not add marketplace/model scraping.
- Do not claim production-quality unattended show deployment.
- Do not broaden support to every legacy profile until the beta path is stable.
- Do not merge stale broad branches or giant draft PRs without rebasing, splitting, and revalidating first.
