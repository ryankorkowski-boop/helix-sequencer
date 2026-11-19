"""Infinity Showcase uses nested groups, submodels, spatial order, and blend XML."""
from __future__ import annotations

import xml.etree.ElementTree as ET

from core.helix_flow_spatial_graph import build_spatial_graph, route_names_by_axis
from core.model_parser import parse_layout
from tools.build_infinity_showcase_layout import make_layout
from tools.infinity_showcase_clip import write_infinity_clip


def test_nested_districts_expand_and_faces_route_in_x(tmp_path):
    layout_xml = tmp_path / "infinity.xml"
    make_layout(layout_xml, tmp_path / "infinity.json", 128)
    layout = parse_layout(layout_xml)
    members = layout.expand_group_members("HX_INFINITY_DISTRICTS")
    roots = [model for model in layout.models.values() if not model.is_submodel]
    assert len(members) == len(roots)
    assert layout.sequence_element_type("HX_INFINITY_FAMILY_ARCH") == "modelGroup"
    face = next(name for name, model in layout.models.items() if model.is_submodel and name.endswith("/Mouth"))
    assert layout.sequence_element_type(face) == "submodel"
    graph = build_spatial_graph(layout_path=layout_xml)
    faces = tuple(name for name, model in layout.models.items() if not model.is_submodel and "SINGING_FACE" in name)
    ordered = route_names_by_axis(graph, faces, "x")
    xs = [graph.by_name[name].x for name in ordered]
    assert xs == sorted(xs)
    assert any(abs(graph.by_name[name].z) > 1 for name in ordered)
    mouth = graph.by_name[face]
    eyes = graph.by_name[face.replace("/Mouth", "/Eyes")]
    assert (mouth.x, mouth.y, mouth.z) != (eyes.x, eyes.y, eyes.z)


def test_clip_emits_group_submodel_and_blend(tmp_path):
    layout_xml = tmp_path / "infinity.xml"
    make_layout(layout_xml, tmp_path / "infinity.json", 128)
    report = write_infinity_clip(layout_xml, tmp_path / "clip.xsq", duration_ms=2000)
    assert report["group_type"] == "modelGroup"
    assert report["submodel_type"] == "submodel"
    root = ET.parse(tmp_path / "clip.xsq").getroot()
    kinds = {element.attrib["name"]: element.attrib["type"] for element in root.find("ElementEffects")}
    assert kinds["HX_INFINITY_DISTRICTS"] == "modelGroup"
    assert kinds[report["mouth"]] == "submodel"
    mouth = next(element for element in root.find("ElementEffects") if element.attrib["name"] == report["mouth"])
    settings = mouth.find(".//Effect").attrib["settings"]
    assert "T_CHOICE_LayerMethod=Layered" in settings
    assert "T_CHECKBOX_Canvas=1" in settings
    group = next(element for element in root.find("ElementEffects") if element.attrib["name"] == "HX_INFINITY_DISTRICTS")
    assert "T_CHOICE_LayerMethod=Average" in group.find(".//Effect").attrib["settings"]
