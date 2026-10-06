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
DRUMMER_V3_MODEL = "HX_SNOWMAN_DRUMMER_V3"
DRUMMER_COMPONENTS = tuple(
    f"{DRUMMER_V3_MODEL}_{name}"
    for name in (
        "KICK",
        "SNARE",
        "HI_HAT",
        "TOM_HIGH",
        "TOM_MID",
        "TOM_FLOOR",
        "CYMBAL_LEFT",
        "CYMBAL_RIGHT",
    )
)
KICK, SNARE, HI_HAT, TOM_HIGH, TOM_MID, TOM_FLOOR, CYMBAL_LEFT, CYMBAL_RIGHT = DRUMMER_COMPONENTS
TOM_COMPONENT_BY_CLASS = {"high": TOM_HIGH, "mid": TOM_MID, "floor": TOM_FLOOR}
TOM_POSE_BY_CLASS = {
    "high": "tom_high_hit",
    "mid": "tom_mid_hit",
    "floor": "tom_floor_hit",
}

DRUMMER_V3_POSE_BY_TYPE = {
    "kick": "kick_hit",
    "snare": "snare_hit",
    "hihat": "hi_hat_pulse",
}
DRUMMER_V3_DURATION_BY_POSE = {
    "kick_hit": 150,
    "snare_hit": 125,
    "hi_hat_pulse": 90,
    "tom_high_hit": 165,
    "tom_mid_hit": 165,
    "tom_floor_hit": 175,
    "left_crash": 320,
    "right_crash": 320,
}


@dataclass(frozen=True)
class DrumMappingConfig:
    merge_window_ms: int = 24
    clutter_window_ms: int = 70
    max_hits_per_window: int = 4
    rapid_repeat_window_ms: int = 90

    # A final safety gate for quiet/non-drum intros. This is pattern-based,
    # not a song timestamp: a track that genuinely starts with drums opens at
    # once, while isolated weak transients remain dark.
    intro_gate_enabled: bool = True
    intro_anchor_min_velocity: float = 0.42
    intro_support_min_velocity: float = 0.36
    intro_confirm_window_ms: int = 1400
    intro_preroll_ms: int = 80
    intro_search_limit_ms: int = 30000


def flatten_drum_streams(streams: dict[str, list[DrumEvent]]) -> list[DrumEvent]:
    events: list[DrumEvent] = []
    for key in DRUM_STREAM_KEYS:
        events.extend(streams.get(key, []))
    return sorted(
        events,
        key=lambda event: (
            event.timestamp_ms,
            DRUM_PRIORITY.get(event.drum_type, 9),
            -event.velocity,
        ),
    )


def build_streams_from_legacy(
    kicks: Iterable[int],
    snares: Iterable[int],
    hats: Iterable[int],
    cymbals: Iterable[int] = (),
) -> dict[str, list[DrumEvent]]:
    streams = empty_drum_streams()
    for drum_type, marks, velocity in (
        ("kick", kicks, .78),
        ("snare", snares, .68),
        ("hihat", hats, .42),
        ("cymbal", cymbals, .62),
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
    """Ambiguous drum-bus evidence is deliberately non-emitting.

    Older code fabricated a rotating kick/hat/snare/tom/cymbal pattern from
    unclassified transients. That is exactly the behavior that created false
    drummer hits. Keep the helper for API compatibility, but never manufacture
    a performance from bus events.
    """
    _ = tuple(events)
    return []


def suppress_intro_false_hits(
    events: Iterable[DrumEvent],
    config: DrumMappingConfig = DrumMappingConfig(),
) -> tuple[list[DrumEvent], int | None, int]:
    ordered = sorted(
        (event for event in events if event.drum_type != "drum_bus"
         and (event.drum_type != "tom" or _explicit_tom_class(event)[0] is not None)),
        key=lambda event: (
            event.timestamp_ms,
            DRUM_PRIORITY.get(event.drum_type, 9),
            -event.velocity,
        ),
    )
    if not config.intro_gate_enabled or len(ordered) < 2:
        return ordered, None, 0

    anchors = {"kick", "snare", "tom"}
    typed = {"kick", "snare", "tom", "hihat", "cymbal"}
    for anchor in ordered:
        if anchor.timestamp_ms > config.intro_search_limit_ms:
            break
        if anchor.drum_type not in anchors:
            continue
        if anchor.velocity < config.intro_anchor_min_velocity:
            continue

        supporters = [
            other
            for other in ordered
            if 0 < other.timestamp_ms - anchor.timestamp_ms <= config.intro_confirm_window_ms
            and other.drum_type in typed
            and other.velocity >= config.intro_support_min_velocity
        ]
        if not supporters:
            continue

        start_ms = max(0, anchor.timestamp_ms - config.intro_preroll_ms)
        kept = [event for event in ordered if event.timestamp_ms >= start_ms]
        return kept, start_ms, len(ordered) - len(kept)

    # Do not erase an intentionally soft performance if it never crosses the
    # final safety gate; the upstream detector remains the primary authority.
    return ordered, None, 0


def schedule_drum_events(
    events: Iterable[DrumEvent],
    config: DrumMappingConfig = DrumMappingConfig(),
) -> list[DrumEvent]:
    sorted_events = sorted(
        (event for event in events if event.drum_type != "drum_bus"
         and (event.drum_type != "tom" or _explicit_tom_class(event)[0] is not None)),
        key=lambda event: (
            event.timestamp_ms,
            DRUM_PRIORITY.get(event.drum_type, 9),
            -event.velocity,
        ),
    )

    merged: list[DrumEvent] = []
    for event in sorted_events:
        if (
            merged
            and event.drum_type == merged[-1].drum_type
            and event.timestamp_ms - merged[-1].timestamp_ms <= config.merge_window_ms
        ):
            previous = merged[-1]
            merged[-1] = (
                event
                if (event.velocity, event.confidence) > (previous.velocity, previous.confidence)
                else previous
            )
            continue
        merged.append(event)

    scheduled: list[DrumEvent] = []
    last_by_type: dict[str, DrumEvent] = {}
    for event in merged:
        nearby = [
            item
            for item in scheduled
            if 0 <= event.timestamp_ms - item.timestamp_ms <= config.clutter_window_ms
        ]
        if len(nearby) >= config.max_hits_per_window:
            worst = max(
                nearby,
                key=lambda item: (
                    DRUM_PRIORITY.get(item.drum_type, 9),
                    -item.velocity,
                ),
            )
            if (
                DRUM_PRIORITY.get(event.drum_type, 9),
                -event.velocity,
            ) >= (
                DRUM_PRIORITY.get(worst.drum_type, 9),
                -worst.velocity,
            ):
                continue
            scheduled.remove(worst)

        previous = last_by_type.get(event.drum_type)
        if previous and event.timestamp_ms - previous.timestamp_ms <= config.rapid_repeat_window_ms:
            event = DrumEvent(
                timestamp=event.timestamp,
                velocity=round(max(.08, event.velocity * .74), 3),
                confidence=event.confidence,
                frequency_band_info={
                    **event.frequency_band_info,
                    "rapid_repeat_scale": .74,
                },
                cluster_id=event.cluster_id,
                drum_type=event.drum_type,
                source=event.source,
            )

        scheduled.append(event)
        last_by_type[event.drum_type] = event

    return sorted(
        scheduled,
        key=lambda event: (
            event.timestamp_ms,
            DRUM_PRIORITY.get(event.drum_type, 9),
        ),
    )


def _explicit_tom_class(event: DrumEvent) -> tuple[str | None, float]:
    info = event.frequency_band_info or {}
    raw = str(info.get("tom_class", info.get("tom_position", ""))).strip().lower()
    aliases = {
        "high_tom": "high",
        "hi": "high",
        "upper": "high",
        "1": "high",
        "1.0": "high",
        "mid_tom": "mid",
        "middle": "mid",
        "medium": "mid",
        "2": "mid",
        "2.0": "mid",
        "floor_tom": "floor",
        "low": "floor",
        "3": "floor",
        "3.0": "floor",
    }
    raw = aliases.get(raw, raw)
    if raw not in TOM_COMPONENT_BY_CLASS:
        return None, 0.0

    try:
        confidence = float(info.get("tom_class_confidence", event.confidence) or 0.0)
    except (TypeError, ValueError):
        confidence = float(event.confidence)
    return raw, max(0.0, min(1.0, confidence))


def tom_class_for_event(event: DrumEvent, event_index: int = 0) -> str:
    explicit, _ = _explicit_tom_class(event)
    if explicit:
        return explicit
    raise ValueError("Tom event has no detected physical class")


def drummer_v3_pose_for_event(event: DrumEvent, event_index: int = 0) -> str:
    if event.drum_type == "tom":
        return TOM_POSE_BY_CLASS[tom_class_for_event(event, event_index)]
    if event.drum_type == "cymbal":
        return "left_crash" if event_index % 2 == 0 else "right_crash"
    if event.drum_type == "drum_bus":
        raise ValueError("Ambiguous drum_bus events are not valid drummer poses")
    return DRUMMER_V3_POSE_BY_TYPE.get(event.drum_type, "kick_hit")


def _pose_components(
    event: DrumEvent,
    *,
    pose: str,
    tom_index: int = 0,
) -> tuple[tuple[str, ...], str | None, str | None]:
    if event.drum_type == "kick":
        return (KICK,), None, None
    if event.drum_type == "snare":
        return (SNARE,), None, None
    if event.drum_type == "hihat":
        return (HI_HAT,), None, None
    if event.drum_type == "tom":
        tom_class = tom_class_for_event(event, tom_index)
        source = "detected_tom_class"
        return (TOM_COMPONENT_BY_CLASS[tom_class],), tom_class, source
    if event.drum_type == "cymbal":
        component = CYMBAL_LEFT if pose == "left_crash" else CYMBAL_RIGHT
        return (component,), None, "deterministic_cymbal_alternation"
    if event.drum_type == "drum_bus":
        return (), None, "ambiguous_bus_rejected"
    return (), None, "unknown_rejected"


def map_events_to_drummer_v3_poses(events: Iterable[DrumEvent]) -> list[dict[str, object]]:
    ordered = sorted(
        (event for event in events if event.drum_type != "drum_bus"
         and (event.drum_type != "tom" or _explicit_tom_class(event)[0] is not None)),
        key=lambda item: (
            item.timestamp_ms,
            DRUM_PRIORITY.get(item.drum_type, 9),
            -item.velocity,
        ),
    )

    mapped: list[dict[str, object]] = []
    tom_index = 0
    cymbal_index = 0
    for event in ordered:
        if event.drum_type == "tom":
            pose = drummer_v3_pose_for_event(event, tom_index)
            components, tom_class, tom_class_source = _pose_components(
                event,
                pose=pose,
                tom_index=tom_index,
            )
            tom_index += 1
        elif event.drum_type == "cymbal":
            pose = drummer_v3_pose_for_event(event, cymbal_index)
            components, tom_class, tom_class_source = _pose_components(
                event,
                pose=pose,
            )
            cymbal_index += 1
        else:
            pose = drummer_v3_pose_for_event(event, 0)
            components, tom_class, tom_class_source = _pose_components(
                event,
                pose=pose,
            )

        if not components:
            continue

        mapped.append(
            {
                "timestamp_ms": event.timestamp_ms,
                "end_ms": event.timestamp_ms + DRUMMER_V3_DURATION_BY_POSE.get(pose, 140),
                "model": DRUMMER_V3_MODEL,
                "drum_type": event.drum_type,
                "pose": pose,
                "component": components[0],
                "submodels": list(components),
                "components": list(components),
                "tom_class": tom_class,
                "tom_class_source": tom_class_source,
                "intensity": round(event.velocity, 3),
                "confidence": event.confidence,
                "source": event.source,
            }
        )
    return mapped


def map_events_to_drummer_components(events: Iterable[DrumEvent]) -> list[dict[str, object]]:
    placements: list[dict[str, object]] = []
    for event in map_events_to_drummer_v3_poses(events):
        for component in event["components"]:
            placements.append({**event, "component": component})
    return placements


def drummer_component_for_event(event: DrumEvent, *, event_index: int = 0) -> str:
    pose = drummer_v3_pose_for_event(event, event_index)
    components, _, _ = _pose_components(
        event,
        pose=pose,
        tom_index=event_index,
    )
    if not components:
        raise ValueError(f"No canonical drummer component for {event.drum_type!r}")
    return components[0]


def map_events_to_submodels(events: Iterable[DrumEvent]) -> list[dict[str, object]]:
    return [
        {
            "timestamp_ms": event.timestamp_ms,
            "drum_type": event.drum_type,
            "submodel": DRUM_SUBMODEL_BY_TYPE.get(event.drum_type, "drum_bus"),
            "velocity": event.velocity,
            "confidence": event.confidence,
            "frequency_band_info": event.frequency_band_info,
            "cluster_id": event.cluster_id,
            "source": event.source,
        }
        for event in events
        if event.drum_type != "drum_bus"
    ]


def resolve_drum_streams(
    streams: dict[str, list[DrumEvent]] | None,
    *,
    fallback_kicks: Iterable[int] = (),
    fallback_snares: Iterable[int] = (),
    fallback_hats: Iterable[int] = (),
    fallback_cymbals: Iterable[int] = (),
    config: DrumMappingConfig = DrumMappingConfig(),
) -> dict[str, object]:
    """Resolve only typed drum evidence into the eight physical components.

    drum_bus is diagnostic evidence, not a musical event. It is always rejected.
    This prevents ambiguous guitar/piano/intro transients from being turned into
    fake kick/snare/cymbal choreography.
    """
    streams = streams or empty_drum_streams()
    typed_streams = {
        key: list(streams.get(key, []))
        for key in DRUM_STREAM_KEYS
        if key != "drum_bus_events"
    }
    typed_count = sum(len(value) for value in typed_streams.values())
    bus_count = len(streams.get("drum_bus_events", []))

    if typed_count:
        events = flatten_drum_streams(typed_streams)
        fallback_mode = "typed_detection_bus_suppressed" if bus_count else "typed_detection"
    else:
        legacy = build_streams_from_legacy(
            fallback_kicks,
            fallback_snares,
            fallback_hats,
            fallback_cymbals,
        )
        legacy_events = flatten_drum_streams(legacy)
        if legacy_events:
            events = legacy_events
            fallback_mode = "legacy_marks"
        else:
            events = []
            fallback_mode = "ambiguous_bus_rejected" if bus_count else "no_drum_evidence"

    gated_events, intro_gate_start_ms, intro_gate_suppressed_count = suppress_intro_false_hits(
        events,
        config,
    )
    scheduled = schedule_drum_events(gated_events, config)
    poses = map_events_to_drummer_v3_poses(scheduled)

    return {
        "fallback_mode": fallback_mode,
        "intro_gate_start_ms": intro_gate_start_ms,
        "intro_gate_suppressed_count": intro_gate_suppressed_count,
        "ambiguous_bus_rejected_count": bus_count,
        "events": scheduled,
        "mapped_events": map_events_to_submodels(scheduled),
        "drummer_v3_pose_events": poses,
        "drummer_component_events": map_events_to_drummer_components(scheduled),
        "counts": {
            key: len(
                [
                    event
                    for event in scheduled
                    if stream_key_for_type(event.drum_type) == key
                ]
            )
            for key in DRUM_STREAM_KEYS
        },
    }
