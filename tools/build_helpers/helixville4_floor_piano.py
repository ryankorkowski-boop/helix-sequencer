from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PianoKeySpec:
    note: str
    label: str
    key_type: str
    octave_band: str
    x: int
    width: int
    y: int
    height: int
    count: int


WHITE_NOTES = ("C", "D", "E", "F", "G", "A", "B")
BLACK_AFTER = {"C": "CS", "D": "DS", "F": "FS", "G": "GS", "A": "AS"}

FLOOR_PIANO_ANIMATION_STATES: tuple[str, ...] = (
    "idle_shimmer",
    "note_hit",
    "melody_run",
    "chord_bloom",
    "bass_note_pulse",
    "sustain_trail",
    "octave_sweep",
    "left_to_right_chase",
    "drop_impact",
    "finale_all_keys",
)


def _build_keys() -> tuple[PianoKeySpec, ...]:
    keys: list[PianoKeySpec] = []
    white_w = 6
    black_w = 4
    white_h = 28
    black_h = 17
    x = 4
    for octave_band in ("LOW", "HIGH"):
        for note in WHITE_NOTES:
            label = f"{note}_{octave_band}"
            keys.append(PianoKeySpec(note=note, label=label, key_type="white", octave_band=octave_band, x=x, width=white_w, y=8, height=white_h, count=18))
            if note in BLACK_AFTER:
                black_note = BLACK_AFTER[note]
                keys.append(PianoKeySpec(note=black_note, label=f"{black_note}_{octave_band}", key_type="black", octave_band=octave_band, x=x + white_w - 2, width=black_w, y=8, height=black_h, count=12))
            x += white_w + 1
    return tuple(keys)


FLOOR_PIANO_KEYS: tuple[PianoKeySpec, ...] = _build_keys()


def note_submodel_name(label: str) -> str:
    return f"HX_FLOOR_PIANO_{label}"


def note_order() -> tuple[str, ...]:
    return tuple(key.label for key in FLOOR_PIANO_KEYS)


def pitch_class_to_floor_piano_labels(pitch_class: str) -> tuple[str, ...]:
    normalized = pitch_class.strip().upper().replace("#", "S")
    return tuple(key.label for key in FLOOR_PIANO_KEYS if key.note == normalized)


def chord_to_floor_piano_labels(pitch_classes: tuple[str, ...]) -> tuple[str, ...]:
    labels: list[str] = []
    for pitch_class in pitch_classes:
        labels.extend(pitch_class_to_floor_piano_labels(pitch_class))
    return tuple(dict.fromkeys(labels))


def _rect_points(x: int, y: int, w: int, h: int, count: int) -> list[tuple[int, int]]:
    perimeter: list[tuple[int, int]] = []
    for px in range(x, x + w):
        perimeter.append((px, y))
    for py in range(y + 1, y + h):
        perimeter.append((x + w - 1, py))
    for px in range(x + w - 2, x - 1, -1):
        perimeter.append((px, y + h - 1))
    for py in range(y + h - 2, y, -1):
        perimeter.append((x, py))
    if not perimeter:
        return [(x, y)] * count
    return [perimeter[int(idx * len(perimeter) / count) % len(perimeter)] for idx in range(count)]


def _line_points(x1: int, y1: int, x2: int, y2: int, count: int) -> list[tuple[int, int]]:
    points: list[tuple[int, int]] = []
    for idx in range(count):
        ratio = 0 if count <= 1 else idx / (count - 1)
        points.append((round(x1 + (x2 - x1) * ratio), round(y1 + (y2 - y1) * ratio)))
    return points


def build_floor_piano_custom_model(width: int = 104, height: int = 44) -> tuple[str, list[tuple[str, int, int]]]:
    grid = [["." for _ in range(width)] for _ in range(height)]
    cursor = 1
    runs: list[tuple[str, int, int]] = []

    def put_points(name: str, points: list[tuple[int, int]]) -> None:
        nonlocal cursor
        start = cursor
        for x, y in points:
            if 0 <= x < width and 0 <= y < height:
                grid[y][x] = str(cursor)
            cursor += 1
        runs.append((name, start, cursor - 1))

    for key in FLOOR_PIANO_KEYS:
        put_points(note_submodel_name(key.label), _rect_points(key.x, key.y, key.width, key.height, key.count))

    white_points: list[tuple[int, int]] = []
    black_points: list[tuple[int, int]] = []
    low_points: list[tuple[int, int]] = []
    high_points: list[tuple[int, int]] = []
    for key in FLOOR_PIANO_KEYS:
        center = (key.x + key.width // 2, key.y + key.height // 2)
        if key.key_type == "white":
            white_points.append(center)
        else:
            black_points.append(center)
        if key.octave_band == "LOW":
            low_points.append(center)
        else:
            high_points.append(center)

    put_points("HX_FLOOR_PIANO_WHITE_KEYS", white_points)
    put_points("HX_FLOOR_PIANO_BLACK_KEYS", black_points)
    put_points("HX_FLOOR_PIANO_OCTAVE_LOW", low_points)
    put_points("HX_FLOOR_PIANO_OCTAVE_HIGH", high_points)
    put_points("HX_FLOOR_PIANO_CHORD_BLOOM", _line_points(4, 38, width - 5, 38, 48))
    put_points("HX_FLOOR_PIANO_SUSTAIN_GLOW", _line_points(4, 40, width - 5, 40, 48))
    put_points("HX_FLOOR_PIANO_LEFT_TO_RIGHT_CHASE", _line_points(4, 4, width - 5, 4, 52))
    put_points("HX_FLOOR_PIANO_VELOCITY_LANE", _line_points(4, 42, width - 5, 42, 52))
    put_points("HX_FLOOR_PIANO_PLATFORM", _line_points(2, height - 1, width - 3, height - 1, 60))

    text = ";".join(",".join(row) for row in grid)
    return text, runs


def add_floor_piano_model(models_el: ET.Element, *, start_channel: int = 920000) -> ET.Element:
    width = 104
    height = 44
    custom_model, runs = build_floor_piano_custom_model(width, height)
    model = ET.SubElement(models_el, "model", {
        "name": "HX_FLOOR_PIANO",
        "DisplayAs": "Custom",
        "WorldPosX": "315.000",
        "WorldPosY": "-12.000",
        "WorldPosZ": "1.000",
        "StartChannel": str(start_channel),
        "StringType": "RGB Nodes",
        "parm1": str(width),
        "parm2": str(height),
        "CustomWidth": str(width),
        "CustomHeight": str(height),
        "CustomModel": custom_model,
        "HelixVisualTarget": "docs/HELIXVILLE4_FLOOR_PIANO_TARGET.md",
        "HelixImplementationState": "floor_piano_note_reactive_v1",
        "HelixAnimationStates": ",".join(FLOOR_PIANO_ANIMATION_STATES),
        "HelixSequenceAxis": "low_to_high",
        "HelixNoteOrder": ",".join(note_order()),
        "HelixNodeCount": str(runs[-1][2] if runs else 0),
    })
    for name, start, end in runs:
        ET.SubElement(model, "subModel", {"name": name, "line0": f"{start}-{end}", "HelixPixelCount": str(end - start + 1)})
    return model


def add_floor_piano_to_layout(layout_path: Path) -> None:
    tree = ET.parse(layout_path)
    root = tree.getroot()
    models_el = root.find("models") or ET.SubElement(root, "models")
    groups_el = root.find("modelGroups") or ET.SubElement(root, "modelGroups")
    add_floor_piano_model(models_el)
    ET.SubElement(groups_el, "modelGroup", {"name": "HX_FLOOR_PIANO_GROUP", "models": "HX_FLOOR_PIANO"})
    ET.SubElement(groups_el, "modelGroup", {"name": "HX_SEQUENTIAL_MUSIC_PROPS", "models": "HX_FLOOR_PIANO"})
    tree.write(layout_path, encoding="utf-8", xml_declaration=True)
