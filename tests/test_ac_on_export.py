"""Strict safety regression for Light-O-Rama-oriented AC-only outputs."""
from __future__ import annotations

from pathlib import Path
import xml.etree.ElementTree as ET

import pytest

from tools.ac_on_export import inventory_layout, export_ac_on


def layout(path: Path, *, rgb_only=False):
    models = (
        '<model name="RGB matrix" StringType="RGB Nodes" StartChannel="4"/>'
        if rgb_only else (
            '<model name="R" StringType="Single Color Red" StartChannel="1"/>'
            '<model name="G" StringType="Single Color Green" StartChannel="2"/>'
            '<model name="W" StringType="Single Color White" StartChannel="3"/>'
            '<model name="Unknown white?" StringType="Single Color Intensity" StartChannel="9"/>'
            '<model name="RGB matrix" StringType="RGB Nodes" StartChannel="10"/>'
        )
    )
    path.write_text(
        '<xrgb><models>' + models + '</models><modelGroups>'
        '<modelGroup name="Triad" models="R,G,W,RGB matrix"/>'
        '<modelGroup name="Mixed nested" models="Triad,Unknown white?"/>'
        '</modelGroups></xrgb>',
        encoding="utf-8",
    )


def xsq(path: Path, *, only_rgb=False):
    target = "RGB matrix" if only_rgb else "Mixed nested"
    path.write_text(
        '<xsequence><head><sequenceDuration>2</sequenceDuration></head>'
        '<nextid>100</nextid><ColorPalettes><ColorPalette>'
        'C_BUTTON_Palette1=#00BFFF,C_CHECKBOX_Palette1=1'
        '</ColorPalette></ColorPalettes><EffectDB><Effect>foo</Effect></EffectDB>'
        '<DataLayers><DataLayer source="legacy"/></DataLayers>'
        '<DisplayElements><Element type="model" name="Triad"/>'
        '<Element type="timing" name="Parts"/></DisplayElements>'
        '<ElementEffects><Element type="model" name="' + target + '"><EffectLayer>'
        '<Effect name="Spirals" startTime="100" endTime="400" palette="0" ref="0"/>'
        '<Effect name="Bars" startTime="350" endTime="800" palette="0" ref="0"/>'
        '</EffectLayer></Element><Element type="model" name="RGB matrix"><EffectLayer>'
        '<Effect name="Plasma" startTime="100" endTime="1000"/>'
        '</EffectLayer></Element>'
        '<Element type="timing" name="Parts"><EffectLayer><Effect label="VERSE" startTime="0" endTime="2000"/>'
        '</EffectLayer></Element></ElementEffects></xsequence>',
        encoding="utf-8",
    )


def test_ac_export_group_expansion_color_safety_and_raw_preservation(tmp_path):
    l, source, output = (tmp_path / name for name in ("layout.xml", "raw.xsq", "ac.xsq"))
    layout(l)
    xsq(source)
    original = source.read_bytes()
    models, groups, excluded = inventory_layout(l)
    assert set(models) == {"R", "G", "W"}
    assert "Triad" in groups
    assert excluded["rgb nodes"] == 1
    report = export_ac_on(source, l, output)
    assert source.read_bytes() == original
    assert report["active_ac_channels"] == 3
    assert report["output_effects"] == 3  # overlapping 100-400 and 350-800 merged
    assert report["requires_manual_lor_unit_circuit_mapping"]
    assert report["excluded_input_effects"] == 1
    root = ET.parse(output).getroot()
    effects = root.findall("./ElementEffects/Element[@type='model']/EffectLayer/Effect")
    assert {e.get("name") for e in effects} == {"On"}
    assert {(e.get("startTime"), e.get("endTime")) for e in effects} == {("100", "800")}
    assert {e.get("palette") for e in effects} == {"0"}
    assert {e.get("ref") for e in effects} == {"0"}
    assert {e.get("name") for e in root.findall("./ElementEffects/Element[@type='model']")} == {"R", "G", "W"}
    assert len(root.findall("./ElementEffects/Element[@type='timing']")) == 1
    assert not root.findall("./DataLayers/DataLayer")
    assert {e.get("name") for e in root.findall("./DisplayElements/Element[@type='model']")} == {"R", "G", "W"}
    assert output.with_suffix(".ac_channel_map.csv").exists()
    assert output.with_suffix(".ac_validation.json").exists()


def test_rgb_only_layout_must_fail_closed(tmp_path):
    l, source, out = (tmp_path / p for p in ("rgb.xml", "raw.xsq", "out.xsq"))
    layout(l, rgb_only=True)
    xsq(source)
    with pytest.raises(ValueError, match="No explicit Single Color"):
        export_ac_on(source, l, out)
    assert not out.exists()


def test_no_mapped_source_effects_is_an_error(tmp_path):
    l, source, out = (tmp_path / p for p in ("mixed.xml", "raw.xsq", "out.xsq"))
    layout(l)
    xsq(source, only_rgb=True)
    with pytest.raises(ValueError, match="No incoming effects target"):
        export_ac_on(source, l, out)
    assert not out.exists()


def test_duplicate_channel_rejected(tmp_path):
    l = tmp_path / "duplicate.xml"
    l.write_text(
        '<xrgb><models>'
        '<model name="red" StringType="Single Color Red" StartChannel="1"/>'
        '<model name="white" StringType="Single Color White" StartChannel="1"/>'
        '</models></xrgb>'
    )
    with pytest.raises(ValueError, match="collision"):
        inventory_layout(l)


def test_repository_legacy_layout_is_not_rgb_only():
    source = Path(__file__).resolve().parents[1] / "xlights_rgbeffects.xml"
    if not source.exists():
        pytest.skip("Original root layout unavailable")
    models, _groups, _excluded = inventory_layout(source)
    assert {"red", "green", "white"} <= {m["color"] for m in models.values()}
    assert len(models) >= 70
