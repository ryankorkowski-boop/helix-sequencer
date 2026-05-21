from __future__ import annotations

from pathlib import Path


WORKFLOW = Path('.github/workflows/helix-flow-review-artifacts.yml')


def _workflow_text() -> str:
    assert WORKFLOW.exists(), f'Missing workflow: {WORKFLOW}'
    return WORKFLOW.read_text(encoding='utf-8')


def test_review_artifact_workflow_exists() -> None:
    text = _workflow_text()

    assert 'name: Helix Flow Review Artifacts' in text
    assert 'export-review-artifacts:' in text


def test_review_artifact_workflow_renders_mp4_and_xsq() -> None:
    text = _workflow_text()

    assert 'render_xsq_skeleton_preview.py' in text
    assert 'helix_flow_demo.xsq' in text
    assert 'helix_flow_demo.mp4' in text


def test_review_artifact_workflow_uploads_expected_artifacts() -> None:
    text = _workflow_text()

    assert 'uses: actions/upload-artifact@v4' in text
    assert 'name: helix-flow-review-artifacts' in text
    assert '*.json' in text
    assert '*.xsq' in text
    assert '*.mp4' in text
    assert '*.md' in text


def test_review_artifact_workflow_exports_acceptance_summary() -> None:
    text = _workflow_text()

    assert 'helix_flow_acceptance_summary.md' in text
    assert 'Refresh acceptance summary after MP4 exists' in text
