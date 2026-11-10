from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

LayerRole = Literal["base", "event", "motion", "sustain", "accent"]
SequenceAxis = Literal[
    "low_to_high",
    "high_to_low",
    "left_to_right",
    "right_to_left",
    "bottom_to_top",
    "top_to_bottom",
]


@dataclass(frozen=True)
class SequentialGroup:
    group_name: str
    sequence_axis: SequenceAxis
    ordered_members: tuple[str, ...]
    families: dict[str, tuple[str, ...]]
    supported_layers: tuple[LayerRole, ...]


DEFAULT_LAYERS: tuple[LayerRole, ...] = (
    "base",
    "event",
    "motion",
    "sustain",
    "accent",
)


FLOOR_PIANO_GROUP = SequentialGroup(
    group_name="HX_FLOOR_PIANO",
    sequence_axis="low_to_high",
    ordered_members=(
        "HX_FLOOR_PIANO_C_LOW",
        "HX_FLOOR_PIANO_CS_LOW",
        "HX_FLOOR_PIANO_D_LOW",
        "HX_FLOOR_PIANO_DS_LOW",
        "HX_FLOOR_PIANO_E_LOW",
        "HX_FLOOR_PIANO_F_LOW",
        "HX_FLOOR_PIANO_FS_LOW",
        "HX_FLOOR_PIANO_G_LOW",
        "HX_FLOOR_PIANO_GS_LOW",
        "HX_FLOOR_PIANO_A_LOW",
        "HX_FLOOR_PIANO_AS_LOW",
        "HX_FLOOR_PIANO_B_LOW",
        "HX_FLOOR_PIANO_C_HIGH",
        "HX_FLOOR_PIANO_CS_HIGH",
        "HX_FLOOR_PIANO_D_HIGH",
        "HX_FLOOR_PIANO_DS_HIGH",
        "HX_FLOOR_PIANO_E_HIGH",
        "HX_FLOOR_PIANO_F_HIGH",
        "HX_FLOOR_PIANO_FS_HIGH",
        "HX_FLOOR_PIANO_G_HIGH",
        "HX_FLOOR_PIANO_GS_HIGH",
        "HX_FLOOR_PIANO_A_HIGH",
        "HX_FLOOR_PIANO_AS_HIGH",
        "HX_FLOOR_PIANO_B_HIGH",
    ),
    families={
        "white_keys": (
            "HX_FLOOR_PIANO_WHITE_KEYS",
        ),
        "black_keys": (
            "HX_FLOOR_PIANO_BLACK_KEYS",
        ),
        "low_octave": (
            "HX_FLOOR_PIANO_OCTAVE_LOW",
        ),
        "high_octave": (
            "HX_FLOOR_PIANO_OCTAVE_HIGH",
        ),
        "motion": (
            "HX_FLOOR_PIANO_LEFT_TO_RIGHT_CHASE",
        ),
        "sustain": (
            "HX_FLOOR_PIANO_SUSTAIN_GLOW",
        ),
        "accent": (
            "HX_FLOOR_PIANO_CHORD_BLOOM",
            "HX_FLOOR_PIANO_VELOCITY_LANE",
        ),
    },
    supported_layers=DEFAULT_LAYERS,
)


SEQUENTIAL_GROUPS: dict[str, SequentialGroup] = {
    FLOOR_PIANO_GROUP.group_name: FLOOR_PIANO_GROUP,
}


PITCH_CLASS_INDEX = {
    "C": 0,
    "CS": 1,
    "D": 2,
    "DS": 3,
    "E": 4,
    "F": 5,
    "FS": 6,
    "G": 7,
    "GS": 8,
    "A": 9,
    "AS": 10,
    "B": 11,
}


NOTE_LABELS = tuple(PITCH_CLASS_INDEX.keys())


@dataclass(frozen=True)
class LayerEvent:
    layer: LayerRole
    members: tuple[str, ...]
    intensity: float
    sustain_ms: int
    source: str


@dataclass(frozen=True)
class ChordMapping:
    root: str
    quality: str
    pitch_classes: tuple[str, ...]


CHORD_LIBRARY: dict[str, ChordMapping] = {
    "major": ChordMapping(root="", quality="major", pitch_classes=("C", "E", "G")),
    "minor": ChordMapping(root="", quality="minor", pitch_classes=("C", "DS", "G")),
    "sus2": ChordMapping(root="", quality="sus2", pitch_classes=("C", "D", "G")),
    "sus4": ChordMapping(root="", quality="sus4", pitch_classes=("C", "F", "G")),
}


def sequential_group(name: str) -> SequentialGroup:
    return SEQUENTIAL_GROUPS[name]


def ordered_members(name: str) -> tuple[str, ...]:
    return sequential_group(name).ordered_members


def pitch_to_member(group_name: str, pitch_class: str, octave: Literal["LOW", "HIGH"] = "LOW") -> str:
    normalized = pitch_class.strip().upper().replace("#", "S")
    member = f"HX_FLOOR_PIANO_{normalized}_{octave}"
    if member not in sequential_group(group_name).ordered_members:
        raise KeyError(f"Pitch class {normalized} is not mapped in {group_name}")
    return member


def chord_to_members(group_name: str, root_pitch: str, quality: str = "major") -> tuple[str, ...]:
    normalized_root = root_pitch.strip().upper().replace("#", "S")
    if normalized_root not in PITCH_CLASS_INDEX:
        raise KeyError(normalized_root)
    mapping = CHORD_LIBRARY[quality]
    root_index = PITCH_CLASS_INDEX[normalized_root]
    resolved: list[str] = []
    for pc in mapping.pitch_classes:
        interval_index = PITCH_CLASS_INDEX[pc]
        final_index = (root_index + interval_index) % 12
        note = NOTE_LABELS[final_index]
        resolved.append(pitch_to_member(group_name, note, "LOW"))
        resolved.append(pitch_to_member(group_name, note, "HIGH"))
    return tuple(dict.fromkeys(resolved))


def melody_run(group_name: str, start_index: int, end_index: int) -> tuple[str, ...]:
    members = ordered_members(group_name)
    start = max(0, min(len(members) - 1, start_index))
    end = max(0, min(len(members) - 1, end_index))
    if start <= end:
        return members[start : end + 1]
    return tuple(reversed(members[end : start + 1]))


def layer_merge_priority(layer: LayerRole) -> int:
    priorities = {
        "base": 10,
        "motion": 20,
        "sustain": 30,
        "event": 40,
        "accent": 50,
    }
    return priorities[layer]


def merge_layer_events(events: tuple[LayerEvent, ...]) -> tuple[LayerEvent, ...]:
    return tuple(sorted(events, key=lambda event: layer_merge_priority(event.layer)))
