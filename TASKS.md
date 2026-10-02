# Helix Agent Task Index

> Start here: ROADMAP_BETA_TODO.md is the canonical beta-readiness roadmap for the current phase.

## First read

1. ROADMAP_BETA_TODO.md — active beta roadmap, phase order, acceptance criteria, and PR slicing.
2. AGENTS.md — mandatory operating rules for this repo.
3. MASTER_TODO.md — canonical project ledger for active technical work and cross-agent continuity.
4. README.md / README_CURRENT.md — active entrypoints and current repo structure.

## Working contract

- Keep changes small and scoped to one phase or milestone at a time.
- Work in the order specified by ROADMAP_BETA_TODO.md unless a blocker is explicitly documented.
- Preserve existing behavior unless the current task is a repo-safety or beta-harness change.
- Update MASTER_TODO.md in the same change set whenever any engineering, docs, workflow, or product-facing work changes.
- Never commit private tester layouts, templates, songs, screenshots, or generated files without explicit written permission in repo docs.

## Current next recommended task

Follow the roadmap's Immediate first tasks in order:

1. Confirm TASKS.md points to the beta roadmap and current next task.
2. Confirm docs/SUPPORT_MATRIX.md is current and linked from README.
3. Confirm docs/BETA_POLICY.md is current and linked from README and beta guidance.
4. Keep dependency policy and CI aligned with requirements-dev.txt.
5. Keep smoke fixture and validation scripts repo-safe.
6. Add/keep run manifest support without changing sequencing output.
7. Add/keep GUI beta mode and dry-check behavior.
8. Add/keep beta README and feedback form templates.
9. Add/keep Windows packaging smoke validation.
10. Only after those gates, begin engine facade/extraction work.

## Recovery / evidence

Do not treat a task as fully closed until the applicable evidence exists:

- [ ] CI status or a documented reason dry-run testing was not possible
- [ ] targeted/full tests for the changed behavior
- [ ] generated artifact path or reproduction steps
- [ ] run manifest/log evidence when relevant
- [ ] explicit note of remaining known gaps

## Non-goals for near-term agents

- Do not perform a major rewrite of core/effect_engine.py without a documented migration plan.
- Do not train on user/tester sequences or layouts.
- Do not add marketplace/model scraping.
- Do not claim production-quality unattended show deployment.
- Do not broaden legacy-profile support until the beta path is stable.
