from __future__ import annotations
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, ElementTree


def build_style_effects_xml(rows):
    root = Element("HelixStyleEffects")

    for row in rows:
        effect = SubElement(root, "Effect")

        # Set flat attributes except palette
        for key, value in row.items():
            if key == "palette":
                continue
            effect.set(str(key), str(value))

        # Nested palette structure
        palette_node = SubElement(effect, "Palette")
        for color in row.get("palette", []):
            SubElement(palette_node, "Color", {"name": str(color)})

    return root


def write_style_effects_xml(rows, output_path):
    root = build_style_effects_xml(rows)
    tree = ElementTree(root)
    output_path = Path(output_path)
    tree.write(output_path, encoding="utf-8")
    return output_path
