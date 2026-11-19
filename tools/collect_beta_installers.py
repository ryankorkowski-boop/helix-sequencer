"""Collect successful same-SHA Actions runs using the runner's read-only gh token."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import time

from tools.package_beta_installers import ARTIFACT_NAMES, WORKFLOWS, assemble, require


def api(repository, endpoint):
    return json.loads(subprocess.check_output(['gh', 'api', f'repos/{repository}/{endpoint}']))


def select_runs(repository, source_sha):
    selected = {}
    for role, path in WORKFLOWS.items():
        # Server-side SHA/workflow filtering avoids unrelated or stale builds.
        runs = api(repository, f'actions/workflows/{Path(path).name}/runs?head_sha={source_sha}&event=push&per_page=100')['workflow_runs']
        candidates = [r for r in runs if r['head_sha'] == source_sha and r['event'] == 'push']
        require(candidates, f'{role}: no push run found for {source_sha}')
        latest = max(candidates, key=lambda r: (r['run_number'], r['run_attempt']))
        require(latest['conclusion'] not in ('failure', 'cancelled', 'timed_out', 'action_required', 'skipped', 'stale'),
                f'{role}: latest exact-source run did not succeed ({latest["conclusion"]})')
        if latest['status'] == 'completed':
            require(latest['conclusion'] == 'success', f'{role}: run did not succeed')
            selected[role] = latest
    return selected


def collect(repository, source_sha, work: Path, output: Path, timeout: int = 2100):
    deadline = time.monotonic() + timeout
    while True:
        try:
            runs = select_runs(repository, source_sha)
        except ValueError as error:
            # On a push, other workflows may not yet appear in the Actions API.
            if 'no push run found' not in str(error):
                raise
            runs = {}
        print('Completed same-source gates: ' + ', '.join(sorted(runs)), flush=True)
        if len(runs) == len(WORKFLOWS):
            break
        require(time.monotonic() < deadline, 'Timed out waiting for same-source CI gates')
        time.sleep(30)
    work.mkdir(parents=True, exist_ok=False)
    artifacts, archives = {}, {}
    for role, name in ARTIFACT_NAMES.items():
        platform = 'android' if role.startswith('android') else role
        available = api(repository, f'actions/runs/{runs[platform]["id"]}/artifacts?per_page=100')['artifacts']
        matching = [a for a in available if a['name'] == name and not a['expired']]
        require(len(matching) == 1, f'Expected one unexpired {name}')
        artifact = artifacts[role] = matching[0]
        path = archives[role] = work / (role + '.zip')
        with path.open('wb') as stream:
            subprocess.run(['gh', 'api', f'repos/{repository}/actions/artifacts/{artifact["id"]}/zip'],
                           stdout=stream, check=True)
    inputs = {'schema': 'helix.installer-inputs.v1', 'repository': repository,
              'source_sha': source_sha, 'runs': runs, 'artifacts': artifacts}
    (work / 'candidate-inputs.json').write_text(json.dumps(inputs, indent=2) + '\n')
    return assemble(source_sha=source_sha, repository=repository, inputs=inputs,
                    archives=archives, output=output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', required=True)
    parser.add_argument('--source-sha', required=True)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    collect(args.repository, args.source_sha, args.work, args.output)
