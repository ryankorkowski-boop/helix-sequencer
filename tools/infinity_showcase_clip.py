"""Short Infinity Showcase sequence that targets nested groups and submodels.

The layout comes from tools/build_infinity_showcase_layout.py. Element types
and blend keys are the ones xLights 2026.19 stores. Prop order comes from the
spatial graph, so a chase follows real X coordinates.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from core.helix_flow_spatial_graph import build_spatial_graph, route_names_by_axis
from core.model_parser import parse_layout
from xlights.layer_blend import blend_settings
from xlights.layout_sync import sync_xsq_to_layout
from xlights.xsq_writer import XsqIndex


def write_infinity_clip(layout_xml: Path, xsq_path: Path, *, duration_ms: int = 2000) -> dict:
    layout = parse_layout(layout_xml)
    graph = build_spatial_graph(layout_path=layout_xml)
    faces = tuple(
        name
        for name, model in layout.models.items()
        if not model.is_submodel and "SINGING_FACE" in name
    )
    ordered = route_names_by_axis(graph, faces, "x")
    if not ordered:
        raise ValueError("Infinity layout has no singing faces to route")
    districts = layout.expand_group_members("HX_INFINITY_DISTRICTS")
    if len(districts) < 2:
        raise ValueError("HX_INFINITY_DISTRICTS did not expand to member models")

    root = ET.Element("xsequence", {"BaseChannel": "0", "FixedPointTiming": "1", "ModelBlending": "true"})
    head = ET.SubElement(root, "head")
    ET.SubElement(head, "version").text = "2026.19"
    ET.SubElement(head, "sequenceTiming").text = "50 ms"
    ET.SubElement(head, "sequenceType").text = "Media"
    ET.SubElement(head, "mediaFile").text = "clip.wav"
    ET.SubElement(head, "sequenceDuration").text = f"{duration_ms / 1000:.3f}"
    palettes = ET.SubElement(root, "ColorPalettes")
    ET.SubElement(palettes, "ColorPalette").text = "C_BUTTON_Palette1=#FF2244,C_CHECKBOX_Palette1=1"
    ET.SubElement(palettes, "ColorPalette").text = "C_BUTTON_Palette1=#22AAFF,C_CHECKBOX_Palette1=1"
    ET.SubElement(root, "DisplayElements")
    ET.SubElement(root, "ElementEffects")
    xsq = XsqIndex(tree=ET.ElementTree(root), root=root, elements={}, on_tpl=None, ramp_tpl=None)
    sync_xsq_to_layout(xsq, layout_xml)

    effects = {element.attrib["name"]: element for element in root.find("ElementEffects")}
    _add_effect(
        effects["HX_INFINITY_DISTRICTS"],
        start=0,
        end=duration_ms,
        palette="0",
        settings=blend_settings("E_TEXTCTRL_Eff_On_Start=40,E_TEXTCTRL_Eff_On_End=40", "Average"),
    )
    mouth = f"{ordered[0]}/Mouth"
    _add_effect(
        effects[mouth],
        start=0,
        end=duration_ms,
        palette="1",
        settings=blend_settings(
            "E_TEXTCTRL_Eff_On_Start=80,E_TEXTCTRL_Eff_On_End=80",
            "Layered",
            canvas=True,
            mix=50,
            layers_selected="1",
        ),
    )
    slice_ms = max(1, duration_ms // len(ordered))
    for index, name in enumerate(ordered):
        _add_effect(
            effects[name],
            start=index * slice_ms,
            end=min(duration_ms, (index + 1) * slice_ms),
            palette="0",
            settings=blend_settings("E_TEXTCTRL_Eff_On_Start=70,E_TEXTCTRL_Eff_On_End=70", "Normal"),
        )

    xsq_path.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root).write(xsq_path, encoding="utf-8", xml_declaration=True)
    return {
        "ordered_faces": list(ordered),
        "district_members": len(districts),
        "mouth": mouth,
        "group_type": effects["HX_INFINITY_DISTRICTS"].attrib["type"],
        "submodel_type": effects[mouth].attrib["type"],
    }


def _add_effect(element: ET.Element, *, start: int, end: int, palette: str, settings: str) -> None:
    layer = element.find("EffectLayer")
    if layer is None:
        layer = ET.SubElement(element, "EffectLayer")
    ET.SubElement(
        layer,
        "Effect",
        {
            "name": "On",
            "startTime": str(start),
            "endTime": str(end),
            "palette": palette,
            "settings": settings,
        },
    )
