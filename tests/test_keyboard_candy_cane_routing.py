from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from tools.integrate_keyboard_candy_canes_into_xsq import (
    NOTE_TO_MODELS,
    extract_polyphonic_timing_events,
    inject_keyboard_candy_canes,
)


def _fixture() -> ET.Element:
    root = ET.Element("sequence")
    effects = ET.SubElement(root, "ElementEffects")
    timing = ET.SubElement(
        effects,
        "Element",
        {"type": "timing", "name": "Polyphonic Transcription"},
    )
    layer = ET.SubElement(timing, "EffectLayer", {"name": "Notes"})
    for model_name in sorted({model for pair in NOTE_TO_MODELS.values() for model in pair}):
        ET.SubElement(effects, "Element", {"type": "model", "name": model_name})
    for label, start, end in (
        ("C4", 50, 500),
        ("D4", 600, 900),
        ("C5", 1000, 1250),
        ("F#4", 1300, 1450),
        ("C3", 1500, 1650),
    ):
        ET.SubElement(
            layer,
            "Effect",
            {"label": label, "startTime": str(start), "endTime": str(end)},
        )
    return root


def test_exact_former_mapping():
    assert NOTE_TO_MODELS["C4"] == ("North Candy Cane 6", "South Candy Cane 3")
    assert NOTE_TO_MODELS["D4"] == ("North Candy Cane 7", "South Candy Cane 4")
    assert NOTE_TO_MODELS["E4"] == ("North Candy Cane 8", "South Candy Cane 5")
    assert NOTE_TO_MODELS["F4"] == ("North Candy Cane 9", "South Candy Cane 6")
    assert NOTE_TO_MODELS["G4"] == ("North Candy Cane 10", "South Candy Cane 7")
    assert NOTE_TO_MODELS["A4"] == ("North Candy Cane 11", "South Candy Cane 8")
    assert NOTE_TO_MODELS["B4"] == ("North Candy Cane 12", "South Candy Cane 9")
    assert NOTE_TO_MODELS["C5"] == ("North Candy Cane 13", "South Candy Cane 10")


def test_polyphonic_track_filters_to_explicit_natural_note_range():
    events = extract_polyphonic_timing_events(_fixture())
    assert events == [("C4", 50, 500), ("D4", 600, 900), ("C5", 1000, 1250)]


def test_injector_lights_both_sides_for_each_note(tmp_path: Path):
    base = tmp_path / "base.xsq"
    out = tmp_path / "mapped.xsq"
    ET.ElementTree(_fixture()).write(base, encoding="utf-8", xml_declaration=True)

    report = inject_keyboard_candy_canes(base, out)
    assert report["recognized_note_events"] == 3
    assert report["placement_count"] == 6
    assert report["simultaneous_sides"] is True

    root = ET.parse(out).getroot()
    for model in (
        "North Candy Cane 6",
        "North Candy Cane 7",
        "North Candy Cane 13",
        "South Candy Cane 3",
        "South Candy Cane 4",
        "South Candy Cane 10",
    ):
        effects = root.find("ElementEffects")
        element = next(e for e in effects.findall("Element") if e.get("name") == model)
        layer = element.find("EffectLayer")
        assert layer is not None
        assert len(layer.findall("Effect")) == 1

    # Out-of-range notes must not create mapped effects.
    effects = root.find("ElementEffects")
    assert not any(
        e.get("name") == "North Candy Cane 9" and e.find("EffectLayer/Effect") is not None
        for e in effects.findall("Element")
    )


def test_missing_polyphonic_notes_fails_loudly(tmp_path: Path):
    base = tmp_path / "empty.xsq"
    ET.ElementTree(ET.Element("sequence")).write(base, encoding="utf-8", xml_declaration=True)
    try:
        inject_keyboard_candy_canes(base, tmp_path / "out.xsq")
    except RuntimeError as exc:
        assert "Polyphonic Transcription" in str(exc)
    else:
        raise AssertionError("expected fail-loud missing timing track error")


def test_normalized_keyboard_events_prefer_event_map(tmp_path: Path):
    from audio.musical_event_model import MusicalEvent

    base = tmp_path / "base.xsq"
    out = tmp_path / "mapped.xsq"
    ET.ElementTree(_fixture()).write(base, encoding="utf-8", xml_declaration=True)

    events = [
        MusicalEvent(200, "note_event", 0.95, 0.80, instrument="mix_harmonic", duration_ms=300, pitch_midi=60, metadata={"note_name": "C4"}),
        MusicalEvent(700, "note_event", 0.90, 0.70, instrument="mix_harmonic", duration_ms=200, pitch_midi=62, metadata={"note_name": "D4"}),
    ]
    report = inject_keyboard_candy_canes(base, out, normalized_events=events)

    assert report["source_timing_track"] == "helix.musical_event_map.note_event"
    assert report["normalized_note_events"] == 2
    assert report["legacy_note_events"] == 3
    assert report["placement_count"] == 4

    root = ET.parse(out).getroot()
    effects = root.find("ElementEffects")
    c4 = next(e for e in effects.findall("Element") if e.get("name") == "North Candy Cane 6")
    d4 = next(e for e in effects.findall("Element") if e.get("name") == "North Candy Cane 7")
    assert c4.find("EffectLayer/Effect").get("startTime") == "200"
    assert d4.find("EffectLayer/Effect").get("startTime") == "700"


def test_normalized_melody_run_creates_sequential_candy_cane_layer(tmp_path: Path):
    from audio.musical_event_model import MusicalEvent

    base = tmp_path / "base.xsq"
    out = tmp_path / "mapped.xsq"
    ET.ElementTree(_fixture()).write(base, encoding="utf-8", xml_declaration=True)

    run = MusicalEvent(
        100,
        "melody_run",
        0.9,
        0.8,
        instrument="keyboard",
        duration_ms=400,
        pitch_midi=60,
        metadata={"pitches_midi": [60, 62, 64], "direction": "ascending"},
    )
    report = inject_keyboard_candy_canes(base, out, normalized_events=[run])
    assert report["normalized_melody_run_events"] == 3

    root = ET.parse(out).getroot()
    effects = root.find("ElementEffects")
    starts = []
    for name in ("North Candy Cane 6", "North Candy Cane 7", "North Candy Cane 8"):
        element = next(e for e in effects.findall("Element") if e.get("name") == name)
        layer = next(layer for layer in element.findall("EffectLayer") if layer.get("name") == "AUTO_Keyboard_MelodyRuns")
        starts.append(int(layer.find("Effect").get("startTime")))
    assert starts == [100, 233, 366]


def test_descending_melody_run_preserves_descending_candy_cane_order(tmp_path: Path):
    from audio.musical_event_model import MusicalEvent

    base = tmp_path / "base.xsq"
    out = tmp_path / "mapped.xsq"
    ET.ElementTree(_fixture()).write(base, encoding="utf-8", xml_declaration=True)

    run = MusicalEvent(
        100,
        "melody_run",
        0.95,
        0.85,
        instrument="keyboard",
        duration_ms=400,
        metadata={"pitches_midi": [67, 65, 64, 60], "direction": "descending"},
    )
    report = inject_keyboard_candy_canes(base, out, normalized_events=[run])
    assert report["normalized_melody_run_events"] == 4

    root = ET.parse(out).getroot()
    effects = root.find("ElementEffects")
    starts = []
    for name in ("North Candy Cane 10", "North Candy Cane 9", "North Candy Cane 8", "North Candy Cane 6"):
        element = next(e for e in effects.findall("Element") if e.get("name") == name)
        layer = next(layer for layer in element.findall("EffectLayer") if layer.get("name") == "AUTO_Keyboard_MelodyRuns")
        starts.append(int(layer.find("Effect").get("startTime")))
    assert starts == [100, 200, 300, 400]
