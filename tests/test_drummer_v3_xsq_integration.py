from __future__ import annotations

import xml.etree.ElementTree as ET

from audio.drum_classification import DrumEvent
from mapping.drum_mapper import DRUMMER_COMPONENTS, map_events_to_drummer_components, map_events_to_drummer_v3_poses

LEGACY_STICK_OR_ARM_TOKENS = ("LEFT_STICK", "RIGHT_STICK", "LEFT_ARM", "RIGHT_ARM")
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


def test_component_mapper_preserves_historical_rack_tom_and_cymbal_orientation() -> None:
    events = [
        DrumEvent(0.1, 0.8, 0.7, {}, 1, "kick"),
        DrumEvent(0.2, 0.9, 0.8, {}, 2, "snare"),
        DrumEvent(0.3, 0.6, 0.7, {}, 3, "hihat"),
        DrumEvent(0.4, 0.7, 0.7, {}, 4, "tom"),
        DrumEvent(0.5, 0.7, 0.7, {}, 5, "tom"),
        DrumEvent(0.6, 0.7, 0.7, {}, 6, "tom"),
        DrumEvent(0.8, 0.8, 0.8, {}, 8, "cymbal"),
        DrumEvent(0.9, 0.8, 0.8, {}, 9, "cymbal"),
    ]
    mapped = map_events_to_drummer_components(events)
    components = [str(item["component"]) for item in mapped]
    assert set(components).issubset(set(DRUMMER_COMPONENTS))
    assert not any(any(token in component for token in LEGACY_STICK_OR_ARM_TOKENS) for component in components)
    assert components[:3] == [
        "HX_SNOWMAN_DRUMMER_V3_KICK",
        "HX_SNOWMAN_DRUMMER_V3_SNARE",
        "HX_SNOWMAN_DRUMMER_V3_HI_HAT",
    ]
    assert components[3:6] == [CANONICAL_TOMS[0], CANONICAL_TOMS[1], CANONICAL_TOMS[0]]
    assert components[6:8] == [
        "HX_SNOWMAN_DRUMMER_V3_CYMBAL_RIGHT",
        "HX_SNOWMAN_DRUMMER_V3_CYMBAL_LEFT",
    ]
    assert not any("TOM_4" in component for component in components)


def test_strong_floor_evidence_extends_historical_two_rack_tom_logic() -> None:
    events = [
        DrumEvent(0.1, 0.7, 0.9, {"tom_class": "high", "tom_class_confidence": 0.85}, 1, "tom"),
        DrumEvent(0.2, 0.7, 0.9, {"tom_class": "mid", "tom_class_confidence": 0.85}, 2, "tom"),
        DrumEvent(0.3, 0.7, 0.9, {"tom_class": "floor", "tom_class_confidence": 0.92}, 3, "tom"),
    ]
    mapped = map_events_to_drummer_components(events)
    assert [item["component"] for item in mapped] == [CANONICAL_TOMS[0], CANONICAL_TOMS[1], CANONICAL_TOMS[2]]
    assert mapped[2]["tom_class_source"] == "spectral_floor_extension"


def test_v3_pose_adapter_preserves_historical_cymbal_orientation_and_integrated_targets() -> None:
    events = [
        DrumEvent(0.1, 0.8, 0.7, {}, 1, "kick"),
        DrumEvent(0.2, 0.9, 0.8, {}, 2, "snare"),
        DrumEvent(0.3, 0.6, 0.7, {}, 3, "hihat"),
        DrumEvent(0.4, 0.7, 0.7, {}, 4, "tom"),
        DrumEvent(0.5, 0.8, 0.8, {}, 5, "cymbal"),
        DrumEvent(0.7, 0.8, 0.8, {}, 6, "cymbal"),
    ]
    mapped = map_events_to_drummer_v3_poses(events)
    assert mapped[3]["pose"] == "right_tom_hit"
    assert mapped[4]["pose"] == "right_crash"
    assert mapped[5]["pose"] == "left_crash"
    for item in mapped:
        assert item["components"]
        assert set(item["components"]).issubset(set(DRUMMER_COMPONENTS))
        assert list(item["submodels"]) == list(item["components"])


def test_historical_downbeat_impact_maps_to_integrated_eight_component_contract() -> None:
    event = DrumEvent(0.1, 0.8, 0.4, {}, 1, "drum_bus")
    pose = map_events_to_drummer_v3_poses([event])[0]
    assert pose["pose"] == "downbeat_impact"
    assert pose["components"] == [
        "HX_SNOWMAN_DRUMMER_V3_KICK",
        "HX_SNOWMAN_DRUMMER_V3_SNARE",
        "HX_SNOWMAN_DRUMMER_V3_CYMBAL_LEFT",
        "HX_SNOWMAN_DRUMMER_V3_CYMBAL_RIGHT",
    ]


def test_injection_helper_preserves_existing_xlights_effect_container() -> None:
    from tools.integrate_drummer_v3_into_xsq import _find_or_create_element_effects
    root = ET.fromstring("<xsequence><ElementEffects><Element type='model' name='Existing'/></ElementEffects></xsequence>")
    container = _find_or_create_element_effects(root)
    assert container is root.find("ElementEffects")
    assert [e.get("name") for e in container.findall("Element")] == ["Existing"]


def test_injection_helper_creates_current_xlights_container_without_legacy_effects() -> None:
    from tools.integrate_drummer_v3_into_xsq import _find_or_create_element_effects
    root = ET.fromstring("<xsequence/>")
    container = _find_or_create_element_effects(root)
    assert container.tag == "ElementEffects"
    assert root.find("effects") is None


def test_xlights_brightness_uses_percent_scale_and_carries_pose_metadata() -> None:
    from tools.integrate_drummer_v3_into_xsq import _add_on
    layer = ET.Element("EffectLayer")
    _add_on(layer, 100, 200, 0.25, DRUMMER_COMPONENTS[0], "kick", "kick_hit")
    effect = layer.find("Effect")
    settings = effect.get("settings", "")
    brightness = int(settings.split("E_SLIDER_Brightness=", 1)[1].split(",", 1)[0])
    assert 60 <= brightness <= 100
    assert brightness > 1
    assert effect.get("sourcePose") == "kick_hit"


def test_high_energy_cymbal_retains_historical_both_crash_semantics() -> None:
    event = DrumEvent(0.1, 0.95, 0.8, {}, 1, "cymbal")
    mapped = map_events_to_drummer_v3_poses([event])[0]
    assert mapped["pose"] == "both_crash"
    assert mapped["components"] == [
        "HX_SNOWMAN_DRUMMER_V3_CYMBAL_LEFT",
        "HX_SNOWMAN_DRUMMER_V3_CYMBAL_RIGHT",
    ]
