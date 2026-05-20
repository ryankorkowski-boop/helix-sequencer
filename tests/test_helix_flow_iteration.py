from __future__ import annotations

from core.helix_flow_iteration import build_iteration_advice, build_iteration_report


def _quality(**overrides):
    base = {
        "score": 0.60,
        "musicality": 0.60,
        "spatial_coherence": 0.60,
        "layering": 0.60,
        "novelty": 0.60,
        "emotion": 0.60,
    }
    base.update(overrides)
    return base


def test_iteration_advice_targets_weakest_category() -> None:
    advice = build_iteration_advice(_quality(spatial_coherence=0.10), iteration=2)

    assert advice.iteration == 2
    assert advice.weakest_category == "spatial_coherence"
    assert advice.action == "lengthen directional spatial paths"
    assert advice.parameter_updates["spread_path_max_models"] == 5


def test_iteration_advice_handles_layering() -> None:
    advice = build_iteration_advice(_quality(layering=0.05))

    assert advice.weakest_category == "layering"
    assert advice.parameter_updates["cascade_stagger_seconds"] == 0.18


def test_iteration_advice_handles_novelty() -> None:
    advice = build_iteration_advice(_quality(novelty=0.05))

    assert advice.weakest_category == "novelty"
    assert advice.parameter_updates["novelty_weight"] == 1.20


def test_iteration_report_contains_comparison_and_advice() -> None:
    report = build_iteration_report(_quality(emotion=0.05), iteration=3)

    assert report["comparison"]["weakest_category"] == "emotion"
    assert report["iteration_advice"]["iteration"] == 3
    assert report["iteration_advice"]["weakest_category"] == "emotion"


def test_iteration_advice_rejects_invalid_iteration() -> None:
    try:
        build_iteration_advice(_quality(), iteration=0)
    except ValueError as exc:
        assert "iteration must be > 0" in str(exc)
    else:
        raise AssertionError("Expected ValueError for invalid iteration")
