import xml.etree.ElementTree as ET
from pathlib import Path

from core.musical_bed import apply_musical_bed, bed_intervals, bed_level


def test_long_gaps_receive_a_dim_bed_and_hits_stay():
    assert bed_intervals([(1000, 1200), (8000, 8300)], 10000) == [(0, 1000), (1200, 8000), (8300, 10000)]
    assert bed_intervals([(0, 100), (200, 300)], 400, min_gap_ms=700) == []
    assert bed_level(0) == 12
    assert bed_level(1) == 28
    path = Path("/tmp/bed-test.xsq")
    root = ET.Element("xsequence")
    effects = ET.SubElement(root, "ElementEffects")
    element = ET.SubElement(effects, "Element", {"type": "model", "name": "Arch"})
    layer = ET.SubElement(element, "EffectLayer")
    ET.SubElement(layer, "Effect", {"name": "On", "startTime": "1000", "endTime": "1200", "settings": "E_TEXTCTRL_Eff_On_Start=100"})
    ET.ElementTree(root).write(path)
    report = apply_musical_bed(path, 10000, 0.5)
    assert report["beds"] == 2
    assert report["level"] == 20
    saved = ET.parse(path)
    names = [e.attrib.get("source") for e in saved.findall(".//Effect")]
    assert names.count("HelixMusicalBed") == 2
    assert any(e.attrib.get("startTime") == "1000" for e in saved.findall(".//Effect"))
