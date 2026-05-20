from __future__ import annotations

from core.helix_flow_baseline_compare import BASELINE_QUALITY, compare_to_baseline, recommended_next_adjustment


def test_compare_to_baseline_reports_deltas_and_pass_status() -> None:
    report = {
        "score": 0.60,
        "musicality": 0.58,
        "spatial_coherence": 0.52,
        "layering": 0.50,
        "novelty": 0.57,
        "emotion": 0.49,
    }

    comparison = compare_to_baseline(report, min_delta=0.01)

    assert comparison.score == 0.60
    assert comparison.baseline_score == BASELINE_QUALITY["score"]
    assert comparison.delta == 0.05
    assert comparison.passed is True
    assert comparison.deltas["score"] == 0.05


def test_compare_to_baseline_can_fail_gate() -> None:
    comparison = compare_to_baseline({"score": 0.54}, min_delta=0.0)

    assert comparison.passed is False
    assert comparison.delta == -0.01


def test_compare_to_baseline_finds_weakest_category() -> None:
    comparison = compare_to_baseline(
        {
            "score": 0.70,
            "musicality": 0.80,
            "spatial_coherence": 0.20,
            "layering": 0.60,
            "novelty": 0.60,
            "emotion": 0.60,
        }
    )

    assert comparison.weakest_category == "spatial_coherence"


def test_recommended_next_adjustment_matches_weakest_category() -> None:
    comparison = compare_to_baseline(
        {
            "score": 0.70,
            "musicality": 0.80,
            "spatial_coherence": 0.70,
            "layering": 0.15,
            "novelty": 0.60,
            "emotion": 0.60,
        }
    )

    assert comparison.weakest_category == "layering"
    assert "staggered overlaps" in recommended_next_adjustment(comparison)


def test_comparison_serializes_to_dict() -> None:
    comparison = compare_to_baseline({"score": 0.55})
    data = comparison.as_dict()

    assert data["score"] == 0.55
    assert data["baseline_score"] == 0.55
    assert data["delta"] == 0.0
    assert data["passed"] is True
    assert "deltas" in data
