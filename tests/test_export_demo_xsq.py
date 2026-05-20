from __future__ import annotations

from pathlib import Path
import xml.etree.ElementTree as ET

from tools.export_demo_xsq import build_demo_xsq_text, export_demo_xsq
from tools.validate_xsq_structure import validate_xsq


def test_generated_demo_is_deterministic():
    first = build_demo_xsq_text()
    second = build_demo_xsq_text()

    assert first == second


def test_export_writes_valid_xsq(tmp_path: Path):
    output = tmp_path / "demo.xsq"

    export_demo_xsq(output)

    assert output.exists()
    validate_xsq(output)

    xml = output.read_text(encoding="utf-8")

    assert "<xsequence" in xml
    assert "<timingtrack" in xml
    assert "<effects" in xml
    assert "phoneme" in xml


def test_demo_xsq_contains_ordered_matching_phonemes_and_effects(tmp_path: Path):
    output = export_demo_xsq(tmp_path / "demo.xsq")
    root = ET.fromstring(output.read_text(encoding="utf-8"))

    timing_track = root.find("timingtrack")
    effects = root.find("effects")

    assert timing_track is not None
    assert effects is not None

    phonemes = timing_track.findall("phoneme")
    effect_nodes = effects.findall("effect")

    assert phonemes
    assert len(phonemes) == len(effect_nodes)

    previous_start = -1.0
    for idx, (phoneme, effect) in enumerate(zip(phonemes, effect_nodes)):
        assert phoneme.attrib["index"] == str(idx)
        assert effect.attrib["index"] == str(idx)
        assert effect.attrib["type"] == "face"
        assert effect.attrib["phoneme"] == phoneme.attrib["phoneme"]
        assert effect.attrib["start"] == phoneme.attrib["start"]
        assert effect.attrib["duration"] == phoneme.attrib["duration"]

        start = float(phoneme.attrib["start"])
        duration = float(phoneme.attrib["duration"])
        intensity = float(phoneme.attrib["intensity"])

        assert start >= previous_start
        assert duration > 0
        assert 0.0 <= intensity <= 1.0
        previous_start = start


def test_demo_xsq_parameters_change_output_deterministically():
    low_energy = build_demo_xsq_text(section_energy=0.25, beat_interval=0.5, grid_division=2)
    high_energy = build_demo_xsq_text(section_energy=1.0, beat_interval=0.5, grid_division=2)
    coarser_grid = build_demo_xsq_text(section_energy=0.25, beat_interval=1.0, grid_division=1)

    assert low_energy == build_demo_xsq_text(section_energy=0.25, beat_interval=0.5, grid_division=2)
    assert low_energy != high_energy
    assert low_energy != coarser_grid
