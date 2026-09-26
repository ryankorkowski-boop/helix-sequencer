from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from audio.drum_classification import DRUM_STREAM_KEYS, DrumEvent, empty_drum_streams, stream_key_for_type


DRUM_SUBMODEL_BY_TYPE = {
    "kick": "kick",
    "snare": "snare",
    "tom": "tom",
    "tom_left": "tom_left",
    "tom_right": "tom_right",
    "floor_tom": "floor_tom",
    "hihat": "hi_hat",
    "cymbal": "cymbal",
    "crash": "cymbal_left",
    "ride": "ride",
    "drum_bus": "drum_bus",
}

DRUM_PRIORITY = {"kick": 0, "snare": 1, "cymbal": 2, "crash": 2, "ride": 3, "tom": 4, "tom_left": 4, "tom_right": 4, "floor_tom": 4, "hihat": 5, "drum_bus": 6}
DRUMMER_V3_MODEL = "HX_SNOWMAN_DRUMMER_V3"
DRUMMER_V3_POSE_BY_TYPE = {
    "kick": "kick_hit",
    "snare": "snare_hit",
    "hihat": "hi_hat_pulse",
    "tom": "left_tom_hit",
    "cymbal": "right_crash",
    "drum_bus": "downbeat_impact",
}
DRUMMER_V3_SUBMODELS_BY_POSE = {
    "idle_ready": ("HX_SNOWMAN_DRUMMER_V3_LEFT_ARM_IDLE", "HX_SNOWMAN_DRUMMER_V3_RIGHT_ARM_IDLE"),
    "kick_hit": ("HX_SNOWMAN_DRUMMER_V3_HIT_KICK",),
    "snare_hit": ("HX_SNOWMAN_DRUMMER_V3_HIT_SNARE",),
    "hi_hat_pulse": ("HX_SNOWMAN_DRUMMER_V3_HIT_HIHAT",),
    "left_tom_hit": ("HX_SNOWMAN_DRUMMER_V3_HIT_LEFT_TOM",),
    "right_tom_hit": ("HX_SNOWMAN_DRUMMER_V3_HIT_RIGHT_TOM",),
    "floor_tom_hit": ("HX_SNOWMAN_DRUMMER_V3_HIT_FLOOR_TOM",),
    "ride_hit": ("HX_SNOWMAN_DRUMMER_V3_HIT_RIDE",),
    "left_crash": ("HX_SNOWMAN_DRUMMER_V3_HIT_LEFT_CRASH",),
    "right_crash": ("HX_SNOWMAN_DRUMMER_V3_HIT_RIGHT_CRASH",),
    "both_crash": ("HX_SNOWMAN_DRUMMER_V3_HIT_BOTH_CRASH",),
    "downbeat_impact": ("HX_SNOWMAN_DRUMMER_V3_DOWNBEAT_IMPACT",),
}
DRUMMER_V3_DURATION_BY_POSE = {
    "kick_hit": 150,
    "snare_hit": 125,
    "hi_hat_pulse": 80,
    "left_tom_hit": 155,
    "right_tom_hit": 155,
    "floor_tom_hit": 180,
    "ride_hit": 105,
    "left_crash": 320,
    "right_crash": 320,
    "both_crash": 360,
    "downbeat_impact": 220,
}


@dataclass(frozen=True)
class DrumMappingConfig:
    merge_window_ms: int = 24
    clutter_window_ms: int = 70
    max_hits_per_window: int = 4
    rapid_repeat_window_ms: int = 90
    fallback_distribution_seed: int = 414


def flatten_drum_streams(streams: dict[str, list[DrumEvent]]) -> list[DrumEvent]:
    events: list[DrumEvent] = []
    for key in DRUM_STREAM_KEYS:
        events.extend(streams.get(key, []))
    return sorted(events, key=lambda event: (event.timestamp_ms, DRUM_PRIORITY.get(event.drum_type, 9), -event.velocity))


def build_streams_from_legacy(kicks: Iterable[int], snares: Iterable[int], hats: Iterable[int], cymbals: Iterable[int] = ()) -> dict[str, list[DrumEvent]]:
    streams = empty_drum_streams()
    for drum_type, marks, velocity in (("kick", kicks, 0.78), ("snare", snares, 0.68), ("hihat", hats, 0.42), ("cymbal", cymbals, 0.62)):
        for idx, mark in enumerate(sorted(set(int(value) for value in marks))):
            event = DrumEvent(timestamp=round(mark / 1000.0, 4), velocity=velocity, confidence=0.48, frequency_band_info={"legacy_ms": float(mark)}, cluster_id=idx, drum_type=drum_type, source="legacy_drum_marks")
            streams[stream_key_for_type(drum_type)].append(event)
    return streams


def distribute_drum_bus_events(events: Iterable[DrumEvent]) -> list[DrumEvent]:
    pattern = ("kick", "hihat", "snare", "hihat", "tom", "cymbal", "snare", "hihat")
    return [DrumEvent(timestamp=e.timestamp, velocity=e.velocity, confidence=round(max(0.22, e.confidence * 0.72), 3), frequency_band_info={**e.frequency_band_info, "fallback_from_bus": 1.0}, cluster_id=e.cluster_id, drum_type=pattern[i % len(pattern)], source="drum_bus_probabilistic_fallback") for i, e in enumerate(sorted(events, key=lambda item: item.timestamp_ms))]


def schedule_drum_events(events: Iterable[DrumEvent], config: DrumMappingConfig = DrumMappingConfig()) -> list[DrumEvent]:
    sorted_events = sorted(events, key=lambda event: (event.timestamp_ms, DRUM_PRIORITY.get(event.drum_type, 9), -event.velocity))
    merged: list[DrumEvent] = []
    for event in sorted_events:
        if merged and event.drum_type == merged[-1].drum_type and event.timestamp_ms - merged[-1].timestamp_ms <= config.merge_window_ms:
            prev = merged[-1]
            merged[-1] = event if (event.velocity, event.confidence) > (prev.velocity, prev.confidence) else prev
            continue
        merged.append(event)
    scheduled: list[DrumEvent] = []
    last_by_type: dict[str, DrumEvent] = {}
    for event in merged:
        nearby = [item for item in scheduled if 0 <= event.timestamp_ms - item.timestamp_ms <= config.clutter_window_ms]
        if len(nearby) >= config.max_hits_per_window:
            worst = max(nearby, key=lambda item: (DRUM_PRIORITY.get(item.drum_type, 9), -item.velocity))
            if (DRUM_PRIORITY.get(event.drum_type, 9), -event.velocity) >= (DRUM_PRIORITY.get(worst.drum_type, 9), -worst.velocity):
                continue
            scheduled.remove(worst)
        previous = last_by_type.get(event.drum_type)
        if previous and event.timestamp_ms - previous.timestamp_ms <= config.rapid_repeat_window_ms:
            event = DrumEvent(timestamp=event.timestamp, velocity=round(max(0.08, event.velocity * 0.74), 3), confidence=event.confidence, frequency_band_info={**event.frequency_band_info, "rapid_repeat_scale": 0.74}, cluster_id=event.cluster_id, drum_type=event.drum_type, source=event.source)
        scheduled.append(event)
        last_by_type[event.drum_type] = event
    return sorted(scheduled, key=lambda event: (event.timestamp_ms, DRUM_PRIORITY.get(event.drum_type, 9)))


@dataclass(frozen=True)
class DrummerChoreographyConfig:
    accent_velocity: float = 0.82
    fill_density_threshold: int = 4
    fill_window_ms: int = 420
    max_motion_span_ms: int = 260


def apply_drummer_choreography(
    events: Iterable[DrumEvent],
    config: DrummerChoreographyConfig = DrummerChoreographyConfig(),
) -> list[dict[str, object]]:
    """Annotate scheduled hits with deterministic performer-motion intent.

    This is intentionally separate from XSQ emission. It turns musical hit
    streams into choreography metadata without allocating physical channels
    or changing event timing.
    """
    ordered = sorted(
        events,
        key=lambda event: (
            event.timestamp_ms,
            DRUM_PRIORITY.get(event.drum_type, 9),
            -event.velocity,
        ),
    )
    output: list[dict[str, object]] = []
    for index, event in enumerate(ordered):
        nearby = [
            other
            for other in ordered
            if abs(other.timestamp_ms - event.timestamp_ms) <= config.fill_window_ms
        ]
        density = len(nearby)
        accented = event.velocity >= config.accent_velocity
        fill = density >= config.fill_density_threshold and event.drum_type in {
            "tom", "tom_left", "tom_right", "floor_tom", "snare"
        }

        if event.drum_type == "kick":
            motion = "foot_stomp" if accented else "foot_tap"
        elif event.drum_type == "snare":
            motion = "two_hand_snap" if accented else ("left_snap" if index % 2 == 0 else "right_snap")
        elif event.drum_type == "hihat":
            motion = "right_hand_tight_pulse"
        elif event.drum_type == "ride":
            motion = "right_hand_ride_pattern"
        elif event.drum_type in {"crash", "cymbal"}:
            motion = "both_arm_crash" if accented else "alternating_cymbal_sweep"
        elif event.drum_type in {"tom", "tom_left", "tom_right", "floor_tom"}:
            motion = "traveling_tom_fill" if fill else "single_tom_hit"
        else:
            motion = "full_kit_downbeat" if accented else "kit_idle_accent"

        output.append({
            "timestamp_ms": event.timestamp_ms,
            "drum_type": event.drum_type,
            "motion_profile": motion,
            "accent": accented,
            "fill": fill,
            "local_density": density,
            "velocity": event.velocity,
            "confidence": event.confidence,
            "source": event.source,
            "max_motion_span_ms": config.max_motion_span_ms,
        })
    return output


def map_events_to_submodels(events: Iterable[DrumEvent]) -> list[dict[str, object]]:
    mapped = []
    for event in events:
        submodel = DRUM_SUBMODEL_BY_TYPE.get(event.drum_type, "drum_bus")
        mapped.append({"timestamp_ms": event.timestamp_ms, "drum_type": event.drum_type, "submodel": submodel, "composite_submodels": ["drumkit_all", "drum_bus" if event.drum_type == "drum_bus" else submodel], "velocity": event.velocity, "confidence": event.confidence, "frequency_band_info": event.frequency_band_info, "cluster_id": event.cluster_id, "source": event.source})
    return mapped


def drummer_v3_pose_for_event(event: DrumEvent, event_index: int = 0) -> str:
    drum_type = event.drum_type
    if drum_type == "floor_tom":
        return "floor_tom_hit"
    if drum_type == "tom_left":
        return "left_tom_hit"
    if drum_type == "tom_right":
        return "right_tom_hit"
    if drum_type == "tom":
        return ("left_tom_hit", "right_tom_hit", "floor_tom_hit")[event_index % 3]
    if drum_type == "ride":
        return "ride_hit"
    if drum_type in {"cymbal", "crash"}:
        if event.velocity >= 0.9 and event.confidence >= 0.65:
            return "both_crash"
        return "left_crash" if event_index % 2 else "right_crash"
    return DRUMMER_V3_POSE_BY_TYPE.get(drum_type, "downbeat_impact")


def drummer_hand_for_event(event: DrumEvent, event_index: int = 0) -> str:
    if event.drum_type == "kick":
        return "foot"
    if event.drum_type in {"hihat", "ride"}:
        return "right"
    if event.drum_type in {"crash", "cymbal"}:
        return "right" if event_index % 2 == 0 else "left"
    if event.drum_type in {"floor_tom", "tom_right"}:
        return "right"
    if event.drum_type == "tom_left":
        return "left"
    if event.drum_type == "tom":
        return ("left", "right")[event_index % 2]
    if event.drum_type == "snare":
        return ("left", "right")[event_index % 2]
    return "both"


def map_events_to_drummer_v3_poses(events: Iterable[DrumEvent]) -> list[dict[str, object]]:
    mapped: list[dict[str, object]] = []
    ordered_events = sorted(
        events,
        key=lambda item: (item.timestamp_ms, DRUM_PRIORITY.get(item.drum_type, 9), -item.velocity),
    )
    choreography = apply_drummer_choreography(ordered_events)
    tom_index = 0
    cymbal_index = 0
    snare_index = 0
    for event, motion in zip(ordered_events, choreography):
        if event.drum_type in {"tom", "tom_left", "tom_right", "floor_tom"}:
            hand_index = tom_index
            pose = drummer_v3_pose_for_event(event, tom_index)
            tom_index += 1
        elif event.drum_type in {"cymbal", "crash", "ride"}:
            hand_index = cymbal_index
            pose = drummer_v3_pose_for_event(event, cymbal_index)
            cymbal_index += 1
        else:
            hand_index = snare_index
            pose = drummer_v3_pose_for_event(event, snare_index if event.drum_type == "snare" else 0)
            if event.drum_type == "snare":
                snare_index += 1
        mapped.append({
            "timestamp_ms": event.timestamp_ms,
            "end_ms": event.timestamp_ms + DRUMMER_V3_DURATION_BY_POSE.get(pose, 140),
            "model": DRUMMER_V3_MODEL,
            "drum_type": event.drum_type,
            "pose": pose,
            "hand": drummer_hand_for_event(event, hand_index),
            "submodels": list(DRUMMER_V3_SUBMODELS_BY_POSE[pose]),
            "intensity": round(event.velocity, 3),
            "confidence": event.confidence,
            "source": event.source,
            "motion_profile": motion["motion_profile"],
            "accent": motion["accent"],
            "fill": motion["fill"],
            "local_density": motion["local_density"],
            "max_motion_span_ms": motion["max_motion_span_ms"],
        })
    return mapped


def resolve_drum_streams(streams: dict[str, list[DrumEvent]] | None, *, fallback_kicks: Iterable[int] = (), fallback_snares: Iterable[int] = (), fallback_hats: Iterable[int] = (), fallback_cymbals: Iterable[int] = (), config: DrumMappingConfig = DrumMappingConfig()) -> dict[str, object]:
    streams = streams or empty_drum_streams()
    typed_count = sum(len(streams.get(key, [])) for key in DRUM_STREAM_KEYS if key != "drum_bus_events")
    bus_events = list(streams.get("drum_bus_events", []))
    if typed_count == 0 and bus_events:
        events = distribute_drum_bus_events(bus_events); fallback_mode = "drum_bus_distribution"
    elif typed_count == 0:
        events = flatten_drum_streams(build_streams_from_legacy(fallback_kicks, fallback_snares, fallback_hats, fallback_cymbals)); fallback_mode = "legacy_marks"
    else:
        events = flatten_drum_streams(streams); fallback_mode = "typed_detection"
        if bus_events and typed_count < max(2, len(bus_events) // 2):
            events.extend(distribute_drum_bus_events(bus_events)); fallback_mode = "partial_detection_plus_bus"
    scheduled = schedule_drum_events(events, config)
    return {"fallback_mode": fallback_mode, "events": scheduled, "mapped_events": map_events_to_submodels(scheduled), "drummer_v3_pose_events": map_events_to_drummer_v3_poses(scheduled), "counts": {key: len([event for event in scheduled if stream_key_for_type(event.drum_type) == key]) for key in DRUM_STREAM_KEYS}}


def normalized_events_to_drum_streams(events: Iterable[object]) -> dict[str, list[DrumEvent]]:
    """Adapt normalized MusicalEvent objects into the existing drummer input contract."""
    streams = empty_drum_streams()
    for index, event in enumerate(events):
        kind = str(getattr(event, "instrument", None) or getattr(event, "kind", "drum_bus"))
        kind = kind.removeprefix("drum_").removeprefix("stem_drum_")
        if kind in {"hi_hat", "hat", "hat_closed", "hat_open"}:
            kind = "hihat"
        if kind in {"crash", "crash_cymbal"}:
            kind = "crash"
        if kind in {"floor", "floor_tom", "low_tom"}:
            kind = "floor_tom"
        if kind in {"left_tom", "tom_left"}:
            kind = "tom_left"
        if kind in {"right_tom", "tom_right"}:
            kind = "tom_right"
        if kind in {"ride_cymbal"}:
            kind = "ride"
        if kind not in {"kick", "snare", "tom", "tom_left", "tom_right", "floor_tom", "hihat", "cymbal", "crash", "ride"}:
            continue
        confidence = max(0.0, min(1.0, float(getattr(event, "confidence", 0.0))))
        velocity = max(0.0, min(1.0, float(getattr(event, "strength", confidence))))
        raw = DrumEvent(
            timestamp=max(0.0, float(getattr(event, "time_ms", 0)) / 1000.0),
            velocity=velocity,
            confidence=confidence,
            frequency_band_info={"normalized_event": 1.0},
            cluster_id=index,
            drum_type=kind,
            source=str(getattr(event, "source", "helix.drum_fusion")),
        )
        streams[stream_key_for_type(kind)].append(raw)
    return streams
