from __future__ import annotations

from pathlib import Path
import json
import re
import subprocess
import textwrap

import pytest


WORKFLOW = Path('.github/workflows/helix-remote-review-preview.yml')


def _workflow_text() -> str:
    assert WORKFLOW.exists(), f'Missing workflow: {WORKFLOW}'
    return WORKFLOW.read_text(encoding='utf-8')


def test_remote_review_workflow_exists_and_has_render_job() -> None:
    text = _workflow_text()

    assert 'name: Helix Remote Review Preview MP4' in text
    assert 'jobs:' in text
    assert 'render-winner-preview:' in text


def test_remote_review_workflow_uploads_mp4_artifacts() -> None:
    text = _workflow_text()

    assert 'uses: actions/upload-artifact@v4' in text
    assert 'name: helix-remote-review-preview-mp4' in text
    assert 'review_summary.md' in text
    assert '**/*.mp4' in text
    assert '**/*.xsq' in text
    assert '**/*.json' in text


def test_remote_review_workflow_contains_fallback_renderer_path() -> None:
    text = _workflow_text()

    assert 'render_xsq_skeleton_preview.py' in text
    assert 'validated_demo_xsq_fallback' in text
    assert 'preview_hq.py' in text


def test_remote_review_workflow_generates_validated_demo_fallback() -> None:
    text = _workflow_text()

    assert 'export_demo_xsq.py' in text
    assert 'validate_xsq_structure.py' in text
    assert 'helix_demo_vocal.xsq' in text


@pytest.mark.parametrize('second_score,second_issues,expected', [
    (90, 0, 'first'),  # Exact ties must not compare the result dictionaries.
    (90, 1, 'first'),
    (91, 1, 'second'),
])
def test_actual_winner_step_renders_tied_candidates(
    tmp_path, monkeypatch, second_score, second_issues, expected,
) -> None:
    workflow = _workflow_text()
    step = workflow.split('      - name: Pick highest-scoring', 1)[1]
    script = textwrap.dedent(step.split("python - <<'PY'\n", 1)[1].split('\n          PY', 1)[0])
    # Actions interpolates these expressions before Python receives the step.
    script = re.sub(r'\$\{\{.*?\}\}', 'test-value', script)
    monkeypatch.chdir(tmp_path)
    out = Path('test_runs/remote_review_preview')
    out.mkdir(parents=True)
    results = []
    for name, score, issues in [('first', 90, 0), ('second', second_score, second_issues)]:
        sequence = out / (name + '.xsq')
        sequence.write_text('<xsequence/>')
        results.append({'version': name, 'sequence': str(sequence), 'sequence_ok': True,
                        'report': {'quality_score': score, 'validation_issues': issues}})
    (out / 'v28_legacy_256_preview_summary.json').write_text(json.dumps({'results': results}))
    commands = []

    def render(command, *, check):
        assert check
        commands.append(command)
        Path(command[2]).with_suffix('.mp4').write_bytes(b'test renderer output')

    monkeypatch.setattr(subprocess, 'run', render)
    exec(compile(script, str(WORKFLOW), 'exec'), {})
    receipt = json.loads((out / 'remote_review_winner.json').read_text())
    assert receipt['winner_version'] == expected
    assert len(commands) == 1
    assert Path(receipt['winner_mp4']).read_bytes() == b'test renderer output'
