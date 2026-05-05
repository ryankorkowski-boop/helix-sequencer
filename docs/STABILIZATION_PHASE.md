# Stabilization Phase

## Current Repo Phase

- Helix Sequencer is in stabilization and production-validation mode.
- The current goal is to prove deterministic, parser-valid, regression-protected behavior before merge or release.
- New capability work is secondary to validation, merge safety, and reproducibility.

## Priorities

- Keep the full local gate green: `PYTHONPATH=. python -m pytest`.
- Preserve deterministic generated sequence, report, and XML behavior.
- Validate existing systems before extending them.
- Prefer small, isolated, testable changes.
- Document factual implementation state over roadmap intent.

## Forbidden Work

- Broad refactors.
- Experimental feature expansion.
- Architecture redesign.
- Unseeded randomness in production outputs.
- Filesystem-order-dependent output.
- Generated artifact churn without a validation reason.
- Editing backup XML snapshots.

## Acceptable Work

- Regression tests for existing behavior.
- CI alignment with validated local commands.
- Determinism fixes such as sorted iteration or fixed seeds.
- Parser-validity checks for generated XML.
- Documentation that records current verified state.
- Small production-validation tools that compose existing systems.

## Deterministic Output Expectations

- Identical inputs must produce identical XML, XSQ, reports, and summaries unless a documented seed changes.
- Iteration over files, models, groups, and generated reports must be explicitly ordered.
- Randomized behavior must use stable local `random.Random(...)` instances.
- Snapshot comparisons should ignore environment-specific absolute paths only when documented.

## Validation-First Philosophy

- Validate parser correctness before claiming xLights compatibility.
- Validate generated structure before judging creative quality.
- Validate quality and scoring reports before using them for merge decisions.
- Prefer rule-based checks before AI-assisted review.

## Protected Core Modules

- `core/effect_engine.py`
- scoring systems
- XML generators
- source-policy enforcement

Changes to protected modules require a failing deterministic test, a focused fix, and a full validation rerun.
