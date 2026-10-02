from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from audio.drum_classification import DRUM_STREAM_KEYS, DrumEvent, empty_drum_streams, stream_key_for_type


DRUM_SUBMODEL_BY_TYPE = {
    "kick": "kick",
    "snare": "snare",
    "tom": "tom",
    "hihat": "hi_hat",
    "cymbal": "cymbal",
    "drum_bus": "drum_bus",
}

DRUM_PRIORITY = {"kick": 0, "snare": 1, "cymbal": 2, "tom": 3, "hihat": 4, "drum_bus": 5}
DRUMMER_V3_MODEL = "HX_SNOWMAN_DRUMMER"

# Canonical sequenced drummer components. Arms/sticks remain geometry inside these
# components; they are never independent sequencing channels.
DRUMMER_COMPONENTS = (
    "HX_SNOWMAN_DRUMMER_KICK",
    "HX_SNOWMAN_DRUMMER_SNARE",
    "HX_SNOWMAN_DRUMMER_HI_HAT",
    "HX_SNOWMAN_DRUMMER_TOM_1",
    "HX_SNOWMAN_DRUMMER_TOM_2",
    "HX_SNOWMAN_DRUMMER_TOM_3",
    "HX_SNOWMAN_DRUMMER_TOM_4",
    "HX_SNOWMAN_DRUMMER_CYMBAL_LEFT",
    "HX_SNOWMAN_DRUMMER_CYMBAL_RIGHT",
)

DRUMMER_V3_POSE_BY_TYPE = {
    "kick": "kick_hit",
    "snare": "snare_hit",
    "hihat": "hi_hat_pulse",
    "tom": "tom_hit",
    "cymbal": "cymbal_hit",
    "drum_bus": "downbeat_impact",
}

# Poses resolve to sequenced components only. Contacting-stick geometry is part
# of the target component and must not become a separate target.
DRUMMER_V3_SUBMODELS_BY_POSE = {
    "idle_ready": (),
    "kick_hit": ("HX_SNOWMAN_DRUMMER_KICK",),
    "snare_hit": ("HX_SNOWMAN_DRUMMER_SNARE",),
    "hi_hat_pulse": ("HX_SNOWMAN_DRUMMER_HI_HAT",),
    "tom_hit": ("HX_SNOWMAN_DRUMMER_TOM_1",),
    "cymbal_hit": ("HX_SNOWMAN_DRUMMER_CYMBAL_RIGHT",),
    "downbeat_impact": (
        "HX_SNOWMAN_DRUMMER_KICK",
        "HX_SNOWMAN_DRUMMER_SNARE",
        "HX_SNOWMAN_DRUMMER_CYMBAL_LEFT",
    ),
}

DRUMMER_V3_DURATION_BY_POSE = {
    "kick_hit": 150,
    "snare_hit": 125,
    "hi_hat_pulse": 80,
    "tom_hit": 155,
    "cymbal_hit": 320,
    "downbeat_impact": 220,
}


@dataclass(frozen=True)
class DrumMappingConfig:
    merge_window_ms: int = 24
    clutter_window_ms: int = 70
    max_hits_per_window: int = 6
    rapid_repeat_window_ms: int = 90
    rapid_repeat_velocity_scale: float = 0.82
    fallback_confidence_floor: float = 0.24


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


def infer_drum_bus_type(event: DrumEvent, *, prior_type: str | None = None) -> tuple[str, float]:
    """Infer an uncertain bus hit from measured spectral features; never guess by event index."""
    f = event.frequency_band_info
    low = float(f.get("low_ratio", 0.0))
    mid_low = float(f.get("mid_low_ratio", 0.0))
    mid = float(f.get("mid_ratio", 0.0))
    high = float(f.get("high_ratio", 0.0))
    centroid = float(f.get("centroid_hz", 0.0))
    sharp = float(f.get("transient_sharpness", 0.0))
    decay = float(f.get("decay_profile", 0.0))
    flatness = float(f.get("spectral_flatness", 0.0))
    percussive = float(f.get("percussive_ratio", 0.0))
    scores = {
        "kick": low * 0.60 + max(0.0, 1.0 - centroid / 1400.0) * 0.20 + sharp * 0.20,
        "snare": mid * 0.42 + sharp * 0.30 + mid_low * 0.12,
        "tom": mid_low * 0.48 + max(0.0, 1.0 - abs(centroid - 900.0) / 1800.0) * 0.22 + decay * 0.18 + sharp * 0.12,
        "hihat": high * 0.52 + sharp * 0.18 + (1.0 - decay) * 0.16 + percussive * 0.14,
        "cymbal": high * 0.34 + decay * 0.24 + percussive * 0.22 + flatness * 0.10,
    }
    if prior_type in scores:
        scores[prior_type] += 0.025
    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    best, best_score = ranked[0]
    margin = best_score - ranked[1][1]
    if best_score < 0.34 or margin < 0.10:
        return "drum_bus", round(max(0.18, event.confidence * 0.72), 3)
    return best, round(min(0.88, max(event.confidence * 0.72, best_score * 0.82)), 3)


def distribute_drum_bus_events(events: Iterable[DrumEvent], config: DrumMappingConfig = DrumMappingConfig()) -> list[DrumEvent]:
    """Resolve bus events from their features; unresolved events stay on the bus."""
    resolved: list[DrumEvent] = []
    prior_type: str | None = None
    for event in sorted(events, key=lambda item: item.timestamp_ms):
        drum_type, confidence = infer_drum_bus_type(event, prior_type=prior_type)
        resolved.append(DrumEvent(
            timestamp=event.timestamp,
            velocity=event.velocity,
            confidence=max(config.fallback_confidence_floor, confidence),
            frequency_band_info={**event.frequency_band_info, "bus_inference": 1.0, "inferred_type": drum_type},
            cluster_id=event.cluster_id,
            drum_type=drum_type,
            source="drum_bus_inferred" if drum_type != "drum_bus" else "drum_bus_unresolved",
        ))
        if drum_type != "drum_bus":
            prior_type = drum_type
    return resolved


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
        nearby = [item for item in scheduled if abs(event.timestamp_ms - item.timestamp_ms) <= config.clutter_window_ms]
        if len(nearby) >= config.max_hits_per_window:
            weakest = min(nearby, key=lambda item: (item.confidence, item.velocity))
            if weakest.confidence < event.confidence and weakest.velocity < event.velocity:
                scheduled.remove(weakest)
            else:
                continue
        previous = last_by_type.get(event.drum_type)
        if previous and event.timestamp_ms - previous.timestamp_ms <= config.rapid_repeat_window_ms:
            event = DrumEvent(timestamp=event.timestamp, velocity=round(max(0.08, event.velocity * config.rapid_repeat_velocity_scale), 3), confidence=event.confidence, frequency_band_info={**event.frequency_band_info, "rapid_repeat_scale": config.rapid_repeat_velocity_scale}, cluster_id=event.cluster_id, drum_type=event.drum_type, source=event.source)
        scheduled.append(event)
        last_by_type[event.drum_type] = event
    return sorted(scheduled, key=lambda event: (event.timestamp_ms, DRUM_PRIORITY.get(event.drum_type, 9)))


def map_events_to_submodels(events: Iterable[DrumEvent]) -> list[dict[str, object]]:
    mapped = []
    for event in events:
        # Unresolved bus hits remain available in the source-event/debug path,
        # but must never become a concrete drummer component placement.
        if event.drum_type == "drum_bus":
            continue
        submodel = DRUM_SUBMODEL_BY_TYPE[event.drum_type]
        mapped.append({"timestamp_ms": event.timestamp_ms, "drum_type": event.drum_type, "submodel": submodel, "composite_submodels": ["drumkit_all", "drum_bus" if event.drum_type == "drum_bus" else submodel], "velocity": event.velocity, "confidence": event.confidence, "frequency_band_info": event.frequency_band_info, "cluster_id": event.cluster_id, "source": event.source})
    return mapped


def drummer_component_for_event(event: DrumEvent, *, event_index: int = 0) -> str:
    """Return exactly one canonical nine-component target for a drum event.

    Generic toms rotate deterministically across four tom components. Cymbals
    alternate left/right. No arm or stick target is ever emitted.
    """
    if event.drum_type == "kick":
        return DRUMMER_COMPONENTS[0]
    if event.drum_type == "snare":
        return DRUMMER_COMPONENTS[1]
    if event.drum_type == "hihat":
        return DRUMMER_COMPONENTS[2]
    if event.drum_type == "tom":
        return DRUMMER_COMPONENTS[3 + (event_index % 4)]
    if event.drum_type == "cymbal":
        return DRUMMER_COMPONENTS[7 + (event_index % 2)]
    return ""


def map_events_to_drummer_components(events: Iterable[DrumEvent]) -> list[dict[str, object]]:
    """Map detected events to the canonical nine-component drummer contract."""
    mapped: list[dict[str, object]] = []
    tom_index = 0
    cymbal_index = 0
    for event in sorted(events, key=lambda item: (item.timestamp_ms, DRUM_PRIORITY.get(item.drum_type, 9), -item.velocity)):
        if event.drum_type == "drum_bus":
            continue
        if event.drum_type == "tom":
            component = drummer_component_for_event(event, event_index=tom_index)
            tom_index += 1
        elif event.drum_type == "cymbal":
            component = drummer_component_for_event(event, event_index=cymbal_index)
            cymbal_index += 1
        else:
            component = drummer_component_for_event(event)
        mapped.append({
            "timestamp_ms": event.timestamp_ms,
            "end_ms": event.timestamp_ms + DRUMMER_V3_DURATION_BY_POSE.get(DRUMMER_V3_POSE_BY_TYPE.get(event.drum_type, "kick_hit"), 140),
            "model": DRUMMER_V3_MODEL,
            "drum_type": event.drum_type,
            "component": component,
            "intensity": round(event.velocity, 3),
            "confidence": event.confidence,
            "source": event.source,
        })
    return mapped


def drummer_v3_pose_for_event(event: DrumEvent, event_index: int = 0) -> str:
    return DRUMMER_V3_POSE_BY_TYPE.get(event.drum_type, "downbeat_impact")


def map_events_to_drummer_v3_poses(events: Iterable[DrumEvent]) -> list[dict[str, object]]:
    mapped: list[dict[str, object]] = []
    component_events = map_events_to_drummer_components(events)
    for item in component_events:
        pose = DRUMMER_V3_POSE_BY_TYPE.get(str(item["drum_type"]), "downbeat_impact")
        mapped.append({
            "timestamp_ms": item["timestamp_ms"],
            "end_ms": item["end_ms"],
            "model": DRUMMER_V3_MODEL,
            "drum_type": item["drum_type"],
            "pose": pose,
            "submodels": [item["component"]],
            "component": item["component"],
            "intensity": item["intensity"],
            "confidence": item["confidence"],
            "source": item["source"],
        })
    return mapped


def resolve_drum_streams(streams: dict[str, list[DrumEvent]] | None, *, fallback_kicks: Iterable[int] = (), fallback_snares: Iterable[int] = (), fallback_hats: Iterable[int] = (), fallback_cymbals: Iterable[int] = (), config: DrumMappingConfig = DrumMappingConfig()) -> dict[str, object]:
    streams = streams or empty_drum_streams()
    typed_count = sum(len(streams.get(key, [])) for key in DRUM_STREAM_KEYS if key != "drum_bus_events")
    bus_events = list(streams.get("drum_bus_events", []))
    if typed_count == 0 and bus_events:
        events = distribute_drum_bus_events(bus_events, config); fallback_mode = "drum_bus_inference"
    elif typed_count == 0:
        events = flatten_drum_streams(build_streams_from_legacy(fallback_kicks, fallback_snares, fallback_hats, fallback_cymbals)); fallback_mode = "legacy_marks"
    else:
        events = flatten_drum_streams(streams); fallback_mode = "typed_detection"
        if bus_events and typed_count < max(2, len(bus_events) // 2):
            events.extend(distribute_drum_bus_events(bus_events, config)); fallback_mode = "partial_detection_plus_bus"
    scheduled = schedule_drum_events(events, config)
    return {"fallback_mode": fallback_mode, "events": scheduled, "mapped_events": map_events_to_submodels(scheduled), "drummer_v3_pose_events": map_events_to_drummer_v3_poses(scheduled), "drummer_component_events": map_events_to_drummer_components(scheduled), "counts": {key: len([event for event in scheduled if stream_key_for_type(event.drum_type) == key]) for key in DRUM_STREAM_KEYS}}
