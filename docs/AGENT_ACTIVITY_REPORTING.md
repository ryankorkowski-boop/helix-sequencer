# Agent activity reporting for the Helix approval dashboard

Owner-requested dashboard: https://helix-beta-approval.cherishedanchovy.chatgpt.site
Site project: `appgprj_6aee7cac9bd08191bdd7d7d764eb195c`.

When changing Helix code, tests, workflows, or documentation, report your actual identity and task at start, at material checkpoints, after a push, and at completion when the Site tools are available. This supplements MASTER_TODO.md; it never replaces the canonical task ledger. If reporting is unavailable, record that limitation in the handoff and continue authorized beta work.

Use the Sites `get_site` operation for the exact project. Confirm the Site remains owner-private. Obtain its current supported service-access token in session memory. Send it only to the Site as `OAI-Sites-Authorization: Bearer <token>`; never put it in source, logs, URLs, or commit messages. Do not generate or rotate credentials just to probe access. Retrieve the current private instructions at `GET /api/sync-instructions` before writing.

POST `/api/agents` with schema `helix.agent-activity.v1`, a stable unique `agentId`, actual `name`, `provider`, optional known `model`, `project:helix`, `status` (`working`, `blocked`, `pushed`, `done`), concrete `task`, actual `branch`, optional full `commitSha`, and factual `note`. Use `project:site` for dashboard work. Read back `GET /api/agents` to verify persistence.

Working reports become stale after 15 minutes without another report. Do not fabricate heartbeats, report another agent as active, or infer an agent from a shared GitHub author account. The dashboard labels reports as self-reported; a commit observed on GitHub is a separate fact.

Add accurate commit trailers when appropriate:
```text
Agent-Name: <actual agent name>
Agent-ID: <same stable run ID>
Agent-Provider: <actual provider>
```

The dashboard synchronizes current PR/branch evidence on PR events and via the existing hourly release check. It preserves exact source SHA and source/write timestamps, labels earlier-source workflow runs, and cannot infer owner approval from tests or repository claims. Syncing is not authority to merge PR #188, close issue #199, publish beta, relabel diagnostics, or relax acceptance gates. Engine changes still follow AGENTS.md and MASTER_TODO.md.
