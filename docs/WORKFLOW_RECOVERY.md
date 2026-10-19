# GitHub Actions Queue Recovery Playbook

1. Collect run URL, run ID, workflow name, branch, commit SHA, queued_at, status, conclusion and jobs.
2. Check whether jobs are awaiting runner, concurrency lock, environment approval, quota/billing, repository Actions policy, or dependent job. Inspect workflow YAML and exact runs before changing settings.
3. If cancellation says run is not in progress, preserve exact error and do not claim cancellation. Avoid repeated dispatches while queue root cause is unknown.
4. Once corrected, dispatch one lightweight diagnostic run and confirm it transitions queued → in_progress → completed successfully. Only then launch one native render.
5. Capture logs, actual artifact links, media duration/streams and source provenance. Never substitute diagnostics or synthetic video for authentic native xLights render.
6. Before session exhaustion, update roadmap and handoff with run IDs, unresolved cause, owner-side actions and next exact step; commit/push.

No current workflow queue state has yet been verified by this checkpoint.
