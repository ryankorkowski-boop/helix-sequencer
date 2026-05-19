# Helix Agent Task Index

This is the short starting point for humans, Codex-style coding agents, and autonomous repo agents.

## First read

1. `ROADMAP_BETA_TODO.md` — canonical beta-version roadmap and autonomous TODO.
2. `docs/SUPPORT_MATRIX.md` — supported beta platforms, inputs, and boundaries.
3. `docs/BETA_POLICY.md` — data-use, safety, and asset-handling policy.
4. `AGENTS.md` — repo-wide agent rules.
5. `README.md` — active entrypoints and current repo structure.

## Current status

Phase 1 dependency, CI, bootstrap, and smoke-script normalization is complete enough for beta follow-up work. The required smoke path is now centralized through `scripts/ci/run_required_checks.py`, with Unix and PowerShell smoke wrappers delegating to it.

## Current next recommended task

Proceed with Phase 2/contract hardening before adding more creative sequencing behavior:

1. Strengthen the canonical xLights output contract with focused tests.
2. Add small golden or structural fixtures for importability invariants.
3. Keep generated outputs out of git unless they are tiny, intentional fixtures.
4. Then continue GUI beta hardening and run-manifest/no-overwrite behavior.

## Agent operating checklist

Before editing:

- [ ] Work on a feature branch; do not edit `main` directly.
- [ ] Read the roadmap phase you are implementing.
- [ ] Run `python scripts/ci/run_required_checks.py` or the platform smoke wrapper.
- [ ] Confirm the change is the smallest useful slice.
- [ ] Do not commit private tester files, songs, layouts, templates, screenshots, or generated outputs.

Before opening a PR:

- [ ] Update roadmap checkboxes if acceptance criteria changed.
- [ ] Add or update docs when behavior changes.
- [ ] Include test output, manual reproduction steps, or a clear reason tests were not run.
- [ ] Record notable technical decisions in `docs/DECISIONS.md` when they affect future agents.

## Current beta priorities

1. Canonical xLights contract hardening.
2. Clean-room smoke fixture and structural importability checks.
3. Run manifest and no-overwrite guarantees.
4. GUI beta mode and dry-check behavior.
5. Beta README, feedback form, and issue templates.
6. Windows packaging smoke.
7. Engine facade and typed config/result containment.

## Non-goals for near-term agents

- Do not perform a major rewrite of `core/effect_engine.py` yet.
- Do not train on user/tester sequences or layouts.
- Do not add marketplace/model scraping.
- Do not claim production-quality unattended show deployment.
- Do not broaden support to every legacy profile until the beta path is stable.
