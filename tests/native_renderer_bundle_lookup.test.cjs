"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const {findNativeRendererBundle} = require("../tools/find_native_renderer_bundle.cjs");

const artifact = {id: 8, name: "pinned-build", expired: false, workflow_run: {id: 42}};
const run = {id: 42, head_repository: {full_name: "owner/repo"},
  head_branch: "codex/eight-hour-recovery-20261019", event: "pull_request",
  path: ".github/workflows/fresh-real-band-mp4.yml", html_url: "https://example.test/run/42"};

function harness(artifacts = [artifact], runs = {42: run}) {
  const outputs = {}, requested = [];
  return {outputs, requested, options: {
    owner: "owner", repo: "repo", branch: "work/current", name: "pinned-build",
    core: {setOutput: (key, value) => {outputs[key] = value;}, info: () => {}},
    github: {paginate: async (_endpoint, query) => {
      assert.equal(query.name, "pinned-build"); return artifacts;
    }, rest: {actions: {listArtifacts: () => {}, getWorkflowRun: async ({run_id}) => {
      requested.push(run_id); return {data: runs[run_id]};
    }}}},
  }};
}

test("reuses exact build from recovery even if later musical acceptance failed", async () => {
  const h = harness([artifact], {42: {...run, conclusion: "failure"}});
  await findNativeRendererBundle(h.options);
  assert.deepEqual(h.outputs, {run_id: "42"});
});

test("missing, expired and differently named bundles fall back to cold build", async () => {
  const h = harness([{...artifact, expired: true}, {...artifact, name: "old-patch"}]);
  await findNativeRendererBundle(h.options);
  assert.deepEqual(h.outputs, {});
  assert.deepEqual(h.requested, []);
});

test("recovery reuses the reviewed renderer-build branch after integration", async () => {
  const h = harness([artifact], {42: {...run, head_branch: "codex/native-build-reuse-20261020"}});
  h.options.branch = "codex/eight-hour-recovery-20261019";
  await findNativeRendererBundle(h.options);
  assert.deepEqual(h.outputs, {run_id: "42"});
});

for (const wrong of [
  {head_repository: {full_name: "fork/repo"}}, {head_branch: "unrelated"},
  {path: ".github/workflows/other.yml"}, {event: "pull_request_target"},
]) {
  test("rejects incompatible workflow provenance " + JSON.stringify(wrong), async () => {
    const h = harness([artifact], {42: {...run, ...wrong}});
    await findNativeRendererBundle(h.options);
    assert.deepEqual(h.outputs, {});
  });
}

test("chooses newest eligible artifact instead of newest foreign candidate", async () => {
  const h = harness([{...artifact, id: 9, workflow_run: {id: 43}}, artifact],
    {43: {...run, id: 43, head_repository: {full_name: "fork/repo"}}, 42: run});
  await findNativeRendererBundle(h.options);
  assert.deepEqual(h.requested, [43, 42]);
  assert.deepEqual(h.outputs, {run_id: "42"});
});

test("provider errors are surfaced", async () => {
  const h = harness();
  h.options.github.paginate = async () => {throw new Error("rate limited");};
  await assert.rejects(findNativeRendererBundle(h.options), /rate limited/);
});
