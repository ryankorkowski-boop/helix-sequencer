from __future__ import annotations

from audio.drum_classification import DrumEvent, empty_drum_streams
from mapping.drum_mapper import resolve_drum_streams


def _event(timestamp: float, drum_type: str, confidence: float = 0.7) -> DrumEvent:
    return DrumEvent(
        timestamp=timestamp,
        velocity=0.8,
        confidence=confidence,
        frequency_band_info={},
        cluster_id=int(round(timestamp * 1000)),
        drum_type=drum_type,
        source="test",
    )


def test_typed_detection_suppresses_ambiguous_bus_without_fake_kick() -> None:
    streams = empty_drum_streams()
    streams["kick_events"] = [_event(0.10, "kick")]
    streams["snare_events"] = [_event(0.20, "snare")]
    streams["hihat_events"] = [_event(0.30, "hihat")]
    streams["drum_bus_events"] = [_event(0.40, "drum_bus")]

    resolved = resolve_drum_streams(streams)

    assert resolved["fallback_mode"] == "typed_detection_bus_suppressed"
    assert resolved["suppressed_bus_count"] == 1
    assert [event.drum_type for event in resolved["events"]] == ["kick", "snare", "hihat"]
    assert resolved["counts"]["drum_bus_events"] == 0
    assert resolved["counts"]["kick_events"] == 1


def test_partial_detection_distributes_bus_once_not_twice() -> None:
    streams = empty_drum_streams()
    streams["kick_events"] = [_event(0.10, "kick")]
    streams["drum_bus_events"] = [
        _event(0.30, "drum_bus"),
        _event(0.50, "drum_bus"),
        _event(0.70, "drum_bus"),
        _event(0.90, "drum_bus"),
        _event(1.10, "drum_bus"),
        _event(1.30, "drum_bus"),
    ]

    resolved = resolve_drum_streams(streams)

    assert resolved["fallback_mode"] == "partial_detection_plus_bus"
    assert resolved["counts"]["drum_bus_events"] == 0
    assert len(resolved["events"]) <= 1 + len(streams["drum_bus_events"])
    assert all(event.drum_type != "drum_bus" for event in resolved["events"])


def test_all_bus_still_uses_legacy_distribution_fallback() -> None:
    streams = empty_drum_streams()
    streams["drum_bus_events"] = [
        _event(0.10, "drum_bus"),
        _event(0.30, "drum_bus"),
        _event(0.50, "drum_bus"),
    ]

    resolved = resolve_drum_streams(streams)

    assert resolved["fallback_mode"] == "drum_bus_distribution"
    assert resolved["counts"]["drum_bus_events"] == 0
    assert len(resolved["events"]) == 3
    assert all(event.drum_type != "drum_bus" for event in resolved["events"])
