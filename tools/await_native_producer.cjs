"use strict";

// Keep exact-source acceptance strict; distinguish a missing producer from a slow one.
async function awaitNativeProducer({
  github, core, owner, repo, sha, branch,
  maxAttempts = 220, missingGraceAttempts = 5,
  pause = ms => new Promise(resolve => setTimeout(resolve, ms)),
}) {
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    const response = await github.rest.actions.listWorkflowRuns({
      owner, repo, workflow_id: "fresh-real-band-mp4.yml",
      branch, head_sha: sha, per_page: 100,
    });
    const runs = response.data.workflow_runs.filter(run =>
      run.head_sha === sha && run.head_repository?.full_name === owner + "/" + repo);
    for (const run of runs.filter(run => run.conclusion === "success")) {
      const listing = await github.rest.actions.listWorkflowRunArtifacts({
        owner, repo, run_id: run.id,
      });
      const artifacts = listing.data.artifacts.filter(artifact =>
        !artifact.expired &&
        artifact.name === "helix-fresh-original-audio-six-snowmen-keyboard");
      if (artifacts.length !== 1) {
        throw new Error("Successful native run must have exactly one source-bound artifact");
      }
      core.setOutput("run_id", String(run.id));
      core.setOutput("sha", sha);
      core.info("Accepting only native producer " + run.html_url + " at " + sha);
      return;
    }
    if (attempt + 1 >= missingGraceAttempts) {
      if (!runs.length) {
        throw new Error("No native producer was scheduled for exact source " + sha +
          "; check fresh-real-band-mp4.yml event/path/branch filters before retrying");
      }
      if (runs.every(run => run.status === "completed")) {
        throw new Error("No successful native producer at " + sha + ": " +
          runs.map(run => run.id + ":" + run.conclusion).join(", "));
      }
    }
    core.info("Waiting for genuine native producer at " + sha +
      " (" + (attempt + 1) + "/" + maxAttempts + ")");
    if (attempt + 1 < maxAttempts) await pause(30000);
  }
  throw new Error("Native producer did not succeed within the polling deadline");
}

module.exports = { awaitNativeProducer };
