from __future__ import annotations

import argparse
import json
import re
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


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


def _normalize(name: str) -> str:
    return " ".join((name or "").lower().replace("_", " ").replace("-", " ").split())


def _extract_channel_number(raw: str) -> int:
    text = (raw or "").strip()
    if not text:
        return 0
    m = re.match(r"(\d+)", text)
    return int(m.group(1)) if m else 0


def _max_channel(models_el: ET.Element) -> int:
    out = 0
    for model in models_el.findall("model"):
        out = max(out, _extract_channel_number(model.attrib.get("StartChannel", "")))
    return out


def _to_float(text: str, default: float = 0.0) -> float:
    try:
        return float(text)
    except Exception:
        return default


def _set_world_z(model: ET.Element, value: float) -> None:
    model.attrib["WorldPosZ"] = f"{value:.4f}"


def _collect_model_names(models_el: ET.Element) -> set[str]:
    return {str(model.attrib.get("name") or "").strip() for model in models_el.findall("model") if str(model.attrib.get("name") or "").strip()}


def _infer_scene_bucket(model_name: str) -> str:
    norm = _normalize(model_name)
    if any(token in norm for token in ("n bh", "nbh", "helixmascot", "matrix", "spinner", "mega", "cube", "sphere", "custom")):
        return "showcase_3d"
    if any(token in norm for token in ("roof", "icicle", "arch", "star", "wreath", "c9", "ac", "single color")):
        return "core_ac"
    return "subtle_neighbors"


def _add_or_replace_group(model_groups_el: ET.Element, name: str, members: list[str]) -> None:
    members = [m for m in members if m]
    if not members:
        return
    existing = None
    for group in model_groups_el.findall("modelGroup"):
        if str(group.attrib.get("name") or "") == name:
            existing = group
            break
    if existing is not None:
        model_groups_el.remove(existing)
    attrs = {
        "name": name,
        "GridSize": "400",
        "XCentreOffset": "0",
        "YCentreOffset": "0",
        "DefaultCamera": "2D",
        "layout": "minimalGrid",
        "TagColour": "black",
        "LayoutGroup": "Helixville",
        "models": ",".join(members),
        "centrex": "0",
        "centrey": "0",
        "centreDefined": "0",
        "centreMinx": "0",
        "centreMiny": "0",
        "centreMaxx": "0",
        "centreMaxy": "0",
    }
    ET.SubElement(model_groups_el, "modelGroup", attrs)


def _parse_xmodel(path: Path) -> dict[str, Any] | None:
    try:
        root = ET.parse(path).getroot()
    except Exception:
        return None
    if root.tag.lower() != "custommodel":
        return None
    name = str(root.attrib.get("name") or path.stem).strip()
    parm1 = str(root.attrib.get("parm1") or "16")
    parm2 = str(root.attrib.get("parm2") or "16")
    string_type = str(root.attrib.get("StringType") or "RGB Nodes")
    custom_model = str(root.attrib.get("CustomModel") or "")
    if not custom_model:
        return None
    return {
        "name": name,
        "parm1": parm1,
        "parm2": parm2,
        "string_type": string_type,
        "custom_model": custom_model,
    }


def _import_custom_models(
    *,
    models_el: ET.Element,
    xmodel_files: list[Path],
    start_channel: int,
) -> tuple[list[str], int]:
    imported_names: list[str] = []
    used_names = _collect_model_names(models_el)
    channel = max(1, int(start_channel))
    base_x = 4600.0
    base_y = 920.0
    for idx, xmodel_path in enumerate(sorted(xmodel_files)):
        parsed = _parse_xmodel(xmodel_path)
        if parsed is None:
            continue
        raw_name = f"HELIXVILLE_OS_{parsed['name']}".strip()
        name = raw_name
        suffix = 2
        while name in used_names:
            name = f"{raw_name}_{suffix}"
            suffix += 1
        used_names.add(name)
        row = idx // 8
        col = idx % 8
        x = base_x + (col * 170.0)
        y = base_y + (row * 140.0)
        z = 28.0 + ((idx % 5) * 9.5)
        attrs = {
            "DisplayAs": "Custom",
            "StringType": str(parsed["string_type"]),
            "Dir": "L",
            "StartSide": "T",
            "Antialias": "1",
            "PixelSize": "2",
            "Transparency": "0",
            "parm1": str(parsed["parm1"]),
            "parm2": str(parsed["parm2"]),
            "parm3": "1",
            "name": name,
            "LayoutGroup": "Helixville Imported",
            "WorldPosX": f"{x:.4f}",
            "WorldPosY": f"{y:.4f}",
            "WorldPosZ": f"{z:.4f}",
            "ScaleX": "2.6000",
            "ScaleY": "2.6000",
            "ScaleZ": "0.3500",
            "RotateX": "0.00000000",
            "RotateY": "0.00000000",
            "RotateZ": "0.00000000",
            "CustomModel": str(parsed["custom_model"]),
            "versionNumber": "7",
            "StartChannel": str(channel),
        }
        model = ET.SubElement(models_el, "model", attrs)
        ET.SubElement(model, "ControllerConnection", {"Protocol": "LOR Optimised"})
        imported_names.append(name)
        channel += int(max(12, _to_float(parsed["parm1"], 16.0) * _to_float(parsed["parm2"], 16.0) * 3))
    return imported_names, channel


def _apply_depth_staging(models_el: ET.Element) -> dict[str, int]:
    buckets = {"core_ac": 0, "showcase_3d": 0, "subtle_neighbors": 0}
    for model in models_el.findall("model"):
        name = str(model.attrib.get("name") or "")
        bucket = _infer_scene_bucket(name)
        z = _to_float(model.attrib.get("WorldPosZ", "0"), 0.0)
        if z != 0.0:
            buckets[bucket] += 1
            continue
        if bucket == "showcase_3d":
            x = _to_float(model.attrib.get("WorldPosX", "0"), 0.0)
            staged = 22.0 + ((abs(x) % 420.0) / 420.0) * 46.0
            _set_world_z(model, staged)
        elif bucket == "subtle_neighbors":
            x = _to_float(model.attrib.get("WorldPosX", "0"), 0.0)
            staged = 4.0 + ((abs(x) % 260.0) / 260.0) * 15.0
            _set_world_z(model, staged)
        else:
            _set_world_z(model, 0.0)
        buckets[bucket] += 1
    return buckets


def build_layout(
    *,
    base_layout: Path,
    xmodel_root: Path,
    output_layout: Path,
) -> dict[str, Any]:
    tree = ET.parse(base_layout)
    root = tree.getroot()
    models_el = root.find("models")
    groups_el = root.find("modelGroups")
    if models_el is None or groups_el is None:
        raise RuntimeError("Layout is missing <models> or <modelGroups> sections.")

    existing_model_names = [str(model.attrib.get("name") or "") for model in models_el.findall("model")]
    max_channel = _max_channel(models_el)
    xmodels = sorted(xmodel_root.rglob("*.xmodel")) if xmodel_root.exists() else []
    imported_names, next_channel = _import_custom_models(models_el=models_el, xmodel_files=xmodels, start_channel=max_channel + 1)
    bucket_counts = _apply_depth_staging(models_el)

    core_ac = [name for name in existing_model_names if _infer_scene_bucket(name) == "core_ac"]
    showcase = [name for name in existing_model_names if _infer_scene_bucket(name) == "showcase_3d"]
    subtle = [name for name in existing_model_names if _infer_scene_bucket(name) == "subtle_neighbors"]
    showcase.extend(imported_names)

    _add_or_replace_group(groups_el, "HELIXVILLE_CORE_AC", core_ac[:320])
    _add_or_replace_group(groups_el, "HELIXVILLE_NEXTDOOR_SHOWCASE_3D", showcase[:420])
    _add_or_replace_group(groups_el, "HELIXVILLE_SUBTLE_NEIGHBORS", subtle[:420])
    _add_or_replace_group(groups_el, "HELIXVILLE_IMPORTED_CUSTOM_MODELS", imported_names[:320])

    _indent_xml(root)
    output_layout.parent.mkdir(parents=True, exist_ok=True)
    tree.write(output_layout, encoding="utf-8", xml_declaration=True)

    return {
        "base_layout": str(base_layout),
        "output_layout": str(output_layout),
        "imported_xmodel_count": len(imported_names),
        "next_channel": int(next_channel),
        "depth_bucket_counts": bucket_counts,
        "xmodel_source_root": str(xmodel_root),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Helixville importable 3D layout with open-source custom model imports.")
    parser.add_argument(
        "--base-layout",
        default="allmodels/xlights_rgbeffects.xml",
        help="Base xlights_rgbeffects.xml to extend.",
    )
    parser.add_argument(
        "--xmodel-root",
        default="external/open_source_assets/models",
        help="Folder containing downloaded .xmodel files.",
    )
    parser.add_argument(
        "--output-layout",
        default="outputs/layouts/helixville_importable_3d/xlights_rgbeffects.xml",
        help="Output importable layout path.",
    )
    parser.add_argument(
        "--report",
        default="outputs/layouts/helixville_importable_3d/layout_report.json",
        help="Output report path.",
    )
    parser.add_argument(
        "--copy-support-files",
        action="store_true",
        help="Copy xlights_networks.xml and xlights_keybindings.xml next to output layout when present.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    base_layout = Path(args.base_layout).resolve()
    xmodel_root = Path(args.xmodel_root).resolve()
    output_layout = Path(args.output_layout).resolve()
    report_path = Path(args.report).resolve()
    if not base_layout.exists():
        raise SystemExit(f"Base layout not found: {base_layout}")

    payload = build_layout(base_layout=base_layout, xmodel_root=xmodel_root, output_layout=output_layout)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    if args.copy_support_files:
        for filename in ("xlights_networks.xml", "xlights_keybindings.xml"):
            src = base_layout.parent.parent / filename
            if not src.exists():
                src = Path.cwd() / filename
            if src.exists():
                shutil.copy2(src, output_layout.parent / filename)

    print(f"Helixville layout built: {output_layout}")
    print(f"Imported custom models: {payload['imported_xmodel_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
