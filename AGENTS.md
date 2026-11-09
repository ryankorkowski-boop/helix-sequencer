# Agent Rules

- System is modular, not monolithic.
- Always modify focused modules, not the entire pipeline at once.
- Prefer rule-based logic before AI calls.
- Keep changes small, stable, and testable.
- Use feature branches only.
- Never edit `main` directly.
- Keep commit messages in `type(scope): description` format.
- Favor one active implementation per subsystem and archive legacy variants instead of deleting them.


## Master roadmap / cross-agent continuity (mandatory)

- READ FIRST: MASTER_TODO.md is the canonical cross-agent roadmap and handoff ledger.
- Before changing code, inspect the relevant roadmap items and current implementation.
- Any agent that changes code, tests, configuration, workflows, GUI, mapping, sequencing, rendering, or documentation MUST update MASTER_TODO.md in the same change set.
- Every change entry must record: goal, changed files/modules, intentionally preserved behavior, new behavior, tests/evidence, limitations, deferred work, and regression risks.
- Never silently remove or supersede an existing roadmap item. Mark it deferred, archived, superseded, or complete and explain why.
- Do not claim a feature is complete without evidence appropriate to the feature. For sequencing behavior, rendered XSQ/MP4 and/or xLights import evidence may be required in addition to unit tests.
- If an undocumented existing behavior is discovered, preserve it until its fate is explicitly documented.
- Handoffs must point the next agent to the master ledger rather than relying on chat-only context.

## Approval dashboard activity

- When changing this repository, follow [docs/AGENT_ACTIVITY_REPORTING.md](docs/AGENT_ACTIVITY_REPORTING.md) to report your real agent identity, task, source commit and completion when supported access is available.
- Do not infer another agent's identity or liveness from commits under a shared account. Reporting supplements MASTER_TODO.md and must not delay authorized beta work if the dashboard is unavailable.
