"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const { awaitNativeProducer } = require("../tools/await_native_producer.cjs");

const artifactName = "helix-fresh-original-audio-six-snowmen-keyboard";
const good = { id: 10, head_sha: "wanted", head_repository: {full_name: "owner/repo"},
  status: "completed", conclusion: "success", html_url: "https://example.test/run/10" };

function harness(sequence, artifacts = [{name: artifactName, expired: false}]) {
  let polls = 0, waits = 0, artifactReads = 0;
  const outputs = {};
  return {
    options: {
      owner: "owner", repo: "repo", sha: "wanted", branch: "work/test",
      github: {rest: {actions: {
        listWorkflowRuns: async request => {
          assert.equal(request.head_sha, "wanted");
          assert.equal(request.branch, "work/test");
          const runs = sequence[Math.min(polls++, sequence.length - 1)];
          return {data: {workflow_runs: runs}};
        },
        listWorkflowRunArtifacts: async request => {
          artifactReads++;
          assert.equal(request.run_id, 10);
          return {data: {artifacts}};
        },
      }}},
      core: {setOutput: (key, value) => {outputs[key] = value;}, info: () => {}},
      pause: async milliseconds => {assert.equal(milliseconds, 30000); waits++;},
    },
    state: () => ({polls, waits, artifactReads, outputs}),
  };
}

test("missing producer fails after five polls, without a 55-minute wait", async () => {
  const h = harness([[]]);
  await assert.rejects(awaitNativeProducer(h.options), /No native producer was scheduled/);
  assert.deepEqual(h.state(), {polls: 5, waits: 4, artifactReads: 0, outputs: {}});
});

test("queued/running source producers retain the full opportunity to finish", async () => {
  const queued = {...good, status: "queued", conclusion: null};
  const running = {...queued, status: "in_progress"};
  const h = harness([[queued], [queued], [running], [running], [running], [running], [good]]);
  await awaitNativeProducer(h.options);
  assert.equal(h.state().polls, 7);
  assert.deepEqual(h.state().outputs, {run_id: "10", sha: "wanted"});
});

test("old SHA and foreign-repository successes cannot satisfy this source", async () => {
  const h = harness([[{...good, head_sha: "old"},
    {...good, head_repository: {full_name: "fork/repo"}}]]);
  await assert.rejects(awaitNativeProducer(h.options), /No native producer was scheduled/);
  assert.equal(h.state().artifactReads, 0);
  assert.deepEqual(h.state().outputs, {});
});

for (const artifacts of [
  [], [{name: artifactName, expired: true}],
  [{name: "unrelated-movie", expired: false}],
  [{name: artifactName, expired: false}, {name: artifactName, expired: false}],
]) {
  test("successful producer requires exactly one live named artifact: " + JSON.stringify(artifacts), async () => {
    const h = harness([[good]], artifacts);
    await assert.rejects(awaitNativeProducer(h.options), /exactly one source-bound artifact/);
    assert.deepEqual(h.state().outputs, {});
  });
}

test("completed failed producers fail with actual conclusions after grace", async () => {
  const h = harness([[{...good, conclusion: "failure"}]]);
  await assert.rejects(awaitNativeProducer(h.options), /10:failure/);
  assert.equal(h.state().polls, 5);
});

test("a running producer has a bounded overall deadline", async () => {
  const h = harness([[{...good, status: "in_progress", conclusion: null}]]);
  await assert.rejects(awaitNativeProducer({...h.options, maxAttempts: 8}), /polling deadline/);
  assert.equal(h.state().polls, 8);
  assert.equal(h.state().waits, 7);
});

test("provider failure is surfaced rather than mistaken for absent media", async () => {
  const h = harness([[]]);
  h.options.github.rest.actions.listWorkflowRuns = async () => {throw new Error("rate limited");};
  await assert.rejects(awaitNativeProducer(h.options), /rate limited/);
  assert.equal(h.state().waits, 0);
});
