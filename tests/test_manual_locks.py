import pytest

from tools.build_helpers.manual_locks import (
    ManualLockError,
    locks_overlap,
    locks_touch_at_boundary,
    parse_manual_lock_file,
)


def _sample_lock_file():
    return {
        "version": "0.1",
        "sequence_id": "song_02",
        "sequence_plan_ref": "sequence_plan.json",
        "source_audio_ref": "2.wav",
        "fps": 40,
        "timebase": "ms",
        "defaults": {
            "mode": "protect",
            "strength": "hard",
            "padding_before_ms": 100,
            "padding_after_ms": 120,
        },
        "locks": [
            {
                "id": "lock_chorus_burst_01",
                "label": "Manual whole-house chorus burst",
                "enabled": True,
                "origin": "manual",
                "scope": "cue",
                "anchor": {
                    "type": "cue_ref",
                    "cue_id": "cue_manual_034",
                    "fallback_interval": {"start_ms": 42000, "end_ms": 43200},
                },
                "selector": {
                    "groups": ["whole_house"],
                    "layers": ["base"],
                    "effect_ids": ["cue_manual_034"],
                },
                "freeze": ["occupancy", "timing", "targeting", "payload"],
                "policy": {
                    "mode": "protect",
                    "strength": "hard",
                    "padding_before_ms": 120,
                    "padding_after_ms": 180,
                    "require_user_consent": False,
                },
                "notes": "Keep the hand-placed burst exactly as authored.",
            },
            {
                "id": "lock_singer_phrase_01",
                "label": "Protect singer lane during lyric phrase",
                "enabled": True,
                "origin": "manual",
                "scope": "group",
                "anchor": {
                    "type": "time_range",
                    "start_ms": 55300,
                    "end_ms": 58800,
                },
                "selector": {
                    "groups": ["snowman_singer"],
                    "layers": ["base"],
                },
                "freeze": ["occupancy"],
                "policy": {
                    "mode": "trim",
                    "strength": "hard",
                    "padding_before_ms": 80,
                    "padding_after_ms": 80,
                    "min_remaining_ms": 250,
                    "require_user_consent": False,
                },
            },
        ],
    }


def test_parse_manual_lock_file_accepts_sample_contract():
    lock_file = parse_manual_lock_file(_sample_lock_file())

    assert lock_file.version == "0.1"
    assert lock_file.sequence_id == "song_02"
    assert len(lock_file.locks) == 2
    assert lock_file.summary()["enabled"] == 2
    assert lock_file.summary()["protect"] == 1
    assert lock_file.summary()["trim"] == 1


def test_lock_shadow_window_applies_padding_to_fallback_interval():
    lock_file = parse_manual_lock_file(_sample_lock_file())
    first = lock_file.locks[0]

    assert first.resolved_shadow_window == (41880, 43380)


def test_half_open_touching_edges_do_not_overlap():
    raw = _sample_lock_file()
    raw["locks"] = [
        {
            "id": "left",
            "label": "Left",
            "enabled": True,
            "scope": "time_range",
            "anchor": {"type": "time_range", "start_ms": 1000, "end_ms": 2000},
            "selector": {"groups": ["roofline"]},
            "policy": {"mode": "protect", "strength": "hard"},
        },
        {
            "id": "right",
            "label": "Right",
            "enabled": True,
            "scope": "time_range",
            "anchor": {"type": "time_range", "start_ms": 2000, "end_ms": 3000},
            "selector": {"groups": ["roofline"]},
            "policy": {"mode": "protect", "strength": "hard"},
        },
    ]
    lock_file = parse_manual_lock_file(raw)

    assert locks_touch_at_boundary(lock_file.locks[0], lock_file.locks[1]) is True
    assert locks_overlap(lock_file.locks[0], lock_file.locks[1]) is False


def test_overlapping_shadow_windows_are_detected():
    raw = _sample_lock_file()
    raw["locks"] = [
        {
            "id": "left",
            "label": "Left",
            "enabled": True,
            "scope": "time_range",
            "anchor": {"type": "time_range", "start_ms": 1000, "end_ms": 2100},
            "selector": {"groups": ["roofline"]},
            "policy": {"mode": "protect", "strength": "hard"},
        },
        {
            "id": "right",
            "label": "Right",
            "enabled": True,
            "scope": "time_range",
            "anchor": {"type": "time_range", "start_ms": 2000, "end_ms": 3000},
            "selector": {"groups": ["roofline"]},
            "policy": {"mode": "protect", "strength": "hard"},
        },
    ]
    lock_file = parse_manual_lock_file(raw)

    assert locks_overlap(lock_file.locks[0], lock_file.locks[1]) is True


def test_duplicate_lock_ids_raise_error():
    raw = _sample_lock_file()
    raw["locks"][1]["id"] = raw["locks"][0]["id"]

    with pytest.raises(ManualLockError, match="Duplicate lock ids"):
        parse_manual_lock_file(raw)


def test_override_requires_user_consent():
    raw = _sample_lock_file()
    raw["locks"] = [
        {
            "id": "override_without_consent",
            "label": "Unsafe override",
            "enabled": True,
            "scope": "time_range",
            "anchor": {"type": "time_range", "start_ms": 1000, "end_ms": 2000},
            "selector": {"groups": ["mega_tree"]},
            "policy": {"mode": "override", "strength": "hard", "require_user_consent": False},
        }
    ]

    with pytest.raises(ManualLockError, match="override locks must require user consent"):
        parse_manual_lock_file(raw)


def test_selector_requires_target():
    raw = _sample_lock_file()
    raw["locks"] = [
        {
            "id": "bad_selector",
            "label": "Bad selector",
            "enabled": True,
            "scope": "time_range",
            "anchor": {"type": "time_range", "start_ms": 1000, "end_ms": 2000},
            "selector": {},
            "policy": {"mode": "protect", "strength": "hard"},
        }
    ]

    with pytest.raises(ManualLockError, match="lock selector must target"):
        parse_manual_lock_file(raw)


def test_invalid_interval_raises_error():
    raw = _sample_lock_file()
    raw["locks"][0]["anchor"] = {"type": "time_range", "start_ms": 2000, "end_ms": 1000}

    with pytest.raises(ManualLockError, match="end_ms > start_ms"):
        parse_manual_lock_file(raw)
