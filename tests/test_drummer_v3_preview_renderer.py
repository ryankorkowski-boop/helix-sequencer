from __future__ import annotations

from pathlib import Path

from helix.preview.drummer_v3 import (
    DRUMMER_V3_MODEL,
    POSE_TO_LAYER,
    active_events,
    build_render_event,
    pose_for_drum_type,
    submodels_for_pose,
    validate_asset_contract,
)


def test_drum_types_resolve_to_authored_v3_poses() -> None:
    assert pose_for_drum_type("kick") == "kick_hit"
    assert pose_for_drum_type("snare") == "snare_hit"
    assert pose_for_drum_type("hihat") == "hi_hat_pulse"
    assert pose_for_drum_type("tom", index=0) == "left_tom_hit"
    assert pose_for_drum_type("tom", index=1) == "right_tom_hit"
    assert pose_for_drum_type("cymbal", index=0) == "left_crash"
    assert pose_for_drum_type("cymbal", index=1) == "right_crash"
    assert pose_for_drum_type("cymbal", index=2) == "both_crash"


def test_each_pose_has_an_authored_layer() -> None:
    assert set(POSE_TO_LAYER) == {
        "idle_ready",
        "kick_hit",
        "snare_hit",
        "hi_hat_pulse",
        "left_tom_hit",
        "right_tom_hit",
        "left_crash",
        "right_crash",
        "both_crash",
    }
    assert all(name.endswith(".png") for name in POSE_TO_LAYER.values())


def test_build_render_event_exposes_real_xmodel_submodel_target() -> None:
    event = build_render_event(
        timestamp_ms=1200,
        drum_type="snare",
        velocity=0.82,
    )

    assert event.pose == "snare_hit"
    assert event.timestamp_ms == 1200
    assert event.end_ms == 1350
    assert event.intensity == 0.82
    assert event.submodels == ("HX_SNOWMAN_DRUMMER_V3_HIT_SNARE",)
    assert DRUMMER_V3_MODEL == "HX_SNOWMAN_DRUMMER_V3"


def test_active_events_respects_hit_window() -> None:
    event = build_render_event(timestamp_ms=1000, drum_type="kick", velocity=1.0)

    assert active_events([event], 999) == []
    assert active_events([event], 1000) == [event]
    assert active_events([event], 1149) == [event]
    assert active_events([event], 1150) == []


def test_v3_assets_are_present_in_repo_checkout() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    missing = validate_asset_contract(repo_root)

    assert not missing, f"Missing authored Drummer V3 assets: {missing}"


def test_submodel_mapping_matches_pose_identity() -> None:
    assert submodels_for_pose("kick_hit") == ("HX_SNOWMAN_DRUMMER_V3_HIT_KICK",)
    assert submodels_for_pose("hi_hat_pulse") == ("HX_SNOWMAN_DRUMMER_V3_HIT_HIHAT",)
    assert submodels_for_pose("both_crash") == (
        "HX_SNOWMAN_DRUMMER_V3_HIT_LEFT_CRASH",
        "HX_SNOWMAN_DRUMMER_V3_HIT_RIGHT_CRASH",
    )
