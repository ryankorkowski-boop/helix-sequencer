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
    assert any(text != palette_text(("#FFFFFF",)) and "C_BUTTON_Palette1=#" in text for text in texts)
    assert not any("#CCCCCC" in text for text in texts)



def test_vivid_accents_keep_white_highlight_but_never_white_only(tmp_path: Path):
    from core.effect_engine import color_palette_table, enabled_palette_hexes, hex_is_near_white
    layout = tmp_path / "layout.xml"
    sequence = tmp_path / "show.xsq"
    _layout(layout)
    _sequence(sequence)
    apply_vivid_style(sequence, layout)
    root = ET.parse(sequence).getroot()
    tables = color_palette_table(root)
    accents = [effect for effect in root.iter("Effect")
               if effect.attrib.get("source") == "HelixVivid"
               and effect.attrib.get("label") == "white accent"]
    assert accents, "Synthetic AC layout should exercise occasional vivid highlights"
    vivid_effects = [effect for effect in root.iter("Effect")
                     if effect.attrib.get("source") == "HelixVivid"]
    for effect in vivid_effects:
        colors = enabled_palette_hexes(tables[int(effect.attrib["palette"])])
        assert colors, "Every generated effect must reference an enabled palette"
        assert any(not hex_is_near_white(color) for color in colors), (
            "HelixVivid must never emit a white-only effect", effect.attrib)
        if effect.attrib.get("label") == "white accent":
            assert any(hex_is_near_white(color) for color in colors)


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


def test_every_model_including_grove_gets_effects_during_active_music(tmp_path: Path):
    layout = tmp_path / "layout.xml"
    _layout(layout)
    dense = tmp_path / "dense.xml"
    append_show_grove(layout, dense, spirals=4, dna_pairs=1)
    sequence = tmp_path / "show.xsq"
    _sequence(sequence)
    root = ET.parse(sequence).getroot()
    layer = root.find("ElementEffects/Element/EffectLayer")
    for start in range(0, 4000, 200):
        ET.SubElement(layer, "Effect", {"name": "On", "startTime": str(start), "endTime": str(start + 80), "palette": "0"})
    ET.ElementTree(root).write(sequence)
    apply_vivid_style(sequence, dense)
    saved = ET.parse(sequence).getroot()
    from core.vivid_style import models_without_effects

    assert models_without_effects(saved, dense) == []
    groups = {
        item.attrib["name"]: item.attrib["models"]
        for item in ET.parse(dense).getroot().findall("./modelGroups/modelGroup")
    }
    assert "HX Vivid Spiral 01" in groups["HX Vivid Spirals"]
    assert "HX Vivid DNA 01 A" in groups["HX Vivid DNA"]
    covered = {
        element.attrib.get("name")
        for element in saved.find("ElementEffects").findall("Element")
        if element.findall(".//Effect")
    }
    assert "HX Vivid Spirals" in covered and "HX Vivid DNA" in covered
    watched = (
        "Matrix",
        "HX Vivid Spiral 01",
        "HX Vivid Spiral 02",
        "HX Vivid Spiral 03",
        "HX Vivid Spiral 04",
        "HX Vivid DNA 01 A",
        "HX Vivid DNA 01 B",
    )
    samples = []
    for t in range(200, 3800, 120):
        lit = 0
        for name in watched:
            element = next(item for item in saved.find("ElementEffects") if item.attrib.get("name") == name)
            if any(int(effect.attrib["startTime"]) <= t < int(effect.attrib["endTime"]) for effect in element.findall(".//Effect")):
                lit += 1
        samples.append(lit / len(watched))
    assert 0.15 <= sum(samples) / len(samples) <= 0.45


def test_singers_and_drummers_keep_their_effects(tmp_path: Path):
    layout = tmp_path / "layout.xml"
    _layout(layout)
    text = layout.read_text(encoding="utf-8").replace(
        "</models>",
        '<model name="Singing Face 1" DisplayAs="Poly Line" StringType="RGB Nodes" StartChannel="100" parm1="1" parm2="48" WorldPosX="10" WorldPosY="10" WorldPosZ="0" CustomColor="#FFD0A8">'
        '<subModel name="Mouth" layout="horizontal" type="ranges" line0="1-24"/>'
        '</model>'
        '<model name="HX_SNOWMAN_DRUMMER_KICK" DisplayAs="Single Line" StringType="RGB Nodes" StartChannel="300" parm1="1" parm2="8" WorldPosX="20" WorldPosY="0" WorldPosZ="0" CustomColor="#F6AD55"/>'
        "</models>",
    )
    layout.write_text(text, encoding="utf-8")
    sequence = tmp_path / "show.xsq"
    root = ET.Element("xsequence")
    head = ET.SubElement(root, "head")
    ET.SubElement(head, "sequenceDuration").text = "4.000"
    ET.SubElement(root, "ColorPalettes")
    effects = ET.SubElement(root, "ElementEffects")
    mouth = ET.SubElement(effects, "Element", {"type": "submodel", "name": "Singing Face 1/Mouth"})
    mouth_layer = ET.SubElement(mouth, "EffectLayer")
    ET.SubElement(mouth_layer, "Effect", {
        "name": "On", "startTime": "0", "endTime": "340", "palette": "0",
        "settings": "E_TEXTCTRL_Eff_On_Start=80", "label": "phoneme",
    })
    kick = ET.SubElement(effects, "Element", {"type": "model", "name": "HX_SNOWMAN_DRUMMER_KICK"})
    kick_layer = ET.SubElement(kick, "EffectLayer")
    ET.SubElement(kick_layer, "Effect", {
        "name": "On", "startTime": "800", "endTime": "1000", "palette": "0", "label": "kick",
    })
    matrix = ET.SubElement(effects, "Element", {"type": "model", "name": "Matrix"})
    matrix_layer = ET.SubElement(matrix, "EffectLayer")
    ET.SubElement(matrix_layer, "Effect", {
        "name": "On", "startTime": "800", "endTime": "1140", "palette": "0", "label": "held",
    })
    ET.ElementTree(root).write(sequence)
    apply_vivid_style(sequence, layout, sections=[
        {"label": "GROOVE", "start_ms": 0, "end_ms": 2000, "energy": 0.4},
        {"label": "DROP", "start_ms": 2000, "end_ms": 4000, "energy": 0.9},
    ])
    saved = ET.parse(sequence).getroot()
    mouth_effect = next(effect for effect in saved.findall(".//Effect") if effect.attrib.get("label") == "phoneme")
    kick_effect = next(effect for effect in saved.findall(".//Effect") if effect.attrib.get("label") == "kick")
    held = next(effect for effect in saved.findall(".//Effect") if effect.attrib.get("label") == "held")
    assert mouth_effect.attrib["endTime"] == "340" and mouth_effect.attrib["palette"] == "0"
    assert kick_effect.attrib["startTime"] == "800" and kick_effect.attrib["endTime"] == "1000"
    assert held.attrib["endTime"] == "1140"
    for name in ("Singing Face 1/Mouth", "HX_SNOWMAN_DRUMMER_KICK"):
        element = next(item for item in saved.find("ElementEffects") if item.attrib.get("name") == name)
        assert element.find("EffectLayer[@name='Helix Vivid']") is None


def test_vivid_layer_is_beat_locked_and_does_not_overlap(tmp_path: Path):
    layout = tmp_path / "layout.xml"
    _layout(layout)
    sequence = tmp_path / "show.xsq"
    _sequence(sequence)
    root = ET.parse(sequence).getroot()
    timing = ET.SubElement(root.find("ElementEffects"), "Element", {"type": "timing", "name": "Sections"})
    layer = ET.SubElement(timing, "EffectLayer")
    ET.SubElement(layer, "Effect", {"name": "On", "label": "INTRO", "startTime": "0", "endTime": "2000"})
    ET.SubElement(layer, "Effect", {"name": "On", "label": "DROP", "startTime": "2000", "endTime": "4000"})
    ET.ElementTree(root).write(sequence)
    first = apply_vivid_style(sequence, layout)
    other_layout = tmp_path / "neon-world.xml"
    other_layout.write_text(layout.read_text(encoding="utf-8"), encoding="utf-8")
    other = tmp_path / "other.xsq"
    _sequence(other)
    second = apply_vivid_style(other, other_layout)
    assert first["strategy"] != second["strategy"]
    saved = ET.parse(sequence).getroot()
    beat_starts = {
        int(float(effect.attrib["startTime"]))
        for effect in saved.findall(".//Effect")
        if effect.attrib.get("source") != "HelixVivid"
    }
    assert beat_starts
    for element in saved.find("ElementEffects"):
        vivid = element.find("EffectLayer[@name='Helix Vivid']")
        if vivid is None:
            continue
        spans = []
        for effect in vivid.findall("Effect"):
            start = int(effect.attrib["startTime"])
            end = int(effect.attrib["endTime"])
            assert start in beat_starts
            spans.append((start, end))
        spans.sort()
        for left, right in zip(spans, spans[1:]):
            assert left[1] <= right[0]


def test_white_bulbs_become_saturated():
    assert saturated_bulb("Window", (255, 255, 255)) != (255, 255, 255)
    assert saturated_bulb("Tree", (0, 255, 0)) == (0, 255, 0)
