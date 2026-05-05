"""Named timing-track model for Helix audio intelligence.

Helix should preserve separate timing tracks instead of melting every event into
one flat list. This module provides the shared data contract.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from tools.style_engine import AudioSegment


@dataclass(frozen=True)
class TimingTrack:
    """One named timing/intelligence track."""

    name: str
    kind: str
    segments: tuple[AudioSegment, ...] = field(default_factory=tuple)
    source: str = "unknown"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "kind": self.kind,
            "source": self.source,
            "metadata": self.metadata,
            "segments": [segment.__dict__ for segment in self.segments],
        }


@dataclass(frozen=True)
class TimingTrackSet:
    """Collection of separate named timing tracks."""

    tracks: tuple[TimingTrack, ...] = field(default_factory=tuple)

    def by_name(self, name: str) -> TimingTrack | None:
        for track in self.tracks:
            if track.name == name:
                return track
        return None

    def names(self) -> list[str]:
        return [track.name for track in self.tracks]

    def to_dict(self) -> dict[str, Any]:
        return {"tracks": [track.to_dict() for track in self.tracks]}


def select_segments_for_style_engine(track_set: TimingTrackSet, preferred_tracks: tuple[str, ...] = ("beats", "sections", "drops", "builds")) -> list[AudioSegment]:
    """Create an explicit Style Engine view from selected tracks only.

    This is intentionally explicit so track preservation remains the default.
    """

    selected: list[AudioSegment] = []
    for name in preferred_tracks:
        track = track_set.by_name(name)
        if track is not None:
            selected.extend(track.segments)
    return sorted(selected, key=lambda segment: segment.start)
