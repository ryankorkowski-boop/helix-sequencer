"""The artifact's PR head and the bundled source must refer to the same code."""
from pathlib import Path

import pytest
import yaml


@pytest.mark.parametrize('workflow,job', [
    ('windows-portable.yml', 'build'),
    ('android-offline.yml', 'build-and-offline-smoke'),
])
def test_installable_build_pins_and_checks_requested_source(workflow, job):
    root = Path(__file__).resolve().parents[1]
    definition = yaml.safe_load((root / '.github/workflows' / workflow).read_text())
    build = definition['jobs'][job]
    requested = '${{ github.event.pull_request.head.sha || github.sha }}'
    assert build['env']['HELIX_SOURCE_COMMIT'] == requested
    checkout = next(step for step in build['steps']
                    if step.get('uses') == 'actions/checkout@v4')
    assert checkout['with']['ref'] == requested
    checks = [step.get('run', '') for step in build['steps']]
    assert any("'rev-parse', 'HEAD'" in command
               and "os.environ['HELIX_SOURCE_COMMIT']" in command
               and 'assert actual ==' in command for command in checks)
