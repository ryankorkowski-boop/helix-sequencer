from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

from core.birdsong_issue2_runtime import (
    BirdsongRuntimeConfig,
    emit_birdsong_rows,
    generate_birdsong_rows,
    plan_birdsong_runtime,
    write_birdsong_runtime_manifest,
)
from core.feature_state import FeatureState


FIXTURE_PATH = Path(__file__).resolve().parents[1] / "fixtures" / "birdsong_issue2" / "runtime_fixture.json"


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


def _enabled_config(**overrides):
    values = {"enabled": True}
    values.update(overrides)
    return BirdsongRuntimeConfig(**values)


def _fixture_payload():
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _fixture_frames(payload):
    state = FeatureState()
    frames = []
    for index, item in enumerate(payload["frames"]):
        frames.append(
            state.update(
                index,
                energy=item["energy"],
                onset=item["onset"],
                centroid=item["centroid"],
                low=item["low"],
                mid=item["mid"],
                high=item["high"],
                beat_phase=item["beat_phase"],
                time_s=item["time_s"],
            )
        )
    return frames


def test_generate_birdsong_rows_defaults_off() -> None:
    rows = generate_birdsong_rows(_frames(), ["star", "arch"])

    assert rows == []


def test_plan_birdsong_runtime_reports_disabled_skip() -> None:
    plan = plan_birdsong_runtime(_frames(), ["star", "arch"])

    assert plan.rows == ()
    assert plan.phrase_snapshots == ()
    assert plan.decision_report.enabled is False
    assert plan.decision_report.skipped_reason == "disabled"
    assert plan.decision_report.row_count == 0
    assert plan.decision_report.average_score == 0.0


def test_generate_birdsong_rows_requires_explicit_enable_value() -> None:
    disabled_values = (False, None, 0, "0", "false", "no", "off", "")
    for value in disabled_values:
        rows = generate_birdsong_rows(
            _frames(),
            ["star", "arch"],
            config=BirdsongRuntimeConfig(enabled=value),
        )
        assert rows == []

    rows = generate_birdsong_rows(
        _frames(),
        ["star", "arch"],
        config=BirdsongRuntimeConfig(enabled="true", max_targets_per_frame=1),
    )

    assert rows


def test_generate_birdsong_rows_emits_deterministic_rows_when_enabled() -> None:
    frames = _frames()
    models = ["star", "arch", "ground", "mega"]
    config = _enabled_config(max_targets_per_frame=2, duration_ms=120)

    first = generate_birdsong_rows(frames, models, config=config)
    second = generate_birdsong_rows(frames, models, config=config)

    assert first == second
    assert len(first) == 4
    assert {row.label for row in first} == {"birdsong_issue2"}
    assert {row.motif for row in first} == {
        "sparkle_field",
        "pulse_cascade",
    }
    assert all(row.end_ms > row.start_ms for row in first)


def test_birdsong_fixture_generates_persistent_phrase_plan() -> None:
    payload = _fixture_payload()
    frames = _fixture_frames(payload)
    config = BirdsongRuntimeConfig(**payload["config"])

    plan = plan_birdsong_runtime(frames, payload["model_names"], config=config)

    assert len(plan.rows) == payload["expected"]["row_count"]
    assert len(plan.phrase_snapshots) == payload["expected"]["phrase_count"]
    assert [snapshot.motif for snapshot in plan.phrase_snapshots] == payload["expected"]["motifs"]
    assert [snapshot.phrase_id for snapshot in plan.phrase_snapshots] == [
        "birdsong_issue2_0001",
        "birdsong_issue2_0002",
    ]
    assert [list(snapshot.target_models) for snapshot in plan.phrase_snapshots] == payload["expected"]["target_models"]
    assert [snapshot.spatial_intent for snapshot in plan.phrase_snapshots] == [
        "high_sparkle",
        "ground_pulse",
    ]
    assert all(snapshot.selection_reason.endswith("_adjacent_ring_score") for snapshot in plan.phrase_snapshots)
    assert all(0.0 < snapshot.score <= 1.0 for snapshot in plan.phrase_snapshots)
    assert all("spatial_fit" in snapshot.score_components for snapshot in plan.phrase_snapshots)
    assert plan.decision_report.enabled is True
    assert plan.decision_report.skipped_reason is None
    assert plan.decision_report.row_count == payload["expected"]["row_count"]
    assert plan.decision_report.phrase_count == payload["expected"]["phrase_count"]
    assert list(plan.decision_report.motifs) == payload["expected"]["motifs"]
    assert plan.decision_report.average_score > 0.0
    assert {row.motif for row in plan.rows} == set(payload["expected"]["motifs"])


def test_spatial_targeting_prefers_adjoining_believable_models() -> None:
    frames = _frames()
    models = ["star_top", "arch_mid", "ground_floor", "mega_tree"]
    config = _enabled_config(max_targets_per_frame=2, duration_ms=120)

    plan = plan_birdsong_runtime(frames, models, config=config)

    assert plan.phrase_snapshots[0].spatial_intent == "high_sparkle"
    assert plan.phrase_snapshots[0].target_models == ("mega_tree", "star_top")
    assert plan.phrase_snapshots[1].spatial_intent == "ground_pulse"
    assert plan.phrase_snapshots[1].target_models == ("ground_floor", "arch_mid")
    assert plan.phrase_snapshots[0].score_components["adjacency_fit"] >= 0.8
    assert plan.phrase_snapshots[1].score_components["spatial_fit"] >= 0.8


def test_write_birdsong_runtime_manifest_outputs_repo_safe_contract(tmp_path) -> None:
    payload = _fixture_payload()
    frames = _fixture_frames(payload)
    config = BirdsongRuntimeConfig(**payload["config"])
    output = tmp_path / "birdsong_runtime_manifest.json"

    written = write_birdsong_runtime_manifest(
        output,
        frames,
        payload["model_names"],
        config=config,
    )

    assert written == output
    manifest = json.loads(output.read_text(encoding="utf-8"))
    assert manifest["schema"] == "helix.birdsong_issue2.runtime_manifest.v1"
    assert manifest["status"] == "repo_safe_synthetic_runtime_fixture"
    assert manifest["feature_frame_count"] == len(payload["frames"])
    assert manifest["model_names"] == payload["model_names"]
    assert len(manifest["rows"]) == payload["expected"]["row_count"]
    assert len(manifest["phrase_snapshots"]) == payload["expected"]["phrase_count"]
    assert manifest["phrase_snapshots"][0]["phrase_id"] == "birdsong_issue2_0001"
    assert manifest["phrase_snapshots"][0]["spatial_intent"] == "high_sparkle"
    assert manifest["decision_report"]["enabled"] is True
    assert manifest["decision_report"]["row_count"] == payload["expected"]["row_count"]
    assert manifest["decision_report"]["average_score"] > 0.0
    assert "audio_path" not in manifest
    assert "layout_path" not in manifest


def test_generate_birdsong_rows_dedupes_models_and_limits_targets() -> None:
    config = _enabled_config(max_targets_per_frame=1)

    rows = generate_birdsong_rows(
        _frames(),
        ["star", "STAR", "arch"],
        config=config,
    )

    assert len(rows) == 2
    assert all(row.model in {"star", "arch"} for row in rows)


def test_emit_birdsong_rows_uses_existing_add_model_contract() -> None:
    rows = generate_birdsong_rows(
        _frames(),
        ["star", "arch"],
        config=_enabled_config(max_targets_per_frame=1),
    )
    calls: list[tuple[str, int, int, str, str, str]] = []

    def add_model(
        model: str,
        st: int,
        en: int,
        label: str,
        eff: str = "On",
        stem: str = "other",
    ) -> None:
        calls.append((model, st, en, label, eff, stem))

    emitted = emit_birdsong_rows(rows, add_model)

    assert emitted == len(rows)
    assert emitted == len(calls)
    assert all(call[3] == "birdsong_issue2" for call in calls)
    assert all(call[5] == "other" for call in calls)


def _constant_callback(value):
    def callback(*_args, **_kwargs):
        return value

    return callback


def test_emit_birdsong_rows_counts_boolean_callback_results() -> None:
    rows = generate_birdsong_rows(
        _frames(),
        ["star"],
        config=_enabled_config(max_targets_per_frame=1),
    )[:1]

    assert emit_birdsong_rows(rows, _constant_callback(True)) == 1
    assert emit_birdsong_rows(rows, _constant_callback(False)) == 0


def test_emit_counts_int_and_unknown_callback_results() -> None:
    rows = generate_birdsong_rows(
        _frames(),
        ["star"],
        config=_enabled_config(max_targets_per_frame=1),
    )[:1]

    assert emit_birdsong_rows(rows, _constant_callback(3)) == 3
    assert emit_birdsong_rows(rows, _constant_callback(None)) == 1


def test_emit_skips_callback_failures_by_default() -> None:
    rows = generate_birdsong_rows(
        _frames(),
        ["star", "arch"],
        config=_enabled_config(max_targets_per_frame=1),
    )
    calls = 0

    def sometimes_fails(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("simulated placement failure")
        return True

    assert emit_birdsong_rows(rows, sometimes_fails) == len(rows) - 1


def test_emit_can_raise_callback_failures_in_strict_mode() -> None:
    rows = generate_birdsong_rows(
        _frames(),
        ["star"],
        config=_enabled_config(max_targets_per_frame=1),
    )[:1]

    def fails(*_args, **_kwargs):
        raise RuntimeError("simulated placement failure")

    try:
        emit_birdsong_rows(rows, fails, strict=True)
    except RuntimeError as exc:
        assert "simulated placement failure" in str(exc)
    else:
        raise AssertionError("strict mode should propagate callback failures")


def test_generate_birdsong_rows_sanitizes_invalid_config_values() -> None:
    rows = generate_birdsong_rows(
        _frames(),
        ["star", "arch", "ground", "mega"],
        config=_enabled_config(
            duration_ms="invalid",
            max_targets_per_frame="invalid",
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
        config=_enabled_config(max_targets_per_frame=1),
    )

    assert rows == []
