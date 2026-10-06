from __future__ import annotations

import xml.etree.ElementTree as ET

from audio.drum_classification import DrumEvent
from mapping.drum_mapper import (
    DRUMMER_COMPONENTS,
    map_events_to_drummer_components,
    map_events_to_drummer_v3_poses,
    resolve_drum_streams,
)

CANONICAL_TOMS = (
    "HX_SNOWMAN_DRUMMER_V3_TOM_HIGH",
    "HX_SNOWMAN_DRUMMER_V3_TOM_MID",
    "HX_SNOWMAN_DRUMMER_V3_TOM_FLOOR",
)


def test_canonical_drummer_has_exactly_eight_components() -> None:
    assert len(DRUMMER_COMPONENTS) == 8
    assert len(set(DRUMMER_COMPONENTS)) == 8
    assert all("STICK" not in name and "ARM" not in name for name in DRUMMER_COMPONENTS)
    assert CANONICAL_TOMS == DRUMMER_COMPONENTS[3:6]
    assert not any("TOM_4" in name for name in DRUMMER_COMPONENTS)


def test_component_mapper_uses_exact_detected_tom_class_and_cymbal_alternation() -> None:
    events = [
        DrumEvent(0.1, 0.8, 0.7, {}, 1, "kick"),
        DrumEvent(0.2, 0.9, 0.8, {}, 2, "snare"),
        DrumEvent(0.3, 0.6, 0.7, {}, 3, "hihat"),
        DrumEvent(0.4, 0.7, 0.8, {"tom_class": "high"}, 4, "tom"),
        DrumEvent(0.5, 0.7, 0.8, {"tom_class": "mid"}, 5, "tom"),
        DrumEvent(0.6, 0.7, 0.8, {"tom_class": "floor"}, 6, "tom"),
        DrumEvent(0.8, 0.8, 0.8, {}, 8, "cymbal"),
        DrumEvent(0.9, 0.8, 0.8, {}, 9, "cymbal"),
    ]
    mapped = map_events_to_drummer_components(events)
    assert [item["component"] for item in mapped] == [
        DRUMMER_COMPONENTS[0],
        DRUMMER_COMPONENTS[1],
        DRUMMER_COMPONENTS[2],
        *CANONICAL_TOMS,
        DRUMMER_COMPONENTS[6],
        DRUMMER_COMPONENTS[7],
    ]


def test_pose_adapter_names_the_three_toms_directly() -> None:
    events = [
        DrumEvent(0.1, 0.7, 0.9, {"tom_class": "high"}, 1, "tom"),
        DrumEvent(0.2, 0.7, 0.9, {"tom_class": "mid"}, 2, "tom"),
        DrumEvent(0.3, 0.7, 0.9, {"tom_class": "floor"}, 3, "tom"),
    ]
    mapped = map_events_to_drummer_v3_poses(events)
    assert [item["pose"] for item in mapped] == [
        "tom_high_hit",
        "tom_mid_hit",
        "tom_floor_hit",
    ]
    assert [item["component"] for item in mapped] == list(CANONICAL_TOMS)
    assert all(item["tom_class_source"] == "detected_tom_class" for item in mapped)


def test_high_energy_cymbal_does_not_fabricate_a_both_crash() -> None:
    event = DrumEvent(0.1, 1.0, 0.95, {}, 1, "cymbal")
    mapped = map_events_to_drummer_v3_poses([event])
    assert len(mapped) == 1
    assert mapped[0]["pose"] == "left_crash"
    assert mapped[0]["components"] == [DRUMMER_COMPONENTS[6]]


def test_ambiguous_bus_never_becomes_a_drummer_hit() -> None:
    streams = {
        "kick_events": [],
        "snare_events": [],
        "tom_events": [],
        "hihat_events": [],
        "cymbal_events": [],
        "drum_bus_events": [
            DrumEvent(0.1, 0.9, 0.2, {}, 1, "drum_bus"),
            DrumEvent(0.2, 0.9, 0.2, {}, 2, "drum_bus"),
        ],
    }
    resolved = resolve_drum_streams(streams)
    assert resolved["fallback_mode"] == "ambiguous_bus_rejected"
    assert resolved["events"] == []
    assert resolved["ambiguous_bus_rejected_count"] == 2


def test_injection_helper_preserves_existing_xlights_effect_container() -> None:
    from tools.integrate_drummer_v3_into_xsq import _find_or_create_element_effects

    root = ET.fromstring("<xsequence><ElementEffects><Element type='model' name='Existing'/></ElementEffects></xsequence>")
    container = _find_or_create_element_effects(root)
    assert container is root.find("ElementEffects")
    assert [element.get("name") for element in container.findall("Element")] == ["Existing"]


def test_injection_helper_creates_current_xlights_container_without_legacy_effects() -> None:
    from tools.integrate_drummer_v3_into_xsq import _find_or_create_element_effects

    root = ET.fromstring("<xsequence/>")
    container = _find_or_create_element_effects(root)
    assert container.tag == "ElementEffects"
    assert root.find("effects") is None


def test_xlights_effect_uses_percent_brightness_color_and_pose_metadata() -> None:
    from tools.integrate_drummer_v3_into_xsq import _add_on

    layer = ET.Element("EffectLayer")
    _add_on(
        layer,
        100,
        200,
        0.25,
        palette_hex="#DC2D1C",
        source_component=DRUMMER_COMPONENTS[0],
        source_type="kick",
        source_pose="kick_hit",
        role="logical_component",
    )
    effect = layer.find("Effect")
    assert effect is not None
    settings = effect.get("settings", "")
    brightness = int(settings.split("E_SLIDER_Brightness=", 1)[1].split(",", 1)[0])
    assert 68 <= brightness <= 100
    assert "#DC2D1C" in effect.get("palette", "")
    assert effect.get("sourcePose") == "kick_hit"
    assert effect.get("sourceDetector") == "v3_multi_detector_hpss"


def test_visual_geometry_keeps_instrument_color_separate_from_actuator() -> None:
    from tools.integrate_drummer_v3_into_xsq import COMPONENT_VISUAL_PARTS

    kick_parts = COMPONENT_VISUAL_PARTS[DRUMMER_COMPONENTS[0]]
    assert kick_parts == (("HX_SNOWMAN_DRUMMER_V3_KICK_SURFACE", "#DC2D1C"),)

    for tom in DRUMMER_COMPONENTS[3:6]:
        parts = COMPONENT_VISUAL_PARTS[tom]
        assert parts[0][0] == f"{tom}_SURFACE"
        assert parts[0][1] == "#2CB242"
        assert parts[1][0].endswith("_ARM_STICK")
        assert parts[1][1] != "#2CB242"

    hi_hat_parts = COMPONENT_VISUAL_PARTS[DRUMMER_COMPONENTS[2]]
    assert hi_hat_parts[1][0] == "HX_SNOWMAN_DRUMMER_V3_HI_HAT_FOOT"
    assert all("ARM_STICK" not in name for name, _ in hi_hat_parts)
