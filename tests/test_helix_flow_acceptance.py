from __future__ import annotations

from core.helix_flow_acceptance import build_acceptance_summary


def test_acceptance_summary_requires_review_artifacts_and_score() -> None:
    summary = build_acceptance_summary(
        {"score": 0.95},
        {"delta": 0.10, "weakest_category": "layering"},
        {"iteration_advice": {"action": "increase controlled stagger overlap"}},
        has_xsq=True,
        has_mp4=True,
        min_score=0.93,
    )

    assert summary.passed is True
    assert summary.checked_items["review_artifacts"] is True
    assert summary.score == 0.95
    assert summary.baseline_delta == 0.10
    assert summary.weakest_category == "layering"
    assert "Helix Flow Issue #2 Acceptance Summary" in summary.summary_markdown
    assert "- [x] 20-second XSQ and MP4 review artifacts generated" in summary.summary_markdown


def test_acceptance_summary_fails_without_mp4() -> None:
    summary = build_acceptance_summary(
        {"score": 0.99},
        {"delta": 0.20, "weakest_category": "novelty"},
        {"iteration_advice": {"action": "rotate repeated effect families"}},
        has_xsq=True,
        has_mp4=False,
    )

    assert summary.passed is False
    assert summary.checked_items["review_artifacts"] is False
    assert "- [ ] MP4 preview generated" in summary.summary_markdown


def test_acceptance_summary_fails_below_target_score() -> None:
    summary = build_acceptance_summary(
        {"score": 0.80},
        {"delta": 0.10, "weakest_category": "emotion"},
        {"iteration_advice": {"action": "increase phrase-level strength contrast"}},
        has_xsq=True,
        has_mp4=True,
        min_score=0.93,
    )

    assert summary.passed is False
    assert summary.checked_items["review_artifacts"] is True
    assert "Target score: **0.930**" in summary.summary_markdown


def test_acceptance_summary_serializes_to_dict() -> None:
    summary = build_acceptance_summary(
        {"score": 0.93},
        {"delta": 0.0, "weakest_category": "musicality"},
        {"iteration_advice": {"action": "prefer higher context-fit effects"}},
        has_xsq=True,
        has_mp4=True,
    )
    data = summary.as_dict()

    assert data["score"] == 0.93
    assert data["weakest_category"] == "musicality"
    assert "summary_markdown" in data
