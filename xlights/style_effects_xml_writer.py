from __future__ import annotations
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, tostring


def build_style_effects_xml(effects: list[dict]) -> str:
    root = Element("StyleEffects")
    for effect in effects:
        e = SubElement(root, "Effect")
        for k, v in effect.items():
            e.set(str(k), str(v))
    return tostring(root, encoding="unicode")


def write_style_effects_xml(effects: list[dict], output_path: str | Path) -> Path:
    xml_string = build_style_effects_xml(effects)
    path = Path(output_path)
    path.write_text(xml_string, encoding="utf-8")
    return path
