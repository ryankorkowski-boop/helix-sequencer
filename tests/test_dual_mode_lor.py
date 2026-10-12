"""Regression for direct LMS -> Helix virtual layout -> mapped LMS workflow."""
from __future__ import annotations

import json
from pathlib import Path
import xml.etree.ElementTree as ET

import pytest

from tools.lor_lms_import import prepare_lms_workspace
from tools.lor_lms_export_from_source import export_lms_from_xsq
from tools.lor_compatibility import ac_layout_targets


def source(path: Path):
    path.write_text(
        '<?xml version="1.0"?><sequence saveFileVersion="14" musicFilename="original.wav">'
        '<channels>'
        '<channel name="Roof red" deviceType="LOR" unit="1" circuit="1" '
        'color="255" savedIndex="12" centiseconds="900">'
        '<effect type="intensity" startCentisecond="100" endCentisecond="160" intensity="100"/>'
        '</channel>'
        '<channel name="Roof green" deviceType="LOR" unit="1" circuit="2" '
        'color="65280" savedIndex="14" centiseconds="900"/>'
        '<channel name="Snowflake white" deviceType="LOR" unit="2" circuit="1" '
        'color="16777215" savedIndex="19" centiseconds="900"/>'
        '</channels>'
        '<timingGrids><timingGrid saveID="0" name="Old song grid" type="fixed" spacing="10"/></timingGrids>'
        '<tracks><track totalCentiseconds="900" timingGrid="0">'
        '<channels><channel savedIndex="12"/><channel savedIndex="14"/><channel savedIndex="19"/>'
        '</channels><loopLevels/></track></tracks>'
        '</sequence>', encoding="utf-8",
    )


def test_import_lms_keeps_real_addresses_and_generates_all_models(tmp_path: Path):
    original = tmp_path / "source.lms"
    source(original)
    untouched = original.read_bytes()
    workspace = tmp_path / "workspace"
    result = prepare_lms_workspace(original, workspace)
    assert original.read_bytes() == untouched
    assert len(result["channels"]) == 3
    assert [(x["unit"], x["circuit"], x["savedIndex"]) for x in result["channels"]] == [
        (1, 1, "12"), (1, 2, "14"), (2, 1, "19")
    ]
    safe, other, groups = ac_layout_targets(result["layout"])
    assert len(safe) == 3 and not other
    assert "01_ALL" in groups
    root = ET.parse(result["template"]).getroot()
    assert len(root.findall("./ElementEffects/Element[@type='model']")) == 3
    assert all(row.get("name") in safe for row in root.findall("./DisplayElements/Element"))


def test_direct_lms_export_reuses_real_controller_wiring(tmp_path: Path):
    original = tmp_path / "source.lms"
    source(original)
    imp = prepare_lms_workspace(original, tmp_path / "workspace")
    sequence = ET.parse(imp["template"])
    root = sequence.getroot()
    ET.SubElement(root.find("ColorPalettes"), "ColorPalette").text = (
        "C_BUTTON_Palette1=#FFFFFF,C_CHECKBOX_Palette1=1"
    )
    root.find("./head/sequenceDuration").text = "3.5"
    root.find("./head/mediaFile").text = "mysong.wav"
    names = {c["name"]: c["model"] for c in imp["channels"]}
    row1 = next(e for e in root.findall("./ElementEffects/Element") if e.get("name") == names["Roof red"])
    layer1 = row1.find("EffectLayer")
    ET.SubElement(layer1, "Effect", {"name": "On", "startTime": "100",
                  "endTime": "430", "ref": "0", "palette": "0"})
    ET.SubElement(layer1, "Effect", {"name": "Shimmer", "startTime": "500",
                  "endTime": "900", "ref": "0", "palette": "0"})
    row2 = next(e for e in root.findall("./ElementEffects/Element") if e.get("name") == names["Roof green"])
    ET.SubElement(row2.find("EffectLayer"), "Effect", {"name": "Twinkle",
                  "startTime": "700", "endTime": "980", "ref": "0", "palette": "0"})
    song = tmp_path / "song.xsq"
    sequence.write(song, encoding="utf-8")
    destination = tmp_path / "new-song.lms"
    report = export_lms_from_xsq(song, original, destination, Path(imp["manifest"]))
    assert report["output_effects"] == 3
    output_root = ET.parse(destination).getroot()
    assert output_root.get("musicFilename") == "mysong.wav"
    channels = output_root.findall("./channels/channel")
    assert [(c.get("unit"), c.get("circuit"), c.get("savedIndex")) for c in channels] == [
        ("1", "1", "12"), ("1", "2", "14"), ("2", "1", "19")
    ]
    assert [(e.get("type"), e.get("startCentisecond"), e.get("endCentisecond"))
            for e in channels[0].findall("effect")] == [
        ("intensity", "10", "43"), ("shimmer", "50", "90")
    ]
    assert channels[1].find("effect").get("type") == "twinkle"
    assert channels[2].findall("effect") == []
    assert original.read_text().find("original.wav") >= 0
    assert report["verified_lor_import"] is False


def test_changed_lms_is_rejected(tmp_path: Path):
    original = tmp_path / "source.lms"
    source(original)
    imp = prepare_lms_workspace(original, tmp_path / "work")
    original.write_text(original.read_text().replace('unit="1"', 'unit="9"'))
    with pytest.raises(ValueError, match="has changed"):
        export_lms_from_xsq(Path(imp["template"]), original, tmp_path / "new.lms", Path(imp["manifest"]))


def test_duplicate_controller_address_is_rejected(tmp_path: Path):
    original = tmp_path / "bad.lms"
    source(original)
    original.write_text(original.read_text().replace('unit="1" circuit="2"', 'unit="1" circuit="1"'))
    with pytest.raises(ValueError, match="Duplicate LOR"):
        prepare_lms_workspace(original, tmp_path / "work")


def test_loredit_requires_explicit_unavailable_legacy_import(tmp_path: Path):
    wrong = tmp_path / "modern.loredit"
    wrong.write_bytes(b"not an LMS")
    with pytest.raises(ValueError, match="Modern .loredit"):
        prepare_lms_workspace(wrong, tmp_path / "work")
