# Determinism And Regression

## Stable Ordering Requirements

- Sort filesystem reads before selecting, copying, reporting, or deleting generated outputs.
- Sort model, group, family, and report iteration when output order is user-visible.
- Preserve XML element ordering from authoritative generators.
- Prefer explicit order lists over dictionary or set iteration for generated outputs.

## Seeded Randomness Policy

- Use local `random.Random(seed)` instances.
- Never use module-level random state for production outputs.
- Derive seeds from stable constants and normalized input names.
- Record seed changes when they affect generated artifacts.

## Filesystem-Order Protections

- Do not depend on `glob`, `rglob`, `iterdir`, or `listdir` natural order.
- Sort by stable path fields when selecting generated files.
- Avoid modification-time selection unless the command intentionally asks for newest output.
- Clean temp work directories before deterministic generation.

## Snapshot Guidance

- Snapshot parser counts and structural summaries before snapshotting full XML.
- Avoid snapshots that include machine-specific absolute paths.
- Do not update snapshots to hide nondeterminism.
- Generated backup XML snapshots are protected and should not be edited.

## Regression Philosophy

- Add small tests around observed risks.
- Validate behavior before changing protected core modules.
- Prefer regression tests that use temp directories.
- Keep production-validation tests deterministic and fast enough for CI.

## Deterministic XML Expectations

- Same generator inputs should produce byte-identical XML.
- Attribute values must be stable.
- Model and group ordering must be stable.
- Parser-valid XML is required but not sufficient for production-ready status.

## CI Expectations

- CI should run `PYTHONPATH=. python -m pytest` when practical.
- If a full gate is too expensive, CI must run a documented deterministic staged pytest strategy.
- CI must not silently skip missing tests.
- CI failures block merge during stabilization.
