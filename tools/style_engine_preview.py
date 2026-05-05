"""Safe preview runner for Helix Style Engine.

This does NOT modify rendering. It runs style decisions over demo segments and
prints JSON so the decision layer can be inspected before renderer integration.
"""

from __future__ import annotations

import json

from tools.style_engine import AudioSegment, HelixStyleEngine, LayoutProfile


def build_demo_layout() -> LayoutProfile:
    return LayoutProfile.from_iterable(
        [
            {"name": "MegaTree", "role": "centerpiece"},
            {"name": "Arch_01", "role": "motion"},
            {"name": "HouseOutline", "role": "outline"},
            {"name": "Matrix", "role": "matrix"},
            {"name": "HelixStrand", "role": "centerpiece", "supports_3d": True},
        ]
    )


def demo_segments() -> list[AudioSegment]:
    return [
        AudioSegment(start=0.0, duration=0.5, section="intro", energy=0.2),
        AudioSegment(start=1.0, duration=0.5, section="verse", energy=0.4),
        AudioSegment(start=2.0, duration=0.5, section="chorus", energy=0.8),
        AudioSegment(start=3.0, duration=0.5, section="drop", energy=0.95, event_type="drop"),
    ]


def run_preview(style: str = "SpatialHelix") -> list[dict]:
    engine = HelixStyleEngine(style, build_demo_layout())
    return [engine.decide(segment).to_dict() for segment in demo_segments()]


if __name__ == "__main__":
    print(json.dumps(run_preview(), indent=2))
