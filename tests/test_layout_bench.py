"""Structural checks for the clean-room layout test bench fixtures."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

from core import model_parser as xmp
from tools.layout_bench.generate_layouts import BUILDERS, build_ac


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures" / "layout_bench"


def test_ac_channel_counts_match_lor_sizes():
    for count in (16, 32, 64):
        layout = build_ac(count)
        assert layout.channel_count == count
        assert len(layout.models) == count
        assert all(model["channels"] == 1 and not model["rgb"] for model in layout.models)


def test_fixture_manifest_matches_parsed_layouts():
    manifest = json.loads((FIXTURES / "manifest.json").read_text(encoding="utf-8"))
    assert len(manifest) == len(BUILDERS) == 16
    ids = [row["id"] for row in manifest]
    assert ids[:3] == ["ac16_lor", "ac32_house", "ac64_yard"]
    assert "band_stage" in ids
    for row in manifest:
        parsed = xmp.parse_layout(ROOT / row["layout"])
        roots = [model for model in parsed.models.values() if not model.is_submodel]
        channels = sum(model.total_pixels * (3 if model.is_rgb_capable() else 1) for model in roots)
        assert len(roots) == row["props"]
        assert channels == row["channels"]
        assert (ROOT / row["template"]).exists()
        if row["tier"] == "ac":
            assert channels == {"ac16_lor": 16, "ac32_house": 32, "ac64_yard": 64}[row["id"]]


def test_band_stage_has_singing_faces_and_drummer_kit():
    layout = ET.parse(FIXTURES / "band_stage" / "xlights_rgbeffects.xml")
    names = {model.attrib["name"] for model in layout.findall("./models/model")}
    assert {"Singing Face 1", "Singing Face 2", "Singing Face 3", "Snowman Singer", "Snowman Guitar", "Snowman Bass", "Snowman Drummer"} <= names
    for piece in (
        "HX_SNOWMAN_DRUMMER_KICK",
        "HX_SNOWMAN_DRUMMER_SNARE",
        "HX_SNOWMAN_DRUMMER_HI_HAT",
        "HX_SNOWMAN_DRUMMER_CYMBAL_LEFT",
        "HX_SNOWMAN_DRUMMER_CYMBAL_RIGHT",
    ):
        assert piece in names
    lead = next(model for model in layout.findall("./models/model") if model.attrib["name"] == "Singing Face 1")
    face = lead.find("./faceInfo")
    assert face is not None
    assert face.attrib["Type"] == "NodeRange"
    assert face.attrib["Mouth-AI"]
    assert face.attrib["Eyes-Open"]
    assert {sub.attrib["name"] for sub in lead.findall("./subModel")} >= {"Mouth", "Eyes"}


def test_templates_are_clean_room_and_seed_on_and_ramp():
    for template in FIXTURES.glob("*/template.xsq"):
        text = template.read_text(encoding="utf-8")
        assert "Bench Palette" in text
        assert "copyright" not in text.lower()
        root = ET.parse(template).getroot()
        effect_names = {effect.attrib.get("name") for effect in root.iter("Effect") if effect.attrib.get("name")}
        assert {"On", "Ramp", "Faces"} <= effect_names


def test_common_group_names_exist_on_pixel_classic():
    root = ET.parse(FIXTURES / "pixel_classic" / "xlights_rgbeffects.xml").getroot()
    groups = {group.attrib["name"] for group in root.findall("./modelGroups/modelGroup")}
    assert {"All Arches", "All Canes", "All Mini Trees", "All Stars", "All Snowflakes", "Whole House"} <= groups
    model_names = {model.attrib["name"] for model in root.findall("./models/model")}
    assert "Mega Tree" in model_names
    assert "North Candy Cane 1" in model_names
    assert "South Candy Cane 1" in model_names
    assert any(name.startswith("Arch 1 Sec ") for name in model_names)
