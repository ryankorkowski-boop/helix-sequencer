"""Structured audio-event analysis layer for the Helix V2 development branch.

This module defines a neutral contract for combining multiple independent
audio detectors. It does not copy implementation, labels, or terminology
from any external sequencer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class AudioEvent:
    time: float
    kind: str
    strength: float = 1.0
    frequency_hz: float | None = None
    confidence: float = 1.0
    source: str = "detector"
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class AudioAnalysis:
    duration: float
    sample_rate: int
    frame_rate: float
    events: list[AudioEvent] = field(default_factory=list)
    tracks: dict[str, list[AudioEvent]] = field(default_factory=dict)
    features: dict[str, Any] = field(default_factory=dict)

    def add(self, event: AudioEvent) -> None:
        self.events.append(event)
        self.tracks.setdefault(event.kind, []).append(event)

    def sort(self) -> None:
        self.events.sort(key=lambda e: (e.time, e.kind))
        for values in self.tracks.values():
            values.sort(key=lambda e: e.time)


class AudioFeatureFusion:
    """Fuse detector outputs without coupling the sequence compiler to them."""

    def __init__(self, detectors: list[Any] | None = None) -> None:
        self.detectors = detectors or []

    def analyze(self, audio_path: str, **options: Any) -> AudioAnalysis:
        result = AudioAnalysis(
            duration=0.0,
            sample_rate=int(options.get("sample_rate", 44100)),
            frame_rate=float(options.get("frame_rate", 20.0)),
        )
        for detector in self.detectors:
            produced = detector.analyze(audio_path, **options)
            if produced is None:
                continue
            for event in produced.events if hasattr(produced, "events") else produced:
                result.add(event)
            if hasattr(produced, "features"):
                result.features.update(produced.features)
            result.duration = max(result.duration, float(getattr(produced, "duration", 0.0)))
        result.sort()
        return result
