from __future__ import annotations

from core.birdsong_completion_gate import (
    BirdsongCompletionGateConfig,
    run_birdsong_completion_gate,
)
from core.feature_state import FeatureState


def _frames():
    state = FeatureState()
    return [
        state.update(
            0,
            energy=0.12,
            onset=0.05,
            centroid=1200.0,
            low=0.10,
            mid=0.08,
            high=0.04,
            beat_phase=0.00,
            time_s=0.00,
        ),
        state.update(
            1,
            energy=0.88,
            onset=0.92,
            centroid=7200.0,
            low=0.12,
            mid=0.18,
            high=0.90,
            beat_phase=0.50,
            time_s=0.50,
        ),
        state.update(
            2,
            energy=0.72,
            onset=0.66,
            centroid=950.0,
            low=0.82,
            mid=0.22,
            high=0.12,
            beat_phase=0.12,
            time_s=1.00,
        ),
        state.update(
            3,
            energy=0.61,
            onset=0.55,
            centroid=3500.0,
            low=0.25,
            mid=0.70,
            high=0.24,
            beat_phase=0.82,
            time_s=1.50,
        ),
    ]


def test_completion_gate_runs_full_issue2_pipeline() -> None:
    report = run_birdsong_completion_gate(
        _frames(),
        ["mega_tree", "arches", "roofline", "matrix"],
    )

    assert report.passed is True
    assert report.frame_count == 4
    assert report.phrase_count >= 1
    assert report.intent_count >= 1
    assert report.runtime_row_count >= 1
    assert report.xsq_effect_count >= 1
    assert report.quality["score"] >= 0.35
    assert report.checks["uses_allowed_motifs_only"] is True
    assert any(item["motif"] == "sparkle_field" for item in report.intents)


def test_completion_gate_reports_failures_cleanly() -> None:
    report = run_birdsong_completion_gate(
        [],
        [],
        config=BirdsongCompletionGateConfig(min_quality_score=0.95),
    )

    assert report.passed is False
    assert report.checks["has_frames"] is False
    assert report.checks["has_models"] is False
    assert report.warnings
