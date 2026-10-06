from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from audio.drum_classification import DRUM_STREAM_KEYS, DrumEvent, empty_drum_streams, stream_key_for_type

DRUM_SUBMODEL_BY_TYPE = {
    "kick": "kick", "snare": "snare", "tom": "tom",
    "hihat": "hi_hat", "cymbal": "cymbal", "drum_bus": "drum_bus",
}
DRUM_PRIORITY = {"kick": 0, "snare": 1, "cymbal": 2, "tom": 3, "hihat": 4, "drum_bus": 5}
DRUMMER_V3_MODEL = "HX_SNOWMAN_DRUMMER_V3"
DRUMMER_COMPONENTS = tuple(
    f"{DRUMMER_V3_MODEL}_{name}"
    for name in ("KICK", "SNARE", "HI_HAT", "TOM_HIGH", "TOM_MID", "TOM_FLOOR", "CYMBAL_LEFT", "CYMBAL_RIGHT")
)
KICK, SNARE, HI_HAT, TOM_HIGH, TOM_MID, TOM_FLOOR, CYMBAL_LEFT, CYMBAL_RIGHT = DRUMMER_COMPONENTS
TOM_COMPONENT_BY_CLASS = {"high": TOM_HIGH, "mid": TOM_MID, "floor": TOM_FLOOR}

# These pose names and durations are the behavioral oracle from b27e8d77.
# The physical output contract is now eight integrated components, but the
# approved timing/pose semantics remain unchanged.
DRUMMER_V3_POSE_BY_TYPE = {
    "kick": "kick_hit",
    "snare": "snare_hit",
    "hihat": "hi_hat_pulse",
    "tom": "right_tom_hit",
    "cymbal": "right_crash",
    "drum_bus": "downbeat_impact",
}
DRUMMER_V3_DURATION_BY_POSE = {
    "kick_hit": 150,
    "snare_hit": 125,
    "hi_hat_pulse": 80,
    "left_tom_hit": 155,
    "right_tom_hit": 155,
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


def build_streams_from_legacy(
    kicks: Iterable[int],
    snares: Iterable[int],
    hats: Iterable[int],
    cymbals: Iterable[int] = (),
) -> dict[str, list[DrumEvent]]:
    streams = empty_drum_streams()
    for drum_type, marks, velocity in (
        ("kick", kicks, .78), ("snare", snares, .68),
        ("hihat", hats, .42), ("cymbal", cymbals, .62),
    ):
        for idx, mark in enumerate(sorted(set(int(v) for v in marks))):
            streams[stream_key_for_type(drum_type)].append(
                DrumEvent(
                    timestamp=round(mark / 1000.0, 4),
                    velocity=velocity,
                    confidence=.48,
                    frequency_band_info={"legacy_ms": float(mark)},
                    cluster_id=idx,
                    drum_type=drum_type,
                    source="legacy_drum_marks",
                )
            )
    return streams


def distribute_drum_bus_events(events: Iterable[DrumEvent]) -> list[DrumEvent]:
    pattern = ("kick", "hihat", "snare", "hihat", "tom", "cymbal", "snare", "hihat")
    return [
        DrumEvent(
            timestamp=e.timestamp,
            velocity=e.velocity,
            confidence=round(max(.22, e.confidence * .72), 3),
            frequency_band_info={**e.frequency_band_info, "fallback_from_bus": 1.0},
            cluster_id=e.cluster_id,
            drum_type=pattern[i % len(pattern)],
            source="drum_bus_probabilistic_fallback",
        )
        for i, e in enumerate(sorted(events, key=lambda item: item.timestamp_ms))
    ]


def schedule_drum_events(
    events: Iterable[DrumEvent],
    config: DrumMappingConfig = DrumMappingConfig(),
) -> list[DrumEvent]:
    # Keep this scheduling contract byte-for-behavior compatible with the
    # b27e8d77 ground truth: merge same-type near-duplicates, retain at most
    # four hits in a 70 ms clutter window, and attenuate rapid repeats.
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
            if (DRUM_PRIORITY.get(event.drum_type, 9), -event.velocity) >= (
                DRUM_PRIORITY.get(worst.drum_type, 9), -worst.velocity
            ):
                continue
            scheduled.remove(worst)
        previous = last_by_type.get(event.drum_type)
        if previous and event.timestamp_ms - previous.timestamp_ms <= config.rapid_repeat_window_ms:
            event = DrumEvent(
                timestamp=event.timestamp,
                velocity=round(max(.08, event.velocity * .74), 3),
                confidence=event.confidence,
                frequency_band_info={**event.frequency_band_info, "rapid_repeat_scale": .74},
                cluster_id=event.cluster_id,
                drum_type=event.drum_type,
                source=event.source,
            )
        scheduled.append(event)
        last_by_type[event.drum_type] = event
    return sorted(scheduled, key=lambda event: (event.timestamp_ms, DRUM_PRIORITY.get(event.drum_type, 9)))


def _explicit_tom_class(event: DrumEvent) -> tuple[str | None, float]:
    info = event.frequency_band_info or {}
    raw = str(info.get("tom_class", info.get("tom_position", ""))).strip().lower()
    aliases = {
        "high_tom": "high", "hi": "high", "upper": "high", "1": "high", "1.0": "high",
        "mid_tom": "mid", "middle": "mid", "medium": "mid", "2": "mid", "2.0": "mid",
        "floor_tom": "floor", "low": "floor", "3": "floor", "3.0": "floor",
    }
    raw = aliases.get(raw, raw)
    if raw not in TOM_COMPONENT_BY_CLASS:
        return None, 0.0
    try:
        confidence = float(info.get("tom_class_confidence", 0.0) or 0.0)
    except (TypeError, ValueError):
        confidence = 0.0
    return raw, max(0.0, min(1.0, confidence))


def tom_class_for_event(event: DrumEvent, event_index: int = 0) -> str:
    explicit, _ = _explicit_tom_class(event)
    if explicit:
        return explicit
    # Three-tom fallback for callers that do not carry subclass evidence.
    return ("high", "mid", "floor")[event_index % 3]


def drummer_v3_pose_for_event(event: DrumEvent, event_index: int = 0) -> str:
    """Return the exact historical b27e8d77 pose semantics."""
    if event.drum_type == "tom":
        return "right_tom_hit" if event_index % 2 == 0 else "left_tom_hit"
    if event.drum_type == "cymbal":
        if event.velocity >= 0.9 and event.confidence >= 0.65:
            return "both_crash"
        # Historical orientation starts on the RIGHT, then alternates LEFT.
        return "left_crash" if event_index % 2 else "right_crash"
    return DRUMMER_V3_POSE_BY_TYPE.get(event.drum_type, "downbeat_impact")


def _tom_floor_selection(ordered: list[DrumEvent]) -> set[int]:
    """Select only strong floor-tom evidence without destroying old L/R logic.

    The approved oracle had two rack-tom poses (RIGHT/LEFT). V3 now has a real
    floor tom too. We keep the oracle's rack alternation and allow at most one
    third of detected toms to move to FLOOR when the new subclass estimator has
    strong evidence. This extends rather than replaces the old behavior.
    """
    toms = [event for event in ordered if event.drum_type == "tom"]
    if len(toms) < 3:
        return set()
    candidates: list[tuple[float, int]] = []
    for idx, event in enumerate(toms):
        klass, confidence = _explicit_tom_class(event)
        if klass == "floor" and confidence >= 0.72:
            candidates.append((confidence, idx))
    quota = max(1, len(toms) // 3)
    candidates.sort(reverse=True)
    return {idx for _, idx in candidates[:quota]}


def _pose_components(
    event: DrumEvent,
    *,
    pose: str,
    tom_index: int = 0,
    floor_selected: bool = False,
) -> tuple[tuple[str, ...], str | None, str | None]:
    if event.drum_type == "kick":
        return (KICK,), None, None
    if event.drum_type == "snare":
        return (SNARE,), None, None
    if event.drum_type == "hihat":
        return (HI_HAT,), None, None
    if event.drum_type == "cymbal":
        if pose == "both_crash":
            return (CYMBAL_LEFT, CYMBAL_RIGHT), None, None
        if pose == "left_crash":
            return (CYMBAL_LEFT,), None, None
        return (CYMBAL_RIGHT,), None, None
    if event.drum_type == "tom":
        if floor_selected:
            return (TOM_FLOOR,), "floor", "spectral_floor_extension"
        if pose == "right_tom_hit":
            return (TOM_HIGH,), "high", "historical_right_tom"
        return (TOM_MID,), "mid", "historical_left_tom"
    if event.drum_type == "drum_bus":
        # Historical DOWNBEAT_IMPACT = body + kick + snare + cymbal + both sticks.
        # The new physical contract integrates the contacting arms/sticks into
        # their hit components, so this is the faithful eight-component form.
        return (KICK, SNARE, CYMBAL_LEFT, CYMBAL_RIGHT), None, "historical_downbeat_impact"
    return (KICK,), None, "unknown_fallback"


def map_events_to_drummer_v3_poses(events: Iterable[DrumEvent]) -> list[dict[str, object]]:
    ordered = sorted(events, key=lambda item: (item.timestamp_ms, DRUM_PRIORITY.get(item.drum_type, 9), -item.velocity))
    floor_indices = _tom_floor_selection(ordered)
    mapped: list[dict[str, object]] = []
    tom_index = 0
    cymbal_index = 0
    for event in ordered:
        if event.drum_type == "tom":
            pose = drummer_v3_pose_for_event(event, tom_index)
            components, tom_class, tom_class_source = _pose_components(
                event, pose=pose, tom_index=tom_index, floor_selected=tom_index in floor_indices
            )
            tom_index += 1
        elif event.drum_type == "cymbal":
            pose = drummer_v3_pose_for_event(event, cymbal_index)
            components, tom_class, tom_class_source = _pose_components(event, pose=pose)
            cymbal_index += 1
        else:
            pose = drummer_v3_pose_for_event(event, 0)
            components, tom_class, tom_class_source = _pose_components(event, pose=pose)

        mapped.append({
            "timestamp_ms": event.timestamp_ms,
            "end_ms": event.timestamp_ms + DRUMMER_V3_DURATION_BY_POSE.get(pose, 140),
            "model": DRUMMER_V3_MODEL,
            "drum_type": event.drum_type,
            "pose": pose,
            "submodels": list(components),
            "components": list(components),
            "tom_class": tom_class,
            "tom_class_source": tom_class_source,
            "intensity": round(event.velocity, 3),
            "confidence": event.confidence,
            "source": event.source,
        })
    return mapped


def map_events_to_drummer_components(events: Iterable[DrumEvent]) -> list[dict[str, object]]:
    """Flatten pose events into physical component placements."""
    placements: list[dict[str, object]] = []
    for event in map_events_to_drummer_v3_poses(events):
        for component in event["components"]:
            placements.append({**event, "component": component})
    return placements


def drummer_component_for_event(event: DrumEvent, *, event_index: int = 0) -> str:
    """Compatibility helper returning the primary physical component."""
    pose = drummer_v3_pose_for_event(event, event_index)
    components, _, _ = _pose_components(event, pose=pose, tom_index=event_index)
    return components[0]


def map_events_to_submodels(events: Iterable[DrumEvent]) -> list[dict[str, object]]:
    return [{
        "timestamp_ms": e.timestamp_ms,
        "drum_type": e.drum_type,
        "submodel": DRUM_SUBMODEL_BY_TYPE.get(e.drum_type, "drum_bus"),
        "velocity": e.velocity,
        "confidence": e.confidence,
        "frequency_band_info": e.frequency_band_info,
        "cluster_id": e.cluster_id,
        "source": e.source,
    } for e in events]


def resolve_drum_streams(
    streams: dict[str, list[DrumEvent]] | None,
    *,
    fallback_kicks: Iterable[int] = (),
    fallback_snares: Iterable[int] = (),
    fallback_hats: Iterable[int] = (),
    fallback_cymbals: Iterable[int] = (),
    config: DrumMappingConfig = DrumMappingConfig(),
) -> dict[str, object]:
    """Resolve streams with the exact b27e8d77 bus semantics.

    A previous rewrite suppressed drum_bus whenever typed hits existed, deleting
    47 approved downbeat-impact events from Helix Audiolights. The historical
    contract keeps those bus events as real DOWNBEAT_IMPACT cues.
    """
    streams = streams or empty_drum_streams()
    typed_count = sum(len(streams.get(key, [])) for key in DRUM_STREAM_KEYS if key != "drum_bus_events")
    bus_events = list(streams.get("drum_bus_events", []))
    if typed_count == 0 and bus_events:
        events = distribute_drum_bus_events(bus_events)
        fallback_mode = "drum_bus_distribution"
    elif typed_count == 0:
        events = flatten_drum_streams(build_streams_from_legacy(
            fallback_kicks, fallback_snares, fallback_hats, fallback_cymbals
        ))
        fallback_mode = "legacy_marks"
    else:
        # Historical behavior: typed streams AND drum_bus are scheduled together.
        events = flatten_drum_streams(streams)
        fallback_mode = "typed_detection"
        if bus_events and typed_count < max(2, len(bus_events) // 2):
            events.extend(distribute_drum_bus_events(bus_events))
            fallback_mode = "partial_detection_plus_bus"

    scheduled = schedule_drum_events(events, config)
    poses = map_events_to_drummer_v3_poses(scheduled)
    return {
        "fallback_mode": fallback_mode,
        "events": scheduled,
        "mapped_events": map_events_to_submodels(scheduled),
        "drummer_v3_pose_events": poses,
        "drummer_component_events": map_events_to_drummer_components(scheduled),
        "counts": {
            key: len([event for event in scheduled if stream_key_for_type(event.drum_type) == key])
            for key in DRUM_STREAM_KEYS
        },
    }
