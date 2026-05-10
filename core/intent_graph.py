from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable, Iterator, Sequence

from core.choreography_intent import ChoreographyIntent


@dataclass(frozen=True)
class IntentOverlap:
    left: ChoreographyIntent
    right: ChoreographyIntent
    overlap_start: float
    overlap_end: float

    @property
    def overlap_duration(self) -> float:
        return round(self.overlap_end - self.overlap_start, 6)


class IntentGraph:
    """Ordered choreography intent timeline.

    This becomes the canonical sequencing graph shared by:
    - Style Engine
    - Sequential Layering
    - Prop Specialists
    - Composition Governor
    - GUI diagnostics
    - Exporters
    """

    def __init__(self, intents: Iterable[ChoreographyIntent] | None = None):
        self._intents: list[ChoreographyIntent] = []
        if intents:
            for intent in intents:
                self.add_intent(intent)

    def __len__(self) -> int:
        return len(self._intents)

    def __iter__(self) -> Iterator[ChoreographyIntent]:
        return iter(self._intents)

    @property
    def intents(self) -> tuple[ChoreographyIntent, ...]:
        return tuple(self._intents)

    @property
    def start(self) -> float:
        if not self._intents:
            return 0.0
        return self._intents[0].start

    @property
    def end(self) -> float:
        if not self._intents:
            return 0.0
        return max(intent.end for intent in self._intents)

    @property
    def duration(self) -> float:
        return round(self.end - self.start, 6)

    def add_intent(self, intent: ChoreographyIntent) -> None:
        self._intents.append(intent)
        self._intents.sort(key=lambda item: (item.start, item.duration, item.intent_id))

    def extend(self, intents: Iterable[ChoreographyIntent]) -> None:
        for intent in intents:
            self.add_intent(intent)

    def by_section(self, section: str) -> tuple[ChoreographyIntent, ...]:
        return tuple(intent for intent in self._intents if intent.section == section)

    def by_style(self, style: str) -> tuple[ChoreographyIntent, ...]:
        return tuple(intent for intent in self._intents if intent.style == style)

    def by_event_type(self, event_type: str) -> tuple[ChoreographyIntent, ...]:
        return tuple(intent for intent in self._intents if intent.event_type == event_type)

    def by_dominant_prop(self, prop_name: str) -> tuple[ChoreographyIntent, ...]:
        return tuple(intent for intent in self._intents if intent.dominant_prop == prop_name)

    def within_window(self, start: float, end: float) -> tuple[ChoreographyIntent, ...]:
        return tuple(
            intent
            for intent in self._intents
            if intent.start < end and intent.end > start
        )

    def sections(self) -> dict[str, tuple[ChoreographyIntent, ...]]:
        grouped: dict[str, list[ChoreographyIntent]] = defaultdict(list)
        for intent in self._intents:
            grouped[intent.section].append(intent)
        return {key: tuple(value) for key, value in grouped.items()}

    def styles(self) -> dict[str, tuple[ChoreographyIntent, ...]]:
        grouped: dict[str, list[ChoreographyIntent]] = defaultdict(list)
        for intent in self._intents:
            grouped[intent.style].append(intent)
        return {key: tuple(value) for key, value in grouped.items()}

    def detect_overlaps(self) -> tuple[IntentOverlap, ...]:
        overlaps: list[IntentOverlap] = []

        for index, left in enumerate(self._intents):
            for right in self._intents[index + 1 :]:
                if right.start >= left.end:
                    break

                overlap_start = max(left.start, right.start)
                overlap_end = min(left.end, right.end)

                if overlap_end > overlap_start:
                    overlaps.append(
                        IntentOverlap(
                            left=left,
                            right=right,
                            overlap_start=overlap_start,
                            overlap_end=overlap_end,
                        )
                    )

        return tuple(overlaps)

    def timeline_density(self, resolution: float = 1.0) -> list[tuple[float, int]]:
        if resolution <= 0:
            raise ValueError("resolution must be positive")

        if not self._intents:
            return []

        current = self.start
        output: list[tuple[float, int]] = []

        while current < self.end:
            active = self.within_window(current, current + resolution)
            output.append((round(current, 6), len(active)))
            current += resolution

        return output

    def ordered_sections(self) -> tuple[str, ...]:
        ordered: list[str] = []
        seen: set[str] = set()

        for intent in self._intents:
            if intent.section not in seen:
                seen.add(intent.section)
                ordered.append(intent.section)

        return tuple(ordered)

    def to_dict(self) -> dict:
        return {
            "start": self.start,
            "end": self.end,
            "duration": self.duration,
            "intent_count": len(self._intents),
            "ordered_sections": list(self.ordered_sections()),
            "intents": [intent.to_dict() for intent in self._intents],
        }

    @classmethod
    def from_sequence(cls, intents: Sequence[ChoreographyIntent]) -> "IntentGraph":
        return cls(intents)
