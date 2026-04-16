#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LAYOUT = ROOT / "allmodels" / "xlights_rgbeffects.xml"
DEFAULT_BACKUP = ROOT / "allmodels" / "xlights_rgbeffects.pre_neighbor_art_backup.xml"
PREFIX = "NBH_"


@dataclass
class ModelPlacement:
    template: str
    name: str
    x: float
    y: float
    x2: float | None = None
    y2: float | None = None
    scale_x: float | None = None
    scale_y: float | None = None
    parm1: int | None = None
    parm2: int | None = None
    parm3: int | None = None
    display_as: str | None = None
    string_type: str | None = None
    direction: str | None = None
    start_side: str | None = None
    extra_attrs: dict[str, str] | None = None
    submodels: list[tuple[str, str]] | None = None


def _to_int(value: str | None, default: int = 0) -> int:
    text = (value or "").strip()
    if not text:
        return default
    try:
        return int(round(float(text)))
    except Exception:
        return default


def _fmt(value: float) -> str:
    return f"{value:.4f}"


def estimate_channels(attrs: dict[str, str]) -> int:
    display = (attrs.get("DisplayAs") or "").lower()
    p1 = max(1, _to_int(attrs.get("parm1"), 1))
    p2 = max(1, _to_int(attrs.get("parm2"), 1))
    p3 = max(1, _to_int(attrs.get("parm3"), 1))

    if "matrix" in display or "image" in display:
        return max(3, p1 * p2 * 3)
    if "tree" in display:
        return max(3, p1 * p2 * 3)
    if "spinner" in display:
        return max(3, p1 * p2 * p3 * 3)
    if "sphere" in display:
        return max(3, p1 * p2 * 3)
    if "arches" in display:
        return max(3, p1 * p2 * 3)
    if "candy cane" in display:
        return max(3, p1 * p2 * 3)
    if "window" in display:
        return max(3, (p1 + p2 + p3) * 3)
    if "single line" in display or "poly line" in display:
        return max(3, max(p1, p2) * 3)
    if "circle" in display or "star" in display:
        return max(3, max(p2, p1 * 8) * 3)
    if "custom" in display:
        width = max(1, _to_int(attrs.get("CustomWidth"), p1))
        height = max(1, _to_int(attrs.get("CustomHeight"), p2))
        return max(3, width * height * 3)
    return max(3, p1 * p2 * 3)


def next_start_channel(models: list[ET.Element]) -> int:
    max_end = 1
    for model in models:
        attrs = dict(model.attrib)
        start = max(1, _to_int(attrs.get("StartChannel"), 1))
        span = estimate_channels(attrs)
        max_end = max(max_end, start + span)
    return max_end + 180


def add_submodel(parent: ET.Element, name: str, line_spec: str) -> None:
    sub = ET.SubElement(parent, "subModel")
    sub.attrib.update(
        {
            "name": name,
            "layout": "horizontal",
            "type": "ranges",
            "bufferstyle": "Default",
            "line0": line_spec,
        }
    )
    ET.SubElement(sub, "Aliases")
    ET.SubElement(sub, "ControllerConnection")


def default_arch_submodels(model: ET.Element) -> None:
    arches = max(1, _to_int(model.attrib.get("parm1"), 1))
    nodes_per_arch = max(1, _to_int(model.attrib.get("parm2"), 1))
    total = arches * nodes_per_arch
    left_end = max(1, total // 3)
    center_start = max(1, left_end + 1)
    center_end = max(center_start, (2 * total) // 3)
    right_start = max(1, center_end + 1)
    center_nodes = ", ".join(
        str((idx * nodes_per_arch) + max(1, (nodes_per_arch // 2)) + 1) for idx in range(arches)
    )
    add_submodel(model, "left_lane", f"1-{left_end}")
    add_submodel(model, "center_lane", f"{center_start}-{center_end}")
    add_submodel(model, "right_lane", f"{right_start}-{total}")
    add_submodel(model, "center_nodes", center_nodes)
    add_submodel(model, "sweep_forward", f"1-{total}")
    add_submodel(model, "sweep_reverse", f"{total}-1")


def clone_model(template: ET.Element, placement: ModelPlacement, start_channel: int) -> ET.Element:
    model = copy.deepcopy(template)
    model.attrib["name"] = placement.name
    model.attrib["StartChannel"] = str(start_channel)
    model.attrib["WorldPosX"] = _fmt(placement.x)
    model.attrib["WorldPosY"] = _fmt(placement.y)
    model.attrib["WorldPosZ"] = model.attrib.get("WorldPosZ", "0")

    if placement.display_as is not None:
        model.attrib["DisplayAs"] = placement.display_as
    if placement.x2 is not None:
        model.attrib["X2"] = _fmt(placement.x2)
    if placement.y2 is not None:
        model.attrib["Y2"] = _fmt(placement.y2)
    if placement.scale_x is not None:
        model.attrib["ScaleX"] = _fmt(placement.scale_x)
    if placement.scale_y is not None:
        model.attrib["ScaleY"] = _fmt(placement.scale_y)
    if placement.parm1 is not None:
        model.attrib["parm1"] = str(max(1, int(placement.parm1)))
    if placement.parm2 is not None:
        model.attrib["parm2"] = str(max(1, int(placement.parm2)))
    if placement.parm3 is not None:
        model.attrib["parm3"] = str(max(1, int(placement.parm3)))
    if placement.string_type is not None:
        model.attrib["StringType"] = placement.string_type
    if placement.direction is not None:
        model.attrib["Dir"] = placement.direction
    if placement.start_side is not None:
        model.attrib["StartSide"] = placement.start_side
    if placement.extra_attrs:
        for key, value in placement.extra_attrs.items():
            model.attrib[key] = str(value)

    for child in list(model):
        if child.tag != "ControllerConnection":
            model.remove(child)
    if not any(child.tag == "ControllerConnection" for child in list(model)):
        controller = ET.SubElement(model, "ControllerConnection")
        controller.attrib["Protocol"] = "ws2811"

    if placement.submodels:
        for sub_name, line_spec in placement.submodels:
            add_submodel(model, sub_name, line_spec)
    elif (model.attrib.get("DisplayAs") or "").lower() == "arches":
        default_arch_submodels(model)

    return model


def make_group(name: str, model_names: list[str], center: tuple[float, float]) -> ET.Element:
    group = ET.Element("modelGroup")
    group.attrib.update(
        {
            "layout": "minimalGrid",
            "GridSize": "400",
            "LayoutGroup": "All Previews",
            "name": name,
            "centrex": _fmt(center[0]),
            "centrey": _fmt(center[1]),
            "centreDefined": "0",
            "centreMinx": str(int(center[0] - 360)),
            "centreMiny": str(int(center[1] - 280)),
            "centreMaxx": str(int(center[0] + 360)),
            "centreMaxy": str(int(center[1] + 280)),
            "models": ",".join(model_names),
        }
    )
    return group


def center_for(placements: list[ModelPlacement]) -> tuple[float, float]:
    if not placements:
        return (0.0, 0.0)
    sx = sum(item.x for item in placements)
    sy = sum(item.y for item in placements)
    return (sx / len(placements), sy / len(placements))


def build_left_neighbor() -> list[ModelPlacement]:
    out: list[ModelPlacement] = []
    base_x = -2480.0

    for idx in range(6):
        out.append(
            ModelPlacement(
                template=("Tree-2", "Tree-3", "Tree")[idx % 3],
                name=f"{PREFIX}LEFT_MEGA_TREE_{idx + 1:02d}",
                x=base_x - idx * 285.0,
                y=1030.0 + (idx % 2) * 72.0,
                parm1=16,
                parm2=66 + (idx % 3) * 8,
                scale_x=2.30 + (idx % 2) * 0.24,
                scale_y=2.24 + (idx % 3) * 0.18,
            )
        )

    for idx in range(6):
        out.append(
            ModelPlacement(
                template="Tree",
                name=f"{PREFIX}LEFT_MINI_TREE_{idx + 1:02d}",
                x=base_x - 70.0 - idx * 250.0,
                y=760.0 + (idx % 3) * 36.0,
                parm1=8,
                parm2=42,
                scale_x=1.52,
                scale_y=1.42,
            )
        )

    for idx in range(8):
        out.append(
            ModelPlacement(
                template="Arches",
                name=f"{PREFIX}LEFT_ARCH_{idx + 1:02d}",
                x=base_x - idx * 220.0,
                y=400.0 + (idx % 3) * 30.0,
                parm1=7,
                parm2=50,
                x2=188.0 + (idx % 2) * 10.0,
                y2=-5.0,
                direction=("L" if idx % 2 == 0 else "R"),
            )
        )

    for idx in range(5):
        out.append(
            ModelPlacement(
                template="Single Line-5",
                name=f"{PREFIX}LEFT_ROOFLINE_{idx + 1:02d}",
                x=base_x - idx * 365.0,
                y=1280.0 + (idx % 2) * 26.0,
                parm2=175 + idx * 25,
                x2=282.0 + idx * 16.0,
                y2=-76.0 + (idx % 3) * 24.0,
                direction=("R" if idx % 2 == 0 else "L"),
            )
        )

    for idx in range(4):
        out.append(
            ModelPlacement(
                template=("Matrix-2" if idx % 2 == 0 else "Matrix-3"),
                name=f"{PREFIX}LEFT_MATRIX_PANEL_{idx + 1:02d}",
                x=base_x - idx * 470.0,
                y=1460.0 + (idx % 2) * 70.0,
                parm1=38,
                parm2=30,
                display_as="Horiz Matrix",
                scale_x=1.0,
                scale_y=1.0,
            )
        )

    for idx in range(3):
        out.append(
            ModelPlacement(
                template="Window Frame",
                name=f"{PREFIX}LEFT_WINDOW_FRAME_{idx + 1:02d}",
                x=base_x - 110.0 - idx * 410.0,
                y=1045.0 + (idx % 2) * 64.0,
                parm1=14,
                parm2=42,
                parm3=14,
                scale_x=27.0 + idx * 2.6,
                scale_y=8.1 + idx * 0.8,
            )
        )

    for idx in range(4):
        out.append(
            ModelPlacement(
                template="Spinner",
                name=f"{PREFIX}LEFT_SPINNER_{idx + 1:02d}",
                x=base_x - 70.0 - idx * 520.0,
                y=260.0 + (idx % 2) * 26.0,
                parm1=2,
                parm2=14 + idx,
                parm3=7,
                scale_x=14.2 + idx * 0.5,
                scale_y=9.2 + idx * 0.25,
                direction=("L" if idx % 2 == 0 else "R"),
            )
        )

    for idx in range(5):
        out.append(
            ModelPlacement(
                template="Star-2",
                name=f"{PREFIX}LEFT_STAR_{idx + 1:02d}",
                x=base_x - idx * 380.0,
                y=1710.0 + (idx % 2) * 22.0,
                parm2=26 + idx * 2,
                scale_x=8.2 + idx * 0.2,
                scale_y=7.8 + idx * 0.2,
            )
        )

    for idx in range(6):
        out.append(
            ModelPlacement(
                template="Candy Canes",
                name=f"{PREFIX}LEFT_CANDY_ROW_{idx + 1:02d}",
                x=base_x - idx * 320.0,
                y=175.0 + (idx % 2) * 18.0,
                parm1=8,
                parm2=34,
                parm3=34,
                x2=196.0,
                y2=-5.0,
            )
        )

    for idx in range(3):
        out.append(
            ModelPlacement(
                template="Sphere",
                name=f"{PREFIX}LEFT_GLOBE_{idx + 1:02d}",
                x=base_x - 190.0 - idx * 620.0,
                y=1520.0 + (idx % 2) * 46.0,
                parm1=12 + idx,
                parm2=12 + idx,
                scale_x=120.0 + idx * 16.0,
                scale_y=70.0 + idx * 8.0,
            )
        )

    out.extend(
        [
            ModelPlacement("Sphere", f"{PREFIX}LEFT_SNOWMAN_A_BODY", -2890.0, 890.0, parm1=12, parm2=12, scale_x=128.0, scale_y=92.0),
            ModelPlacement("Sphere", f"{PREFIX}LEFT_SNOWMAN_A_HEAD", -2890.0, 1020.0, parm1=8, parm2=8, scale_x=72.0, scale_y=58.0),
            ModelPlacement("Matrix-4", f"{PREFIX}LEFT_SINGING_FACE_5", -2890.0, 1012.0, parm1=11, parm2=14, scale_x=6.2, scale_y=6.2),
            ModelPlacement("Matrix-4", f"{PREFIX}LEFT_MOUTH_5", -2890.0, 984.0, parm1=8, parm2=6, scale_x=4.0, scale_y=3.4),
            ModelPlacement("Sphere", f"{PREFIX}LEFT_SNOWMAN_B_BODY", -3250.0, 860.0, parm1=12, parm2=12, scale_x=122.0, scale_y=88.0),
            ModelPlacement("Sphere", f"{PREFIX}LEFT_SNOWMAN_B_HEAD", -3250.0, 988.0, parm1=8, parm2=8, scale_x=70.0, scale_y=56.0),
            ModelPlacement("Matrix-4", f"{PREFIX}LEFT_SINGING_FACE_6", -3250.0, 980.0, parm1=10, parm2=12, scale_x=5.6, scale_y=5.6),
            ModelPlacement("Matrix-4", f"{PREFIX}LEFT_MOUTH_6", -3250.0, 952.0, parm1=8, parm2=6, scale_x=3.9, scale_y=3.3),
        ]
    )

    return out


def build_right_neighbor() -> list[ModelPlacement]:
    out: list[ModelPlacement] = []
    base_x = 2480.0

    for idx in range(6):
        out.append(
            ModelPlacement(
                template=("Tree-3", "Tree-2", "Tree")[idx % 3],
                name=f"{PREFIX}RIGHT_MEGA_TREE_{idx + 1:02d}",
                x=base_x + idx * 285.0,
                y=1050.0 + (idx % 2) * 68.0,
                parm1=16,
                parm2=68 + (idx % 3) * 7,
                scale_x=2.34 + (idx % 2) * 0.24,
                scale_y=2.28 + (idx % 3) * 0.16,
            )
        )

    for idx in range(6):
        out.append(
            ModelPlacement(
                template="Tree",
                name=f"{PREFIX}RIGHT_MINI_TREE_{idx + 1:02d}",
                x=base_x + 96.0 + idx * 250.0,
                y=762.0 + (idx % 3) * 34.0,
                parm1=8,
                parm2=44,
                scale_x=1.55,
                scale_y=1.45,
            )
        )

    for idx in range(8):
        out.append(
            ModelPlacement(
                template="Arches",
                name=f"{PREFIX}RIGHT_ARCH_{idx + 1:02d}",
                x=base_x + idx * 224.0,
                y=418.0 + (idx % 3) * 28.0,
                parm1=7,
                parm2=52,
                x2=196.0 + (idx % 2) * 8.0,
                y2=-4.0,
                direction=("R" if idx % 2 == 0 else "L"),
            )
        )

    for idx in range(4):
        out.append(
            ModelPlacement(
                template="Single Line-5",
                name=f"{PREFIX}RIGHT_ROOFLINE_{idx + 1:02d}",
                x=base_x + idx * 410.0,
                y=1290.0 + (idx % 2) * 28.0,
                parm2=188 + idx * 30,
                x2=300.0 + idx * 18.0,
                y2=-80.0 + (idx % 2) * 22.0,
                direction=("L" if idx % 2 == 0 else "R"),
            )
        )

    for idx in range(6):
        out.append(
            ModelPlacement(
                template=("Matrix-2" if idx % 2 == 0 else "Matrix-3"),
                name=f"{PREFIX}RIGHT_MATRIX_PANEL_{idx + 1:02d}",
                x=base_x + idx * 340.0,
                y=1480.0 + (idx % 2) * 72.0,
                parm1=36 if idx % 2 else 44,
                parm2=30 if idx % 2 else 32,
                display_as="Horiz Matrix",
                scale_x=1.0,
                scale_y=1.0,
            )
        )

    for idx in range(4):
        out.append(
            ModelPlacement(
                template="Window Frame",
                name=f"{PREFIX}RIGHT_WINDOW_FRAME_{idx + 1:02d}",
                x=base_x + 130.0 + idx * 372.0,
                y=1038.0 + (idx % 2) * 66.0,
                parm1=14,
                parm2=44,
                parm3=14,
                scale_x=27.0 + idx * 2.2,
                scale_y=8.2 + idx * 0.8,
            )
        )

    for idx in range(6):
        out.append(
            ModelPlacement(
                template="Spinner",
                name=f"{PREFIX}RIGHT_SPINNER_{idx + 1:02d}",
                x=base_x + idx * 330.0,
                y=252.0 + (idx % 2) * 30.0,
                parm1=2 + (idx % 2),
                parm2=14 + idx,
                parm3=7 + (idx % 2),
                scale_x=14.6 + idx * 0.35,
                scale_y=9.4 + idx * 0.24,
                direction=("R" if idx % 2 == 0 else "L"),
            )
        )

    for idx in range(6):
        out.append(
            ModelPlacement(
                template="Star-2",
                name=f"{PREFIX}RIGHT_STAR_{idx + 1:02d}",
                x=base_x + idx * 300.0,
                y=1730.0 + (idx % 2) * 18.0,
                parm2=26 + idx * 2,
                scale_x=8.6 + idx * 0.2,
                scale_y=8.1 + idx * 0.2,
            )
        )

    for idx in range(2):
        out.append(
            ModelPlacement(
                template="Sphere",
                name=f"{PREFIX}RIGHT_GLOBE_{idx + 1:02d}",
                x=base_x + 470.0 + idx * 760.0,
                y=1550.0 + idx * 26.0,
                parm1=12 + idx,
                parm2=12 + idx,
                scale_x=128.0 + idx * 18.0,
                scale_y=76.0 + idx * 10.0,
            )
        )

    out.extend(
        [
            ModelPlacement("Sphere", f"{PREFIX}RIGHT_SNOWMAN_A_BODY", 4120.0, 880.0, parm1=12, parm2=12, scale_x=126.0, scale_y=90.0),
            ModelPlacement("Sphere", f"{PREFIX}RIGHT_SNOWMAN_A_HEAD", 4120.0, 1008.0, parm1=8, parm2=8, scale_x=72.0, scale_y=58.0),
            ModelPlacement("Matrix-4", f"{PREFIX}RIGHT_SINGING_FACE_7", 4120.0, 1000.0, parm1=10, parm2=13, scale_x=5.8, scale_y=5.8),
            ModelPlacement("Matrix-4", f"{PREFIX}RIGHT_MOUTH_7", 4120.0, 972.0, parm1=8, parm2=6, scale_x=4.0, scale_y=3.4),
            ModelPlacement("Sphere", f"{PREFIX}RIGHT_SNOWMAN_B_BODY", 4460.0, 848.0, parm1=12, parm2=12, scale_x=120.0, scale_y=86.0),
            ModelPlacement("Sphere", f"{PREFIX}RIGHT_SNOWMAN_B_HEAD", 4460.0, 974.0, parm1=8, parm2=8, scale_x=68.0, scale_y=54.0),
            ModelPlacement("Matrix-4", f"{PREFIX}RIGHT_SINGING_FACE_8", 4460.0, 966.0, parm1=10, parm2=12, scale_x=5.5, scale_y=5.5),
            ModelPlacement("Matrix-4", f"{PREFIX}RIGHT_MOUTH_8", 4460.0, 938.0, parm1=8, parm2=6, scale_x=3.8, scale_y=3.2),
        ]
    )

    return out


def build_rock_band() -> list[ModelPlacement]:
    out: list[ModelPlacement] = []

    out.extend(
        [
            ModelPlacement("Sphere", f"{PREFIX}BAND_LEAD_BODY", 3320.0, 860.0, parm1=14, parm2=14, scale_x=150.0, scale_y=106.0),
            ModelPlacement("Sphere", f"{PREFIX}BAND_LEAD_HEAD", 3320.0, 1010.0, parm1=9, parm2=9, scale_x=84.0, scale_y=64.0),
            ModelPlacement("Matrix-4", f"{PREFIX}BAND_LEAD_SINGING_FACE_1", 3320.0, 1005.0, parm1=16, parm2=22, scale_x=7.2, scale_y=8.2),
            ModelPlacement("Matrix-4", f"{PREFIX}BAND_LEAD_MOUTH_1", 3320.0, 972.0, parm1=10, parm2=6, scale_x=4.8, scale_y=3.8),
            ModelPlacement("Single Line-5", f"{PREFIX}BAND_LEAD_MIC_STAND", 3380.0, 822.0, parm2=44, x2=0.0, y2=178.0),
            ModelPlacement("Sphere", f"{PREFIX}BAND_LEAD_MIC_HEAD", 3380.0, 1004.0, parm1=4, parm2=4, scale_x=26.0, scale_y=24.0),
        ]
    )

    out.extend(
        [
            ModelPlacement("Sphere", f"{PREFIX}BAND_BASS_BODY", 3570.0, 844.0, parm1=12, parm2=12, scale_x=130.0, scale_y=92.0),
            ModelPlacement("Sphere", f"{PREFIX}BAND_BASS_HEAD", 3570.0, 972.0, parm1=8, parm2=8, scale_x=70.0, scale_y=56.0),
            ModelPlacement("Matrix-4", f"{PREFIX}BAND_BASS_SINGING_FACE_2", 3570.0, 965.0, parm1=11, parm2=14, scale_x=5.8, scale_y=6.0),
            ModelPlacement("Sphere", f"{PREFIX}BAND_BASS_GUITAR_BODY", 3646.0, 874.0, parm1=8, parm2=8, scale_x=88.0, scale_y=52.0),
            ModelPlacement("Single Line-5", f"{PREFIX}BAND_BASS_GUITAR_NECK", 3640.0, 888.0, parm2=72, x2=106.0, y2=36.0),
            ModelPlacement("Single Line-5", f"{PREFIX}BAND_BASS_STRINGS", 3650.0, 882.0, parm2=86, x2=100.0, y2=0.0),
            ModelPlacement("Single Line-5", f"{PREFIX}BAND_BASS_PICK_HAND", 3592.0, 892.0, parm2=38, x2=54.0, y2=24.0),
        ]
    )

    out.extend(
        [
            ModelPlacement("Sphere", f"{PREFIX}BAND_GUITAR_BODY", 3040.0, 842.0, parm1=12, parm2=12, scale_x=128.0, scale_y=90.0),
            ModelPlacement("Sphere", f"{PREFIX}BAND_GUITAR_HEAD", 3040.0, 970.0, parm1=8, parm2=8, scale_x=70.0, scale_y=56.0),
            ModelPlacement("Matrix-4", f"{PREFIX}BAND_GUITAR_SINGING_FACE_3", 3040.0, 963.0, parm1=11, parm2=13, scale_x=5.6, scale_y=5.8),
            ModelPlacement("Sphere", f"{PREFIX}BAND_GUITAR_LEAD_BODY", 2970.0, 874.0, parm1=8, parm2=8, scale_x=84.0, scale_y=50.0),
            ModelPlacement("Single Line-5", f"{PREFIX}BAND_GUITAR_NECK", 2968.0, 888.0, parm2=72, x2=-108.0, y2=36.0),
            ModelPlacement("Single Line-5", f"{PREFIX}BAND_GUITAR_STRINGS", 2972.0, 882.0, parm2=86, x2=-100.0, y2=0.0),
            ModelPlacement("Single Line-5", f"{PREFIX}BAND_GUITAR_PICK_HAND", 3006.0, 892.0, parm2=38, x2=-48.0, y2=22.0),
        ]
    )

    out.extend(
        [
            ModelPlacement("Sphere", f"{PREFIX}BAND_DRUMMER_BODY", 3820.0, 876.0, parm1=12, parm2=12, scale_x=132.0, scale_y=92.0),
            ModelPlacement("Sphere", f"{PREFIX}BAND_DRUMMER_HEAD", 3820.0, 1002.0, parm1=8, parm2=8, scale_x=72.0, scale_y=58.0),
            ModelPlacement("Matrix-4", f"{PREFIX}BAND_DRUMMER_SINGING_FACE_4", 3820.0, 996.0, parm1=10, parm2=12, scale_x=5.4, scale_y=5.6),
            ModelPlacement("Sphere", f"{PREFIX}BAND_DRUM_KICK", 3820.0, 764.0, parm1=12, parm2=12, scale_x=118.0, scale_y=78.0),
            ModelPlacement("Sphere", f"{PREFIX}BAND_DRUM_SNARE", 3728.0, 806.0, parm1=8, parm2=8, scale_x=62.0, scale_y=42.0),
            ModelPlacement("Sphere", f"{PREFIX}BAND_DRUM_TOM_HIGH", 3792.0, 842.0, parm1=7, parm2=7, scale_x=52.0, scale_y=36.0),
            ModelPlacement("Sphere", f"{PREFIX}BAND_DRUM_TOM_MID", 3862.0, 842.0, parm1=7, parm2=7, scale_x=52.0, scale_y=36.0),
            ModelPlacement("Sphere", f"{PREFIX}BAND_DRUM_FLOOR_TOM", 3926.0, 794.0, parm1=8, parm2=8, scale_x=68.0, scale_y=48.0),
            ModelPlacement("Star-2", f"{PREFIX}BAND_DRUM_HIHAT_CYMBAL", 3696.0, 894.0, parm2=18, scale_x=6.6, scale_y=6.0),
            ModelPlacement("Star-2", f"{PREFIX}BAND_DRUM_CRASH_CYMBAL", 3868.0, 934.0, parm2=22, scale_x=7.2, scale_y=6.6),
            ModelPlacement("Star-2", f"{PREFIX}BAND_DRUM_RIDE_CYMBAL", 3986.0, 908.0, parm2=22, scale_x=7.2, scale_y=6.6),
            ModelPlacement("Single Line-5", f"{PREFIX}BAND_DRUM_STICK_LEFT", 3788.0, 936.0, parm2=40, x2=-48.0, y2=-84.0),
            ModelPlacement("Single Line-5", f"{PREFIX}BAND_DRUM_STICK_RIGHT", 3852.0, 938.0, parm2=40, x2=44.0, y2=-80.0),
        ]
    )

    return out


def placements_by_name(placements: list[ModelPlacement]) -> dict[str, ModelPlacement]:
    return {item.name: item for item in placements}


def center_for_names(names: list[str], index: dict[str, ModelPlacement]) -> tuple[float, float]:
    chosen = [index[name] for name in names if name in index]
    return center_for(chosen)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Rebuild NBH neighbor props with a cleaner artistic dual-yard layout.")
    parser.add_argument("--layout", type=Path, default=DEFAULT_LAYOUT, help="Path to xlights_rgbeffects.xml")
    parser.add_argument("--backup", type=Path, default=DEFAULT_BACKUP, help="Backup path for the original layout")
    parser.add_argument("--sync-xbkp", action="store_true", help="Also mirror XML output to sibling .xbkp when present")
    args = parser.parse_args(argv)

    layout_path = args.layout
    backup_path = args.backup
    if not layout_path.is_absolute():
        layout_path = (ROOT / layout_path).resolve()
    if not backup_path.is_absolute():
        backup_path = (ROOT / backup_path).resolve()

    if not layout_path.exists():
        raise SystemExit(f"Layout file not found: {layout_path}")
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    if not backup_path.exists():
        backup_path.write_bytes(layout_path.read_bytes())
        print(f"Backup saved: {backup_path}")

    tree = ET.parse(layout_path)
    root = tree.getroot()
    models_el = root.find("models")
    groups_el = root.find("modelGroups")
    if models_el is None:
        raise SystemExit("Layout has no <models> section.")
    if groups_el is None:
        groups_el = ET.SubElement(root, "modelGroups")

    template_map: dict[str, ET.Element] = {}
    for model in list(models_el):
        name = (model.attrib.get("name") or "").strip()
        if name and not name.startswith(PREFIX):
            template_map[name] = model

    required_templates = [
        "Tree",
        "Tree-2",
        "Tree-3",
        "Arches",
        "Single Line-5",
        "Matrix-2",
        "Matrix-3",
        "Matrix-4",
        "Window Frame",
        "Spinner",
        "Star-2",
        "Candy Canes",
        "Sphere",
    ]
    missing = [name for name in required_templates if name not in template_map]
    if missing:
        raise SystemExit("Missing required templates: " + ", ".join(missing))

    removed_models = 0
    for model in list(models_el):
        if (model.attrib.get("name") or "").startswith(PREFIX):
            models_el.remove(model)
            removed_models += 1
    removed_groups = 0
    for group in list(groups_el):
        if (group.attrib.get("name") or "").startswith(PREFIX):
            groups_el.remove(group)
            removed_groups += 1
    if removed_models or removed_groups:
        print(f"Removed previous neighbor artifacts: models={removed_models}, groups={removed_groups}")

    left = build_left_neighbor()
    right = build_right_neighbor()
    band = build_rock_band()
    all_new = left + right + band
    index = placements_by_name(all_new)

    channel_cursor = next_start_channel(list(models_el))
    created_names: list[str] = []
    for placement in all_new:
        template = template_map[placement.template]
        cloned = clone_model(template, placement, channel_cursor)
        models_el.append(cloned)
        created_names.append(placement.name)
        channel_cursor += estimate_channels(dict(cloned.attrib)) + 9

    left_names = [item.name for item in left]
    right_names = [item.name for item in right]
    band_names = [item.name for item in band]
    singing_faces = [name for name in created_names if "SINGING_FACE" in name]
    spinner_names = [name for name in created_names if "SPINNER" in name]
    matrix_names = [name for name in created_names if "MATRIX_PANEL" in name or "SINGING_FACE" in name or "MOUTH" in name]
    arch_names = [name for name in created_names if "_ARCH_" in name]
    tree_names = [name for name in created_names if "_TREE_" in name]
    drum_names = [name for name in created_names if "BAND_DRUM_" in name]
    bass_names = [name for name in created_names if "BAND_BASS_" in name]
    guitar_names = [name for name in created_names if "BAND_GUITAR_" in name]

    group_specs: list[tuple[str, list[str]]] = [
        (f"{PREFIX}LEFT_NEIGHBOR", left_names),
        (f"{PREFIX}RIGHT_NEIGHBOR", right_names),
        (f"{PREFIX}ROCK_BAND", band_names),
        (f"{PREFIX}BAND_DRUM_KIT", drum_names),
        (f"{PREFIX}BAND_BASS_RIG", bass_names),
        (f"{PREFIX}BAND_GUITAR_RIG", guitar_names),
        (f"{PREFIX}SINGING_FACES", singing_faces),
        (f"{PREFIX}CHAOS_SPINNERS", spinner_names),
        (f"{PREFIX}MATRIX_DISTRICT", matrix_names),
        (f"{PREFIX}ARCH_RIVER", arch_names),
        (f"{PREFIX}MEGA_FOREST", tree_names),
        (f"{PREFIX}ALL_MODELS", created_names),
    ]
    for group_name, model_names in group_specs:
        if not model_names:
            continue
        groups_el.append(make_group(group_name, model_names, center_for_names(model_names, index)))

    try:
        ET.indent(tree, space="  ")
    except Exception:
        pass
    tree.write(layout_path, encoding="utf-8", xml_declaration=True)
    print(f"Neighbor layout updated: {layout_path}")
    print(f"Generated models: {len(created_names)}")
    print(f"Generated groups: {sum(1 for _name, members in group_specs if members)}")

    if args.sync_xbkp:
        xbkp_path = layout_path.with_suffix(".xbkp")
        if xbkp_path.exists():
            xbkp_path.write_bytes(layout_path.read_bytes())
            print(f"Synced backup project: {xbkp_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
