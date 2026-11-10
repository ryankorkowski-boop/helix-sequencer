"""Shared showcase trace contracts.

The trace layer is deliberately source-neutral and legal-safe. It represents
synthetic, internal, or permissioned per-section/per-beat telemetry. It does not
store raw copyrighted media, downloaded videos, or externally authored choreography.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping


@dataclass(frozen=True)
class SectionTrace:
    name: str
    kind: str = "unknown"
    start: float = 0.0
    end: float = 0.0
    intensity: float = 0.5
    breadth: float = 0.5
    motion: float = 0.5
    darkness: float = 0.0
    hero_share: float = 0.0
    palette: str = ""
    colors: tuple[str, ...] = field(default_factory=tuple)

    @property
    def duration(self) -> float:
        return max(0.0, self.end - self.start)

    @property
    def visual_energy(self) -> float:
        return _clamp01((0.45 * self.intensity) + (0.25 * self.breadth) + (0.2 * self.motion) + (0.1 * (1.0 - self.darkness)))

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "kind": self.kind,
            "start": self.start,
            "end": self.end,
            "intensity": self.intensity,
            "breadth": self.breadth,
            "motion": self.motion,
            "darkness": self.darkness,
            "hero_share": self.hero_share,
            "palette": self.palette,
            "colors": list(self.colors),
            "visual_energy": self.visual_energy,
        }


def normalize_section_trace(raw: Mapping[str, object] | SectionTrace) -> SectionTrace:
    if isinstance(raw, SectionTrace):
        return raw
    colors_raw = raw.get("colors", ())
    if isinstance(colors_raw, str):
        colors = (colors_raw,)
    elif isinstance(colors_raw, Iterable):
        colors = tuple(str(color) for color in colors_raw if str(color).strip())
    else:
        colors = ()
    return SectionTrace(
        name=str(raw.get("name", raw.get("kind", "unknown"))),
        kind=str(raw.get("kind", "unknown")),
        start=float(raw.get("start", 0.0)),
        end=float(raw.get("end", 0.0)),
        intensity=_clamp01(float(raw.get("intensity", raw.get("target_intensity", 0.5)))),
        breadth=_clamp01(float(raw.get("breadth", raw.get("prop_breadth", 0.5)))),
        motion=_clamp01(float(raw.get("motion", raw.get("motion_amount", 0.5)))),
        darkness=_clamp01(float(raw.get("darkness", 0.0))),
        hero_share=_clamp01(float(raw.get("hero_share", 0.0))),
        palette=str(raw.get("palette", "")),
        colors=colors,
    )


def normalize_section_traces(raw_sections: Iterable[Mapping[str, object] | SectionTrace]) -> list[SectionTrace]:
    return sorted((normalize_section_trace(section) for section in raw_sections), key=lambda section: section.start)


def mean(values: Iterable[float]) -> float:
    items = list(values)
    return sum(items) / len(items) if items else 0.0


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))
