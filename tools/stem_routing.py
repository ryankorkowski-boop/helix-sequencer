"""Native stem-to-model routing for Helix.

This module keeps separated stems/instrument events distinct and maps them to
musician models/submodels instead of collapsing them into one generic audio
track.

Target examples:
- guitar -> guitarist strings + arms/hands
- bass -> bassist strings + arms/hands
- drums -> snare / cymbal / hi-hat / tom / kick submodels
- lead vocals -> lead singer face
- female vocals -> female singer face
- backup vocals -> bassist/guitarist/other singing faces
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable


@dataclass(frozen=True)
class StemEvent:
    """One detected stem/instrument/vocal event."""

    start: float
    duration: float
    stem: str
    event_type: str = "hit"
    intensity: float = 0.5
    pitch: float | None = None
    lyric: str | None = None
    voice_role: str | None = None


@dataclass(frozen=True)
class StemRoute:
    """One routing decision from a stem event to a model/submodel target."""

    start: float
    duration: float
    stem: str
    event_type: str
    target_model: str
    target_submodel: str
    action: str
    intensity: float
    lyric: str | None = None


@dataclass(frozen=True)
class BandRoutingProfile:
    """Model/submodel names used by the stem router."""

    guitarist_model: str = "Guitarist"
    bassist_model: str = "Bassist"
    drummer_model: str = "Drummer"
    lead_singer_model: str = "LeadSinger"
    female_singer_model: str = "FemaleSinger"
    backup_singer_models: tuple[str, ...] = ("Bassist", "Guitarist")
    extra_singing_faces: tuple[str, ...] = field(default_factory=tuple)


class StemRouter:
    """Map separated musical stems to band models/submodels."""

    def __init__(self, profile: BandRoutingProfile | None = None):
        self.profile = profile or BandRoutingProfile()

    def route_event(self, event: StemEvent) -> list[StemRoute]:
        stem = event.stem.lower().replace(" ", "_")
        event_type = event.event_type.lower().replace(" ", "_")

        if stem in {"guitar", "electric_guitar", "acoustic_guitar"}:
            return self._route_string_instrument(event, self.profile.guitarist_model, "guitar")
        if stem in {"bass", "bass_guitar"}:
            return self._route_string_instrument(event, self.profile.bassist_model, "bass")
        if stem in {"drums", "percussion"}:
            return self._route_drum(event, event_type)
        if stem in {"lead_vocal", "lead_vocals", "vocal_lead"}:
            return [self._face_route(event, self.profile.lead_singer_model, "lead_face")]
        if stem in {"female_vocal", "female_vocals", "vocal_female"}:
            return [self._face_route(event, self.profile.female_singer_model, "female_face")]
        if stem in {"backup_vocal", "backup_vocals", "harmony", "choir"}:
            return [
                self._face_route(event, model, "backup_face")
                for model in (*self.profile.backup_singer_models, *self.profile.extra_singing_faces)
            ]

        return [
            StemRoute(
                start=event.start,
                duration=event.duration,
                stem=event.stem,
                event_type=event.event_type,
                target_model="ALL",
                target_submodel="accent",
                action="stem_accent",
                intensity=event.intensity,
                lyric=event.lyric,
            )
        ]

    def route_events(self, events: Iterable[StemEvent]) -> list[StemRoute]:
        routes: list[StemRoute] = []
        for event in events:
            routes.extend(self.route_event(event))
        return routes

    def _route_string_instrument(self, event: StemEvent, model: str, instrument: str) -> list[StemRoute]:
        action = "pluck" if event.event_type.lower() in {"pluck", "note", "hit", "attack"} else "strum"
        prefix = instrument
        return [
            StemRoute(event.start, event.duration, event.stem, event.event_type, model, f"{prefix}_strings", action, event.intensity, event.lyric),
            StemRoute(event.start, event.duration, event.stem, event.event_type, model, "left_hand", "fret_motion", event.intensity, event.lyric),
            StemRoute(event.start, event.duration, event.stem, event.event_type, model, "right_hand", "pick_motion", event.intensity, event.lyric),
            StemRoute(event.start, event.duration, event.stem, event.event_type, model, "arms", "performance_motion", event.intensity, event.lyric),
        ]

    def _route_drum(self, event: StemEvent, event_type: str) -> list[StemRoute]:
        part_map = {
            "kick": ("kick", "kick_hit"),
            "snare": ("snare", "snare_hit"),
            "hihat": ("hi_hat", "hat_tick"),
            "hi_hat": ("hi_hat", "hat_tick"),
            "cymbal": ("cymbal", "cymbal_crash"),
            "crash": ("cymbal", "cymbal_crash"),
            "ride": ("cymbal", "ride_pattern"),
            "tom": ("tom", "tom_hit"),
            "toms": ("tom", "tom_fill"),
        }
        submodel, action = part_map.get(event_type, ("drumkit", "percussion_hit"))
        return [
            StemRoute(event.start, event.duration, event.stem, event.event_type, self.profile.drummer_model, submodel, action, event.intensity, event.lyric),
            StemRoute(event.start, event.duration, event.stem, event.event_type, self.profile.drummer_model, "arms", "stick_motion", event.intensity, event.lyric),
        ]

    @staticmethod
    def _face_route(event: StemEvent, model: str, submodel: str) -> StemRoute:
        return StemRoute(
            start=event.start,
            duration=event.duration,
            stem=event.stem,
            event_type=event.event_type,
            target_model=model,
            target_submodel=submodel,
            action="sing_phoneme" if event.lyric else "vocal_presence",
            intensity=event.intensity,
            lyric=event.lyric,
        )
