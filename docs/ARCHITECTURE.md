# Helix Architecture Map

> Living map of production vs experimental subsystems.
> Keep this file updated when ownership or maturity changes.

## Core Production Subsystems

### `core/`
- **Owner**: @ryankorkowski-boop
- **Status**: active development
- **Maturity**: Beta (proven on internal tests; real-song validation ongoing)
- **Key modules**:
  - `sequence_builder.py` — orchestration entry point
  - `effect_engine.py` — main sequencing logic (monolithic; facade planned)
  - `audio_intelligence.py`, `rhythm_intelligence.py`, `snowman_band.py`, etc.
  - `lazy_imports.py` — optional / deferred imports

### `xlights/`
- **Owner**: @ryankorkowski-boop
- **Status**: stable
- **Maturity**: Production (XSQ structure validated against xLights 2023/2024)
- **Key modules**: XSQ writer, effect catalog, contract validators

### `tools/`
- **Owner**: @ryankorkowski-boop
- **Status**: stable
- **Maturity**: Production
- Shared utilities, preview helpers, file I/O

### `tests/`
- **Owner**: @ryankorkowski-boop
- **Status**: active
- **Maturity**: Beta → Production (expanding regression coverage)

## Experimental / Isolated

### `ai/`
- **Maturity**: Prototype (stubs only, no active production path)

### `legacy_ac/`
- **Maturity**: Beta (isolated research; do not import into core)

### `helixville*`, `helix_*` research trees, `animation/`, etc.
- **Maturity**: Prototype / experimental
- Treat as research-only until explicitly promoted

### `archive/`
- **Maturity**: Legacy (preserve for history; do not modify for features)

## Dependency Direction (simplified)

```
main.py / gui_launcher.py
    ↓
core/sequence_builder.py
    ↓
core/effect_engine.py  (central hub — facade target)
    ├── audio / rhythm / band intelligence
    ├── spatial / style / polish
    └── xlights/ (XSQ output)
```

`legacy_ac/` and most `helixville*` / research trees must not be imported by the production path.

## Related Documents

- [MATURITY_MATRIX.md](MATURITY_MATRIX.md)
- [REPO_IMPROVEMENT_ROADMAP.md](../REPO_IMPROVEMENT_ROADMAP.md)
- [core_dependency_graph.md](core_dependency_graph.md)
- [MASTER_TODO.md](../MASTER_TODO.md)
