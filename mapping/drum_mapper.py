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
DRUMMER_TYPED_HITS = frozenset({"kick", "snare", "hihat", "tom", "cymbal"})

# Canonical sequenced drummer hit composites. These are the only production
# sequencing targets. Contact geometry is embedded in each composite:
# kick = drum only, hi-hat = cymbal + foot/pedal, all other struck instruments
# = instrument + the appropriate arm/stick.
DRUMMER_COMPONENTS = (
    "HX_SNOWMAN_DRUMMER_HIT_KICK",
    "HX_SNOWMAN_DRUMMER_HIT_SNARE",
    "HX_SNOWMAN_DRUMMER_HIT_HI_HAT",
    "HX_SNOWMAN_DRUMMER_HIT_TOM_LEFT",
    "HX_SNOWMAN_DRUMMER_HIT_TOM_RIGHT",
    "HX_SNOWMAN_DRUMMER_HIT_TOM_FLOOR",
    "HX_SNOWMAN_DRUMMER_HIT_CYMBAL_LEFT",
    "HX_SNOWMAN_DRUMMER_HIT_CYMBAL_RIGHT",
)

DRUMMER_POSE_BY_COMPONENT = {
    "HX_SNOWMAN_DRUMMER_HIT_KICK": "kick_hit",
    "HX_SNOWMAN_DRUMMER_HIT_SNARE": "snare_hit",
    "HX_SNOWMAN_DRUMMER_HIT_HI_HAT": "hi_hat_pulse",
    "HX_SNOWMAN_DRUMMER_HIT_TOM_LEFT": "left_tom_hit",
    "HX_SNOWMAN_DRUMMER_HIT_TOM_RIGHT": "right_tom_hit",
    "HX_SNOWMAN_DRUMMER_HIT_TOM_FLOOR": "floor_tom_hit",
    "HX_SNOWMAN_DRUMMER_HIT_CYMBAL_LEFT": "left_crash",
    "HX_SNOWMAN_DRUMMER_HIT_CYMBAL_RIGHT": "right_crash",
}

DRUMMER_V3_POSE_BY_TYPE = {
    "kick": "kick_hit",
    "snare": "snare_hit",
    "hihat": "hi_hat_pulse",
    "tom": "left_tom_hit",
    "cymbal": "left_crash",
    "drum_bus": "downbeat_impact",
}

DRUMMER_V3_SUBMODELS_BY_POSE = {
    "idle_ready": (),
    "kick_hit": ("HX_SNOWMAN_DRUMMER_HIT_KICK",),
    "snare_hit": ("HX_SNOWMAN_DRUMMER_HIT_SNARE",),
    "hi_hat_pulse": ("HX_SNOWMAN_DRUMMER_HIT_HI_HAT",),
    "left_tom_hit": ("HX_SNOWMAN_DRUMMER_HIT_TOM_LEFT",),
    "right_tom_hit": ("HX_SNOWMAN_DRUMMER_HIT_TOM_RIGHT",),
    "floor_tom_hit": ("HX_SNOWMAN_DRUMMER_HIT_TOM_FLOOR",),
    "left_crash": ("HX_SNOWMAN_DRUMMER_HIT_CYMBAL_LEFT",),
    "right_crash": ("HX_SNOWMAN_DRUMMER_HIT_CYMBAL_RIGHT",),
    "downbeat_impact": (
        "HX_SNOWMAN_DRUMMER_HIT_KICK",
        "HX_SNOWMAN_DRUMMER_HIT_SNARE",
        "HX_SNOWMAN_DRUMMER_HIT_CYMBAL_LEFT",
    ),
}

DRUMMER_V3_DURATION_BY_POSE = {
    "kick_hit": 150,
    "snare_hit": 125,
    "hi_hat_pulse": 80,
    "left_tom_hit": 155,
    "right_tom_hit": 155,
    "floor_tom_hit": 175,
    "left_crash": 320,
    "right_crash": 320,
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


def map_events_to_submodels(events: Iterable[DrumEvent]) -> list[dict[str, object]]:
    mapped = []
    for event in events:
        submodel = DRUM_SUBMODEL_BY_TYPE.get(event.drum_type, "drum_bus")
        mapped.append({"timestamp_ms": event.timestamp_ms, "drum_type": event.drum_type, "submodel": submodel, "composite_submodels": ["drumkit_all", "drum_bus" if event.drum_type == "drum_bus" else submodel], "velocity": event.velocity, "confidence": event.confidence, "frequency_band_info": event.frequency_band_info, "cluster_id": event.cluster_id, "source": event.source})
    return mapped


def drummer_component_for_event(event: DrumEvent, *, event_index: int = 0) -> str:
    """Return one approved physical hit composite for a detected drum event.

    Generic toms rotate left -> right -> floor. Cymbals alternate left/right.
    Kick contains no stick; hi-hat contains pedal/foot geometry instead of a
    stick; every other struck drum/cymbal includes its appropriate arm/stick.
    """
    if event.drum_type == "kick":
        return DRUMMER_COMPONENTS[0]
    if event.drum_type == "snare":
        return DRUMMER_COMPONENTS[1]
    if event.drum_type == "hihat":
        return DRUMMER_COMPONENTS[2]
    if event.drum_type == "tom":
        return DRUMMER_COMPONENTS[3 + (event_index % 3)]
    if event.drum_type == "cymbal":
        return DRUMMER_COMPONENTS[6 + (event_index % 2)]
    raise ValueError(f"Unsupported drummer hit type: {event.drum_type!r}")


def map_events_to_drummer_components(events: Iterable[DrumEvent]) -> list[dict[str, object]]:
    """Map detected events to the approved eight-hit drummer contract."""
    mapped: list[dict[str, object]] = []
    tom_index = 0
    cymbal_index = 0
    for event in sorted(events, key=lambda item: (item.timestamp_ms, DRUM_PRIORITY.get(item.drum_type, 9), -item.velocity)):
        # Ambiguous drum_bus events are analysis evidence, not a physical hit.
        # Suppress them defensively here as well as in resolve_drum_streams() so
        # direct mapper callers can never turn uncertainty into a fake kick.
        if event.drum_type not in DRUMMER_TYPED_HITS:
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
            "end_ms": event.timestamp_ms + DRUMMER_V3_DURATION_BY_POSE.get(DRUMMER_POSE_BY_COMPONENT.get(component, "kick_hit"), 140),
            "model": DRUMMER_V3_MODEL,
            "drum_type": event.drum_type,
            "component": component,
            "intensity": round(event.velocity, 3),
            "confidence": event.confidence,
            "source": event.source,
        })
    return mapped


def drummer_v3_pose_for_event(event: DrumEvent, event_index: int = 0) -> str:
    component = drummer_component_for_event(event, event_index=event_index)
    return DRUMMER_POSE_BY_COMPONENT.get(component, "downbeat_impact")


def map_events_to_drummer_v3_poses(events: Iterable[DrumEvent]) -> list[dict[str, object]]:
    mapped: list[dict[str, object]] = []
    component_events = map_events_to_drummer_components(events)
    for item in component_events:
        pose = DRUMMER_POSE_BY_COMPONENT.get(str(item["component"]), "downbeat_impact")
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
    typed_streams = {
        key: list(streams.get(key, []))
        for key in DRUM_STREAM_KEYS
        if key != "drum_bus_events"
    }
    typed_events = flatten_drum_streams({**typed_streams, "drum_bus_events": []})
    typed_count = len(typed_events)
    bus_events = list(streams.get("drum_bus_events", []))

    if typed_count == 0 and bus_events:
        events = distribute_drum_bus_events(bus_events)
        fallback_mode = "drum_bus_distribution"
    elif typed_count == 0:
        events = flatten_drum_streams(
            build_streams_from_legacy(
                fallback_kicks,
                fallback_snares,
                fallback_hats,
                fallback_cymbals,
            )
        )
        fallback_mode = "legacy_marks"
    else:
        # Ambiguous bus events are never scheduled directly. Historically the
        # mapper kept them (which defaulted to kick) and could also add a
        # distributed replacement, double-counting one uncertain onset.
        events = typed_events
        fallback_mode = "typed_detection"
        if bus_events and typed_count < max(2, len(bus_events) // 2):
            events = typed_events + distribute_drum_bus_events(bus_events)
            fallback_mode = "partial_detection_plus_bus"
        elif bus_events:
            fallback_mode = "typed_detection_bus_suppressed"

    scheduled = schedule_drum_events(events, config)
    return {
        "fallback_mode": fallback_mode,
        "events": scheduled,
        "mapped_events": map_events_to_submodels(scheduled),
        "drummer_v3_pose_events": map_events_to_drummer_v3_poses(scheduled),
        "drummer_component_events": map_events_to_drummer_components(scheduled),
        "counts": {
            key: len([event for event in scheduled if stream_key_for_type(event.drum_type) == key])
            for key in DRUM_STREAM_KEYS
        },
        "suppressed_bus_count": len(bus_events) if fallback_mode == "typed_detection_bus_suppressed" else 0,
    }
