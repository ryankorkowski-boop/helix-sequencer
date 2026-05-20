from __future__ import annotations

from pathlib import Path

import yaml


WORKFLOW = Path('.github/workflows/helix-remote-review-preview.yml')


def _load_workflow() -> dict:
    assert WORKFLOW.exists(), f'Missing workflow: {WORKFLOW}'
    return yaml.safe_load(WORKFLOW.read_text(encoding='utf-8'))


def test_remote_review_workflow_exists_and_parses() -> None:
    workflow = _load_workflow()

    assert workflow['name'] == 'Helix Remote Review Preview MP4'
    assert 'jobs' in workflow
    assert 'render-winner-preview' in workflow['jobs']


def test_remote_review_workflow_uploads_mp4_artifacts() -> None:
    workflow = _load_workflow()
    steps = workflow['jobs']['render-winner-preview']['steps']

    upload_steps = [
        step for step in steps
        if step.get('uses', '').startswith('actions/upload-artifact@')
    ]

    assert upload_steps, 'Expected upload-artifact step'

    upload = upload_steps[-1]
    payload = upload['with']['path']

    assert '**/*.mp4' in payload
    assert '**/*.xsq' in payload
    assert 'review_summary.md' in payload


def test_remote_review_workflow_contains_fallback_renderer_path() -> None:
    workflow = _load_workflow()
    steps = workflow['jobs']['render-winner-preview']['steps']

    combined = '\n'.join(step.get('run', '') for step in steps)

    assert 'render_xsq_skeleton_preview.py' in combined
    assert 'validated_demo_xsq_fallback' in combined
    assert 'preview_hq.py' in combined


def test_remote_review_workflow_generates_validated_demo_fallback() -> None:
    workflow = _load_workflow()
    steps = workflow['jobs']['render-winner-preview']['steps']

    combined = '\n'.join(step.get('run', '') for step in steps)

    assert 'export_demo_xsq.py' in combined
    assert 'validate_xsq_structure.py' in combined
    assert 'helix_demo_vocal.xsq' in combined
