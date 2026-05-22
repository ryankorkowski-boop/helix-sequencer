from __future__ import annotations

from dataclasses import replace

import pytest

from core.birdsong_issue2_runtime import (
    BirdsongRuntimeConfig,
    emit_birdsong_rows,
    generate_birdsong_rows,
)
from core.feature_state import FeatureState


def _frames():
    state = FeatureState()
    return [
        state.update(
            0,
            energy=0.05,
            onset=0.0,
            centroid=1000.0,
            low=0.05,
            mid=0.02,
            high=0.01,
            beat_phase=0.0,
            time_s=0.0,
        ),
        state.update(
            1,
            energy=0.90,
            onset=1.0,
            centroid=7000.0,
            low=0.10,
            mid=0.20,
            high=0.90,
            beat_phase=0.50,
            time_s=0.5,
        ),
        state.update(
            2,
            energy=0.75,
            onset=0.70,
            centroid=900.0,
            low=0.80,
            mid=0.20,
            high=0.10,
            beat_phase=0.10,
            time_s=1.0,
        ),
    ]


def test_generate_birdsong_rows_defaults_off() -> None:
    rows = generate_birdsong_rows(_frames(), ["star", "arch"])

    assert rows == []


def test_generate_birdsong_rows_emits_deterministic_rows_when_enabled() -> None:
    frames = _frames()
    models = ["star", "arch", "ground", "mega"]
    config = BirdsongRuntimeConfig(enabled=True, max_targets_per_frame=2, duration_ms=120)

    first = generate_birdsong_rows(frames, models, config=config)
    second = generate_birdsong_rows(frames, models, config=config)

    assert first == second
    assert len(first) == 4
    assert {row.label for row in first} == {"birdsong_issue2"}
    assert {row.motif for row in first} == {"sparkle_field", "pulse_cascade"}
    assert all(row.end_ms > row.start_ms for row in first)


def test_generate_birdsong_rows_dedupes_models_and_limits_targets() -> None:
    config = BirdsongRuntimeConfig(enabled=True, max_targets_per_frame=1)

    rows = generate_birdsong_rows(_frames(), ["star", "STAR", "arch"], config=config)

    assert len(rows) == 2
    assert all(row.model in {"star", "arch"} for row in rows)


def test_emit_birdsong_rows_uses_existing_add_model_contract() -> None:
    rows = generate_birdsong_rows(
        _frames(),
        ["star", "arch"],
        config=BirdsongRuntimeConfig(enabled=True, max_targets_per_frame=1),
    )
    calls: list[tuple[str, int, int, str, str, str]] = []

    def add_model(model: str, st: int, en: int, label: str, eff: str = "On", stem: str = "other") -> None:
        calls.append((model, st, en, label, eff, stem))

    emitted = emit_birdsong_rows(rows, add_model)

    assert emitted == len(rows)
    assert emitted == len(calls)
    assert all(call[3] == "birdsong_issue2" for call in calls)
    assert all(call[5] == "other" for call in calls)


@pytest.mark.parametrize(
    ("callback_result", "expected"),
    [
        (True, 1),
        (False, 0),
        (3, 3),
        (None, 1),
    ],
)
def test_emit_birdsong_rows_counts_callback_confirmation(callback_result: object, expected: int) -> None:
    rows = generate_birdsong_rows(
        _frames(),
        ["star"],
        config=BirdsongRuntimeConfig(enabled=True, max_targets_per_frame=1),
    )[:1]

    def add_model(*_args, **_kwargs):
        return callback_result

    assert emit_birdsong_rows(rows, add_model) == expected


def test_emit_birdsong_rows_counts_placement_object_as_confirmed() -> None:
    rows = generate_birdsong_rows(
        _frames(),
        ["star"],
        config=BirdsongRuntimeConfig(enabled=True, max_targets_per_frame=1),
    )[:1]

    class Placement:
        pass

    assert emit_birdsong_rows(rows, lambda *_args, **_kwargs: Placement()) == 1


@pytest.mark.parametrize("bad_duration", [float("nan"), float("inf"), "bad"])
@pytest.mark.parametrize("bad_target_cap", [float("nan"), float("inf"), "bad"])
def test_generate_birdsong_rows_sanitizes_invalid_config_values(bad_duration: object, bad_target_cap: object) -> None:
    rows = generate_birdsong_rows(
        _frames(),
        ["star", "arch", "ground", "mega"],
        config=BirdsongRuntimeConfig(
            enabled=True,
            duration_ms=bad_duration,  # type: ignore[arg-type]
            max_targets_per_frame=bad_target_cap,  # type: ignore[arg-type]
        ),
    )

    assert len(rows) == 6
    assert all(row.end_ms > row.start_ms for row in rows)


def test_generate_birdsong_rows_skips_non_finite_frame_times() -> None:
    frames = _frames()
    bad_frames = [
        frames[0],
        replace(frames[1], time_s=float("nan")),
        replace(frames[2], time_s=float("inf")),
    ]

    rows = generate_birdsong_rows(
        bad_frames,
        ["star", "arch"],
        config=BirdsongRuntimeConfig(enabled=True, max_targets_per_frame=1),
    )

    assert rows == []
