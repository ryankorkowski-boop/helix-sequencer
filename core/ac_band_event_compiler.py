from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from core.ac_band_channel_map import AcBandChannelMap, ac_band_channel_lookup, build_ac_band_channel_map


@dataclass(frozen=True)
class AcBandEvent:
    channel_name: str
    channel_index: int
    member_id: str
    submodel: str
    start_ms: int
    end_ms: int
    value: float = 1.0
    source_kind: str = "band_cue"

    def to_dict(self) -> dict[str, Any]:
        return {
            "channel_name": self.channel_name,
            "channel_index": self.channel_index,
            "member_id": self.member_id,
            "submodel": self.submodel,
            "start_ms": self.start_ms,
            "end_ms": self.end_ms,
            "value": self.value,
            "source_kind": self.source_kind,
        }


@dataclass(frozen=True)
class AcBandEventCompilation:
    schema: str
    channel_map: AcBandChannelMap
    events: tuple[AcBandEvent, ...]
    dropped_cues: tuple[dict[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "channel_map": self.channel_map.to_dict(),
            "event_count": len(self.events),
            "dropped_cue_count": len(self.dropped_cues),
            "events": [event.to_dict() for event in self.events],
            "dropped_cues": list(self.dropped_cues),
        }


PERFORMER_TO_MEMBER = {
    "lead_singer": "snowman_singer",
    "singer": "snowman_singer",
    "female_singer": "snowman_singer_female",
    "harmony_singer": "snowman_singer_female",
    "guitarist": "snowman_guitarist",
    "bassist": "snowman_bassist",
    "drummer": "snowman_drummer",
}

CUE_FRAME_ALIASES = {
    "mouth_a": "MOUTH_PHONEME",
    "mouth_e": "MOUTH_PHONEME",
    "mouth_i": "MOUTH_PHONEME",
    "mouth_o": "MOUTH_PHONEME",
    "mouth_u": "MOUTH_PHONEME",
    "mouth_mbp": "MOUTH_PHONEME",
    "viseme_ah": "MOUTH_PHONEME",
    "viseme_ee": "MOUTH_PHONEME",
    "viseme_oh": "MOUTH_PHONEME",
    "viseme_mbp": "MOUTH_PHONEME",
    "viseme_fv": "MOUTH_PHONEME",
    "strum_down": "STRUM_ZONE",
    "strum_up": "STRUM_ZONE",
    "strum_frame_a": "STRUM_ZONE",
    "strum_frame_b": "STRUM_ZONE",
    "pluck_zone": "PLUCK_ZONE",
    "string_lane_1": "BASS_STRINGS",
    "string_lane_2": "BASS_STRINGS",
    "string_lane_3": "BASS_STRINGS",
    "string_lane_4": "BASS_STRINGS",
    "kick": "KICK",
    "kick_center": "KICK",
    "kick_mid": "KICK",
    "kick_outer": "KICK",
    "snare": "SNARE",
    "snare_burst": "SNARE",
    "hihat": "HI_HAT",
    "hat_flash": "HI_HAT",
    "cymbal": "CYMBALS",
    "cymbal_frame_1": "CYMBALS",
    "cymbal_frame_2": "CYMBALS",
    "cymbal_frame_3": "CYMBALS",
    "cymbal_frame_4": "CYMBALS",
    "tom": "TOM",
    "tom_bounce": "TOM",
}


def normalize_token(value: str) -> str:
    return "_".join(str(value or "").strip().upper().replace("-", "_").replace(" ", "_").split("_"))


def compile_ac_band_events(
    cues: Iterable[Mapping[str, Any]],
    *,
    channel_map: AcBandChannelMap | None = None,
    start_channel: int = 1,
) -> AcBandEventCompilation:
    resolved_map = channel_map or build_ac_band_channel_map(start_channel=start_channel)
    lookup = ac_band_channel_lookup(resolved_map)
    events: list[AcBandEvent] = []
    dropped: list[dict[str, Any]] = []

    for cue in cues:
        member_id = _member_for_cue(cue)
        start_ms = int(cue.get("start_ms", 0) or 0)
        end_ms = int(cue.get("end_ms", start_ms + 100) or (start_ms + 100))
        value = float(cue.get("value", cue.get("intensity", 1.0)) or 1.0)
        frames = _frames_for_cue(cue)

        if not member_id or not frames:
            dropped.append({"reason": "missing_member_or_frames", "cue": dict(cue)})
            continue

        matched = False
        for frame in frames:
            submodel = _submodel_for_frame(member_id, frame)
            channel = lookup.get((member_id, submodel))
            if channel is None:
                dropped.append(
                    {
                        "reason": "unmapped_submodel",
                        "member_id": member_id,
                        "frame": frame,
                        "submodel": submodel,
                        "cue": dict(cue),
                    }
                )
                continue
            matched = True
            events.append(
                AcBandEvent(
                    channel_name=channel.channel_name,
                    channel_index=channel.channel_index,
                    member_id=member_id,
                    submodel=submodel,
                    start_ms=start_ms,
                    end_ms=max(start_ms + 1, end_ms),
                    value=max(0.0, min(1.0, value)),
                    source_kind=str(cue.get("kind", "band_cue")),
                )
            )

        if not matched:
            dropped.append({"reason": "no_frames_matched_channels", "cue": dict(cue)})

    return AcBandEventCompilation(
        schema="helix.ac_band_event_compilation.v1",
        channel_map=resolved_map,
        events=tuple(sorted(events, key=lambda event: (event.start_ms, event.channel_index))),
        dropped_cues=tuple(dropped),
    )


def ac_band_event_payload(
    cues: Iterable[Mapping[str, Any]],
    *,
    start_channel: int = 1,
) -> dict[str, Any]:
    return compile_ac_band_events(cues, start_channel=start_channel).to_dict()


def _member_for_cue(cue: Mapping[str, Any]) -> str:
    performer = str(cue.get("performer", "") or "").strip().lower().replace("-", "_").replace(" ", "_")
    member = str(cue.get("member_id", "") or "").strip().lower().replace("-", "_").replace(" ", "_")
    return member or PERFORMER_TO_MEMBER.get(performer, performer)


def _frames_for_cue(cue: Mapping[str, Any]) -> tuple[str, ...]:
    frames: list[str] = []
    raw_frames = cue.get("frames", []) or []
    if isinstance(raw_frames, str):
        frames.append(raw_frames)
    else:
        frames.extend(str(frame) for frame in raw_frames if frame)

    for key in ("submodel", "mouth_submodel", "pixel_frame", "matrix_frame", "kind"):
        value = cue.get(key)
        if value:
            frames.append(str(value))

    return tuple(dict.fromkeys(frames))


def _submodel_for_frame(member_id: str, frame: str) -> str:
    token = normalize_token(frame)
    alias = CUE_FRAME_ALIASES.get(frame.strip().lower().replace("-", "_").replace(" ", "_"), token)
    alias_token = normalize_token(alias)

    if alias_token.startswith("HX_SNOWMAN_"):
        return alias_token

    prefixes = {
        "snowman_singer": "HX_SNOWMAN_SINGER",
        "snowman_singer_female": "HX_SNOWMAN_SINGER_FEMALE",
        "snowman_guitarist": "HX_SNOWMAN_GUITARIST",
        "snowman_bassist": "HX_SNOWMAN_BASSIST",
        "snowman_drummer": "HX_SNOWMAN_DRUMMER",
    }
    prefix = prefixes.get(member_id, "")
    if not prefix:
        return alias_token
    if alias_token.startswith(prefix):
        return alias_token
    return f"{prefix}_{alias_token}"
