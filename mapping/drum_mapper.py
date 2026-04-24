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
    for drum_type, marks, velocity in (
        ("kick", kicks, 0.78),
        ("snare", snares, 0.68),
        ("hihat", hats, 0.42),
        ("cymbal", cymbals, 0.62),
    ):
        for idx, mark in enumerate(sorted(set(int(value) for value in marks))):
            event = DrumEvent(
                timestamp=round(mark / 1000.0, 4),
                velocity=velocity,
                confidence=0.48,
                frequency_band_info={"legacy_ms": float(mark)},
                cluster_id=idx,
                drum_type=drum_type,
                source="legacy_drum_marks",
            )
            streams[stream_key_for_type(drum_type)].append(event)
    return streams


def distribute_drum_bus_events(events: Iterable[DrumEvent]) -> list[DrumEvent]:
    pattern = ("kick", "hihat", "snare", "hihat", "tom", "cymbal", "snare", "hihat")
    out: list[DrumEvent] = []
    for idx, event in enumerate(sorted(events, key=lambda item: item.timestamp_ms)):
        drum_type = pattern[idx % len(pattern)]
        out.append(
            DrumEvent(
                timestamp=event.timestamp,
                velocity=event.velocity,
                confidence=round(max(0.22, event.confidence * 0.72), 3),
                frequency_band_info={**event.frequency_band_info, "fallback_from_bus": 1.0},
                cluster_id=event.cluster_id,
                drum_type=drum_type,
                source="drum_bus_probabilistic_fallback",
            )
        )
    return out


def schedule_drum_events(events: Iterable[DrumEvent], config: DrumMappingConfig = DrumMappingConfig()) -> list[DrumEvent]:
    sorted_events = sorted(events, key=lambda event: (event.timestamp_ms, DRUM_PRIORITY.get(event.drum_type, 9), -event.velocity))
    merged: list[DrumEvent] = []
    for event in sorted_events:
        if merged and event.drum_type == merged[-1].drum_type and event.timestamp_ms - merged[-1].timestamp_ms <= config.merge_window_ms:
            prev = merged[-1]
            keep = event if (event.velocity, event.confidence) > (prev.velocity, prev.confidence) else prev
            merged[-1] = keep
            continue
        merged.append(event)

    scheduled: list[DrumEvent] = []
    last_by_type: dict[str, DrumEvent] = {}
    for event in merged:
        nearby = [item for item in scheduled if 0 <= event.timestamp_ms - item.timestamp_ms <= config.clutter_window_ms]
        if len(nearby) >= config.max_hits_per_window:
            worst = max(nearby, key=lambda item: (DRUM_PRIORITY.get(item.drum_type, 9), -item.velocity))
            event_rank = (DRUM_PRIORITY.get(event.drum_type, 9), -event.velocity)
            worst_rank = (DRUM_PRIORITY.get(worst.drum_type, 9), -worst.velocity)
            if event_rank >= worst_rank:
                continue
            scheduled.remove(worst)
        previous = last_by_type.get(event.drum_type)
        if previous and event.timestamp_ms - previous.timestamp_ms <= config.rapid_repeat_window_ms:
            event = DrumEvent(
                timestamp=event.timestamp,
                velocity=round(max(0.08, event.velocity * 0.74), 3),
                confidence=event.confidence,
                frequency_band_info={**event.frequency_band_info, "rapid_repeat_scale": 0.74},
                cluster_id=event.cluster_id,
                drum_type=event.drum_type,
                source=event.source,
            )
        scheduled.append(event)
        last_by_type[event.drum_type] = event
    return sorted(scheduled, key=lambda event: (event.timestamp_ms, DRUM_PRIORITY.get(event.drum_type, 9)))


def map_events_to_submodels(events: Iterable[DrumEvent]) -> list[dict[str, object]]:
    mapped = []
    for event in events:
        submodel = DRUM_SUBMODEL_BY_TYPE.get(event.drum_type, "drum_bus")
        mapped.append(
            {
                "timestamp_ms": event.timestamp_ms,
                "drum_type": event.drum_type,
                "submodel": submodel,
                "composite_submodels": ["drumkit_all", "drum_bus" if event.drum_type == "drum_bus" else submodel],
                "velocity": event.velocity,
                "confidence": event.confidence,
                "frequency_band_info": event.frequency_band_info,
                "cluster_id": event.cluster_id,
                "source": event.source,
            }
        )
    return mapped


def resolve_drum_streams(
    streams: dict[str, list[DrumEvent]] | None,
    *,
    fallback_kicks: Iterable[int] = (),
    fallback_snares: Iterable[int] = (),
    fallback_hats: Iterable[int] = (),
    fallback_cymbals: Iterable[int] = (),
    config: DrumMappingConfig = DrumMappingConfig(),
) -> dict[str, object]:
    streams = streams or empty_drum_streams()
    typed_count = sum(len(streams.get(key, [])) for key in DRUM_STREAM_KEYS if key != "drum_bus_events")
    bus_events = list(streams.get("drum_bus_events", []))
    if typed_count == 0 and bus_events:
        events = distribute_drum_bus_events(bus_events)
        fallback_mode = "drum_bus_distribution"
    elif typed_count == 0:
        legacy = build_streams_from_legacy(fallback_kicks, fallback_snares, fallback_hats, fallback_cymbals)
        events = flatten_drum_streams(legacy)
        fallback_mode = "legacy_marks"
    else:
        events = flatten_drum_streams(streams)
        fallback_mode = "typed_detection"
        if bus_events and typed_count < max(2, len(bus_events) // 2):
            events.extend(distribute_drum_bus_events(bus_events))
            fallback_mode = "partial_detection_plus_bus"
    scheduled = schedule_drum_events(events, config)
    return {
        "fallback_mode": fallback_mode,
        "events": scheduled,
        "mapped_events": map_events_to_submodels(scheduled),
        "counts": {key: len([event for event in scheduled if stream_key_for_type(event.drum_type) == key]) for key in DRUM_STREAM_KEYS},
    }
