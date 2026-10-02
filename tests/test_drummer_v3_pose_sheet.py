from __future__ import annotations

import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

from audio.drum_classification import DrumEvent
from mapping.drum_mapper import DRUMMER_COMPONENTS, map_events_to_drummer_v3_poses
from tools.build_helpers.helixville4_full_band import (
    DRUMMER_HIT_COMPONENT_PARTS,
    FULL_BAND_SPECS,
    add_full_helixville4_band_models,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "fixtures" / "band_geometry" / "source" / "drummerbg.png"


def _drummer_spec():
    return next(spec for spec in FULL_BAND_SPECS if spec.model_name == "HX_SNOWMAN_DRUMMER")


def _rendered_drummer_model() -> ET.Element:
    with tempfile.TemporaryDirectory() as tempdir:
        path = Path(tempdir) / "layout.xml"
        path.write_text("<xrgb><models/><modelGroups/></xrgb>", encoding="utf-8")
        add_full_helixville4_band_models(path)
        model = ET.parse(path).getroot().find(".//model[@name='HX_SNOWMAN_DRUMMER']")
        assert model is not None
        return ET.fromstring(ET.tostring(model, encoding="unicode"))


def test_approved_source_image_remains_visual_reference() -> None:
    assert SOURCE.exists()
    assert SOURCE.stat().st_size > 0


def test_production_drummer_has_exactly_three_toms_and_hi_hat_pedal() -> None:
    names = {part.name for part in _drummer_spec().parts}
    assert {"TOM_LEFT", "TOM_RIGHT", "TOM_FLOOR"} <= names
    assert "HI_HAT_PEDAL" in names
    assert "TOM_4" not in names
    assert not any(
        name.startswith("TOM_") and name not in {"TOM_LEFT", "TOM_RIGHT", "TOM_FLOOR"}
        for name in names
    )


def test_production_hit_composites_encode_contact_rules() -> None:
    assert DRUMMER_HIT_COMPONENT_PARTS["HIT_KICK"] == ("KICK", "KICK_RIM")
    assert DRUMMER_HIT_COMPONENT_PARTS["HIT_HI_HAT"] == ("HI_HAT", "HI_HAT_PEDAL")
    for key in (
        "HIT_SNARE",
        "HIT_TOM_LEFT",
        "HIT_TOM_RIGHT",
        "HIT_TOM_FLOOR",
        "HIT_CYMBAL_LEFT",
        "HIT_CYMBAL_RIGHT",
    ):
        members = DRUMMER_HIT_COMPONENT_PARTS[key]
        assert any("ARM" in member for member in members)
        assert any("STICK" in member for member in members)


def test_exported_layout_contains_all_eight_composites_with_membership_metadata() -> None:
    model = _rendered_drummer_model()
    submodels = {item.get("name"): item for item in model.findall("subModel")}
    assert set(DRUMMER_COMPONENTS) <= set(submodels)
    assert len(DRUMMER_COMPONENTS) == 8

    kick = submodels["HX_SNOWMAN_DRUMMER_HIT_KICK"]
    hihat = submodels["HX_SNOWMAN_DRUMMER_HIT_HI_HAT"]
    floor = submodels["HX_SNOWMAN_DRUMMER_HIT_TOM_FLOOR"]
    assert kick.get("HelixContactMode") == "none"
    assert "STICK" not in kick.get("HelixMembers", "")
    assert hihat.get("HelixContactMode") == "pedal"
    assert "HI_HAT_PEDAL" in hihat.get("HelixMembers", "")
    assert "STICK" not in hihat.get("HelixMembers", "")
    assert floor.get("HelixContactMode") == "arm_and_stick"


def test_detected_toms_rotate_left_right_floor_and_cymbals_alternate() -> None:
    events = [
        DrumEvent(0.10, 0.8, 0.7, {}, 1, "kick", "test"),
        DrumEvent(0.20, 0.9, 0.8, {}, 2, "snare", "test"),
        DrumEvent(0.30, 0.5, 0.7, {}, 3, "hihat", "test"),
        DrumEvent(0.40, 0.7, 0.7, {}, 4, "tom", "test"),
        DrumEvent(0.50, 0.7, 0.7, {}, 5, "tom", "test"),
        DrumEvent(0.60, 0.7, 0.7, {}, 6, "tom", "test"),
        DrumEvent(0.70, 1.0, 0.8, {}, 7, "cymbal", "test"),
        DrumEvent(0.80, 1.0, 0.8, {}, 8, "cymbal", "test"),
    ]
    mapped = map_events_to_drummer_v3_poses(events)
    assert [event["pose"] for event in mapped] == [
        "kick_hit",
        "snare_hit",
        "hi_hat_pulse",
        "left_tom_hit",
        "right_tom_hit",
        "floor_tom_hit",
        "left_crash",
        "right_crash",
    ]
