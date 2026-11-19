"""Nested groups, submodel coordinates, and xLights 2026.19 blend XML."""
from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from core.effect_layering_engine import EffectCandidate, build_layering_plan
from core.helix_flow_spatial_graph import build_spatial_graph, route_names_by_axis
from core.model_parser import parse_layout
from core.musical_bed import apply_musical_bed
from xlights.layer_blend import blend_settings, xlights_layer_method
from xlights.layout_sync import sync_xsq_to_layout
from xlights.xsq_writer import XsqIndex


BAND = Path("fixtures/layout_bench/band_stage/xlights_rgbeffects.xml")
SNOWMEN = (
    "Snowman Lead Singer",
    "Snowman Harmony Singer",
    "Snowman Bassist",
    "Snowman Guitarist",
    "Snowman Keyboardist",
    "Snowman Drummer",
)


def test_nested_group_expands_to_models_and_submodels_keep_their_type():
    layout_path = Path("/tmp/nested-groups.xml")
    layout_path.write_text(
        """<xrgb><models>
        <model name="Arch" DisplayAs="Single Line" WorldPosX="0" WorldPosY="0" WorldPosZ="0" StringType="RGB Nodes" parm2="4">
          <subModel name="Left" layout="horizontal" type="ranges" line0="1-2"/>
        </model>
        <model name="Tree" DisplayAs="Single Line" WorldPosX="10" WorldPosY="0" WorldPosZ="2" StringType="RGB Nodes" parm2="4"/>
        </models><modelGroups>
        <modelGroup name="Inner" models="Arch,Tree"/>
        <modelGroup name="Outer" models="Inner,Arch"/>
        </modelGroups></xrgb>""",
        encoding="utf-8",
    )
    layout = parse_layout(layout_path)
    assert layout.expand_group_members("Outer") == ["Arch", "Tree", "Arch"]
    assert layout.sequence_element_type("Outer") == "modelGroup"
    assert layout.sequence_element_type("Arch/Left") == "submodel"
    assert layout.sequence_element_type("Tree") == "model"


def test_band_group_routes_six_snowmen_by_world_position():
    layout = parse_layout(BAND)
    members = layout.expand_group_members("Snowman Band")
    assert set(members) == set(SNOWMEN)
    graph = build_spatial_graph(layout_path=BAND, model_names=SNOWMEN)
    ordered = route_names_by_axis(graph, SNOWMEN, "x")
    assert ordered[0] == "Snowman Bassist"
    assert ordered[-1] == "Snowman Drummer"
    assert graph.by_name["Snowman Lead Singer"].x < graph.by_name["Snowman Drummer"].x
    mouth = graph.by_name["Singing Face 1/Mouth"]
    eyes = graph.by_name["Singing Face 1/Eyes"]
    assert (mouth.x, mouth.y, mouth.z) != (eyes.x, eyes.y, eyes.z)


def test_sync_emits_modelgroup_and_submodel_elements(tmp_path: Path):
    root = ET.Element("xsequence")
    ET.SubElement(root, "DisplayElements")
    ET.SubElement(root, "ElementEffects")
    xsq = XsqIndex(tree=ET.ElementTree(root), root=root, elements={}, on_tpl=None, ramp_tpl=None)
    report = sync_xsq_to_layout(xsq, BAND)
    assert report["layout_names"] > 0
    kinds = {el.attrib.get("name"): el.attrib.get("type") for el in root.find("ElementEffects")}
    assert kinds["Snowman Band"] == "modelGroup"
    assert kinds["Singing Face 1/Mouth"] == "submodel"
    assert kinds["Snowman Drummer"] == "model"


def test_layer_plan_emits_official_blend_and_canvas_keys():
    plan = build_layering_plan([
        EffectCandidate(model="Matrix", effect="Shockwave", start_ms=0, end_ms=500, layer="motion", intensity=0.8),
        EffectCandidate(model="Matrix", effect="On", start_ms=0, end_ms=500, layer="base", intensity=0.4),
    ])
    by_role = {effect.layer_role: effect for effect in plan.layered_effects}
    motion = by_role["motion"].native_xsq_settings()
    base = by_role["base"].native_xsq_settings()
    assert "T_CHOICE_LayerMethod=" in motion
    assert "T_CHECKBOX_Canvas=1" in motion
    assert "T_LayersSelected=1" in motion
    assert "T_CHECKBOX_Canvas=0" in base
    assert xlights_layer_method("Overlay") == "Average"
    assert xlights_layer_method("Additive") == "Additive"
    assert "T_CHOICE_LayerMethod=Highlight" in blend_settings("", "Screen", canvas=True, mix=40, layers_selected="1")


def test_musical_bed_uses_a_dark_palette_index_and_average_blend(tmp_path: Path):
    path = tmp_path / "bed.xsq"
    root = ET.Element("xsequence")
    palettes = ET.SubElement(root, "ColorPalettes")
    white = ET.SubElement(palettes, "ColorPalette")
    white.text = "C_BUTTON_Palette1=#FFFFFF,C_CHECKBOX_Palette1=1"
    effects = ET.SubElement(root, "ElementEffects")
    element = ET.SubElement(effects, "Element", {"type": "model", "name": "Arch"})
    layer = ET.SubElement(element, "EffectLayer")
    ET.SubElement(layer, "Effect", {"name": "Shockwave", "startTime": "1000", "endTime": "1200", "settings": "E_SLIDER_Shockwave_Accel=0"})
    ET.ElementTree(root).write(path)
    report = apply_musical_bed(path, 10000, 0.5)
    saved = ET.parse(path)
    beds = [e for e in saved.findall(".//Effect") if e.attrib.get("source") == "HelixMusicalBed"]
    assert report["beds"] == 2
    assert beds[0].attrib["palette"] != "0"
    assert "T_CHOICE_LayerMethod=Average" in beds[0].attrib["settings"]
    assert "#FFFFFF" not in (saved.find("ColorPalettes")[int(beds[0].attrib["palette"])].text or "")
    shock = [e for e in saved.findall(".//Effect") if e.attrib.get("name") == "Shockwave"][0]
    assert "T_CHECKBOX_Canvas=1" in shock.attrib["settings"]
    assert saved.find("ElementEffects/Element")[0].attrib.get("name") == "Helix Bed"
