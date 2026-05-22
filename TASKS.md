# Helix Agent Task Index

This is the short starting point for humans, Codex-style coding agents, and autonomous repo agents.

## Recovery: verify before closing

Before treating a recently closed implementation or validation issue as complete, record:

- [ ] CI status.
- [ ] Full and targeted test status.
- [ ] Generated XSQ artifacts.
- [ ] MP4 artifacts.
- [ ] xLights import evidence.
- [ ] Manual validation evidence.
- [ ] Remaining known gaps.

## First read

1. `ROADMAP_BETA_TODO.md` — canonical beta-version roadmap and autonomous TODO.
2. `docs/SUPPORT_MATRIX.md` — supported beta platforms, inputs, and boundaries.
3. `docs/BETA_POLICY.md` — data-use, safety, and asset-handling policy.
4. `AGENTS.md` — repo-wide agent rules.
5. `README.md` — active entrypoints and current repo structure.

## Current next recommended task

Proceed with Phase 1 from `ROADMAP_BETA_TODO.md`:

1. Add `requirements-dev.txt`.
2. Update CI to install from declared requirements only.
3. Add compile/test/profile-list smoke checks.
4. Keep this as a small PR before adding GUI behavior changes.

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

1. Documentation and policy baseline.
2. Reproducible dependency/CI setup.
3. Clean-room smoke fixture.
4. Run manifest and no-overwrite guarantees.
5. GUI beta mode and dry-check behavior.
6. Beta README, feedback form, and issue templates.
7. Windows packaging smoke.
8. Engine facade and typed config/result containment.

## Non-goals for near-term agents

- Do not perform a major rewrite of `core/effect_engine.py` yet.
- Do not train on user/tester sequences or layouts.
- Do not add marketplace/model scraping.
- Do not claim production-quality unattended show deployment.
- Do not broaden support to every legacy profile until the beta path is stable.
