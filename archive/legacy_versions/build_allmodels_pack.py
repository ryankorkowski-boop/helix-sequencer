#!/usr/bin/env python3
from __future__ import annotations

import math
import os
import shutil
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

import v1 as base


ROOT = Path(__file__).resolve().parent
SRC_LAYOUT = ROOT / "xlights_rgbeffects.xml"
SRC_TEMPLATE = ROOT / "template.xsq"
SRC_AUDIO = ROOT / "13.wav"
SRC_IMAGE_CANDIDATES = [ROOT / "13v1_frame0.png", ROOT / "13v1_frame200.png"]
SRC_SUPPORT_FILES = [
    ROOT / "xlights_networks.xml",
    ROOT / "xlights_keybindings.xml",
]

PACK_DIR = ROOT / "allmodels"
OUT_LAYOUT = PACK_DIR / "xlights_rgbeffects.xml"
OUT_LAYOUT_BK = PACK_DIR / "xlights_rgbeffects.xbkp"
OUT_TEMPLATE = PACK_DIR / "template2.xsq"
OUT_AUDIO = PACK_DIR / "13.wav"
OUT_README = PACK_DIR / "README.txt"
OUT_AUDIT = PACK_DIR / "PACK_SUMMARY.txt"
OUT_OUTPUTS = PACK_DIR / "outputs"
OUT_IMAGES = PACK_DIR / "Images"
BACKUP_DIR = PACK_DIR / "_full_synthetic_backup"

SAFE_LAYOUT_GROUP = "All Previews"
SHOWCASE_PREFIX = "ALLMODELS "
PREVIEW_NETWORK_DESC = "Dream Sequence Weaver allmodels preview overflow"
UNSAFE_EDGE_GROUP = "ALLMODELS_EDGE_CASES"
INCLUDE_UNSAFE_EDGE_CASES = True
INCLUDE_MATRIX_FAMILY = True
INCLUDE_CIRCLE_FAMILY = True
PREVIEW_NETWORK_MAX = 100000

COLOR_HEX = {
    "red": "#FF0000",
    "green": "#00FF00",
    "white": "#FFFFFF",
}


@dataclass
class SubModelSpec:
    name: str
    lines: list[str]
    layout: str = "horizontal"
    type: str = "ranges"
    aliases: list[str] = field(default_factory=list)


@dataclass
class ModelSpec:
    name: str
    display_as: str
    string_type: str
    start_channel: int
    total_pixels: int
    x: float
    y: float
    attrs: dict[str, str]
    z: float = 0.0
    custom_color: str | None = None
    tag_color: str | None = None
    aliases: list[str] = field(default_factory=list)
    submodels: list[SubModelSpec] = field(default_factory=list)


def _fmt(value: float) -> str:
    return f"{value:.6f}"


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


def _normalize_csv(names: list[str]) -> str:
    seen: set[str] = set()
    out: list[str] = []
    for name in names:
        key = (name or "").strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(name)
    return ",".join(out)


def _normalized_key(name: str) -> str:
    return (name or "").strip().lower()


def _showcase_name(name: str) -> str:
    stripped = (name or "").strip()
    if not stripped:
        return SHOWCASE_PREFIX.strip()
    if _normalized_key(stripped).startswith(_normalized_key(SHOWCASE_PREFIX)):
        return stripped
    return f"{SHOWCASE_PREFIX}{stripped}"


def _channel_span(string_type: str, total_pixels: int) -> int:
    return max(1, total_pixels * 3) if any(token in (string_type or "").lower() for token in ("rgb", "pixel", "node")) else 1


def _two_point_attrs(x2: float, y2: float, z2: float = 0.0) -> dict[str, str]:
    return {"X2": _fmt(x2), "Y2": _fmt(y2), "Z2": _fmt(z2)}


def _three_point_attrs(x2: float, y2: float, height: float, *, angle: float = 0.0, shear: float = 0.0) -> dict[str, str]:
    attrs = _two_point_attrs(x2, y2)
    attrs.update({"RotateX": "0.000000", "Angle": _fmt(angle), "Shear": _fmt(shear), "Height": _fmt(height)})
    return attrs


def _boxed_attrs(scale_x: float, scale_y: float, *, scale_z: float = 1.0, rotate_z: float = 0.0) -> dict[str, str]:
    return {
        "ScaleX": _fmt(scale_x),
        "ScaleY": _fmt(scale_y),
        "ScaleZ": _fmt(scale_z),
        "RotateX": "0.000000",
        "RotateY": "0.000000",
        "RotateZ": _fmt(rotate_z),
    }


def _poly_attrs(points: list[tuple[float, float]]) -> dict[str, str]:
    flat: list[str] = []
    for x, y in points:
        flat.extend([_fmt(x), _fmt(y), "0.000000"])
    return {
        "ScaleX": "1.000000",
        "ScaleY": "1.000000",
        "ScaleZ": "1.000000",
        "NumPoints": str(len(points)),
        "PointData": ",".join(flat),
        "cPointData": "",
    }


def _multi_attrs(points: list[tuple[float, float]]) -> dict[str, str]:
    flat: list[str] = []
    for x, y in points:
        flat.extend([_fmt(x), _fmt(y), "0.000000"])
    return {"NumPoints": str(len(points)), "PointData": ",".join(flat)}


def _segments(total: int, labels: list[str]) -> list[SubModelSpec]:
    total = max(1, total)
    out: list[SubModelSpec] = []
    for idx, label in enumerate(labels):
        start = int(math.floor(total * idx / len(labels))) + 1
        end = max(start, int(math.floor(total * (idx + 1) / len(labels))))
        out.append(SubModelSpec(label, [f"{start}-{end}"]))
    return out


def _add_model(models_el: ET.Element, spec: ModelSpec) -> None:
    attrs = {
        "name": spec.name,
        "DisplayAs": spec.display_as,
        "StringType": spec.string_type,
        "WorldPosX": _fmt(spec.x),
        "WorldPosY": _fmt(spec.y),
        "WorldPosZ": _fmt(spec.z),
        "PixelSize": "2",
        "Transparency": "0",
        "Antialias": "1",
        "StartChannel": str(spec.start_channel),
        "versionNumber": "7",
    }
    if spec.custom_color:
        attrs["CustomColor"] = spec.custom_color
    if spec.tag_color:
        attrs["TagColour"] = spec.tag_color
    if SAFE_LAYOUT_GROUP:
        attrs["LayoutGroup"] = SAFE_LAYOUT_GROUP
    attrs.update(spec.attrs)
    model = ET.SubElement(models_el, "model", attrs)
    ET.SubElement(model, "ControllerConnection", {"Protocol": "LOR Optimised"})
    if spec.aliases:
        aliases_el = ET.SubElement(model, "Aliases")
        for alias in spec.aliases:
            ET.SubElement(aliases_el, "alias", {"name": alias})
    for sub in spec.submodels:
        sub_el = ET.SubElement(model, "subModel", {"name": sub.name, "layout": sub.layout, "type": sub.type})
        for idx, line in enumerate(sub.lines):
            sub_el.attrib[f"line{idx}"] = line
        if sub.aliases:
            aliases_el = ET.SubElement(sub_el, "aliases")
            for alias in sub.aliases:
                ET.SubElement(aliases_el, "alias", {"name": alias})


def _existing_coords(models_el: ET.Element) -> dict[str, tuple[float, float]]:
    coords: dict[str, tuple[float, float]] = {}
    for model in models_el.findall("model"):
        name = (model.attrib.get("name") or "").strip()
        if not name:
            continue
        try:
            coords[name] = (
                float(model.attrib.get("WorldPosX", "0") or "0"),
                float(model.attrib.get("WorldPosY", "0") or "0"),
            )
        except ValueError:
            coords[name] = (0.0, 0.0)
    return coords


def _group_bbox(group_names: list[str], coords: dict[str, tuple[float, float]]) -> dict[str, str]:
    points = [coords[name] for name in group_names if name in coords]
    if not points:
        return {"centrex": "0", "centrey": "0", "centreDefined": "0", "centreMinx": "0", "centreMiny": "0", "centreMaxx": "0", "centreMaxy": "0"}
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return {
        "centrex": _fmt(sum(xs) / len(xs)),
        "centrey": _fmt(sum(ys) / len(ys)),
        "centreDefined": "0",
        "centreMinx": f"{min(xs):.0f}",
        "centreMiny": f"{min(ys):.0f}",
        "centreMaxx": f"{max(xs):.0f}",
        "centreMaxy": f"{max(ys):.0f}",
    }


def _add_group(groups_el: ET.Element, name: str, members: list[str], coords: dict[str, tuple[float, float]]) -> None:
    attrs = {
        "name": name,
        "GridSize": "400",
        "XCentreOffset": "0",
        "YCentreOffset": "0",
        "DefaultCamera": "2D",
        "layout": "minimalGrid",
        "TagColour": "black",
        "models": _normalize_csv(members),
    }
    if SAFE_LAYOUT_GROUP:
        attrs["LayoutGroup"] = SAFE_LAYOUT_GROUP
    attrs.update(_group_bbox(members, coords))
    ET.SubElement(groups_el, "modelGroup", attrs)


def make_model(name: str, display_as: str, string_type: str, channel: int, total_pixels: int, x: float, y: float, attrs: dict[str, str], *, color: str | None = None, submodels: list[SubModelSpec] | None = None) -> ModelSpec:
    return ModelSpec(
        name=name,
        display_as=display_as,
        string_type=string_type,
        start_channel=channel,
        total_pixels=total_pixels,
        x=x,
        y=y,
        custom_color=(COLOR_HEX.get(color) if color else None),
        tag_color=color,
        attrs=attrs,
        submodels=submodels or [],
    )


def _single_line(name: str, channel: int, x: float, y: float, dx: float, dy: float, pixels: int) -> ModelSpec:
    return make_model(name, "Single Line", "RGB Nodes", channel, pixels, x, y, {"NumStrings": "1", "NodesPerString": str(pixels), "LightsPerNode": "1", **_two_point_attrs(dx, dy)}, submodels=_segments(pixels, ["Left", "Center", "Right"]))


def _poly_line(name: str, channel: int, x: float, y: float, points: list[tuple[float, float]], pixels: int, *, color: str | None = None) -> ModelSpec:
    return make_model(name, "Poly Line", "RGB Nodes" if color is None else f"Single Color {color.title()}", channel, pixels, x, y, {"PolyStrings": "1", "NodesPerString": str(pixels), "LightsPerNode": "1", "ModelHeight": "60", "AlternateNodes": "false", "DropPattern": "", "SegsExpanded": "TRUE", **_poly_attrs(points)}, color=color, submodels=_segments(pixels, ["Lead", "Middle", "Tail"]))


def _arches(name: str, channel: int, x: float, y: float, nodes: int, scale_x: float, scale_y: float) -> ModelSpec:
    return make_model(name, "Arches", "RGB Nodes", channel, nodes, x, y, {"NumArches": "1", "NodesPerArch": str(nodes), "LightsPerNode": "1", "ZigZag": "false", "Hollow": "0", "Arc": "180", "LayerSizes": "", **_three_point_attrs(scale_x, 0.0, scale_y)}, submodels=_segments(nodes, ["Left", "Center", "Right"]))


def _cane(name: str, channel: int, x: float, y: float, nodes: int, reverse: bool) -> ModelSpec:
    return make_model(name, "Candy Canes", "RGB Nodes", channel, nodes, x, y, {"NumCanes": "1", "NodesPerCane": str(nodes), "LightsPerNode": "1", "CandyCaneHeight": "1.0", "CandyCaneReverse": "true" if reverse else "false", "CandyCaneSticks": "false", "AlternateNodes": "false", **_three_point_attrs(0.0, 44.0, 64.0)}, submodels=[SubModelSpec("Stem", [f"1-{max(1, int(nodes * 0.62))}"]), SubModelSpec("Hook", [f"{max(1, int(nodes * 0.62)) + 1}-{nodes}"])])


def _matrix(name: str, channel: int, x: float, y: float, strings: int, nodes: int, scale_x: float, scale_y: float) -> ModelSpec:
    total = strings * nodes
    return make_model(
        name,
        "Vert Matrix",
        "RGB Nodes",
        channel,
        total,
        x,
        y,
        {
            "parm1": str(strings),
            "parm2": str(nodes),
            "parm3": "1",
            "StartSide": "T",
            "Dir": "L",
            "NumStrings": str(strings),
            "NodesPerString": str(nodes),
            "StrandsPerString": "1",
            "Vertical": "true",
            "LowDefinition": "1",
            "AlternateNodes": "false",
            "NoZig": "false",
            **_boxed_attrs(scale_x, scale_y),
        },
        submodels=_segments(total, ["Top", "Center", "Bottom", "Left", "Right"]),
    )


def _tree(name: str, channel: int, x: float, y: float, strings: int, nodes: int, scale_x: float, scale_y: float, degrees: int, spiral: float, rotation: float, tree_type: int) -> ModelSpec:
    total = strings * nodes
    return make_model(name, "Tree", "RGB Nodes", channel, total, x, y, {"NumStrings": str(strings), "NodesPerString": str(nodes), "StrandsPerString": "1", "AlternateNodes": "false", "NoZig": "false", "StrandDir": "Vertical", "exportFirstStrand": "1", "TreeBottomTopRatio": "3.0", "TreePerspective": "0.18", "TreeSpiralRotations": f"{spiral:.2f}", "TreeRotation": f"{rotation:.2f}", "TreeType": str(tree_type), "TreeDegrees": str(degrees), **_boxed_attrs(scale_x, scale_y)}, submodels=_segments(total, ["Top", "Upper", "Middle", "Lower", "Bottom"]))


def _spinner(name: str, channel: int, x: float, y: float, strings: int, nodes_per_arm: int, arms_per_string: int, scale: float, start_angle: int) -> ModelSpec:
    total = strings * arms_per_string * nodes_per_arm
    return make_model(name, "Spinner", "RGB Nodes", channel, total, x, y, {"NumStrings": str(strings), "NodesPerArm": str(nodes_per_arm), "ArmsPerString": str(arms_per_string), "Alternate": "false", "ZigZag": "false", "Hollow": "16", "Arc": "360", "StartAngle": str(start_angle), **_boxed_attrs(scale, scale)}, submodels=_segments(total, ["Center", "Inner", "Outer", "Arm A", "Arm B"]))


def _sphere(name: str, channel: int, x: float, y: float, strings: int, nodes: int, scale: float) -> ModelSpec:
    total = strings * nodes
    return make_model(name, "Sphere", "RGB Nodes", channel, total, x, y, {"NumStrings": str(strings), "NodesPerString": str(nodes), "StrandsPerString": "1", "Degrees": "360", "StartLat": "-75", "EndLat": "75", "LowDefinition": "1", "AlternateNodes": "false", "NoZig": "false", **_boxed_attrs(scale, scale, scale_z=scale)}, submodels=_segments(total, ["North", "East", "South", "West"]))


def _star(name: str, channel: int, x: float, y: float, nodes: int, scale: float) -> ModelSpec:
    return make_model(name, "Star", "RGB Nodes", channel, nodes, x, y, {"NumStrings": "1", "NodesPerString": str(nodes), "StarPoints": "5", "LayerSizes": "", "StarStartLocation": "Bottom Ctr-CW", "starRatio": "2.35", "starCenterPercent": "32.0", **_boxed_attrs(scale, scale, rotate_z=6.0)}, submodels=_segments(nodes, ["Top", "Right", "Bottom", "Left"]))


def _wreath(name: str, channel: int, x: float, y: float, strings: int, nodes: int, scale: float) -> ModelSpec:
    total = strings * nodes
    return make_model(name, "Wreath", "RGB Nodes", channel, total, x, y, {"NumStrings": str(strings), "NodesPerString": str(nodes), **_boxed_attrs(scale, scale)}, submodels=_segments(total, ["North", "East", "South", "West"]))


def _circle(name: str, channel: int, x: float, y: float, nodes: int, scale_x: float, scale_y: float) -> ModelSpec:
    return make_model(
        name,
        "Circle",
        "RGB Nodes",
        channel,
        nodes,
        x,
        y,
        {
            "parm1": "1",
            "parm2": str(nodes),
            "parm3": "50",
            "StartSide": "B",
            "Dir": "L",
            "InsideOut": "0",
            "NumStrings": "1",
            "NodesPerString": str(nodes),
            **_boxed_attrs(scale_x, scale_y),
        },
        submodels=_segments(nodes, ["North", "East", "South", "West"]),
    )


def _window_frame(name: str, channel: int, x: float, y: float, top: int, side: int, bottom: int, scale_x: float, scale_y: float) -> ModelSpec:
    total = top + side * 2 + bottom
    return make_model(name, "Window Frame", "RGB Nodes", channel, total, x, y, {"TopNodes": str(top), "SideNodes": str(side), "BottomNodes": str(bottom), "Rotation": "Clockwise", **_boxed_attrs(scale_x, scale_y)}, submodels=_segments(total, ["Top", "Left", "Right", "Bottom"]))


def _icicles(name: str, channel: int, x: float, y: float, strings: int, nodes: int, width: float, height: float, drop_pattern: str) -> ModelSpec:
    total = strings * nodes
    return make_model(name, "Icicles", "RGB Nodes", channel, total, x, y, {"NumStrings": str(strings), "NodesPerString": str(nodes), "AlternateNodes": "false", "DropPattern": drop_pattern, **_three_point_attrs(width, 0.0, height)}, submodels=_segments(total, ["Left", "Center", "Right"]))


def _cube(name: str, channel: int, x: float, y: float, width: int, height: int, depth: int, scale: float) -> ModelSpec:
    total = width * height * depth
    return make_model(name, "Cube", "RGB Nodes", channel, total, x, y, {"CubeWidth": str(width), "CubeHeight": str(height), "CubeDepth": str(depth), "Style": "Vertical Front/Back", "Start": "Front Bottom Left", "Strings": "1", "StrandPerLine": "Zig Zag", "StrandPerLayer": "FALSE", **_boxed_attrs(scale, scale, scale_z=scale)}, submodels=_segments(total, ["Front", "Middle", "Rear"]))


def _channel_block(name: str, channel: int, x: float, y: float, num_channels: int, dx: float, dy: float) -> ModelSpec:
    return make_model(name, "Channel Block", "Single Color White", channel, num_channels, x, y, {"NumChannels": str(num_channels), "ChannelColor1": "#FFFFFF", "ChannelColor2": "#FF0000", "ChannelColor3": "#00FF00", "ChannelColor4": "#0000FF", **_two_point_attrs(dx, dy)}, color="white", submodels=_segments(num_channels, ["First Half", "Second Half"]))


def _custom(name: str, channel: int, x: float, y: float, width: int, height: int, scale: float) -> ModelSpec:
    rows: list[str] = []
    node = 1
    for row in range(height):
        cols: list[str] = []
        for col in range(width):
            if (row, col) in {(1, 1), (1, 2)}:
                cols.append("")
            else:
                cols.append(str(node))
                node += 1
        rows.append(",".join(cols))
    payload = ";".join(rows)
    total = node - 1
    return make_model(name, "Custom", "RGB Nodes", channel, total, x, y, {"CustomWidth": str(width), "CustomHeight": str(height), "Depth": "1", "CustomModel": payload, **_boxed_attrs(scale, scale)}, submodels=_segments(total, ["Upper", "Core", "Lower"]))


def _multipoint(name: str, channel: int, x: float, y: float, points: list[tuple[float, float]]) -> ModelSpec:
    return make_model(name, "MultiPoint", "RGB Nodes", channel, len(points), x, y, {"MultiStrings": "1", "ModelHeight": "48", **_multi_attrs(points)}, submodels=_segments(len(points), ["Core", "Burst"]))


def _image_model(name: str, channel: int, x: float, y: float, image_rel: str) -> ModelSpec:
    return make_model(name, "Image", "RGB Nodes", channel, 1, x, y, {"Image": image_rel, "WhiteAsAlpha": "False", "OffBrightness": "80", **_boxed_attrs(48.0, 48.0)})


def _prepare_layout_shell(root: ET.Element) -> tuple[ET.Element, ET.Element]:
    models_el = root.find("models")
    groups_el = root.find("modelGroups")
    views_el = root.find("views")
    view_objects_el = root.find("view_objects")
    layout_groups_el = root.find("layoutGroups")
    settings_el = root.find("settings")
    if models_el is None or groups_el is None or layout_groups_el is None or settings_el is None:
        raise RuntimeError("Source xlights_rgbeffects.xml is missing expected sections.")

    existing_preview_groups = {child.attrib.get("name", "") for child in layout_groups_el.findall("layoutGroup")}
    if SAFE_LAYOUT_GROUP and SAFE_LAYOUT_GROUP not in existing_preview_groups:
        ET.SubElement(layout_groups_el, "layoutGroup", {"name": SAFE_LAYOUT_GROUP, "backgroundImage": ""})

    for child in list(settings_el):
        key = child.tag
        value = child.attrib.get("value", "")
        if key == "previewWidth":
            try:
                child.attrib["value"] = str(max(int(float(value or "0")), 1800))
            except ValueError:
                child.attrib["value"] = "1800"
        elif key == "previewHeight":
            try:
                child.attrib["value"] = str(max(int(float(value or "0")), 980))
            except ValueError:
                child.attrib["value"] = "980"
        elif key == "backgroundAlpha" and not value:
            child.attrib["value"] = "0"
    return models_el, groups_el


def _next_start_channel(models_el: ET.Element) -> int:
    max_start = 0
    for model in models_el.findall("model"):
        try:
            max_start = max(max_start, int(model.attrib.get("StartChannel", "0") or "0"))
        except ValueError:
            continue
    return max_start + 1000


def _write_preview_network(target: Path, max_channels: int) -> None:
    computer = os.environ.get("COMPUTERNAME", "WINDOWS")
    src_networks = ROOT / "xlights_networks.xml"
    if src_networks.exists():
        tree = ET.parse(src_networks)
        root = tree.getroot()
        if root.tag != "Networks":
            raise RuntimeError("Source xlights_networks.xml did not contain a Networks root element.")
        if not root.attrib.get("computer"):
            root.attrib["computer"] = computer
        preview_network = None
        for child in root.findall("network"):
            if (child.attrib.get("NetworkType") or "").upper() == "NULL":
                preview_network = child
                break
        attrs = {
            "NetworkType": "NULL",
            "MaxChannels": str(max(max_channels, PREVIEW_NETWORK_MAX)),
            "Description": PREVIEW_NETWORK_DESC,
        }
        if preview_network is None:
            ET.SubElement(root, "network", attrs)
        else:
            preview_network.attrib.update(attrs)
        _indent_xml(root)
        tree.write(target, encoding="utf-8", xml_declaration=True)
        return
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<Networks computer="{computer}">\n'
        f'  <network NetworkType="NULL" MaxChannels="{max(max_channels, PREVIEW_NETWORK_MAX)}" Description="{PREVIEW_NETWORK_DESC}"/>\n'
        "</Networks>\n"
    )
    target.write_text(xml, encoding="utf-8")


def build_allmodels_pack() -> dict[str, Path]:
    if not SRC_LAYOUT.exists() or not SRC_TEMPLATE.exists() or not SRC_AUDIO.exists():
        raise RuntimeError("Required source files were not found in the workspace.")
    PACK_DIR.mkdir(parents=True, exist_ok=True)
    OUT_OUTPUTS.mkdir(parents=True, exist_ok=True)
    OUT_IMAGES.mkdir(parents=True, exist_ok=True)

    if OUT_LAYOUT.exists():
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(OUT_LAYOUT, BACKUP_DIR / "xlights_rgbeffects.full_synthetic.xml")
    if OUT_LAYOUT_BK.exists():
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(OUT_LAYOUT_BK, BACKUP_DIR / "xlights_rgbeffects.full_synthetic.xbkp")
    if OUT_TEMPLATE.exists():
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(OUT_TEMPLATE, BACKUP_DIR / "template2.full_synthetic.xsq")

    image_source = next((path for path in SRC_IMAGE_CANDIDATES if path.exists()), None)
    image_rel = ""
    if image_source is not None:
        image_target = OUT_IMAGES / "allmodels_reference.png"
        shutil.copy2(image_source, image_target)
        image_rel = str(image_target.relative_to(PACK_DIR)).replace("\\", "/")

    tree = ET.parse(SRC_LAYOUT)
    root = tree.getroot()
    models_el, groups_el = _prepare_layout_shell(root)
    original_model_names = [model.attrib.get("name", "") for model in models_el.findall("model") if model.attrib.get("name")]

    channel = _next_start_channel(models_el)
    coords: dict[str, tuple[float, float]] = _existing_coords(models_el)
    type_groups: dict[str, list[str]] = {}
    synthetic_names: list[str] = []

    def add(spec: ModelSpec, group: str) -> None:
        nonlocal channel
        spec.name = _showcase_name(spec.name)
        _add_model(models_el, spec)
        coords[spec.name] = (spec.x, spec.y)
        type_groups.setdefault(group, []).append(spec.name)
        synthetic_names.append(spec.name)
        channel += _channel_span(spec.string_type, spec.total_pixels)

    add(_star("Star 1", channel, 270, 790, 28, 2.1), "stars")
    add(_star("Star 2", channel, 520, 820, 24, 1.9), "stars")
    add(_star("Star 3", channel, 1280, 820, 24, 1.9), "stars")
    add(_star("Star 4", channel, 1530, 790, 28, 2.1), "stars")
    if INCLUDE_CIRCLE_FAMILY:
        add(_wreath("Wreath 1", channel, 690, 760, 2, 24, 1.7), "wreaths")
        add(_wreath("Wreath 2", channel, 1110, 760, 2, 24, 1.7), "wreaths")
        add(_circle("Circle Orb 1", channel, 900, 835, 32, 1.8, 1.4), "circles")
        add(_sphere("Sphere 1", channel, 900, 710, 10, 14, 2.0), "spheres")
    if INCLUDE_MATRIX_FAMILY:
        add(_matrix("Matrix Panel 1", channel, 360, 520, 16, 24, 20.0, 26.0), "matrices")
        add(_matrix("Matrix Panel 2", channel, 1440, 520, 16, 24, 20.0, 26.0), "matrices")
        talking_head = _matrix("Talking Head Matrix 1", channel, 900, 575, 14, 18, 18.0, 22.0)
        talking_head.submodels = [
            SubModelSpec("Forehead", ["1-56"]),
            SubModelSpec("Eyes", ["57-112"]),
            SubModelSpec("Jaw", ["113-168"]),
            SubModelSpec("Mouth", ["169-252"], aliases=["lyrics"]),
        ]
        add(talking_head, "talking_heads")
    add(_tree("Mega Tree 1", channel, 760, 530, 16, 50, 18.0, 30.0, 270, 1.5, 0.0, 0), "trees")
    add(_tree("Mega Tree 2", channel, 1040, 530, 12, 42, 15.0, 26.0, 180, 0.0, 14.0, 1), "trees")
    add(_spinner("Spinner 1", channel, 180, 700, 2, 16, 4, 12.0, 0), "spinners")
    add(_spinner("Spinner 2", channel, 1620, 700, 2, 16, 4, 12.0, 22), "spinners")
    add(_window_frame("Window Frame 1", channel, 610, 600, 18, 14, 18, 11.0, 8.0), "window_frames")
    add(_window_frame("Window Frame 2", channel, 1190, 600, 18, 14, 18, 11.0, 8.0), "window_frames")
    add(_icicles("Icicles Roofline 1", channel, 900, 705, 24, 6, 760.0, 80.0, "5,7,4,6,8,5"), "icicles")
    add(_poly_line("Roof Polyline 1", channel, 900, 745, [(-280, -20), (-190, 55), (-30, 90), (0, 125), (30, 90), (190, 55), (280, -20)], 120), "polylines")
    add(_poly_line("Accent Polyline 2", channel, 900, 695, [(-340, 0), (-250, 48), (-150, -8), (-60, 52), (60, 12), (170, 68), (340, 0)], 90, color="white"), "polylines")
    for idx in range(1, 8):
        x = 360 + (idx - 1) * 85
        add(_single_line(f"Line Tree {idx}", channel, x, 350, 0.0, 150.0 + (idx % 3) * 15.0, 42), "line_trees")
    for idx in range(1, 7):
        x = 435 + (idx - 1) * 120
        add(_arches(f"Front Arch {idx}", channel, x, 255, 36, 82.0, 48.0 + (idx % 2) * 6.0), "arches")
    cane_xs = [180 + (i * 95) for i in range(16)]
    for idx, x in enumerate(cane_xs, start=1):
        add(_cane(f"North Candy Cane {idx}", channel, x, 190, 18, bool(idx % 2)), "north_canes")
        add(_cane(f"South Candy Cane {idx}", channel, x, 115, 18, not bool(idx % 2)), "south_canes")
    add(_single_line("Runway Line 1", channel, 230, 86, 230.0, 0.0, 48), "single_lines")
    add(_single_line("Runway Line 2", channel, 1570, 86, -230.0, 0.0, 48), "single_lines")
    if INCLUDE_UNSAFE_EDGE_CASES:
        add(_channel_block("Channel Block 1", channel, 70, 475, 16, 0.0, 120.0), "channel_blocks")
        add(_multipoint("MultiPoint Burst 1", channel, 1650, 455, [(0, 0), (18, 10), (24, 28), (8, 40), (-10, 38), (-24, 22), (-16, 5), (12, -10)]), "multipoints")
        add(_custom("Custom Glyph 1", channel, 154, 585, 4, 3, 10.0), "customs")
        add(_cube("Cube 1", channel, 1650, 600, 4, 4, 3, 8.0), "cubes")
        if image_rel:
            add(_image_model("Image Panel 1", channel, 155, 735, image_rel), "images")

    north_canes = type_groups.get("north_canes", [])
    south_canes = type_groups.get("south_canes", [])
    canes_combo: list[str] = []
    for idx in range(min(len(north_canes), len(south_canes))):
        canes_combo.append(north_canes[idx])
        canes_combo.append(south_canes[idx])
    full_layout_names = [name for name in original_model_names + synthetic_names if name]
    groups = [
        ("ALLMODELS_ORIGINAL_LAYOUT", original_model_names),
        ("ALLMODELS_SHOWCASE_MODELS", synthetic_names),
        ("ALLMODELS_WHOLEHOUSE", full_layout_names),
        ("ALLMODELS_MATRICES", type_groups.get("matrices", []) + type_groups.get("talking_heads", [])),
        ("ALLMODELS_TREES", type_groups.get("trees", []) + type_groups.get("line_trees", [])),
        ("ALLMODELS_MOTION", type_groups.get("spinners", []) + type_groups.get("spheres", []) + type_groups.get("arches", [])),
        ("ALLMODELS_STRUCTURES", type_groups.get("window_frames", []) + type_groups.get("icicles", []) + type_groups.get("polylines", [])),
        ("ALLMODELS_GEOMETRY", type_groups.get("stars", []) + type_groups.get("wreaths", []) + type_groups.get("circles", [])),
        ("ALLMODELS_EDGE_CASES", type_groups.get("channel_blocks", []) + type_groups.get("multipoints", []) + type_groups.get("customs", []) + type_groups.get("cubes", []) + type_groups.get("images", [])),
        ("ALLMODELS_TALKING_HEADS", type_groups.get("talking_heads", [])),
        ("ALLMODELS_NORTH_CANES", north_canes),
        ("ALLMODELS_SOUTH_CANES", south_canes),
        ("ALLMODELS_CANES_COMBO", canes_combo),
        ("ALLMODELS_MATRIX_SHOWCASE", type_groups.get("matrices", [])),
        ("ALLMODELS_MEGA_TREES", type_groups.get("trees", [])),
        ("ALLMODELS_LINE_TREES", type_groups.get("line_trees", [])),
        ("ALLMODELS_FRONT_ARCHES", type_groups.get("arches", [])),
        ("ALLMODELS_SPINNER_PAIR", type_groups.get("spinners", [])),
        ("ALLMODELS_WINDOW_FRAMES", type_groups.get("window_frames", [])),
    ]
    for name, members in groups:
        if members:
            _add_group(groups_el, name, members, coords)

    _indent_xml(root)
    tree.write(OUT_LAYOUT, encoding="utf-8", xml_declaration=True)
    shutil.copy2(OUT_LAYOUT, OUT_LAYOUT_BK)
    shutil.copy2(SRC_AUDIO, OUT_AUDIO)
    for support_path in SRC_SUPPORT_FILES:
        if support_path.name == "xlights_networks.xml":
            continue
        if support_path.exists():
            shutil.copy2(support_path, PACK_DIR / support_path.name)
    max_start = 0
    for model in models_el.findall("model"):
        try:
            max_start = max(max_start, int(model.attrib.get("StartChannel", "0") or "0"))
        except ValueError:
            continue
    _write_preview_network(PACK_DIR / "xlights_networks.xml", max_start + 5000)
    xsq = base.load_xsq(SRC_TEMPLATE)
    sync_report = base.sync_xsq_to_layout(xsq, OUT_LAYOUT)
    for element in xsq.elements.values():
        base.clear_effects(element, "all", base.AUTO_LAYER_NAME)
    base.replace_audio_references(xsq.root, OUT_AUDIO)
    base.indent_xml(xsq.root)
    xsq.tree.write(OUT_TEMPLATE, encoding="utf-8", xml_declaration=True)

    type_counts = {key: len(value) for key, value in sorted(type_groups.items())}
    OUT_README.write_text(
        "\n".join(
            [
                "Dream Sequence Weaver - allmodels showcase pack",
                "",
                "This pack starts from your real working layout and overlays a full showcase expansion of xLights model families.",
                "The active allmodels show folder preserves your original controller definitions and appends a NULL preview overflow network for showcase-only props above channel 256.",
                "The original show folder in /cod stays untouched.",
                f"Layout:   {OUT_LAYOUT.name}",
                f"Template: {OUT_TEMPLATE.name}",
                f"Audio:    {OUT_AUDIO.name}",
                "",
                "Model families included:",
                "- Original personal layout models and groups",
                "- Single Line / Poly Line / Arches / Candy Canes / Tree / Spinner / Star / Icicles / Window Frame / Wreath / Circle / Sphere / Matrix",
                "- Talking-head matrix with mouth-focused submodel, plus Channel Block / Custom / Cube / Image edge models",
                "",
                "Controller / show-folder notes:",
                "- allmodels/xlights_networks.xml keeps the original 256-channel show controller map and adds a NULL preview overflow network.",
                "- Showcase props use absolute channels starting above the original show so they do not collide with the physical LOR layout.",
                "- DMX fixture imports are not auto-generated here; xLights ships those through the DMX fixture library and imported xmodel workflow.",
                "- The previous generated pack is backed up under _full_synthetic_backup.",
                "",
                "Recommended xLights note:",
                "- Your screenshot showed xLights 2026.01 (January 7, 2026). The official xLights GitHub currently lists release 2026.04 from April 2, 2026.",
            ]
        ),
        encoding="utf-8",
    )
    OUT_AUDIT.write_text(
        "\n".join(
            [
                f"original_models={len(original_model_names)}",
                f"synthetic_models={len(synthetic_names)}",
                f"models_total={sum(type_counts.values())}",
                f"groups_total={len([g for g in groups if g[1]])}",
                f"sync_layout_names={sync_report.get('layout_names', 0)}",
                f"sync_display_updated={sync_report.get('display_updated', 0)}",
                f"sync_effect_rows_updated={sync_report.get('effect_rows_updated', 0)}",
                "type_counts=" + ", ".join(f"{name}:{count}" for name, count in type_counts.items()),
            ]
        ),
        encoding="utf-8",
    )
    return {"pack_dir": PACK_DIR, "layout": OUT_LAYOUT, "template": OUT_TEMPLATE, "audio": OUT_AUDIO, "output_root": OUT_OUTPUTS}


def main() -> int:
    result = build_allmodels_pack()
    print(f"Created allmodels pack: {result['pack_dir']}")
    print(f"Layout:   {result['layout']}")
    print(f"Template: {result['template']}")
    print(f"Audio:    {result['audio']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
