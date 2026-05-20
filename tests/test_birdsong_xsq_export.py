from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from core.birdsong_layout_targets import load_helixville3_target_pool
from core.birdsong_xsq_export import DEFAULT_BIRDSONG_MODEL, emit_birdsong_xsq_sequence, write_birdsong_xsq
from tools.export_birdsong_demo_manifest import build_birdsong_demo_intents
from tools.validate_xsq_structure import validate_xsq


def test_emit_birdsong_xsq_sequence_contains_skeleton_and_element_effects() -> None:
    intents = build_birdsong_demo_intents(duration_seconds=4.0, step_seconds=1.0, bpm=120.0)
    model_pool = ("Model_A", "Model_B")
    sequence = emit_birdsong_xsq_sequence(intents=intents, model_pool=model_pool)
    root = ET.fromstring(sequence.xml_text)

    assert root.tag == "xsequence"
    assert root.attrib["name"] == "HelixBirdsongDemo"
    assert root.attrib["model"] == DEFAULT_BIRDSONG_MODEL
    assert root.find("timingtrack") is not None
    assert root.find("effects") is not None
    assert root.find("ElementEffects") is not None

    element_effects = root.find("ElementEffects")
    elements = element_effects.findall("Element")
    assert elements[0].attrib["type"] == "timing"
    assert [element.attrib["name"] for element in elements[1:]] == list(model_pool)
    assert all(element.attrib["type"] == "model" for element in elements[1:])


def test_write_birdsong_xsq_validates_with_existing_validator(tmp_path: Path) -> None:
    intents = build_birdsong_demo_intents(duration_seconds=6.0, step_seconds=1.0, bpm=120.0)
    output = write_birdsong_xsq(tmp_path / "birdsong.xsq", intents, model_pool=("Model_A", "Model_B"))

    validate_xsq(output)
    assert output.exists()


def test_birdsong_xsq_preserves_intent_effect_metadata_and_spread_path() -> None:
    intents = build_birdsong_demo_intents(duration_seconds=5.0, step_seconds=1.0, bpm=120.0)
    model_pool = ("Model_A", "Model_B", "Model_C")
    root = ET.fromstring(emit_birdsong_xsq_sequence(intents=intents, model_pool=model_pool).xml_text)

    timing_entries = root.find("timingtrack").findall("phoneme")
    effect_entries = root.find("effects").findall("effect")
    model_effects = []
    for element in root.find("ElementEffects").findall("Element")[1:]:
        model_effects.extend(element.find("EffectLayer").findall("Effect"))

    assert len(timing_entries) == len(intents)
    assert len(effect_entries) == len(intents)
    assert len(model_effects) == len(intents) * len(model_pool)

    for idx, intent in enumerate(sorted(intents, key=lambda item: (item.start_time, item.effect_name, item.score))):
        timing = timing_entries[idx]
        effect = effect_entries[idx]
        spread_path = tuple(timing.attrib["spread_path"].split(","))

        assert timing.attrib["index"] == str(idx)
        assert timing.attrib["phoneme"] == intent.effect_name
        assert timing.attrib["motif"] == intent.motif
        assert timing.attrib["direction"] == intent.direction
        assert timing.attrib["target_model"] in model_pool
        assert spread_path
        assert set(spread_path).issubset(set(model_pool))
        assert effect.attrib["type"] == intent.effect_name
        assert effect.attrib["target_model"] == timing.attrib["target_model"]
        assert effect.attrib["spread_path"] == timing.attrib["spread_path"]


def test_birdsong_xsq_spreads_one_intent_across_multiple_model_layers() -> None:
    intents = build_birdsong_demo_intents(duration_seconds=2.0, step_seconds=1.0, bpm=120.0)[:1]
    model_pool = ("Model_A", "Model_B", "Model_C", "Model_D")
    root = ET.fromstring(emit_birdsong_xsq_sequence(intents=intents, model_pool=model_pool).xml_text)

    model_effects = []
    for element in root.find("ElementEffects").findall("Element")[1:]:
        layer_effects = element.find("EffectLayer").findall("Effect")
        if layer_effects:
            model_effects.extend((element.attrib["name"], layer_effects[0]) for _ in layer_effects)

    assert len(model_effects) == 4
    start_times = [int(effect.attrib["startTime"]) for _, effect in model_effects]
    assert start_times == sorted(start_times)
    assert len({model for model, _ in model_effects}) == 4


def test_birdsong_xsq_can_target_real_helixville3_pool() -> None:
    intents = build_birdsong_demo_intents(duration_seconds=8.0, step_seconds=1.0, bpm=120.0)
    pool = load_helixville3_target_pool()
    root = ET.fromstring(emit_birdsong_xsq_sequence(intents=intents, model_pool=pool).xml_text)

    element_names = [element.attrib["name"] for element in root.find("ElementEffects").findall("Element")[1:]]
    targets = [entry.attrib["target_model"] for entry in root.find("timingtrack").findall("phoneme")]
    spread_targets = [target for entry in root.find("timingtrack").findall("phoneme") for target in entry.attrib["spread_path"].split(",")]

    assert pool
    assert element_names == list(pool)
    assert targets
    assert set(targets).issubset(set(pool))
    assert set(spread_targets).issubset(set(pool))


def test_birdsong_xsq_output_is_deterministic() -> None:
    intents = build_birdsong_demo_intents(duration_seconds=8.0, step_seconds=1.0, bpm=120.0)
    model_pool = ("Model_A", "Model_B")

    first = emit_birdsong_xsq_sequence(intents=intents, model_pool=model_pool).xml_text
    second = emit_birdsong_xsq_sequence(intents=tuple(reversed(intents)), model_pool=model_pool).xml_text

    assert first == second
