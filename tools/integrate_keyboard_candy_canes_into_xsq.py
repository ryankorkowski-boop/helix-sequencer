from __future__ import annotations

import argparse
import json
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Iterable

from audio.musical_event_model import MusicalEvent
from audio.audio_intelligence_orchestrator import build_musical_event_map

# Former Helix keyboard/candy-cane routing:
# C4..C5 natural notes drive matching North 6..13 and South 3..10.
# Both sides are intentionally lit for each recognized note.
NORTH_BY_NOTE = {
    "C4": "North Candy Cane 6",
    "D4": "North Candy Cane 7",
    "E4": "North Candy Cane 8",
    "F4": "North Candy Cane 9",
    "G4": "North Candy Cane 10",
    "A4": "North Candy Cane 11",
    "B4": "North Candy Cane 12",
    "C5": "North Candy Cane 13",
}
SOUTH_BY_NOTE = {
    "C4": "South Candy Cane 3",
    "D4": "South Candy Cane 4",
    "E4": "South Candy Cane 5",
    "F4": "South Candy Cane 6",
    "G4": "South Candy Cane 7",
    "A4": "South Candy Cane 8",
    "B4": "South Candy Cane 9",
    "C5": "South Candy Cane 10",
}
NOTE_TO_MODELS = {
    note: (NORTH_BY_NOTE[note], SOUTH_BY_NOTE[note]) for note in NORTH_BY_NOTE
}


def _norm_note(value: str | None) -> str | None:
    if not value:
        return None
    text = str(value).strip().upper().replace("♯", "#")
    # Former timing-track labels are natural notes C4..C5. Do not silently
    # reinterpret accidentals or octave-shifted notes.
    return text if text in NOTE_TO_MODELS else None


def extract_polyphonic_timing_events(root: ET.Element) -> list[tuple[str, int, int]]:
    """Read note labels from the actual Polyphonic Transcription timing element."""
    events: list[tuple[str, int, int]] = []
    candidates: list[ET.Element] = []

    for element in root.findall(".//Element"):
        if element.get("type") == "timing" and element.get("name") == "Polyphonic Transcription":
            candidates.append(element)
    for track in root.findall(".//timingtrack"):
        if track.get("name") == "Polyphonic Transcription":
            candidates.append(track)

    # De-duplicate elements while preserving document order.
    seen: set[int] = set()
    unique = []
    for element in candidates:
        marker = id(element)
        if marker not in seen:
            seen.add(marker)
            unique.append(element)

    for element in unique:
        for effect in element.findall(".//Effect"):
            label = _norm_note(effect.get("label") or effect.get("name"))
            if label is None:
                continue
            try:
                start = int(float(effect.get("startTime", "0")))
                end = int(float(effect.get("endTime", str(start + 50))))
            except (TypeError, ValueError):
                continue
            if end <= start:
                end = start + 50
            events.append((label, max(0, start), end))

    events.sort(key=lambda item: (item[1], item[2], item[0]))
    return events


def _element_effects(root: ET.Element) -> ET.Element:
    container = root.find("ElementEffects")
    return container if container is not None else ET.SubElement(root, "ElementEffects")


def _elements(container: ET.Element) -> dict[str, ET.Element]:
    return {e.get("name", ""): e for e in container.findall("Element") if e.get("name")}


def _layer(container: ET.Element, elements: dict[str, ET.Element], name: str, layer_name: str) -> ET.Element:
    element = elements.get(name)
    if element is None:
        element = ET.SubElement(container, "Element", {"type": "model", "name": name})
        elements[name] = element
    for layer in element.findall("EffectLayer"):
        if layer.get("name") == layer_name:
            return layer
    return ET.SubElement(element, "EffectLayer", {"name": layer_name, "visible": "1"})


def _clear(layer: ET.Element) -> None:
    for child in list(layer):
        layer.remove(child)


def _add_on(layer: ET.Element, start: int, end: int, brightness: float) -> None:
    # Preserve the old AC-safe attack/hold/release intent as a bounded On hit.
    # xLights applies the actual channel transition; duration remains the note
    # duration from the transcription timing track.
    ET.SubElement(
        layer,
        "Effect",
        {
            "name": "On",
            "startTime": str(start),
            "endTime": str(max(start + 50, end)),
            "settings": (
                "E_CHECKBOX_OverlayBkg=0,"
                f"E_SLIDER_Brightness={max(0.0, min(1.0, brightness)):.3f}"
            ),
            "palette": (
                "C_BUTTON_Palette1=#FFFFFF,"
                "C_BUTTON_Palette2=#FFFFFF,"
                "C_BUTTON_Palette3=#FFFFFF"
            ),
            "source": "HelixKeyboardCandyCane",
            "sourceNote": "",
        },
    )


def _normalized_keyboard_note_events(events: Iterable[MusicalEvent]) -> list[tuple[str, int, int, float]]:
    mapped: list[tuple[str, int, int, float]] = []
    for event in events:
        if event.kind not in {"note_event", "note"}:
            continue
        if (event.instrument or "").lower() not in {"keyboard", "piano", "mix_harmonic", "bass", ""}:
            continue
        pitch = event.pitch_midi
        if pitch is None:
            note_name = str(event.metadata.get("note_name", ""))
        else:
            midi = int(round(float(pitch)))
            octave = (midi // 12) - 1
            names = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
            note_name = f"{names[midi % 12]}{octave}"
        note = _norm_note(note_name)
        if note is None:
            continue
        start = max(0, int(event.time_ms))
        end = max(start + 50, start + int(event.duration_ms or 50))
        event_brightness = max(0.0, min(1.0, float(event.strength or event.confidence)))
        mapped.append((note, start, end, event_brightness))
    mapped.sort(key=lambda item: (item[1], item[2], item[0]))
    return mapped


def _melody_run_note_events(events: Iterable[MusicalEvent]) -> list[tuple[str, int, int, float]]:
    routed: list[tuple[str, int, int, float]] = []
    for event in events:
        if event.kind != "melody_run":
            continue
        pitches = event.metadata.get("pitches_midi") or []
        if not isinstance(pitches, list) or len(pitches) < 2:
            continue
        start = max(0, int(event.time_ms))
        duration = max(50, int(event.duration_ms or 50))
        step = max(25, duration // len(pitches))
        for index, pitch in enumerate(pitches):
            try:
                midi = int(round(float(pitch)))
            except (TypeError, ValueError):
                continue
            octave = (midi // 12) - 1
            names = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
            note = _norm_note(f"{names[midi % 12]}{octave}")
            if note is None:
                continue
            hit_start = start + index * step
            hit_end = min(start + duration, hit_start + step)
            if hit_end <= hit_start:
                hit_end = hit_start + 50
            routed.append((note, hit_start, hit_end, float(event.strength or event.confidence)))
    return routed


def inject_keyboard_candy_canes(
    base_xsq: Path,
    output_xsq: Path,
    *,
    layer_name: str = "AUTO_Keyboard_CandyCanes",
    brightness: float = 1.0,
    normalized_events: Iterable[MusicalEvent] | None = None,
    audio_path: Path | None = None,
) -> dict[str, object]:
    if not base_xsq.exists():
        raise FileNotFoundError(f"Missing XSQ: {base_xsq}")

    if output_xsq.resolve() != base_xsq.resolve():
        output_xsq.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(base_xsq, output_xsq)

    tree = ET.parse(output_xsq)
    root = tree.getroot()
    if normalized_events is None and audio_path is not None:
        normalized_events = build_musical_event_map(audio_path).events
    normalized_source = list(normalized_events or ())
    normalized_note_events = _normalized_keyboard_note_events(normalized_source)
    melody_run_events = _melody_run_note_events(normalized_source)
    legacy_note_events = extract_polyphonic_timing_events(root)
    if normalized_note_events:
        note_events = normalized_note_events
        source_timing_track = "helix.musical_event_map.note_event"
    elif legacy_note_events:
        note_events = [(note, start, end, 1.0) for note, start, end in legacy_note_events]
        source_timing_track = "Polyphonic Transcription"
    else:
        raise RuntimeError(
            "No recognized C4-C5 natural-note events were supplied by the normalized "
            "event map or the Polyphonic Transcription timing track; refusing to "
            "produce a fake candy-cane preview."
        )

    container = _element_effects(root)
    elements = _elements(container)
    target_names = sorted({model for pair in NOTE_TO_MODELS.values() for model in pair})
    layers = {
        name: _layer(container, elements, name, layer_name)
        for name in target_names
    }
    for target in layers.values():
        _clear(target)

    placements = 0
    note_counts = {note: 0 for note in NOTE_TO_MODELS}
    for note, start, end, event_brightness in note_events:
        for model_name in NOTE_TO_MODELS[note]:
            _add_on(layers[model_name], start, end, min(brightness, event_brightness))
            placements += 1
        note_counts[note] += 1

    if layer_name not in {item.get("name") for item in root.findall("timingtrack")}:
        ET.SubElement(root, "timingtrack", {"name": layer_name})
    if melody_run_events:
        melody_layers = {
            name: _layer(container, elements, name, melody_layer_name)
            for name in target_names
        }
        for target in melody_layers.values():
            _clear(target)
        for note, start, end, event_brightness in melody_run_events:
            for model_name in NOTE_TO_MODELS[note]:
                _add_on(melody_layers[model_name], start, end, min(brightness, event_brightness))
        if melody_layer_name not in {item.get("name") for item in root.findall("timingtrack")}:
            ET.SubElement(root, "timingtrack", {"name": melody_layer_name})

        # Build a directional companion lane from the same normalized melody runs.
        # It does not replace the former mapping: it adds an inspectable traversal
        # cue so ascending phrases travel forward and descending phrases travel back.
        direction_layer = "AUTO_Keyboard_MelodyDirection"
        direction_timing = root.find("timingtrack")
        for run in normalized_source:
            if run.kind != "melody_run":
                continue
            direction = str(run.metadata.get("direction", "")).lower()
            pitches = run.metadata.get("pitches_midi") or []
            if len(pitches) < 2:
                continue
            ordered_notes = []
            for pitch in pitches:
                try:
                    midi = int(round(float(pitch)))
                except (TypeError, ValueError):
                    continue
                octave = (midi // 12) - 1
                names = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
                note = _norm_note(f"{names[midi % 12]}{octave}")
                if note is not None:
                    ordered_notes.append(note)
            if not ordered_notes:
                continue
            start = max(0, int(run.time_ms))
            duration = max(50, int(run.duration_ms or 50))
            step = max(25, duration // len(ordered_notes))
            sequence = ordered_notes if direction != "descending" else list(reversed(ordered_notes))
            for index, note in enumerate(sequence):
                hit_start = start + index * step
                hit_end = min(start + duration, hit_start + step)
                if hit_end <= hit_start:
                    hit_end = hit_start + 50
                for model_name in NOTE_TO_MODELS[note]:
                    _add_on(melody_layers[model_name], hit_start, hit_end, min(brightness, float(run.strength or run.confidence)))
        if direction_layer not in {item.get("name") for item in root.findall("timingtrack")}:
            ET.SubElement(root, "timingtrack", {"name": direction_layer})


    ET.indent(tree, space="  ")
    tree.write(output_xsq, encoding="utf-8", xml_declaration=True)

    return {
        "schema": "helix.keyboard_candy_cane_routing.v1",
        "routing": {
            note: {"north": NORTH_BY_NOTE[note], "south": SOUTH_BY_NOTE[note]}
            for note in NOTE_TO_MODELS
        },
        "source_timing_track": source_timing_track,
        "normalized_note_events": len(normalized_note_events),
        "normalized_melody_run_events": len(melody_run_events),
        "legacy_note_events": len(legacy_note_events),
        "recognized_note_events": len(note_events),
        "placement_count": placements,
        "note_counts": note_counts,
        "ignored_notes": "All notes outside explicit C4-C5 natural-note mapping are ignored.",
        "simultaneous_sides": True,
        "output_xsq": str(output_xsq),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("base_xsq", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--layer", default="AUTO_Keyboard_CandyCanes")
    parser.add_argument("--brightness", type=float, default=1.0)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--audio", type=Path, help="Build normalized musical events from this audio before routing.")
    parser.add_argument("--audio", type=Path, help="Canonical audio source for normalized keyboard note events.")
    args = parser.parse_args()

    report = inject_keyboard_candy_canes(
        args.base_xsq,
        args.output,
        layer_name=args.layer,
        brightness=args.brightness,
        audio_path=args.audio,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
