from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from core.sequential_layering import (
    LayerEvent,
    chord_to_members,
    melody_run,
    pitch_to_member,
)

FloorPianoTrigger = Literal[
    "idle",
    "note_hit",
    "melody_run",
    "chord_bloom",
    "bass_note",
    "sustain",
    "octave_sweep",
    "drop",
    "finale",
]


@dataclass(frozen=True)
class FloorPianoAnimationPlan:
    trigger: FloorPianoTrigger
    events: tuple[LayerEvent, ...]
    description: str


def plan_note_hit(pitch_class: str, octave: Literal["LOW", "HIGH"] = "LOW", *, velocity: float = 1.0) -> FloorPianoAnimationPlan:
    key = pitch_to_member("HX_FLOOR_PIANO", pitch_class, octave)
    intensity = max(0.0, min(1.0, velocity))
    return FloorPianoAnimationPlan(
        trigger="note_hit",
        events=(
            LayerEvent(layer="event", members=(key,), intensity=intensity, sustain_ms=160, source="pitch_note"),
            LayerEvent(layer="sustain", members=("HX_FLOOR_PIANO_SUSTAIN_GLOW",), intensity=intensity * 0.45, sustain_ms=520, source="pitch_note_decay"),
        ),
        description=f"Pulse {key} with sustain glow.",
    )


def plan_chord_bloom(root_pitch: str, quality: str = "major", *, velocity: float = 1.0) -> FloorPianoAnimationPlan:
    keys = chord_to_members("HX_FLOOR_PIANO", root_pitch, quality)
    intensity = max(0.0, min(1.0, velocity))
    return FloorPianoAnimationPlan(
        trigger="chord_bloom",
        events=(
            LayerEvent(layer="event", members=keys, intensity=intensity, sustain_ms=260, source="chord_notes"),
            LayerEvent(layer="accent", members=("HX_FLOOR_PIANO_CHORD_BLOOM",), intensity=intensity, sustain_ms=180, source="chord_bloom"),
            LayerEvent(layer="sustain", members=("HX_FLOOR_PIANO_SUSTAIN_GLOW",), intensity=intensity * 0.55, sustain_ms=900, source="chord_sustain"),
        ),
        description=f"Bloom {root_pitch} {quality} across ordered note keys.",
    )


def plan_melody_run(start_index: int, end_index: int, *, velocity: float = 0.8) -> FloorPianoAnimationPlan:
    keys = melody_run("HX_FLOOR_PIANO", start_index, end_index)
    intensity = max(0.0, min(1.0, velocity))
    return FloorPianoAnimationPlan(
        trigger="melody_run",
        events=(
            LayerEvent(layer="motion", members=keys, intensity=intensity, sustain_ms=360, source="melody_contour"),
            LayerEvent(layer="motion", members=("HX_FLOOR_PIANO_LEFT_TO_RIGHT_CHASE",), intensity=intensity * 0.65, sustain_ms=360, source="melody_chase_lane"),
        ),
        description="Run across ordered keys using the generic sequential layering engine.",
    )


def plan_bass_note(pitch_class: str, *, velocity: float = 1.0) -> FloorPianoAnimationPlan:
    key = pitch_to_member("HX_FLOOR_PIANO", pitch_class, "LOW")
    intensity = max(0.0, min(1.0, velocity))
    return FloorPianoAnimationPlan(
        trigger="bass_note",
        events=(
            LayerEvent(layer="event", members=(key, "HX_FLOOR_PIANO_OCTAVE_LOW"), intensity=intensity, sustain_ms=220, source="bass_note"),
            LayerEvent(layer="accent", members=("HX_FLOOR_PIANO_VELOCITY_LANE",), intensity=intensity * 0.8, sustain_ms=120, source="bass_velocity"),
        ),
        description=f"Emphasize low-octave {pitch_class} for bass-linked sequencing.",
    )


def plan_drop_impact(*, intensity: float = 1.0) -> FloorPianoAnimationPlan:
    level = max(0.0, min(1.0, intensity))
    return FloorPianoAnimationPlan(
        trigger="drop",
        events=(
            LayerEvent(layer="accent", members=("HX_FLOOR_PIANO_WHITE_KEYS", "HX_FLOOR_PIANO_BLACK_KEYS"), intensity=level, sustain_ms=140, source="drop_impact"),
            LayerEvent(layer="motion", members=("HX_FLOOR_PIANO_LEFT_TO_RIGHT_CHASE",), intensity=level, sustain_ms=360, source="drop_sweep"),
            LayerEvent(layer="sustain", members=("HX_FLOOR_PIANO_SUSTAIN_GLOW",), intensity=level * 0.7, sustain_ms=900, source="drop_decay"),
            LayerEvent(layer="accent", members=("HX_FLOOR_PIANO_PLATFORM",), intensity=level, sustain_ms=220, source="platform_hit"),
        ),
        description="Full keyboard drop impact with chase and sustain decay.",
    )


def plan_idle_shimmer() -> FloorPianoAnimationPlan:
    return FloorPianoAnimationPlan(
        trigger="idle",
        events=(
            LayerEvent(layer="base", members=("HX_FLOOR_PIANO_WHITE_KEYS", "HX_FLOOR_PIANO_BLACK_KEYS"), intensity=0.16, sustain_ms=1200, source="idle_shimmer"),
        ),
        description="Low-level ambient shimmer for the floor piano.",
    )
