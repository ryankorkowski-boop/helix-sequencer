from __future__ import annotations

import xml.etree.ElementTree as ET

from audio.drum_classification import DrumEvent
from mapping.drum_mapper import DRUMMER_COMPONENTS, map_events_to_drummer_components, map_events_to_drummer_v3_poses

LEGACY_STICK_OR_ARM_TOKENS = ("LEFT_STICK", "RIGHT_STICK", "LEFT_ARM", "RIGHT_ARM")
CANONICAL_TOMS = (
    "HX_SNOWMAN_DRUMMER_TOM_HIGH",
    "HX_SNOWMAN_DRUMMER_TOM_MID",
    "HX_SNOWMAN_DRUMMER_TOM_FLOOR",
)


def test_nine_logical_drummer_components_include_three_toms_and_ride() -> None:
    assert len(DRUMMER_COMPONENTS) == 9
    assert len(set(DRUMMER_COMPONENTS)) == 9
    assert DRUMMER_COMPONENTS[-1] == "HX_SNOWMAN_DRUMMER_RIDE"
    assert all("STICK" not in name and "ARM" not in name for name in DRUMMER_COMPONENTS)
    assert CANONICAL_TOMS == DRUMMER_COMPONENTS[3:6]
    assert not any("TOM_4" in name for name in DRUMMER_COMPONENTS)


def test_component_mapper_never_emits_independent_sticks_arms_or_fourth_tom() -> None:
    events = [
        DrumEvent(0.1, 0.8, 0.7, {}, 1, "kick"), DrumEvent(0.2, 0.9, 0.8, {}, 2, "snare"),
        DrumEvent(0.3, 0.6, 0.7, {}, 3, "hihat"), DrumEvent(0.4, 0.7, 0.7, {}, 4, "tom"),
        DrumEvent(0.5, 0.7, 0.7, {}, 5, "tom"), DrumEvent(0.6, 0.7, 0.7, {}, 6, "tom"),
        DrumEvent(0.8, 1.0, 0.8, {}, 8, "cymbal"), DrumEvent(0.9, 0.8, 0.8, {}, 9, "cymbal"),
    ]
    mapped = map_events_to_drummer_components(events)
    components = [str(item["component"]) for item in mapped]
    assert set(components).issubset(set(DRUMMER_COMPONENTS))
    assert not any(any(token in component for token in LEGACY_STICK_OR_ARM_TOKENS) for component in components)
    assert components[0:3] == ["HX_SNOWMAN_DRUMMER_KICK", "HX_SNOWMAN_DRUMMER_SNARE", "HX_SNOWMAN_DRUMMER_HI_HAT"]
    assert components[3:6] == list(CANONICAL_TOMS)
    assert components[6:8] == ["HX_SNOWMAN_DRUMMER_CYMBAL_LEFT", "HX_SNOWMAN_DRUMMER_CYMBAL_RIGHT"]
    assert not any("TOM_4" in component for component in components)


def test_explicit_tom_classes_map_high_mid_floor() -> None:
    events = [
        DrumEvent(0.1, 0.7, 0.9, {"tom_class": "high"}, 1, "tom"),
        DrumEvent(0.2, 0.7, 0.9, {"tom_class": "mid"}, 2, "tom"),
        DrumEvent(0.3, 0.7, 0.9, {"tom_class": "floor"}, 3, "tom"),
    ]
    mapped = map_events_to_drummer_components(events)
    assert [item["component"] for item in mapped] == list(CANONICAL_TOMS)
    assert [item["tom_class"] for item in mapped] == ["high", "mid", "floor"]


def test_v3_pose_adapter_uses_only_canonical_component_targets() -> None:
    events = [DrumEvent(0.1, 0.8, 0.7, {}, 1, "kick"), DrumEvent(0.2, 0.9, 0.8, {}, 2, "snare"), DrumEvent(0.3, 0.6, 0.7, {}, 3, "hihat"), DrumEvent(0.4, 0.7, 0.7, {}, 4, "tom"), DrumEvent(0.5, 1.0, 0.8, {}, 5, "cymbal")]
    mapped = map_events_to_drummer_v3_poses(events)
    for item in mapped:
        assert str(item["component"]) in DRUMMER_COMPONENTS
        assert all(token not in str(item["component"]) for token in LEGACY_STICK_OR_ARM_TOKENS)
        assert "TOM_4" not in str(item["component"])
        assert list(item["submodels"]) == [item["component"]]


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


def test_generated_xmodel_matches_existing_eight_native_targets() -> None:
    """The logical ride must not be falsely represented as a built physical asset."""
    from pathlib import Path
    from tools.integrate_drummer_v3_into_xsq import DRUMMER_TARGETS

    xmodel = Path(__file__).resolve().parents[1] / "fixtures/band_geometry/models/HX_SNOWMAN_DRUMMER_V3.xmodel"
    names = {node.get("name") for node in ET.parse(xmodel).getroot().findall("./subModels/subModel")}
    assert DRUMMER_TARGETS == set(DRUMMER_COMPONENTS[:-1])
    assert DRUMMER_TARGETS <= names
    assert DRUMMER_COMPONENTS[-1] not in names


def test_native_on_effect_emits_percentage_peak_and_decay() -> None:
    from tools.integrate_drummer_v3_into_xsq import _add_on
    layer = ET.Element("EffectLayer")
    _add_on(layer, 100, 250, .72, "HX_SNOWMAN_DRUMMER_SNARE", "snare", hand="L")
    effect = layer.find("Effect")
    assert effect is not None
    settings = effect.attrib["settings"]
    assert "E_TEXTCTRL_Eff_On_Start=72" in settings
    assert "E_TEXTCTRL_Eff_On_End=4" in settings
    assert "E_SLIDER_Brightness" not in settings
    assert effect.attrib["palette"].endswith("C_CHECKBOX_Palette1=1")
    assert effect.get("sourceHand") == "L"
    assert effect.get("startTime") == "100"
    assert effect.get("endTime") == "250"
