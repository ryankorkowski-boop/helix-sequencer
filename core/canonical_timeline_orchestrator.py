from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass, field, replace
from typing import Any

from core.beat_grid import BeatGrid, generate_beat_grid
from core.choreography_intent import (
    ChoreographyIntent,
    DominanceStrategy,
    MotionVocabulary,
)
from core.intent_graph import IntentGraph


@dataclass(frozen=True)
class MusicalSection:
    label: str
    start_ms: int
    end_ms: int
    energy: float


@dataclass(frozen=True)
class MusicalContext:
    """Snapshot of already-analyzed musical data on the exporter clock."""

    duration_ms: int
    sections: tuple[MusicalSection, ...]
    beat_ms: tuple[int, ...] = ()
    bar_ms: tuple[int, ...] = ()
    onset_ms: tuple[int, ...] = ()
    note_onset_ms: tuple[int, ...] = ()
    kicks: tuple[int, ...] = ()
    snares: tuple[int, ...] = ()
    hats: tuple[int, ...] = ()
    bass_peaks: tuple[int, ...] = ()
    vocal_peaks: tuple[int, ...] = ()
    build_lifts: tuple[int, ...] = ()
    releases: tuple[int, ...] = ()
    quiet_windows: tuple[tuple[int, int], ...] = ()
    note_events: tuple[Any, ...] = ()
    lyric_events: tuple[Any, ...] = ()
    mood: str = "neutral"
    _section_starts: tuple[int, ...] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "_section_starts", tuple(section.start_ms for section in self.sections))

    def section_at(self, time_ms: int) -> MusicalSection | None:
        idx = bisect_right(self._section_starts, time_ms) - 1
        if idx >= 0 and time_ms < self.sections[idx].end_ms:
            return self.sections[idx]
        return None

    @property
    def subdivisions_ms(self) -> list[int]:
        if not self.beat_ms:
            return []
        return generate_beat_grid(BeatGrid(beat_track_ms=self.beat_ms), self.duration_ms)

    @property
    def tempo_map(self) -> tuple[tuple[int, float], ...]:
        return tuple(
            (start, round(60000 / (end - start), 2))
            for start, end in zip(self.beat_ms, self.beat_ms[1:])
            if end > start
        )

    def summary(self) -> dict[str, Any]:
        return {
            "duration_ms": self.duration_ms,
            "sections": [vars(section) for section in self.sections],
            "beats": len(self.beat_ms),
            "bars": len(self.bar_ms),
            "subdivisions": len(self.subdivisions_ms),
            "tempo_samples": len(self.tempo_map),
            "onsets": len(self.onset_ms),
            "note_onsets": len(self.note_onset_ms),
            "notes": len(self.note_events),
            "vocal_peaks": len(self.vocal_peaks),
            "lyric_phrases": len(self.lyric_events),
            "percussion": {"kick": len(self.kicks), "snare": len(self.snares), "hat": len(self.hats)},
            "bass_peaks": len(self.bass_peaks),
            "quiet_windows": len(self.quiet_windows),
            "build_lifts": len(self.build_lifts),
            "releases": len(self.releases),
            "mood": self.mood,
        }


class CanonicalTimelineOrchestrator:
    def __init__(self, *, minimum_duration: float = 0.25):
        self.minimum_duration = minimum_duration

    def from_music(self, music: MusicalContext) -> IntentGraph:
        return IntentGraph(
            ChoreographyIntent(
                start=section.start_ms / 1000,
                duration=(section.end_ms - section.start_ms) / 1000,
                section=section.label,
                event_type="section_choreography",
                style="analyzed_audio",
                emotional_energy=section.energy,
                intensity=section.energy,
                focal_region="display",
                dominance_strategy=DominanceStrategy.DISTRIBUTED,
                motion_vocabulary=(MotionVocabulary.TEXTURE,),
                density_budget=section.energy,
                source="canonical_timeline",
                metadata={"audio_mood": music.mood},
            )
            for section in music.sections
            if section.end_ms > section.start_ms
        )

    def orchestrate(self, graph: IntentGraph) -> IntentGraph:
        output = IntentGraph()
        for intent in graph:
            start = max(0.0, round(float(intent.start), 6))
            duration = max(self.minimum_duration, round(float(intent.duration), 6))
            output.add_intent(
                replace(
                    intent,
                    start=start,
                    duration=duration,
                    metadata={
                        **dict(intent.metadata),
                        "canonical_timeline": {
                            "minimum_duration": self.minimum_duration,
                        },
                    },
                )
            )
        return output
