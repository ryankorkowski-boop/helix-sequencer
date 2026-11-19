"""Vivid style keeps AC full-bright and RGB on saturated color with black gaps."""
from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from core.vivid_style import append_show_grove, apply_vivid_style, palette_text
from tools.layout_bench.xlights_fseq import saturated_bulb


def _layout(path: Path) -> None:
    path.write_text(
        """<xrgb><models>
        <model name="Roof" DisplayAs="Single Line" StringType="Single Color White" StartChannel="1" parm1="1" parm2="1" WorldPosX="0" WorldPosY="10" WorldPosZ="0" CustomColor="#FFFFFF"/>
        <model name="Tree" DisplayAs="Single Line" StringType="Single Color Green" StartChannel="2" parm1="1" parm2="1" WorldPosX="40" WorldPosY="10" WorldPosZ="0" CustomColor="#00FF00"/>
        <model name="Arch" DisplayAs="Single Line" StringType="Single Color Red" StartChannel="3" parm1="1" parm2="1" WorldPosX="80" WorldPosY="10" WorldPosZ="0" CustomColor="#FF0000"/>
        <model name="Matrix" DisplayAs="Horiz Matrix" StringType="RGB Nodes" StartChannel="4" parm1="4" parm2="4" WorldPosX="10" WorldPosY="0" WorldPosZ="5" CustomColor="#CCCCCC" PointData="0,0,0,1,0,0,2,0,1,3,0,2"/>
        </models><modelGroups>
        <modelGroup name="All AC" models="Roof,Tree,Arch"/>
        </modelGroups></xrgb>""",
        encoding="utf-8",
    )


def _sequence(path: Path) -> None:
    root = ET.Element("xsequence")
    head = ET.SubElement(root, "head")
    ET.SubElement(head, "sequenceDuration").text = "4.000"
    palettes = ET.SubElement(root, "ColorPalettes")
    ET.SubElement(palettes, "ColorPalette").text = "C_BUTTON_Palette1=#FFFFFF,C_CHECKBOX_Palette1=1"
    effects = ET.SubElement(root, "ElementEffects")
    for name, starts in (("Roof", (0, 2000)), ("Matrix", (500, 2500))):
        element = ET.SubElement(effects, "Element", {"type": "model", "name": name})
        layer = ET.SubElement(element, "EffectLayer")
        for start in starts:
            ET.SubElement(layer, "Effect", {
                "name": "On",
                "startTime": str(start),
                "endTime": str(start + 400),
                "settings": "E_TEXTCTRL_Eff_On_Start=19,E_TEXTCTRL_Eff_On_End=19",
                "palette": "0",
                "source": "HelixMusicalBed" if start == 0 and name == "Roof" else "hit",
            })
    ET.ElementTree(root).write(path)


def test_vivid_removes_the_bed_and_drives_ac_to_full(tmp_path: Path):
    layout = tmp_path / "layout.xml"
    sequence = tmp_path / "show.xsq"
    _layout(layout)
    _sequence(sequence)
    report = apply_vivid_style(sequence, layout)
    root = ET.parse(sequence).getroot()
    assert all(effect.attrib.get("source") != "HelixMusicalBed" for effect in root.iter("Effect"))
    roof = [effect for effect in root.iter("Effect") if effect.attrib.get("source") != "HelixVivid"]
    assert any("E_TEXTCTRL_Eff_On_Start=100" in (effect.attrib.get("settings") or "") for effect in root.iter("Effect"))
    vivid = [effect for effect in root.iter("Effect") if effect.attrib.get("source") == "HelixVivid"]
    assert report["ac_models"] >= 3
    assert report["added"] > 0
    assert len(vivid) > 0
    texts = [palette.text or "" for palette in root.find("ColorPalettes")]
    assert palette_text(("#FF2BD6",)) in texts
    assert palette_text(("#00F0FF",)) in texts
    assert not any("#CCCCCC" in text for text in texts)


def test_grove_appends_without_moving_existing_channels(tmp_path: Path):
    layout = tmp_path / "layout.xml"
    _layout(layout)
    out = tmp_path / "dense.xml"
    report = append_show_grove(layout, out, spirals=4, dna_pairs=1)
    root = ET.parse(out).getroot()
    roof = next(model for model in root.findall("./models/model") if model.attrib["name"] == "Roof")
    assert roof.attrib["StartChannel"] == "1"
    assert report["spirals"] == 4
    assert report["dna"] == 2
    names = {model.attrib["name"] for model in root.findall("./models/model")}
    assert "HX Vivid Spiral 01" in names
    group = next(item for item in root.findall("./modelGroups/modelGroup") if item.attrib["name"] == "HX Vivid Grove")
    assert "HX Vivid Spiral 01" in group.attrib["models"]


def test_white_bulbs_become_saturated():
    assert saturated_bulb("Window", (255, 255, 255)) != (255, 255, 255)
    assert saturated_bulb("Tree", (0, 255, 0)) == (0, 255, 0)
