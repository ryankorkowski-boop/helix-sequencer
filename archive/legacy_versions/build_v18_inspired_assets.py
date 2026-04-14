#!/usr/bin/env python3
from __future__ import annotations

import copy
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

import v1 as base


ROOT = Path(__file__).resolve().parent
SRC_LAYOUT = ROOT / "xlights_rgbeffects.xml"
SRC_LAYOUT_BK = ROOT / "xlights_rgbeffects.xbkp"
SRC_TEMPLATE = ROOT / "template.xsq"
OUT_DIR = ROOT / "showcase_assets" / "v18_showcase_pack"
OUT_LAYOUT = OUT_DIR / "xlights_rgbeffects.xml"
OUT_LAYOUT_BK = OUT_DIR / "xlights_rgbeffects.xbkp"
OUT_TEMPLATE = OUT_DIR / "template_v18_showcase_pack.xsq"
README = OUT_DIR / "README.txt"


def _indent_xml(elem: ET.Element, level: int = 0) -> None:
    pad = "\n" + ("  " * level)
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = pad + "  "
        for child in elem:
            _indent_xml(child, level + 1)
        if not elem[-1].tail or not elem[-1].tail.strip():
            elem[-1].tail = pad
    if level and (not elem.tail or not elem.tail.strip()):
        elem.tail = pad


def _ordered_unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if not item or item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def _parse_layout_coordinates(layout_path: Path) -> dict[str, tuple[float, float]]:
    tree = ET.parse(layout_path)
    root = tree.getroot()
    models_el = root.find("models")
    if models_el is None:
        return {}
    coords: dict[str, tuple[float, float]] = {}
    for child in models_el:
        name = child.attrib.get("name", "").strip()
        if not name:
            continue
        try:
            x = float(child.attrib.get("WorldPosX", "0") or 0.0)
            y = float(child.attrib.get("WorldPosY", "0") or 0.0)
        except ValueError:
            x = 0.0
            y = 0.0
        coords[name] = (x, y)
    return coords


def _bbox_for(names: list[str], coords: dict[str, tuple[float, float]]) -> dict[str, str]:
    points = [coords[name] for name in names if name in coords]
    if not points:
        return {
            "centrex": "0",
            "centrey": "0",
            "centreDefined": "0",
            "centreMinx": "0",
            "centreMiny": "0",
            "centreMaxx": "0",
            "centreMaxy": "0",
        }
    xs = [pt[0] for pt in points]
    ys = [pt[1] for pt in points]
    return {
        "centrex": f"{sum(xs) / len(xs):.3f}",
        "centrey": f"{sum(ys) / len(ys):.3f}",
        "centreDefined": "0",
        "centreMinx": f"{min(xs):.0f}",
        "centreMiny": f"{min(ys):.0f}",
        "centreMaxx": f"{max(xs):.0f}",
        "centreMaxy": f"{max(ys):.0f}",
    }


def _find_or_clone_group_template(models_el: ET.Element) -> ET.Element:
    for child in models_el:
        if child.tag == "modelGroup":
            return copy.deepcopy(child)
    return ET.Element("modelGroup")


def _set_group(group_el: ET.Element, name: str, models: list[str], coords: dict[str, tuple[float, float]]) -> ET.Element:
    group_el.tag = "modelGroup"
    group_el.clear()
    attrs = {
        "layout": "minimalGrid",
        "GridSize": "400",
        "LayoutGroup": "Codex Showcase",
        "name": name,
        "TagColour": "black",
        "XCentreOffset": "0",
        "YCentreOffset": "0",
        "DefaultCamera": "2D",
        "models": ",".join(models),
    }
    attrs.update(_bbox_for(models, coords))
    group_el.attrib.update(attrs)
    return group_el


def main() -> int:
    if not SRC_LAYOUT.exists() or not SRC_TEMPLATE.exists():
        raise SystemExit("Source xLights layout/template not found.")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SRC_TEMPLATE, OUT_TEMPLATE)
    if SRC_LAYOUT_BK.exists():
        shutil.copy2(SRC_LAYOUT_BK, OUT_LAYOUT_BK)

    tree = ET.parse(SRC_LAYOUT)
    root = tree.getroot()
    models_el = root.find("models")
    if models_el is None:
        raise SystemExit("Layout XML did not contain a <models> element.")

    names = [child.attrib.get("name", "") for child in models_el if child.attrib.get("name")]
    coords = _parse_layout_coordinates(SRC_LAYOUT)
    layout = base.discover_layout(names)

    flood_models = [name for name in names if "flood" in base.normalize_name(name) or "strobe" in base.normalize_name(name)]
    arch_models = [model for arch in layout.arches.values() for model in arch]
    star_flake_models = _ordered_unique(layout.stars + layout.snowflakes)
    feature_models = _ordered_unique(
        [layout.mega_group, layout.line_all, layout.cane_g_n, layout.cane_g_s, layout.notes_main, layout.notes_mirror, layout.all_notes]
    )
    wholehouse_models = _ordered_unique(
        [layout.house, layout.garage, layout.perim_all, layout.blvd_all, layout.all_red, layout.all_green, layout.all_white]
    )
    all_pixels = _ordered_unique(wholehouse_models + feature_models + arch_models + flood_models + star_flake_models)

    groups_to_add = {
        "18X_SHOWCASE_WHOLEHOUSE": wholehouse_models,
        "18X_SHOWCASE_FEATURES": feature_models,
        "18X_SHOWCASE_ARCH_DETAIL": arch_models,
        "18X_SHOWCASE_FLOODS": flood_models,
        "18X_SHOWCASE_STARS_FLAKES": star_flake_models,
        "18X_SHOWCASE_ALLPIXELS": all_pixels,
    }

    existing = {child.attrib.get("name", ""): child for child in models_el if child.tag == "modelGroup"}
    template_group = _find_or_clone_group_template(models_el)
    for group_name, group_models in groups_to_add.items():
        if not group_models:
            continue
        new_group = _set_group(copy.deepcopy(template_group), group_name, group_models, coords)
        if group_name in existing:
            models_el.remove(existing[group_name])
        models_el.append(new_group)

    _indent_xml(root)
    tree.write(OUT_LAYOUT, encoding="utf-8", xml_declaration=True)

    README.write_text(
        "\n".join(
            [
                "v18 Showcase Temporary Asset Pack",
                "",
                "This is an original showcase asset pack built from your current layout/template.",
                "It adds reusable showcase groups such as:",
                "- whole-house mapping groups",
                "- feature-prop collections",
                "- arches/canes/mega/flood support groups",
                "- whole-house and feature-prop scene pickups",
                "",
                f"Template: {OUT_TEMPLATE.name}",
                f"Layout:   {OUT_LAYOUT.name}",
                f"Backup:   {OUT_LAYOUT_BK.name if OUT_LAYOUT_BK.exists() else 'not created'}",
            ]
        ),
        encoding="utf-8",
    )
    print(f"Created showcase asset pack in {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
