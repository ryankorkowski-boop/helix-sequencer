from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from tools.integrate_drummer_v3_into_xsq import _find_or_create_element_effects
from tools.validate_xsq_structure import validate_xsq


def test_validator_accepts_current_element_effects_schema(tmp_path: Path) -> None:
    root = ET.Element("xsequence")
    ET.SubElement(root, "timingtrack", {"name": "Drummer"})
    container = _find_or_create_element_effects(root)
    element = ET.SubElement(container, "Element", {"type": "model", "name": "HX_DRUMMER_CH01_KICK"})
    ET.SubElement(element, "EffectLayer", {"name": "AUTO_Drummer_V3", "visible": "1"})

    path = tmp_path / "current.xsq"
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)
    validate_xsq(path)


def test_validator_rejects_empty_current_element_effects_schema(tmp_path: Path) -> None:
    root = ET.Element("xsequence")
    ET.SubElement(root, "timingtrack", {"name": "Drummer"})
    _find_or_create_element_effects(root)

    path = tmp_path / "empty.xsq"
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)

    try:
        validate_xsq(path)
    except Exception as exc:
        assert "No Element entries" in str(exc)
    else:
        raise AssertionError("Empty ElementEffects container should not validate")
