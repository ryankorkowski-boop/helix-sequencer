from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from core.birdsong_xsq_export import DEFAULT_BIRDSONG_MODEL, emit_birdsong_xsq_sequence, write_birdsong_xsq
from tools.export_birdsong_demo_manifest import build_birdsong_demo_intents
from tools.validate_xsq_structure import validate_xsq


def test_emit_birdsong_xsq_sequence_contains_skeleton_and_element_effects() -> None:
    intents = build_birdsong_demo_intents(duration_seconds=4.0, step_seconds=1.0, bpm=120.0)
    sequence = emit_birdsong_xsq_sequence(intents=intents)
    root = ET.fromstring(sequence.xml_text)

    assert root.tag == "xsequence"
    assert root.attrib["name"] == "HelixBirdsongDemo"
    assert root.attrib["model"] == DEFAULT_BIRDSONG_MODEL
    assert root.find("timingtrack") is not None
    assert root.find("effects") is not None
    assert root.find("ElementEffects") is not None

    element_effects = root.find("ElementEffects")
    elements = element_effects.findall("Element")
    assert [element.attrib["type"] for element in elements] == ["timing", "model"]


def test_write_birdsong_xsq_validates_with_existing_validator(tmp_path: Path) -> None:
    intents = build_birdsong_demo_intents(duration_seconds=6.0, step_seconds=1.0, bpm=120.0)
    output = write_birdsong_xsq(tmp_path / "birdsong.xsq", intents)

    validate_xsq(output)
    assert output.exists()


def test_birdsong_xsq_preserves_intent_effect_metadata() -> None:
    intents = build_birdsong_demo_intents(duration_seconds=5.0, step_seconds=1.0, bpm=120.0)
    root = ET.fromstring(emit_birdsong_xsq_sequence(intents=intents).xml_text)

    timing_entries = root.find("timingtrack").findall("phoneme")
    effect_entries = root.find("effects").findall("effect")
    model_effects = root.find("ElementEffects").findall("Element")[1].find("EffectLayer").findall("Effect")

    assert len(timing_entries) == len(intents)
    assert len(effect_entries) == len(intents)
    assert len(model_effects) == len(intents)

    for idx, intent in enumerate(sorted(intents, key=lambda item: (item.start_time, item.effect_name, item.score))):
        timing = timing_entries[idx]
        effect = effect_entries[idx]
        model_effect = model_effects[idx]

        assert timing.attrib["index"] == str(idx)
        assert timing.attrib["phoneme"] == intent.effect_name
        assert timing.attrib["motif"] == intent.motif
        assert timing.attrib["direction"] == intent.direction
        assert effect.attrib["type"] == intent.effect_name
        assert model_effect.attrib["name"] == intent.effect_name
        assert model_effect.attrib["startTime"] == str(int(round(intent.start_time * 1000.0)))
        assert model_effect.attrib["endTime"] == str(int(round(intent.end_time * 1000.0)))


def test_birdsong_xsq_output_is_deterministic() -> None:
    intents = build_birdsong_demo_intents(duration_seconds=8.0, step_seconds=1.0, bpm=120.0)

    first = emit_birdsong_xsq_sequence(intents=intents).xml_text
    second = emit_birdsong_xsq_sequence(intents=tuple(reversed(intents))).xml_text

    assert first == second
