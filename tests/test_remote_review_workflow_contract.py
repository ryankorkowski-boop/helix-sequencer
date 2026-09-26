from __future__ import annotations

from pathlib import Path


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

    assert 'uses: actions/upload-artifact@v7' in text
    assert 'name: helix-remote-review-preview-mp4' in text
    assert 'review_summary.md' in text
    assert '**/*.mp4' in text
    assert '**/*.xsq' in text
    assert '**/*.json' in text


def test_remote_review_workflow_uses_canonical_renderer_path() -> None:
    text = _workflow_text()

    assert 'preview_hq.py' in text
    assert 'Pick highest-scoring valid candidate or fallback and render MP4' in text
    assert 'ranked_256_channel_sequence_with_drummer_v3' in text
def test_remote_review_workflow_generates_validated_demo_fallback() -> None:
    text = _workflow_text()

    assert 'export_demo_xsq.py' in text
    assert 'validate_xsq_structure.py' in text
    assert 'helix_demo_vocal.xsq' in text
