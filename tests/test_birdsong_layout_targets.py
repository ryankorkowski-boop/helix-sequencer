from __future__ import annotations

from core.birdsong_layout_targets import build_spread_path, build_target_plan, choose_target_model, load_helixville3_target_pool


def test_load_helixville3_target_pool_returns_real_or_fallback_models() -> None:
    pool = load_helixville3_target_pool()

    assert pool
    assert all(isinstance(name, str) and name for name in pool)


def test_choose_target_model_is_deterministic() -> None:
    intent = {
        "effect_name": "Bars",
        "motif": "wave_sweep",
        "direction": "left_to_right",
        "start_time": 1.0,
    }
    pool = ("A", "B", "C")

    assert choose_target_model(intent, pool) == choose_target_model(intent, pool)


def test_choose_target_model_respects_direction_path() -> None:
    pool = ("A", "B", "C")
    left = {
        "effect_name": "Bars",
        "motif": "wave_sweep",
        "direction": "left_to_right",
        "start_time": 0.0,
    }
    right = {
        "effect_name": "Bars",
        "motif": "wave_sweep",
        "direction": "right_to_left",
        "start_time": 0.0,
    }

    assert choose_target_model(left, pool) == "A"
    assert choose_target_model(right, pool) == "C"


def test_build_spread_path_wraps_along_directional_order() -> None:
    pool = ("A", "B", "C")
    intent = {
        "effect_name": "Bars",
        "motif": "wave_sweep",
        "direction": "right_to_left",
        "start_time": 0.0,
    }

    assert build_spread_path(intent, pool, max_models=4) == ("C", "B", "A")


def test_build_target_plan_exposes_ordered_and_spread_paths() -> None:
    pool = ("A", "B", "C")
    plan = build_target_plan(
        {
            "effect_name": "Bars",
            "motif": "wave_sweep",
            "direction": "right_to_left",
            "start_time": 0.0,
        },
        model_pool=pool,
    )

    assert plan.model_name == "C"
    assert plan.model_pool == pool
    assert plan.ordered_path == ("C", "B", "A")
    assert plan.spread_path == ("C", "B", "A")


def test_choose_target_model_rejects_empty_pool() -> None:
    try:
        choose_target_model({"direction": "left_to_right"}, ())
    except ValueError as exc:
        assert "model_pool must not be empty" in str(exc)
    else:
        raise AssertionError("Expected ValueError for empty model pool")


def test_build_spread_path_rejects_invalid_max_models() -> None:
    try:
        build_spread_path({"direction": "left_to_right"}, ("A",), max_models=0)
    except ValueError as exc:
        assert "max_models must be > 0" in str(exc)
    else:
        raise AssertionError("Expected ValueError for invalid max_models")
