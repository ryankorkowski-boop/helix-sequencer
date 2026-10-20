"""Real legacy LMS export requires explicit, unambiguous LOR mapping."""
from __future__ import annotations

import csv
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

from tools.legacy_lms_export import export_legacy_lms, read_lor_map
from tools.inspect_lms import inspect_lms


def fixture(tmp: Path, *, mapped=True):
    source = tmp / "ac.xsq"
    source.write_text(
        '<xsequence><head><sequenceDuration>2.0</sequenceDuration>'
        '<mediaFile>jingle.wav</mediaFile><song>Test song</song></head>'
        '<ColorPalettes><ColorPalette>C_BUTTON_Palette1=#FFFFFF,'
        'C_CHECKBOX_Palette1=1</ColorPalette></ColorPalettes>'
        '<EffectDB><Effect>E_TEXTCTRL_Eff_On_Start=100,'
        'E_TEXTCTRL_Eff_On_End=100</Effect></EffectDB>'
        '<ElementEffects><Element type="model" name="Roof Red"><EffectLayer>'
        '<Effect name="On" startTime="105" endTime="334" ref="0" palette="0"/>'
        '<Effect name="On" startTime="330" endTime="600" ref="0" palette="0"/>'
        '</EffectLayer></Element><Element type="model" name="Tree White">'
        '<EffectLayer><Effect name="On" startTime="1200" endTime="1500"'
        ' ref="0" palette="0"/></EffectLayer></Element>'
        '</ElementEffects></xsequence>',
        encoding="utf-8"
    )
    mapping = tmp / "ac.ac_channel_map.csv"
    with mapping.open("w", encoding="utf-8", newline="") as stream:
        w = csv.DictWriter(stream, fieldnames=[
            "model","color","xlights_start_channel","controller_unit",
            "controller_circuit","controller_protocol"
        ])
        w.writeheader()
        w.writerow({"model":"Roof Red","color":"red","xlights_start_channel":256,
                    "controller_unit":"0x02" if mapped else "",
                    "controller_circuit":"1","controller_protocol":"LOR Optimised"})
        w.writerow({"model":"Tree White","color":"white","xlights_start_channel":1024,
                    "controller_unit":"3","controller_circuit":"16",
                    "controller_protocol":"LOR Optimised"})
    return source, mapping


def test_lms_is_a_real_legacy_sequence_with_exact_circuits(tmp_path: Path):
    source, mapping = fixture(tmp_path)
    raw = source.read_bytes()
    destination = tmp_path / "music.lms"
    report = export_legacy_lms(source, mapping, destination)
    assert source.read_bytes() == raw
    assert report["mapped_channels"] == 2 and report["on_effects"] == 2
    assert report["verified_lor_import"] is False
    root = ET.parse(destination).getroot()
    assert root.tag == "sequence" and root.get("saveFileVersion") == "14"
    assert root.get("musicFilename") == "jingle.wav"
    channels = root.findall("./channels/channel")
    assert {(e.get("unit"),e.get("circuit")) for e in channels} == {("2","1"),("3","16")}
    assert [(e.get("startCentisecond"),e.get("endCentisecond"),e.get("intensity"))
            for e in channels[0].findall("effect")] == [("10","60","100")]
    assert root.find("./tracks/track/channels") is not None
    inspection = inspect_lms(destination)
    assert inspection.xml_root == "sequence"
    assert inspection.probable_channel_count >= 2
    assert inspection.probable_duration_seconds == 2.0


def test_lms_refuses_unknown_or_incomplete_controller_mapping(tmp_path: Path):
    source, mapping = fixture(tmp_path, mapped=False)
    destination = tmp_path / "song.lms"
    with pytest.raises(ValueError, match="Missing controller_unit"):
        export_legacy_lms(source, mapping, destination)
    assert not destination.exists()


def test_lms_rejects_duplicate_physical_addresses(tmp_path: Path):
    _source, mapping = fixture(tmp_path)
    text = mapping.read_text().replace("3,16,", "0x02,1,")
    mapping.write_text(text)
    with pytest.raises(ValueError, match="Duplicate LOR Unit/Circuit"):
        read_lor_map(mapping)


def test_lms_rejects_fades_and_non_on_effects(tmp_path: Path):
    source, mapping = fixture(tmp_path)
    source.write_text(source.read_text().replace('name="On"', 'name="Ramp"', 1))
    with pytest.raises(ValueError, match="Only AC On effects allowed"):
        export_legacy_lms(source, mapping, tmp_path / "song.lms")


def test_lms_rejects_unmapped_model_even_with_valid_map(tmp_path: Path):
    source, mapping = fixture(tmp_path)
    source.write_text(source.read_text().replace('name="Tree White"', 'name="Unknown"', 1))
    with pytest.raises(ValueError, match="Missing approved LOR"):
        export_legacy_lms(source, mapping, tmp_path / "song.lms")


@pytest.mark.parametrize("config", [
    "E_TEXTCTRL_Eff_On_Start=1000,E_TEXTCTRL_Eff_On_End=100",
    "E_TEXTCTRL_Eff_On_Start=100,E_TEXTCTRL_Eff_On_End=100.5",
    "E_TEXTCTRL_Eff_On_Start=100,E_TEXTCTRL_Eff_On_End=100,E_TEXTCTRL_Eff_On_Start=0",
    "E_TEXTCTRL_Eff_On_Start=100,E_TEXTCTRL_Eff_On_End=100,B_SLIDER_Brightness=50",
    "E_TEXTCTRL_Eff_On_Start=100,E_TEXTCTRL_Eff_On_End=100,malformed",
])
def test_lms_rejects_unaudited_intensity_before_writing(tmp_path, config):
    source, mapping = fixture(tmp_path)
    tree = ET.parse(source)
    tree.find("./EffectDB/Effect").text = config
    tree.write(source)
    original = source.read_bytes()
    destination = tmp_path / "song.lms"
    with pytest.raises(ValueError, match="Non-constant intensity"):
        export_legacy_lms(source, mapping, destination)
    assert source.read_bytes() == original
    assert not destination.exists()
    assert not destination.with_suffix(".lms_validation.json").exists()


@pytest.mark.parametrize("palette", [
    "C_BUTTON_Palette1=#FFFFFF00,C_CHECKBOX_Palette1=1",
    "C_BUTTON_Palette1=#FFFFFF,C_CHECKBOX_Palette1=0",
    "C_BUTTON_Palette1=#FFFFFF,C_CHECKBOX_Palette1=1,C_CHECKBOX_Palette1=0",
    "C_BUTTON_Palette1=#FFFFFF,C_CHECKBOX_Palette1=1,C_BUTTON_Palette2=#FF0000,C_CHECKBOX_Palette2=1",
])
def test_lms_rejects_unaudited_palette_before_writing(tmp_path, palette):
    source, mapping = fixture(tmp_path)
    tree = ET.parse(source)
    tree.find("./ColorPalettes/ColorPalette").text = palette
    tree.write(source)
    destination = tmp_path / "song.lms"
    with pytest.raises(ValueError, match="white-intensity"):
        export_legacy_lms(source, mapping, destination)
    assert not destination.exists()
    assert not destination.with_suffix(".lms_validation.json").exists()


def test_lms_accepts_reordered_plain_on_settings(tmp_path):
    source, mapping = fixture(tmp_path)
    tree = ET.parse(source)
    tree.find("./EffectDB/Effect").text = (
        " E_TEXTCTRL_Eff_On_End = 100 , E_TEXTCTRL_Eff_On_Start = 100 "
    )
    tree.find("./ColorPalettes/ColorPalette").text = (
        " C_CHECKBOX_Palette1 = 1 , C_BUTTON_Palette1 = #ffffff "
    )
    tree.write(source)
    destination = tmp_path / "song.lms"
    report = export_legacy_lms(source, mapping, destination)
    assert report["on_effects"] == 2
    assert all(effect.get("intensity") == "100"
               for effect in ET.parse(destination).findall("./channels/channel/effect"))
