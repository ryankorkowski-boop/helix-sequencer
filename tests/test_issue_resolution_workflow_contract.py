from __future__ import annotations

from pathlib import Path


WORKFLOW = Path('.github/workflows/helix-issue-resolution-sprint.yml')


def _workflow_text() -> str:
    assert WORKFLOW.exists(), f'Missing workflow: {WORKFLOW}'
    return WORKFLOW.read_text(encoding='utf-8')


def test_issue_resolution_workflow_exists_and_has_core_jobs() -> None:
    text = _workflow_text()

    assert 'name: Helix Issue Resolution Sprint' in text
    assert 'build-sprint-bundle:' in text
    assert 'validation-gates:' in text


def test_issue_resolution_workflow_collects_and_groups_issues() -> None:
    text = _workflow_text()

    assert 'gh issue list' in text
    assert 'grouped_issues.json' in text
    assert 'issue_resolution_plan.md' in text
    assert 'Duplicate candidates' in text


def test_issue_resolution_workflow_runs_validation_paths() -> None:
    text = _workflow_text()

    assert 'python -m pytest -q' in text
    assert 'test_vocal_pipeline_integration.py' in text
    assert 'test_export_demo_xsq.py' in text
    assert 'validation_report.md' in text


def test_issue_resolution_workflow_uploads_reviewable_artifacts() -> None:
    text = _workflow_text()

    assert 'actions/upload-artifact@v4' in text
    assert 'helix-issue-resolution-sprint-bundle' in text
    assert 'helix-issue-resolution-validation-report' in text
