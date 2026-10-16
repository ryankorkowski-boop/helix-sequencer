# Subsystem Maturity Matrix

## Level Definitions

### Prototype
- Proof-of-concept or research code
- Limited or no automated tests
- Not used on the production sequencing path
- Examples: `ai/`, most `helixville*`, experimental composers

### Beta
- Feature-complete for stated scope
- Meaningful unit / contract test coverage
- Manual or oracle validation on representative inputs
- Known limitations documented
- Examples: `core/` (overall), drum classification path, run management

### Production
- Stable, actively used in real workflows
- Strong automated regression baseline preferred
- Backward-compatible changes expected
- Examples: `xlights/` writers, `tools/`, core run-manifest / config plumbing

## Current Snapshot (2026-10)

| Area | Maturity | Notes |
|------|----------|-------|
| `core/sequence_builder.py` + RunConfig/RunManager | Beta | Stable orchestration surface |
| `core/effect_engine.py` | Beta | Monolithic; facade planned after beta-safety gates |
| Drum / band detection path | Beta | Nine-component contract; real-song oracle still required |
| `xlights/` | Production | XSQ emission validated |
| `tools/` | Production | Utilities |
| `ai/` | Prototype | Stubs only |
| `legacy_ac/` | Beta (isolated) | Do not cross-import |
| `helixville*`, research trees | Prototype | Research / demo only |
| Packaging (PyInstaller) | Beta | Windows portable path under active work |

## Graduation Rules

- Prototype → Beta: tests + documented limitations + decision to keep
- Beta → Production: real-song / real-layout validation + automated regression baseline + no known show-stoppers

Update this matrix when a subsystem changes maturity level.
