from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


@dataclass
class SequenceContext:
    timestamp: int = 0
    audio_features: dict[str, Any] = field(default_factory=dict)
    spatial_features: dict[str, Any] = field(default_factory=dict)
    emotion_state: dict[str, Any] = field(default_factory=dict)
    band_state: dict[str, Any] = field(default_factory=dict)
    dominant_elements: list[str] = field(default_factory=list)
    energy_level: float = 0.5
    style_profile: dict[str, Any] = field(default_factory=dict)
    scoring_feedback: dict[str, Any] = field(default_factory=dict)
    debug: dict[str, list[dict[str, Any]]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.timestamp = int(self.timestamp or 0)
        self.energy_level = clamp01(self.energy_level)
        self.audio_features = dict(self.audio_features or {})
        self.spatial_features = dict(self.spatial_features or {})
        self.emotion_state = dict(self.emotion_state or {})
        self.band_state = dict(self.band_state or {})
        self.dominant_elements = [str(item) for item in (self.dominant_elements or [])]
        self.style_profile = dict(self.style_profile or {})
        self.scoring_feedback = dict(self.scoring_feedback or {})
        self.debug = {str(key): list(value or []) for key, value in (self.debug or {}).items()}

    def add_debug(self, module: str, event: str, payload: Mapping[str, Any] | None = None) -> None:
        self.debug.setdefault(module, []).append(
            {
                "timestamp": self.timestamp,
                "event": str(event),
                "payload": dict(payload or {}),
            }
        )

    def update_style(self, profile: Mapping[str, Any]) -> None:
        self.style_profile = dict(profile or {})
        self.add_debug("sequence_context", "style_profile_updated", {"style": self.style_profile.get("name")})

    def update_spatial_features(self, features: Mapping[str, Any]) -> None:
        self.spatial_features.update(dict(features or {}))
        self.add_debug("sequence_context", "spatial_features_updated", {"keys": sorted(features.keys())})

    def update_scoring_feedback(self, feedback: Mapping[str, Any]) -> None:
        self.scoring_feedback.update(dict(feedback or {}))
        self.add_debug("sequence_context", "scoring_feedback_updated", {"keys": sorted(feedback.keys())})

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
