from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping


LEGACY_CHANNELS = 256
DRUMMER_BRIDGE_START_CHANNEL = 247
DRUMMER_BRIDGE_END_CHANNEL = 256


@dataclass(frozen=True)
class LegacyDrummerChannel:
    submodel: str
    channel_index: int
    channel_name: str


# Keep the existing 1-246 legacy layout untouched.  The bridge owns the final
# ten AC channels so Drummer V3 can be represented by real legacy channels.
# Multiple visual submodels can intentionally share a physical AC channel when
# they describe the same hit zone; the canonical V3 hit targets remain distinct
# at the event layer.
DRUMMER_SUBMODEL_TO_CHANNEL = {
    "HX_SNOWMAN_DRUMMER_V3_HIT_KICK": 247,
    "HX_SNOWMAN_DRUMMER_V3_HIT_SNARE": 248,
    "HX_SNOWMAN_DRUMMER_V3_HIT_HIHAT": 249,
    "HX_SNOWMAN_DRUMMER_V3_HIT_LEFT_TOM": 250,
    "HX_SNOWMAN_DRUMMER_V3_HIT_RIGHT_TOM": 251,
    "HX_SNOWMAN_DRUMMER_V3_HIT_LEFT_CRASH": 252,
    "HX_SNOWMAN_DRUMMER_V3_HIT_RIGHT_CRASH": 253,
    "HX_SNOWMAN_DRUMMER_V3_HIT_BOTH_CRASH": 254,
    "HX_SNOWMAN_DRUMMER_V3_DOWNBEAT_IMPACT": 255,
    "HX_SNOWMAN_DRUMMER_V3_LEFT_ARM_IDLE": 256,
}


def build_legacy_drummer_channel_map() -> tuple[LegacyDrummerChannel, ...]:
    return tuple(
        LegacyDrummerChannel(
            submodel=submodel,
            channel_index=channel,
            channel_name=f"CH_{channel:03d}",
        )
        for submodel, channel in DRUMMER_SUBMODEL_TO_CHANNEL.items()
    )


def validate_legacy_drummer_reservation(occupied_channels: Iterable[int]) -> dict[str, object]:
    occupied = {int(channel) for channel in occupied_channels}
    reserved = set(DRUMMER_SUBMODEL_TO_CHANNEL.values())
    collisions = sorted(occupied & reserved)
    invalid = sorted(channel for channel in reserved if channel < 1 or channel > LEGACY_CHANNELS)
    return {
        "valid": not collisions and not invalid,
        "reserved_channels": sorted(reserved),
        "collisions": collisions,
        "invalid_channels": invalid,
    }


def compile_drummer_v3_events_to_legacy(
    events: Iterable[Mapping[str, object]],
    *,
    occupied_channels: Iterable[int] = (),
) -> list[dict[str, object]]:
    validation = validate_legacy_drummer_reservation(occupied_channels)
    if not validation["valid"]:
        raise ValueError(
            "Drummer bridge channel collision: "
            + ", ".join(str(channel) for channel in validation["collisions"])
        )

    compiled: list[dict[str, object]] = []
    for event in events:
        for submodel in event.get("submodels", ()) or ():
            channel = DRUMMER_SUBMODEL_TO_CHANNEL.get(str(submodel))
            if channel is None:
                continue
            start_ms = int(event.get("timestamp_ms", event.get("start_ms", 0)) or 0)
            end_ms = int(event.get("end_ms", start_ms + 140) or (start_ms + 140))
            compiled.append(
                {
                    "channel_index": channel,
                    "channel_name": f"CH_{channel:03d}",
                    "submodel": str(submodel),
                    "start_ms": start_ms,
                    "end_ms": max(start_ms + 1, end_ms),
                    "value": float(event.get("intensity", event.get("value", 1.0)) or 1.0),
                    "source_kind": "drummer_v3_legacy_bridge",
                }
            )
    return compiled
