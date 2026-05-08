"""Deterministic Helix Style Engine v1.

This module translates normalized audio/timing features plus layout metadata into
layout-agnostic choreography decisions. It is intentionally not wired into the
renderer yet; callers can use the returned StyleDecision objects as a stable
contract for later mapping into xLights effects.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Iterable, Mapping, Sequence


STYLE_NAMES = {
    "BeatDrive",
    "ClassicChristmas",
    "CinematicSweep",
    "PartyMode",
    "SpatialHelix",
}

DEFAULT_PALETTES = {
    "BeatDrive": ("blue", "white", "cyan"),
    "ClassicChristmas": ("red", "green", "white", "gold"),
    "CinematicSweep": ("blue", "purple", "white", "gold"),
    "PartyMode": ("pink", "cyan", "lime", "yellow", "white"),
    "SpatialHelix": ("cyan", "violet", "white", "blue"),
}


@dataclass(frozen=True)
class AudioSegment:
    """Normalized music/timing unit consumed by the style engine."""

    start: float
    duration: float
    section: str = "unknown"
    event_type: str = "beat"
    energy: float = 0.5
    beat_strength: float = 0.5
    onset_density: float = 0.5
    bass_energy: float = 0.5
    vocal_presence: float = 0.0
    pitch_direction: str | None = None


@dataclass(frozen=True)
class LayoutProp:
    """Layout metadata for one prop/model."""

    name: str
    type: str = "generic"
    role: str = "accent"
    supports_3d: bool = False


@dataclass(frozen=True)
class LayoutProfile:
    """Normalized layout description used for target selection."""

    props: tuple[LayoutProp, ...] = field(default_factory=tuple)

    @classmethod
    def from_iterable(cls, props: Iterable[LayoutProp | Mapping[str, Any]]) -> "LayoutProfile":
        normalized: list[LayoutProp] = []
        for prop in props:
            if isinstance(prop, LayoutProp):
                normalized.append(prop)
            else:
                normalized.append(
                    LayoutProp(
                        name=str(prop["name"]),
                        type=str(prop.get("type", "generic")),
                        role=str(prop.get("role", "accent")),
                        supports_3d=bool(prop.get("supports_3d", False)),
                    )
                )
        return cls(tuple(normalized))

    def names_for_roles(self, roles: Sequence[str]) -> list[str]:
        role_set = set(roles)
        return [prop.name for prop in self.props if prop.role in role_set]

    def names_supporting_3d(self) -> list[str]:
        return [prop.name for prop in self.props if prop.supports_3d]


@dataclass(frozen=True)
class StylePreset:
    """Style-level preferences for deterministic choreography decisions."""

    name: str
    palette: tuple[str, ...] | None = None
    intensity_bias: float = 0.75
    motion_bias: float = 0.55
    sparkle_bias: float = 0.35

    def __post_init__(self) -> None:
        if self.name not in STYLE_NAMES:
            raise ValueError(f"Unknown style preset: {self.name!r}")


@dataclass(frozen=True)
class StyleDecision:
    """Layout-agnostic choreography decision emitted by the style engine."""

    start: float
    duration: float
    intent: str
    effect: str
    targets: tuple[str, ...]
    palette: tuple[str, ...]
    intensity: float
    motion: str | None = None
    section: str = "unknown"
    event_type: str = "beat"
    style: str = "unknown"

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["targets"] = list(self.targets)
        data["palette"] = list(self.palette)
        return data


class HelixStyleEngine:
    """Deterministic v1 choreography brain for Helix."""

    def __init__(self, style_preset: StylePreset | str, layout_profile: LayoutProfile):
        if isinstance(style_preset, str):
            style_preset = StylePreset(style_preset)
        self.style = style_preset
        self.layout = layout_profile

    def decide(self, audio_segment: AudioSegment | Mapping[str, Any]) -> StyleDecision:
        segment = self._normalize_segment(audio_segment)
        energy = self._clamp(segment.energy)
        intent = self.choose_intent(segment)
        targets = tuple(self.choose_targets(intent))
        effect = self.choose_effect(intent)
        palette = tuple(self.choose_palette(segment))
        motion = self.choose_motion(intent, segment)

        return StyleDecision(
            start=segment.start,
            duration=segment.duration,
            intent=intent,
            effect=effect,
            targets=targets,
            palette=palette,
            intensity=round(energy * self.style.intensity_bias, 3),
            motion=motion,
            section=segment.section,
            event_type=segment.event_type,
            style=self.style.name,
        )

    def choose_intent(self, segment: AudioSegment) -> str:
        style = self.style.name
        energy = self._clamp(segment.energy)
        event = segment.event_type.lower()
        section = segment.section.lower()

        if event in {"silence", "rest"} or energy <= 0.08:
            return "blackout"

        if style == "BeatDrive":
            if event in {"kick", "snare", "beat"} or segment.beat_strength >= 0.75:
                return "pulse" if segment.beat_strength >= 0.85 else "chase"
            return "texture" if energy < 0.4 else "chase"

        if style == "ClassicChristmas":
            if energy >= 0.78 and section in {"chorus", "drop", "finale"}:
                return "sweep"
            if energy >= 0.62:
                return "sparkle"
            return "fade" if energy < 0.35 else "chase"

        if style == "CinematicSweep":
            if event in {"hit", "impact"} or energy >= 0.85:
                return "burst"
            if section in {"build", "chorus", "drop"} or energy >= 0.45:
                return "sweep"
            return "texture"

        if style == "PartyMode":
            if energy >= 0.78 or event in {"drop", "hit"}:
                return "burst"
            if segment.onset_density >= 0.65:
                return "chase"
            return "pulse"

        if style == "SpatialHelix":
            if energy >= 0.8 and section in {"chorus", "drop", "finale"}:
                return "burst"
            if segment.pitch_direction in {"up", "down"} or section in {"build", "chorus"}:
                return "sweep"
            return "texture" if energy < 0.45 else "chase"

        return "texture"

    def choose_targets(self, intent: str) -> list[str]:
        if not self.layout.props:
            return ["ALL"]

        if self.style.name == "SpatialHelix":
            targets_3d = self.layout.names_supporting_3d()
            if targets_3d and intent in {"sweep", "burst", "chase"}:
                return targets_3d

        role_order = {
            "pulse": ("centerpiece", "outline", "accent"),
            "chase": ("motion", "outline", "accent"),
            "sweep": ("centerpiece", "motion", "matrix"),
            "sparkle": ("accent", "centerpiece", "matrix"),
            "burst": ("centerpiece", "motion", "accent", "matrix"),
            "fade": ("outline", "background", "centerpiece"),
            "texture": ("background", "matrix", "outline"),
            "blackout": tuple(prop.role for prop in self.layout.props),
        }.get(intent, ("accent",))

        targets = self.layout.names_for_roles(role_order)
        if targets:
            return targets
        return [self.layout.props[0].name]

    def choose_effect(self, intent: str) -> str:
        table = {
            "pulse": {
                "BeatDrive": "beat_pulse",
                "ClassicChristmas": "warm_pulse",
                "CinematicSweep": "center_flash",
                "PartyMode": "bass_bump",
                "SpatialHelix": "z_pulse",
            },
            "chase": {
                "BeatDrive": "tight_chase",
                "ClassicChristmas": "red_green_chase",
                "CinematicSweep": "slow_chase",
                "PartyMode": "rapid_chase",
                "SpatialHelix": "orbital_chase",
            },
            "sweep": {
                "BeatDrive": "bar_sweep",
                "ClassicChristmas": "whole_house_sweep",
                "CinematicSweep": "cinematic_sweep",
                "PartyMode": "rainbow_sweep",
                "SpatialHelix": "helix_spiral_sweep",
            },
            "sparkle": {
                "BeatDrive": "white_tick_sparkle",
                "ClassicChristmas": "gold_white_sparkle",
                "CinematicSweep": "starfield_sparkle",
                "PartyMode": "confetti_sparkle",
                "SpatialHelix": "orbital_sparkle",
            },
            "burst": {
                "BeatDrive": "impact_burst",
                "ClassicChristmas": "white_gold_burst",
                "CinematicSweep": "trailer_hit_burst",
                "PartyMode": "party_strobe_burst",
                "SpatialHelix": "z_axis_helix_burst",
            },
            "fade": {
                "BeatDrive": "soft_fade",
                "ClassicChristmas": "warm_color_fade",
                "CinematicSweep": "slow_scene_fade",
                "PartyMode": "color_wash_fade",
                "SpatialHelix": "depth_fade",
            },
            "texture": {
                "BeatDrive": "low_level_meter_texture",
                "ClassicChristmas": "gentle_twinkle_texture",
                "CinematicSweep": "ambient_texture",
                "PartyMode": "moving_color_texture",
                "SpatialHelix": "depth_orbit_texture",
            },
            "blackout": {
                "BeatDrive": "blackout",
                "ClassicChristmas": "blackout",
                "CinematicSweep": "blackout",
                "PartyMode": "blackout",
                "SpatialHelix": "blackout",
            },
        }
        return table[intent][self.style.name]

    def choose_palette(self, segment: AudioSegment) -> list[str]:
        palette = list(self.style.palette or DEFAULT_PALETTES[self.style.name])

        if self.style.name == "ClassicChristmas":
            if segment.energy >= 0.75:
                return ["red", "green", "white", "gold"]
            if segment.energy < 0.35:
                return ["warm_white", "gold"]
            return ["red", "green", "white"]

        if self.style.name == "BeatDrive" and segment.event_type.lower() in {"snare", "hit"}:
            return ["white", palette[0]]

        if self.style.name == "SpatialHelix" and segment.pitch_direction == "up":
            return ["cyan", "white", "violet"]

        return palette

    def choose_motion(self, intent: str, segment: AudioSegment) -> str | None:
        if intent in {"blackout", "fade", "texture"}:
            return None

        if self.style.name == "SpatialHelix":
            if segment.pitch_direction == "up":
                return "upward_z"
            if segment.pitch_direction == "down":
                return "downward_z"
            if intent == "burst":
                return "outward_z"
            return "orbital_z"

        if intent == "sweep":
            return "outward"
        if intent == "chase":
            return "left_to_right"
        if intent in {"pulse", "burst", "sparkle"}:
            return "center_out"
        return None

    @staticmethod
    def _normalize_segment(audio_segment: AudioSegment | Mapping[str, Any]) -> AudioSegment:
        if isinstance(audio_segment, AudioSegment):
            return audio_segment
        return AudioSegment(
            start=float(audio_segment.get("start", audio_segment.get("time", 0.0))),
            duration=float(audio_segment.get("duration", 0.5)),
            section=str(audio_segment.get("section", "unknown")),
            event_type=str(audio_segment.get("event_type", audio_segment.get("event", "beat"))),
            energy=float(audio_segment.get("energy", 0.5)),
            beat_strength=float(audio_segment.get("beat_strength", 0.5)),
            onset_density=float(audio_segment.get("onset_density", 0.5)),
            bass_energy=float(audio_segment.get("bass_energy", 0.5)),
            vocal_presence=float(audio_segment.get("vocal_presence", 0.0)),
            pitch_direction=audio_segment.get("pitch_direction"),
        )

    @staticmethod
    def _clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
        return max(lower, min(upper, value))
