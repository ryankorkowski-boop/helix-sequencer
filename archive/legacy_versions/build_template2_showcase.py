#!/usr/bin/env python3
from __future__ import annotations

import math
import shutil
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

import v1 as base


ROOT = Path(__file__).resolve().parent
SRC_LAYOUT = ROOT / "xlights_rgbeffects.xml"
SRC_TEMPLATE = ROOT / "template.xsq"
SRC_AUDIO = ROOT / "13.wav"

PACK_DIR = ROOT / "showcase_assets" / "template2_dynamic_showcase"
OUT_LAYOUT = PACK_DIR / "xlights_rgbeffects.xml"
OUT_LAYOUT_BK = PACK_DIR / "xlights_rgbeffects.xbkp"
OUT_TEMPLATE = PACK_DIR / "template2.xsq"
OUT_AUDIO = PACK_DIR / "13.wav"
OUT_README = PACK_DIR / "README.txt"
OUT_OUTPUTS = PACK_DIR / "outputs"


@dataclass
class ModelSpec:
    name: str
    display_as: str
    string_type: str
    start_channel: int
    x: float
    y: float
    x2: float | None = None
    y2: float | None = None
    scale_x: float | None = None
    scale_y: float | None = None
    rotate_z: float = 0.0
    parm1: int = 1
    parm2: int = 1
    parm3: int = 1
    num_points: int | None = None
    point_data: str | None = None
    inside_out: int | None = None
    star_start: str | None = None
    star_ratio: float | None = None
    start_side: str = "B"
    direction: str = "L"
    custom_color: str | None = None
    tag_color: str | None = None
    aliases: list[str] | None = None


COLOR_HEX = {
    "red": "#FF0000",
    "green": "#00FF00",
    "white": "#FFFFFF",
}


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
        if not name or name in seen:
            continue
        seen.add(name)
        out.append(name)
    return ",".join(out)


def _fmt(num: float) -> str:
    return f"{num:.4f}"


def _line_attrs(spec: ModelSpec) -> dict[str, str]:
    attrs = {
        "DisplayAs": spec.display_as,
        "StartSide": spec.start_side,
        "Dir": spec.direction,
        "Antialias": "1",
        "PixelSize": "2",
        "Transparency": "0",
        "parm1": str(spec.parm1),
        "parm2": str(spec.parm2),
        "parm3": str(spec.parm3),
        "LayoutGroup": "Default",
        "name": spec.name,
        "StringType": spec.string_type,
        "WorldPosX": _fmt(spec.x),
        "WorldPosY": _fmt(spec.y),
        "WorldPosZ": "0.0000",
        "versionNumber": "7",
        "StartChannel": str(spec.start_channel),
    }
    if spec.custom_color:
        attrs["CustomColor"] = spec.custom_color
    if spec.tag_color:
        attrs["TagColour"] = spec.tag_color
    if spec.display_as == "Single Line":
        attrs["X2"] = f"{spec.x2 or 0.0:.6f}"
        attrs["Y2"] = f"{spec.y2 or 0.0:.6f}"
        attrs["Z2"] = "0.000000"
    elif spec.display_as == "Poly Line":
        attrs["ScaleX"] = "1.0000"
        attrs["ScaleY"] = "1.0000"
        attrs["ScaleZ"] = "1.0000"
        attrs["NumPoints"] = str(spec.num_points or 0)
        attrs["PointData"] = spec.point_data or ""
        attrs["cPointData"] = ""
    elif spec.display_as in {"Star", "Circle"}:
        attrs["ScaleX"] = _fmt(spec.scale_x or 1.0)
        attrs["ScaleY"] = _fmt(spec.scale_y or 1.0)
        attrs["ScaleZ"] = "0.0714"
        attrs["RotateX"] = "0.00000000"
        attrs["RotateY"] = "0.00000000"
        attrs["RotateZ"] = f"{spec.rotate_z:.8f}"
        if spec.display_as == "Star":
            attrs["StarStartLocation"] = spec.star_start or "Bottom Ctr-CW"
            if spec.star_ratio is not None:
                attrs["starRatio"] = f"{spec.star_ratio:.6f}"
        if spec.display_as == "Circle":
            attrs["InsideOut"] = str(spec.inside_out or 0)
    return attrs


def _add_model(models_el: ET.Element, spec: ModelSpec) -> None:
    model = ET.SubElement(models_el, "model", _line_attrs(spec))
    ET.SubElement(model, "ControllerConnection", {"Protocol": "LOR Optimised"})
    if spec.aliases:
        aliases_el = ET.SubElement(model, "Aliases")
        for alias in spec.aliases:
            ET.SubElement(aliases_el, "alias", {"name": alias})
    elif spec.display_as == "Single Line":
        ET.SubElement(model, "Aliases")


def _group_bbox(group_names: list[str], coords: dict[str, tuple[float, float]]) -> dict[str, str]:
    points = [coords[name] for name in group_names if name in coords]
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
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return {
        "centrex": f"{sum(xs) / len(xs):.6f}",
        "centrey": f"{sum(ys) / len(ys):.6f}",
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
        "LayoutGroup": "All Previews",
        "models": _normalize_csv(members),
    }
    attrs.update(_group_bbox(members, coords))
    ET.SubElement(groups_el, "modelGroup", attrs)


def _single_color(color: str) -> tuple[str, str, str]:
    return (f"Single Color {color.title()}", COLOR_HEX[color], color if color != "green" else "lime green")


def _rgb_line(name: str, start: int, x: float, y: float, dx: float, dy: float, pixels: int, *, aliases: list[str] | None = None, reverse: bool = False) -> ModelSpec:
    return ModelSpec(
        name=name,
        display_as="Single Line",
        string_type="RGB Nodes",
        start_channel=start,
        x=x,
        y=y,
        x2=dx,
        y2=dy,
        parm1=1,
        parm2=pixels,
        parm3=max(1, pixels),
        aliases=aliases,
        direction="R" if reverse else "L",
    )


def _single_line(name: str, start: int, x: float, y: float, dx: float, dy: float, pixels: int, color: str) -> ModelSpec:
    stype, hex_color, tag = _single_color(color)
    return ModelSpec(
        name=name,
        display_as="Single Line",
        string_type=stype,
        start_channel=start,
        x=x,
        y=y,
        x2=dx,
        y2=dy,
        parm1=1,
        parm2=pixels,
        parm3=max(1, pixels),
        custom_color=hex_color,
        tag_color=tag,
    )


def _polyline(name: str, start: int, x: float, y: float, points: list[tuple[float, float]], pixels: int, color: str | None = None, rgb: bool = False) -> ModelSpec:
    if rgb:
        string_type = "RGB Nodes"
        custom_color = None
        tag_color = None
    else:
        picked = color or "white"
        string_type, custom_color, tag_color = _single_color(picked)
    data = ",".join(f"{px:.6f},{py:.6f},0.000000" for px, py in points)
    return ModelSpec(
        name=name,
        display_as="Poly Line",
        string_type=string_type,
        start_channel=start,
        x=x,
        y=y,
        parm1=1,
        parm2=pixels,
        parm3=max(1, pixels),
        num_points=len(points),
        point_data=data,
        custom_color=custom_color,
        tag_color=tag_color,
    )


def _star(name: str, start: int, x: float, y: float, sx: float, sy: float, points: int, *, color: str | None = None, rgb: bool = False, rotate_z: float = 0.0, star_ratio: float | None = None) -> ModelSpec:
    if rgb:
        string_type = "RGB Nodes"
        custom_color = None
        tag_color = None
    else:
        picked = color or "white"
        string_type, custom_color, tag_color = _single_color(picked)
    return ModelSpec(
        name=name,
        display_as="Star",
        string_type=string_type,
        start_channel=start,
        x=x,
        y=y,
        parm1=1,
        parm2=points,
        parm3=5,
        scale_x=sx,
        scale_y=sy,
        rotate_z=rotate_z,
        custom_color=custom_color,
        tag_color=tag_color,
        star_ratio=star_ratio,
    )


def _circle(name: str, start: int, x: float, y: float, sx: float, sy: float, points: int, *, color: str | None = None, rgb: bool = False, inside_out: int = 0, rotate_z: float = 0.0) -> ModelSpec:
    if rgb:
        string_type = "RGB Nodes"
        custom_color = None
        tag_color = None
    else:
        picked = color or "white"
        string_type, custom_color, tag_color = _single_color(picked)
    return ModelSpec(
        name=name,
        display_as="Circle",
        string_type=string_type,
        start_channel=start,
        x=x,
        y=y,
        parm1=1,
        parm2=points,
        parm3=max(10, points * 2),
        scale_x=sx,
        scale_y=sy,
        rotate_z=rotate_z,
        custom_color=custom_color,
        tag_color=tag_color,
        inside_out=inside_out,
    )


def _next_channel(channel: int, string_type: str, pixels: int) -> int:
    if "rgb" in string_type.lower():
        return channel + max(1, pixels * 3)
    return channel + 1


def _spoke_points(radius_x: float, radius_y: float, spoke_count: int) -> list[tuple[float, float]]:
    out: list[tuple[float, float]] = []
    for idx in range(spoke_count):
        angle = (-math.pi / 2.0) + ((math.pi * 2.0 * idx) / spoke_count)
        out.append((math.cos(angle) * radius_x, math.sin(angle) * radius_y))
    return out


def build_showcase_pack() -> dict[str, Path]:
    PACK_DIR.mkdir(parents=True, exist_ok=True)
    OUT_OUTPUTS.mkdir(parents=True, exist_ok=True)

    src_tree = ET.parse(SRC_LAYOUT)
    root = src_tree.getroot()

    models_el = root.find("models")
    groups_el = root.find("modelGroups")
    views_el = root.find("views")
    view_objects_el = root.find("view_objects")
    layout_groups_el = root.find("layoutGroups")
    settings_el = root.find("settings")

    if models_el is None or groups_el is None or layout_groups_el is None or settings_el is None:
        raise SystemExit("Source xlights_rgbeffects.xml is missing expected sections.")

    for child in list(models_el):
        models_el.remove(child)
    for child in list(groups_el):
        groups_el.remove(child)
    if views_el is not None:
        for child in list(views_el):
            views_el.remove(child)
    if view_objects_el is not None:
        for child in list(view_objects_el):
            view_objects_el.remove(child)
    for child in list(layout_groups_el):
        layout_groups_el.remove(child)
    ET.SubElement(layout_groups_el, "layoutGroup", {"name": "Showcase Dynamic", "backgroundImage": ""})

    for child in list(settings_el):
        key = child.tag
        if key == "backgroundImage":
            child.attrib["value"] = ""
        elif key == "previewWidth":
            child.attrib["value"] = "1600"
        elif key == "previewHeight":
            child.attrib["value"] = "900"
        elif key == "storedLayoutGroup":
            child.attrib["value"] = "Showcase Dynamic"
        elif key == "backgroundAlpha":
            child.attrib["value"] = "0"

    channel = 1
    coords: dict[str, tuple[float, float]] = {}

    def add(spec: ModelSpec) -> None:
        _add_model(models_el, spec)
        coords[spec.name] = (spec.x, spec.y)

    # Whole-house spines and roof accents.
    spine_positions = [
        ("Left Tree", 170, 520),
        ("Left Blvd", 420, 380),
        ("Center Blvd", 800, 360),
        ("Right Blvd", 1180, 380),
        ("Right Linden", 1430, 520),
    ]
    color_models: dict[str, list[str]] = {"red": [], "green": [], "white": []}
    for stem, x, y in spine_positions:
        for color in ("red", "green", "white"):
            spec = _single_line(f"{stem} {color.title()}", channel, x, y, 0, 120 if "Blvd" in stem else 170, 50, color)
            channel = _next_channel(channel, spec.string_type, spec.parm2)
            add(spec)
            color_models[color].append(spec.name)

    for color, y in (("red", 770), ("green", 790), ("white", 810)):
        spec = _single_line(f"Roof Top {color.title()}", channel, 800, y, 900, 0, 90, color)
        channel = _next_channel(channel, spec.string_type, spec.parm2)
        add(spec)
        color_models[color].append(spec.name)

    # RGB mega trees and split-color mega trees.
    mega_rgb: list[str] = []
    mega_color: dict[str, list[str]] = {"red": [], "green": [], "white": []}
    for idx in range(1, 9):
        x = 540 + ((idx - 1) * 80)
        rgb = _rgb_line(f"Mega Tree {idx}", channel, x, 480, 0, 210, 64, aliases=[f"oldname:mega tree rgb {idx}"])
        channel = _next_channel(channel, rgb.string_type, rgb.parm2)
        add(rgb)
        mega_rgb.append(rgb.name)
        for color in ("red", "green", "white"):
            y = 460 if color == "red" else (480 if color == "green" else 500)
            spec = _single_line(f"Mega Tree {color.title()} {idx}", channel, x, y, 0, 220, 64, color)
            channel = _next_channel(channel, spec.string_type, spec.parm2)
            add(spec)
            mega_color[color].append(spec.name)
            color_models[color].append(spec.name)

    # RGB line trees and split-color line trees.
    line_rgb: list[str] = []
    line_color: dict[str, list[str]] = {"red": [], "green": [], "white": []}
    line_xs = [130, 240, 350, 460, 1140, 1250, 1360, 1470, 1580]
    for idx, x in enumerate(line_xs, start=1):
        rgb = _rgb_line(f"Line Tree {idx}", channel, x, 430, 0, 150 + ((idx % 3) * 18), 42, reverse=bool(idx % 2))
        channel = _next_channel(channel, rgb.string_type, rgb.parm2)
        add(rgb)
        line_rgb.append(rgb.name)
        for color in ("red", "green", "white"):
            y = 420 if color == "red" else (432 if color == "green" else 444)
            spec = _single_line(f"Line Tree {color.title()} {idx}", channel, x, y, 0, 155 + ((idx % 3) * 14), 42, color)
            channel = _next_channel(channel, spec.string_type, spec.parm2)
            add(spec)
            line_color[color].append(spec.name)
            color_models[color].append(spec.name)

    # Garage trees.
    garage_rgb: list[str] = []
    garage_color: dict[str, list[str]] = {"red": [], "green": [], "white": []}
    garage_positions = [220, 320, 1280, 1380]
    for idx, x in enumerate(garage_positions, start=1):
        rgb = _rgb_line(f"Garage Trees {idx}", channel, x, 600, 0, 90, 30)
        channel = _next_channel(channel, rgb.string_type, rgb.parm2)
        add(rgb)
        garage_rgb.append(rgb.name)
        for color in ("red", "green", "white"):
            y = 586 if color == "red" else (598 if color == "green" else 610)
            spec = _single_line(f"Garage Trees {color.title()} {idx}", channel, x, y, 0, 94, 30, color)
            channel = _next_channel(channel, spec.string_type, spec.parm2)
            add(spec)
            garage_color[color].append(spec.name)
            color_models[color].append(spec.name)

    # North / South candy canes.
    north_canes: list[str] = []
    south_canes: list[str] = []
    cane_xs = [170 + (i * 80) for i in range(16)]
    for idx, x in enumerate(cane_xs, start=1):
        north = _rgb_line(f"North Candy Cane {idx}", channel, x, 165, 0, 48, 10, reverse=bool(idx % 2))
        channel = _next_channel(channel, north.string_type, north.parm2)
        add(north)
        north_canes.append(north.name)
        south = _rgb_line(f"South Candy Cane {idx}", channel, x, 105, 0, 48, 10, reverse=not bool(idx % 2))
        channel = _next_channel(channel, south.string_type, south.parm2)
        add(south)
        south_canes.append(south.name)

    # Numeric notes runway.
    notes_main: list[str] = []
    notes_mirror: list[str] = []
    for idx in range(1, 33):
        x = 120 + ((idx - 1) * 45)
        y = 250 if idx <= 16 else 210
        spec = _rgb_line(str(idx), channel, x, y, 30, 0, 8, reverse=bool(idx % 2))
        channel = _next_channel(channel, spec.string_type, spec.parm2)
        add(spec)
        if idx <= 16:
            notes_main.append(spec.name)
        else:
            notes_mirror.append(spec.name)

    # Front arches.
    all_arches: list[str] = []
    arch_xs = [220, 420, 620, 820, 1020, 1220]
    for arch_num, x in enumerate(arch_xs, start=1):
        section_models: list[str] = []
        for sec in range(1, 7):
            width = 90 + (sec * 3)
            height = 38 + (sec % 3) * 6
            offset = (sec - 3.5) * 14
            points = [(-width, 0.0), (offset, height), (width, 0.0)]
            spec = _polyline(f"Arch {arch_num} Sec {sec}", channel, x + (sec - 3.5) * 3, 310, points, 24 + sec, color="white")
            channel = _next_channel(channel, spec.string_type, spec.parm2)
            add(spec)
            section_models.append(spec.name)
            color_models["white"].append(spec.name)
        all_arches.extend(section_models)

    # Stars and snowflakes.
    star_models: list[str] = []
    snowflake_models: list[str] = []
    star_xs = [460, 560, 660, 760, 860, 960, 1060, 1160]
    for idx, x in enumerate(star_xs, start=1):
        spec = _star(f"Star {idx}", channel, x, 720 + (idx % 2) * 20, 2.2 + (idx % 3) * 0.25, 2.0 + (idx % 2) * 0.35, 20 + idx, rgb=(idx % 3 == 0), color="white", rotate_z=idx * 3.0, star_ratio=2.25 + (idx % 4) * 0.12)
        channel = _next_channel(channel, spec.string_type, spec.parm2)
        add(spec)
        star_models.append(spec.name)
        if not spec.string_type.startswith("RGB"):
            color_models["white"].append(spec.name)
    flake_xs = [360, 510, 660, 810, 960, 1110, 1260, 1410]
    for idx, x in enumerate(flake_xs, start=1):
        name = f"sf{idx}"
        spec = _star(name, channel, x, 840, 1.9 + (idx % 3) * 0.18, 1.9 + (idx % 2) * 0.18, 18 + idx, rgb=(idx % 2 == 0), color="white", rotate_z=idx * 11.0)
        channel = _next_channel(channel, spec.string_type, spec.parm2)
        add(spec)
        snowflake_models.append(spec.name)
        if not spec.string_type.startswith("RGB"):
            color_models["white"].append(spec.name)

    # Wreaths and sphere-like circle coverage.
    circle_models: list[str] = []
    for idx, (name, x, y, sx, sy, inside_out, rgb) in enumerate(
        [
            ("Sphere Ring 1A", 300, 760, 2.0, 1.8, 0, True),
            ("Sphere Ring 1B", 300, 760, 1.3, 1.1, 1, False),
            ("Sphere Ring 2A", 1300, 760, 2.0, 1.8, 0, True),
            ("Sphere Ring 2B", 1300, 760, 1.3, 1.1, 1, False),
            ("Wreath 1", 690, 655, 1.8, 1.7, 0, False),
            ("Wreath 2", 910, 655, 1.8, 1.7, 0, False),
        ],
        start=1,
    ):
        spec = _circle(name, channel, x, y, sx, sy, 18 + idx, rgb=rgb, color="white", inside_out=inside_out, rotate_z=idx * 7.0)
        channel = _next_channel(channel, spec.string_type, spec.parm2)
        add(spec)
        circle_models.append(spec.name)
        if not rgb:
            color_models["white"].append(spec.name)

    # Matrix/video panels built from stacked RGB line models.
    matrix_groups: dict[str, list[str]] = {}
    for group_name, x_base in (("Matrix Panel 1", 210), ("Matrix Panel 2", 1390), ("Video Panel 3", 800)):
        members: list[str] = []
        for row in range(8):
            spec = _rgb_line(f"{group_name} Row {row + 1}", channel, x_base, 610 - (row * 18), 120 if "3" not in group_name else 180, 0, 40, reverse=bool(row % 2))
            channel = _next_channel(channel, spec.string_type, spec.parm2)
            add(spec)
            members.append(spec.name)
        matrix_groups[group_name] = members

    # Spinner/pinwheel arms built from RGB lines.
    spinner_groups: dict[str, list[str]] = {}
    for group_name, x_center in (("Spinner 1", 230), ("Pinwheel 2", 1370)):
        members: list[str] = []
        for arm, (dx, dy) in enumerate(_spoke_points(72, 72, 8), start=1):
            spec = _rgb_line(f"{group_name} Arm {arm}", channel, x_center, 690, dx, dy, 20, reverse=bool(arm % 2))
            channel = _next_channel(channel, spec.string_type, spec.parm2)
            add(spec)
            members.append(spec.name)
        spinner_groups[group_name] = members

    # Talking heads / singing faces.
    face_groups: dict[str, list[str]] = {}
    for group_name, x_center in (("Talking Head 1", 620), ("Singing Face 2", 980)):
        members: list[str] = []
        outline = _circle(f"{group_name} Outline", channel, x_center, 610, 2.0, 2.2, 24, rgb=True)
        channel = _next_channel(channel, outline.string_type, outline.parm2)
        add(outline)
        members.append(outline.name)
        mouth = _polyline(f"{group_name} Mouth", channel, x_center, 580, [(-28.0, 0.0), (0.0, -12.0), (28.0, 0.0)], 16, rgb=True)
        channel = _next_channel(channel, mouth.string_type, mouth.parm2)
        add(mouth)
        members.append(mouth.name)
        eye_l = _rgb_line(f"{group_name} Eye 1", channel, x_center - 24, 632, 12, 0, 6)
        channel = _next_channel(channel, eye_l.string_type, eye_l.parm2)
        add(eye_l)
        members.append(eye_l.name)
        eye_r = _rgb_line(f"{group_name} Eye 2", channel, x_center + 12, 632, 12, 0, 6)
        channel = _next_channel(channel, eye_r.string_type, eye_r.parm2)
        add(eye_r)
        members.append(eye_r.name)
        face_groups[group_name] = members

    # Floods.
    flood_models: list[str] = []
    for idx, (x, y) in enumerate([(90, 40), (270, 40), (1330, 40), (1510, 40), (680, 45), (920, 45)], start=1):
        spec = _rgb_line(f"Flood Light {idx}", channel, x, y, 25, 0, 6)
        channel = _next_channel(channel, spec.string_type, spec.parm2)
        add(spec)
        flood_models.append(spec.name)

    # Edge-case models zone.
    edge_models: list[str] = []
    edge_specs = [
        _rgb_line("Edge RGB Vertical 1", channel, 70, 300, 0, 110, 12, aliases=["oldname:edge vertical"]),  # type: ignore[arg-type]
    ]
    channel = _next_channel(channel, edge_specs[-1].string_type, edge_specs[-1].parm2)
    edge_specs.extend(
        [
            _rgb_line("Edge RGB Reverse 1", channel, 70, 430, 140, 0, 12, reverse=True),
            _polyline("Edge Zigzag 1", _next_channel(channel, "RGB Nodes", 12), 70, 520, [(-30.0, -20.0), (0.0, 30.0), (30.0, -10.0), (50.0, 28.0)], 18, rgb=True),
        ]
    )
    channel = _next_channel(channel, edge_specs[1].string_type, edge_specs[1].parm2)
    channel = _next_channel(channel, edge_specs[2].string_type, edge_specs[2].parm2)
    edge_specs.extend(
        [
            _circle("Edge Circle RGB 1", channel, 70, 650, 1.0, 1.6, 10, rgb=True, inside_out=1),
            _star("Edge Star RGB 1", _next_channel(channel, "RGB Nodes", 10), 70, 760, 1.0, 1.0, 10, rgb=True, rotate_z=18.0),
        ]
    )
    channel = _next_channel(channel, edge_specs[3].string_type, edge_specs[3].parm2)
    channel = _next_channel(channel, edge_specs[4].string_type, edge_specs[4].parm2)
    for spec in edge_specs:
        add(spec)
        edge_models.append(spec.name)

    # Build group mappings.
    all_red = color_models["red"][:]
    all_green = color_models["green"][:]
    all_white = color_models["white"][:]
    left_tree_group = [f"Left Tree {c.title()}" for c in ("red", "green", "white")]
    right_linden_group = [f"Right Linden {c.title()}" for c in ("red", "green", "white")]
    blvd_left = [f"Left Blvd {c.title()}" for c in ("red", "green", "white")]
    blvd_center = [f"Center Blvd {c.title()}" for c in ("red", "green", "white")]
    blvd_right = [f"Right Blvd {c.title()}" for c in ("red", "green", "white")]

    groups_in_order: list[tuple[str, list[str]]] = [
        ("18_WHOLE_HOUSE", all_red + all_green + all_white + mega_rgb + line_rgb + garage_rgb + north_canes + south_canes + notes_main + notes_mirror + star_models + snowflake_models + flood_models),
        ("17_FLOODS_ALL", flood_models),
        ("16_MATRIX_ALL", [name for members in matrix_groups.values() for name in members]),
        ("15_GT_ALL", garage_rgb + garage_color["red"] + garage_color["green"] + garage_color["white"]),
        ("14_SNOWFLAKES_ALL", snowflake_models),
        ("13_PIXEL_EDGECASES", edge_models),
        ("12_STARS_ALL", star_models),
        ("11_NOTES_MIRROR", notes_mirror),
        ("10_NOTES_MAIN", notes_main),
        ("09_NOTNORTH_CANES", south_canes),
        ("08_NORTH_CANES", north_canes),
        ("07_MEGATREE", mega_rgb + mega_color["red"] + mega_color["green"] + mega_color["white"]),
        ("06_LINE_ALL", line_rgb + line_color["red"] + line_color["green"] + line_color["white"]),
        ("05_ALL_RED", all_red),
        ("04_ALL_WHITE", all_white),
        ("03_ALL_GREEN", all_green),
        ("02_ARCHES", all_arches),
        ("01_EDGE_CASES", edge_models),
        ("BLVD_RIGHT", blvd_right),
        ("BLVD_CENTER", blvd_center),
        ("BLVD_LEFT", blvd_left),
        ("RIGHT_LINDEN", right_linden_group),
        ("LEFT_TREE", left_tree_group),
        ("mega tree red", mega_color["red"]),
        ("mega tree green", mega_color["green"]),
        ("mega tree white", mega_color["white"]),
        ("line tree red", line_color["red"]),
        ("line tree green", line_color["green"]),
        ("line tree white", line_color["white"]),
        ("Matrix Panel 1", matrix_groups["Matrix Panel 1"]),
        ("Matrix Panel 2", matrix_groups["Matrix Panel 2"]),
        ("Video Panel 3", matrix_groups["Video Panel 3"]),
        ("Spinner 1", spinner_groups["Spinner 1"]),
        ("Pinwheel 2", spinner_groups["Pinwheel 2"]),
        ("Sphere 1", ["Sphere Ring 1A", "Sphere Ring 1B"]),
        ("Orb 2", ["Sphere Ring 2A", "Sphere Ring 2B"]),
        ("Talking Head 1", face_groups["Talking Head 1"]),
        ("Singing Face 2", face_groups["Singing Face 2"]),
        ("WREATHS_ALL", ["Wreath 1", "Wreath 2"]),
        ("ALL RGB PIXELS", mega_rgb + line_rgb + garage_rgb + north_canes + south_canes + notes_main + notes_mirror + [name for members in matrix_groups.values() for name in members] + [name for members in spinner_groups.values() for name in members] + [name for members in face_groups.values() for name in members] + flood_models + edge_models),
    ]

    for group_name, members in groups_in_order:
        _add_group(groups_el, group_name, members, coords)

    _indent_xml(root)
    src_tree.write(OUT_LAYOUT, encoding="utf-8", xml_declaration=True)
    shutil.copy2(OUT_LAYOUT, OUT_LAYOUT_BK)
    shutil.copy2(SRC_AUDIO, OUT_AUDIO)

    xsq = base.load_xsq(SRC_TEMPLATE)
    base.sync_xsq_to_layout(xsq, OUT_LAYOUT)
    for element in xsq.elements.values():
        base.clear_effects(element, "all", base.AUTO_LAYER_NAME)
    base.replace_audio_references(xsq.root, OUT_AUDIO)
    base.indent_xml(xsq.root)
    xsq.tree.write(OUT_TEMPLATE, encoding="utf-8", xml_declaration=True)

    OUT_README.write_text(
        "\n".join(
            [
                "Dream Sequence Weaver - template2_dynamic_showcase",
                "",
                "This pack is a broad, valid xLights-safe showcase layout built from model formats already proven in your workspace.",
                "It intentionally covers:",
                "- RGB node props",
                "- single-color red/green/white props",
                "- sequential lanes",
                "- arches, stars, circles, lines, and polylines",
                "- grouped matrix/video/spinner/sphere/talking-head targets using safe underlying props",
                "- alias and geometry edge cases",
                "",
                f"Layout:   {OUT_LAYOUT.name}",
                f"Template: {OUT_TEMPLATE.name}",
                f"Audio:    {OUT_AUDIO.name}",
                "",
                "Recommended variants for this pack:",
                "- v17.3",
                "- v20.3",
                "- v21.3",
            ]
        ),
        encoding="utf-8",
    )

    return {
        "pack_dir": PACK_DIR,
        "layout": OUT_LAYOUT,
        "template": OUT_TEMPLATE,
        "audio": OUT_AUDIO,
        "output_root": OUT_OUTPUTS,
    }


def main() -> int:
    if not SRC_LAYOUT.exists() or not SRC_TEMPLATE.exists() or not SRC_AUDIO.exists():
        raise SystemExit("Required source files were not found in the workspace.")
    result = build_showcase_pack()
    print(f"Created showcase pack: {result['pack_dir']}")
    print(f"Layout:   {result['layout']}")
    print(f"Template: {result['template']}")
    print(f"Audio:    {result['audio']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
