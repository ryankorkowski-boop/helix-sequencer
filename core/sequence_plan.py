"""Minimal sequence plan contract for Helix competitive optimization.

Advisory only. Defines the data structure that later slices will populate and eventually
route the renderer through. No behavior change to existing sequence generation.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class SectionPlan:
    name: str  # intro, verse, chorus, bridge, finale, etc.
    start_ms: int = 0
    end_ms: int = 0
    target_intensity: float = 0.5  # 0.0-1.0
    palette_intent: str = "section_default"
    prop_emphasis: list[str] = field(default_factory=list)  # role names or model groups
    restraint_level: str = "balanced"  # low, balanced, high
    notes: str = ""


@dataclass
class SequencePlan:
    version: str = "0.1"
    song_length_ms: int = 0
    sections: list[SectionPlan] = field(default_factory=list)
    global_palette_family: str = "neutral"
    density_budget: str = "balanced"
    motif_families: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_minimal_plan(song_length_ms: int = 180_000) -> SequencePlan:
    """Return a simple default plan with placeholder sections.

    Later slices will replace this with real audio-derived structure.
    """
    if song_length_ms <= 0:
        song_length_ms = 180_000
    # Rough equal thirds as placeholders
    third = song_length_ms // 3
    sections = [
        SectionPlan(name="intro", start_ms=0, end_ms=third, target_intensity=0.3, restraint_level="high"),
        SectionPlan(name="body", start_ms=third, end_ms=2 * third, target_intensity=0.6, restraint_level="balanced"),
        SectionPlan(name="finale", start_ms=2 * third, end_ms=song_length_ms, target_intensity=0.9, restraint_level="low"),
    ]
    return SequencePlan(song_length_ms=song_length_ms, sections=sections)
