from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from audio.drum_classification import DRUM_STREAM_KEYS, DrumEvent, empty_drum_streams, stream_key_for_type

DRUM_SUBMODEL_BY_TYPE = {"kick": "kick", "snare": "snare", "tom": "tom", "hihat": "hi_hat", "cymbal": "cymbal", "drum_bus": "drum_bus"}
DRUM_PRIORITY = {"kick": 0, "snare": 1, "cymbal": 2, "tom": 3, "hihat": 4, "drum_bus": 5}
DRUMMER_V3_MODEL = "HX_SNOWMAN_DRUMMER_V3"
DRUMMER_COMPONENTS = (
    "HX_SNOWMAN_DRUMMER_KICK", "HX_SNOWMAN_DRUMMER_SNARE", "HX_SNOWMAN_DRUMMER_HI_HAT",
    "HX_SNOWMAN_DRUMMER_TOM_HIGH", "HX_SNOWMAN_DRUMMER_TOM_MID", "HX_SNOWMAN_DRUMMER_TOM_FLOOR",
    "HX_SNOWMAN_DRUMMER_CYMBAL_LEFT", "HX_SNOWMAN_DRUMMER_CYMBAL_RIGHT",
)
TOM_COMPONENT_BY_CLASS = {"high": "HX_SNOWMAN_DRUMMER_TOM_HIGH", "mid": "HX_SNOWMAN_DRUMMER_TOM_MID", "floor": "HX_SNOWMAN_DRUMMER_TOM_FLOOR"}
DRUMMER_V3_POSE_BY_TYPE = {"kick": "kick_hit", "snare": "snare_hit", "hihat": "hi_hat_pulse", "tom": "tom_hit", "cymbal": "cymbal_hit", "drum_bus": "downbeat_impact"}
DRUMMER_V3_DURATION_BY_POSE = {"kick_hit": 150, "snare_hit": 125, "hi_hat_pulse": 80, "tom_hit": 155, "cymbal_hit": 320, "downbeat_impact": 220}

@dataclass(frozen=True)
class DrumMappingConfig:
    merge_window_ms: int = 24
    clutter_window_ms: int = 70
    max_hits_per_window: int = 4
    rapid_repeat_window_ms: int = 90
    fallback_distribution_seed: int = 414


def flatten_drum_streams(streams: dict[str, list[DrumEvent]]) -> list[DrumEvent]:
    events: list[DrumEvent] = []
    for key in DRUM_STREAM_KEYS: events.extend(streams.get(key, []))
    return sorted(events, key=lambda event: (event.timestamp_ms, DRUM_PRIORITY.get(event.drum_type, 9), -event.velocity))


def build_streams_from_legacy(kicks: Iterable[int], snares: Iterable[int], hats: Iterable[int], cymbals: Iterable[int] = ()) -> dict[str, list[DrumEvent]]:
    streams = empty_drum_streams()
    for drum_type, marks, velocity in (("kick", kicks, .78), ("snare", snares, .68), ("hihat", hats, .42), ("cymbal", cymbals, .62)):
        for idx, mark in enumerate(sorted(set(int(v) for v in marks))):
            streams[stream_key_for_type(drum_type)].append(DrumEvent(timestamp=round(mark / 1000.0, 4), velocity=velocity, confidence=.48, frequency_band_info={"legacy_ms": float(mark)}, cluster_id=idx, drum_type=drum_type, source="legacy_drum_marks"))
    return streams


def distribute_drum_bus_events(events: Iterable[DrumEvent]) -> list[DrumEvent]:
    pattern = ("kick", "hihat", "snare", "hihat", "tom", "cymbal", "snare", "hihat")
    return [DrumEvent(timestamp=e.timestamp, velocity=e.velocity, confidence=round(max(.22, e.confidence * .72), 3), frequency_band_info={**e.frequency_band_info, "fallback_from_bus": 1.0}, cluster_id=e.cluster_id, drum_type=pattern[i % len(pattern)], source="drum_bus_probabilistic_fallback") for i, e in enumerate(sorted(events, key=lambda item: item.timestamp_ms))]


def schedule_drum_events(events: Iterable[DrumEvent], config: DrumMappingConfig = DrumMappingConfig()) -> list[DrumEvent]:
    sorted_events = sorted(events, key=lambda event: (event.timestamp_ms, DRUM_PRIORITY.get(event.drum_type, 9), -event.velocity))
    merged: list[DrumEvent] = []
    for event in sorted_events:
        if merged and event.drum_type == merged[-1].drum_type and event.timestamp_ms - merged[-1].timestamp_ms <= config.merge_window_ms:
            prev = merged[-1]; merged[-1] = event if (event.velocity, event.confidence) > (prev.velocity, prev.confidence) else prev; continue
        merged.append(event)
    scheduled: list[DrumEvent] = []; last_by_type: dict[str, DrumEvent] = {}
    for event in merged:
        nearby = [item for item in scheduled if 0 <= event.timestamp_ms - item.timestamp_ms <= config.clutter_window_ms]
        if len(nearby) >= config.max_hits_per_window:
            worst = max(nearby, key=lambda item: (DRUM_PRIORITY.get(item.drum_type, 9), -item.velocity))
            if (DRUM_PRIORITY.get(event.drum_type, 9), -event.velocity) >= (DRUM_PRIORITY.get(worst.drum_type, 9), -worst.velocity): continue
            scheduled.remove(worst)
        previous = last_by_type.get(event.drum_type)
        if previous and event.timestamp_ms - previous.timestamp_ms <= config.rapid_repeat_window_ms:
            event = DrumEvent(timestamp=event.timestamp, velocity=round(max(.08, event.velocity * .74), 3), confidence=event.confidence, frequency_band_info={**event.frequency_band_info, "rapid_repeat_scale": .74}, cluster_id=event.cluster_id, drum_type=event.drum_type, source=event.source)
        scheduled.append(event); last_by_type[event.drum_type] = event
    return sorted(scheduled, key=lambda event: (event.timestamp_ms, DRUM_PRIORITY.get(event.drum_type, 9)))


def tom_class_for_event(event: DrumEvent, event_index: int = 0) -> str:
    """Resolve an explicitly classified tom to the canonical three-tom ground truth."""
    info = event.frequency_band_info or {}
    raw = str(info.get("tom_class", info.get("tom_position", ""))).strip().lower()
    aliases = {"high_tom": "high", "hi": "high", "upper": "high", "mid_tom": "mid", "middle": "mid", "medium": "mid", "floor_tom": "floor", "low": "floor"}
    if raw in aliases: raw = aliases[raw]
    if raw in TOM_COMPONENT_BY_CLASS: return raw
    return ("high", "mid", "floor")[event_index % 3]


def drummer_component_for_event(event: DrumEvent, *, event_index: int = 0) -> str:
    if event.drum_type == "kick": return DRUMMER_COMPONENTS[0]
    if event.drum_type == "snare": return DRUMMER_COMPONENTS[1]
    if event.drum_type == "hihat": return DRUMMER_COMPONENTS[2]
    if event.drum_type == "tom": return TOM_COMPONENT_BY_CLASS[tom_class_for_event(event, event_index)]
    if event.drum_type == "cymbal": return DRUMMER_COMPONENTS[6 + (event_index % 2)]
    return DRUMMER_COMPONENTS[0]


def map_events_to_drummer_components(events: Iterable[DrumEvent]) -> list[dict[str, object]]:
    mapped: list[dict[str, object]] = []; tom_index = cymbal_index = 0
    for event in sorted(events, key=lambda item: (item.timestamp_ms, DRUM_PRIORITY.get(item.drum_type, 9), -item.velocity)):
        if event.drum_type == "tom": component = drummer_component_for_event(event, event_index=tom_index); tom_index += 1
        elif event.drum_type == "cymbal": component = drummer_component_for_event(event, event_index=cymbal_index); cymbal_index += 1
        else: component = drummer_component_for_event(event)
        pose = DRUMMER_V3_POSE_BY_TYPE.get(event.drum_type, "downbeat_impact")
        mapped.append({"timestamp_ms": event.timestamp_ms, "end_ms": event.timestamp_ms + DRUMMER_V3_DURATION_BY_POSE.get(pose, 140), "model": DRUMMER_V3_MODEL, "drum_type": event.drum_type, "component": component, "tom_class": tom_class_for_event(event, tom_index - 1) if event.drum_type == "tom" else None, "intensity": round(event.velocity, 3), "confidence": event.confidence, "source": event.source})
    return mapped


def drummer_v3_pose_for_event(event: DrumEvent, event_index: int = 0) -> str: return DRUMMER_V3_POSE_BY_TYPE.get(event.drum_type, "downbeat_impact")


def map_events_to_drummer_v3_poses(events: Iterable[DrumEvent]) -> list[dict[str, object]]:
    return [{**item, "pose": DRUMMER_V3_POSE_BY_TYPE.get(str(item["drum_type"]), "downbeat_impact"), "submodels": [item["component"]]} for item in map_events_to_drummer_components(events)]


def map_events_to_submodels(events: Iterable[DrumEvent]) -> list[dict[str, object]]:
    return [{"timestamp_ms": e.timestamp_ms, "drum_type": e.drum_type, "submodel": DRUM_SUBMODEL_BY_TYPE.get(e.drum_type, "drum_bus"), "velocity": e.velocity, "confidence": e.confidence, "frequency_band_info": e.frequency_band_info, "cluster_id": e.cluster_id, "source": e.source} for e in events]


def resolve_drum_streams(streams: dict[str, list[DrumEvent]] | None, *, fallback_kicks: Iterable[int] = (), fallback_snares: Iterable[int] = (), fallback_hats: Iterable[int] = (), fallback_cymbals: Iterable[int] = (), config: DrumMappingConfig = DrumMappingConfig()) -> dict[str, object]:
    streams = streams or empty_drum_streams(); typed_count = sum(len(streams.get(key, [])) for key in DRUM_STREAM_KEYS if key != "drum_bus_events"); bus_events = list(streams.get("drum_bus_events", []))
    if typed_count == 0 and bus_events: events = distribute_drum_bus_events(bus_events); fallback_mode = "drum_bus_distribution"
    elif typed_count == 0: events = flatten_drum_streams(build_streams_from_legacy(fallback_kicks, fallback_snares, fallback_hats, fallback_cymbals)); fallback_mode = "legacy_marks"
    else:
        events = flatten_drum_streams(streams); fallback_mode = "typed_detection"
        if bus_events and typed_count < max(2, len(bus_events) // 2): events.extend(distribute_drum_bus_events(bus_events)); fallback_mode = "partial_detection_plus_bus"
    scheduled = schedule_drum_events(events, config)
    return {"fallback_mode": fallback_mode, "events": scheduled, "mapped_events": map_events_to_submodels(scheduled), "drummer_v3_pose_events": map_events_to_drummer_v3_poses(scheduled), "drummer_component_events": map_events_to_drummer_components(scheduled), "counts": {key: len([event for event in scheduled if stream_key_for_type(event.drum_type) == key]) for key in DRUM_STREAM_KEYS}}
