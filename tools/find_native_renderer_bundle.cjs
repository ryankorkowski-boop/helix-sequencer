"use strict";

// A build artifact is reusable across PR/cache scopes. Musical output still
// requires a fresh producer at the consumer's exact Helix source revision.
async function findNativeRendererBundle({github, core, owner, repo, branch, name}) {
  const artifacts = await github.paginate(github.rest.actions.listArtifacts, {
    owner, repo, name, per_page: 100,
  });
  const candidates = artifacts.filter(a => a.name === name && !a.expired && a.workflow_run?.id)
    .sort((a, b) => b.id - a.id);
  for (const artifact of candidates) {
    const {data: run} = await github.rest.actions.getWorkflowRun({
      owner, repo, run_id: artifact.workflow_run.id,
    });
    if (run.head_repository?.full_name !== owner + "/" + repo ||
        run.path !== ".github/workflows/fresh-real-band-mp4.yml" ||
        ![branch, "codex/eight-hour-recovery-20261019"].includes(run.head_branch) ||
        !["push", "pull_request", "workflow_dispatch"].includes(run.event)) continue;
    core.setOutput("run_id", String(run.id));
    core.info("Reusing pinned renderer build from " + run.html_url +
      "; source musical output will be regenerated");
    return;
  }
  core.info("No matching repository renderer bundle; performing bounded cold build");
}

module.exports = { findNativeRendererBundle };
