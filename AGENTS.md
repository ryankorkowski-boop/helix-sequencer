# Agent Rules

- System is modular, not monolithic.
- Always modify focused modules, not the entire pipeline at once.
- Prefer rule-based logic before AI calls.
- Keep changes small, stable, and testable.
- Use feature branches only.
- Never edit `main` directly.
- Keep commit messages in `type(scope): description` format.
- Favor one active implementation per subsystem and archive legacy variants instead of deleting them.

## Current beta operating priority

- Treat `feature/restructure-core` as the active beta base.
- Run `python scripts/ci/run_required_checks.py` before opening or updating PRs when dependencies are installed.
- Phase 1 CI/bootstrap normalization is complete; do not redo it unless the shared runner or workflow breaks.
- Prioritize canonical xLights contract hardening, clean-room smoke fixtures, run manifests, and GUI beta safety before adding more effect-planning features.
- Keep generated `.xsq`, `.fseq`, preview media, private tester layouts, songs, and copied templates out of git unless a tiny fixture is intentionally documented.
