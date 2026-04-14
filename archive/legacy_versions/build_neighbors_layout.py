#!/usr/bin/env python3
from __future__ import annotations

import copy
import math
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent
LAYOUT_PATH = ROOT / "allmodels" / "xlights_rgbeffects.xml"
BACKUP_PATH = ROOT / "allmodels" / "xlights_rgbeffects.pre_neighbors_backup.xml"
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
    image_file: str | None = None
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
    disp = (attrs.get("DisplayAs") or "").lower()
    p1 = max(1, _to_int(attrs.get("parm1"), 1))
    p2 = max(1, _to_int(attrs.get("parm2"), 1))
    p3 = max(1, _to_int(attrs.get("parm3"), 1))
    if "matrix" in disp or "image" in disp:
        return max(3, p1 * p2 * 3)
    if "tree" in disp:
        return max(3, p1 * p2 * 3)
    if "spinner" in disp:
        return max(3, p1 * p2 * p3 * 3)
    if "sphere" in disp:
        return max(3, p1 * p2 * 3)
    if "arches" in disp:
        return max(3, p1 * p2 * 3)
    if "candy cane" in disp:
        return max(3, p1 * p2 * 3)
    if "window" in disp:
        return max(3, (p1 + p2 + p3) * 3)
    if "single line" in disp or "poly line" in disp:
        return max(3, max(p1, p2) * 3)
    if "circle" in disp or "star" in disp:
        return max(3, max(p2, p1 * 8) * 3)
    if "custom" in disp:
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
    return max_end + 120


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
    if placement.image_file is not None:
        model.attrib["Image"] = placement.image_file
        model.attrib.setdefault("ImagePlacement", "Scale Keep Aspect")
    if placement.extra_attrs:
        for key, value in placement.extra_attrs.items():
            model.attrib[key] = str(value)

    # Keep controller connection, drop template-specific submodels/faces/aliases to avoid naming collisions.
    for child in list(model):
        if child.tag != "ControllerConnection":
            model.remove(child)
    if not any(child.tag == "ControllerConnection" for child in list(model)):
        controller = ET.SubElement(model, "ControllerConnection")
        controller.attrib["Protocol"] = "ws2811"

    def add_submodel(name: str, line_spec: str) -> None:
        sub = ET.SubElement(model, "subModel")
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

    if placement.submodels:
        for sub_name, line_spec in placement.submodels:
            add_submodel(sub_name, line_spec)
    elif (model.attrib.get("DisplayAs") or "").lower() == "arches":
        arches = max(1, _to_int(model.attrib.get("parm1"), 1))
        nodes_per_arch = max(1, _to_int(model.attrib.get("parm2"), 1))
        total = arches * nodes_per_arch
        left_end = max(1, total // 3)
        center_start = max(1, left_end + 1)
        center_end = max(center_start, (2 * total) // 3)
        right_start = max(1, center_end + 1)
        center_nodes = ", ".join(
            str((idx * nodes_per_arch) + max(1, (nodes_per_arch // 2)) + 1)
            for idx in range(arches)
        )
        add_submodel("left_lane", f"1-{left_end}")
        add_submodel("center_lane", f"{center_start}-{center_end}")
        add_submodel("right_lane", f"{right_start}-{total}")
        add_submodel("center_nodes", center_nodes)
        add_submodel("sweep_forward", f"1-{total}")
        add_submodel("sweep_reverse", f"{total}-1")
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
            "centreMinx": str(int(center[0] - 350)),
            "centreMiny": str(int(center[1] - 280)),
            "centreMaxx": str(int(center[0] + 350)),
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


def build_showcase_placements() -> tuple[list[ModelPlacement], list[ModelPlacement], list[ModelPlacement]]:
    right: list[ModelPlacement] = []
    left: list[ModelPlacement] = []
    brand: list[ModelPlacement] = []

    # Right neighbor: intentional motion district with dense video walls and staggered chaos spinners.
    base_rx = 2480.0
    for idx in range(18):
        right.append(
            ModelPlacement(
                template="Spinner",
                name=f"{PREFIX}RIGHT_SPINNER_{idx + 1:02d}",
                x=base_rx + idx * 190.0,
                y=250.0 + (14.0 if idx % 2 else -12.0),
                direction=("L" if idx % 2 == 0 else "R"),
                start_side=("B" if idx % 3 else "T"),
                parm1=2 + (idx % 2),
                parm2=18 + (idx % 4),
                parm3=8 + (idx % 3),
                scale_x=15.0 + (idx % 5) * 1.3,
                scale_y=10.0 + (idx % 4) * 0.9,
            )
        )
    for idx in range(10):
        right.append(
            ModelPlacement(
                template="Arches",
                name=f"{PREFIX}RIGHT_TUNNEL_ARCH_{idx + 1:02d}",
                x=2580.0 + idx * 230.0,
                y=565.0 + math.sin(idx * 0.55) * 26.0,
                parm1=8,
                parm2=72,
                x2=220.0 + idx * 10.0,
                y2=-5.0 + ((idx % 2) * 1.2),
                direction=("L" if idx % 2 == 0 else "R"),
            )
        )
    tree_idx = 1
    for row in range(2):
        for col in range(7):
            right.append(
                ModelPlacement(
                    template=("Tree-2" if row == 0 else "Tree-3" if col % 2 == 0 else "Tree"),
                    name=f"{PREFIX}RIGHT_MEGA_TREE_{tree_idx:02d}",
                    x=2520.0 + col * 265.0,
                    y=980.0 + row * 230.0 + (18.0 if col % 2 else -10.0),
                    parm1=22 + row * 2,
                    parm2=98 + col * 6,
                    scale_x=2.45 + row * 0.2,
                    scale_y=2.25 + row * 0.18,
                )
            )
            tree_idx += 1
    for idx in range(6):
        right.append(
            ModelPlacement(
                template="Sphere",
                name=f"{PREFIX}RIGHT_GLOBE_{idx + 1:02d}",
                x=2640.0 + idx * 420.0,
                y=1570.0 + (-55.0 if idx % 2 else 40.0),
                parm1=18 + (idx % 3) * 2,
                parm2=20 + (idx % 4) * 2,
                scale_x=205.0 + idx * 14.0,
                scale_y=104.0 + idx * 8.0,
            )
        )
    for idx in range(12):
        right.append(
            ModelPlacement(
                template="Star-2",
                name=f"{PREFIX}RIGHT_STAR_{idx + 1:02d}",
                x=2520.0 + idx * 205.0,
                y=1780.0 + (34.0 if idx % 2 else -18.0),
                parm2=56 + (idx % 5) * 8,
                scale_x=10.2 + (idx % 4) * 1.7,
                scale_y=9.8 + (idx % 3) * 1.5,
            )
        )
    for row in range(2):
        for col in range(4):
            idx = row * 4 + col + 1
            right.append(
                ModelPlacement(
                    template=("Matrix-3" if col % 2 == 0 else "Matrix-2"),
                    name=f"{PREFIX}RIGHT_VIDEO_WALL_{idx:02d}",
                    x=2550.0 + col * 470.0,
                    y=760.0 + row * 285.0,
                    parm1=96,
                    parm2=64,
                    display_as="Horiz Matrix",
                    scale_x=1.05,
                    scale_y=1.05,
                )
            )
    for idx in range(4):
        right.append(
            ModelPlacement(
                template="Matrix-2",
                name=f"{PREFIX}RIGHT_SINGING_FACE_{idx + 1:02d}_PANEL",
                x=2660.0 + idx * 360.0,
                y=1320.0,
                parm1=34,
                parm2=52,
                display_as="Horiz Matrix",
            )
        )
    for idx in range(6):
        right.append(
            ModelPlacement(
                template="Single Line-5",
                name=f"{PREFIX}RIGHT_WAVE_LINE_{idx + 1:02d}",
                x=2520.0 + idx * 520.0,
                y=660.0 + (idx % 2) * 36.0,
                parm2=240 + idx * 28,
                x2=420.0,
                y2=-165.0 + (idx % 3) * 55.0,
                direction=("R" if idx % 2 else "L"),
            )
        )

    # Branded/custom preview props.
    brand.append(
        ModelPlacement(
            template="Matrix-2",
            name=f"{PREFIX}RIGHT_HH_ICON_IMAGE",
            x=3560.0,
            y=860.0,
            parm1=64,
            parm2=64,
            display_as="Image",
            image_file="hh.png",
        )
    )
    brand.append(
        ModelPlacement(
            template="Matrix-3",
            name=f"{PREFIX}RIGHT_HELIXMASCOT_IMAGE",
            x=4050.0,
            y=860.0,
            parm1=84,
            parm2=56,
            display_as="Image",
            image_file="helixmascot.jpg",
        )
    )
    brand.append(
            ModelPlacement(
                template="Matrix-2",
                name=f"{PREFIX}RIGHT_HH_ICON_CUSTOM",
                x=3560.0,
                y=640.0,
                parm1=56,
                parm2=56,
                display_as="Custom",
                string_type="RGB Nodes",
            )
        )
    brand.append(
            ModelPlacement(
                template="Matrix-2",
                name=f"{PREFIX}RIGHT_HELIXMASCOT_CUSTOM",
                x=4050.0,
                y=640.0,
                parm1=78,
                parm2=46,
                display_as="Custom",
                string_type="RGB Nodes",
            )
        )
    brand.append(
            ModelPlacement(
                template="Spinner",
                name=f"{PREFIX}RIGHT_HELIX_SPIN_A",
                x=3910.0,
                y=760.0,
                direction="L",
                parm1=3,
                parm2=20,
                parm3=9,
                scale_x=18.0,
                scale_y=12.5,
            )
        )
    brand.append(
            ModelPlacement(
                template="Spinner",
                name=f"{PREFIX}RIGHT_HELIX_SPIN_B",
                x=4180.0,
                y=760.0,
                direction="R",
                parm1=3,
                parm2=20,
                parm3=9,
                scale_x=18.0,
                scale_y=12.5,
            )
        )
    helix_letters = ["H", "E", "L", "I", "X"]
    for idx, letter in enumerate(helix_letters):
        brand.append(
            ModelPlacement(
                template="Matrix-4",
                name=f"{PREFIX}WORD_HELIX_{letter}",
                x=3090.0 + idx * 242.0,
                y=1940.0,
                parm1=18,
                parm2=28,
                scale_x=12.0,
                scale_y=20.0,
            )
        )

    # Left neighbor: artistic matrix district with tunnel motion and layered architecture.
    led_idx = 1
    for row in range(3):
        for col in range(6):
            template = ("Matrix", "Matrix-2", "Matrix-4", "Matrix-3")[(row + col) % 4]
            left.append(
                ModelPlacement(
                    template=template,
                    name=f"{PREFIX}LEFT_MATRIX_{led_idx:02d}",
                    x=-2880.0 - col * 430.0,
                    y=930.0 + row * 260.0 + (22.0 if col % 2 else -12.0),
                    parm1=72,
                    parm2=56,
                    display_as="Horiz Matrix",
                    scale_x=1.05,
                    scale_y=1.05,
                )
            )
            led_idx += 1
    for row in range(2):
        for col in range(5):
            idx = row * 5 + col + 1
            left.append(
                ModelPlacement(
                    template="Matrix-3",
                    name=f"{PREFIX}LEFT_TOWER_{idx:02d}",
                    x=-3010.0 - col * 520.0,
                    y=640.0 + row * 620.0,
                    parm1=48,
                    parm2=96,
                    display_as="Horiz Matrix",
                )
            )
    for idx in range(10):
        left.append(
            ModelPlacement(
                template="Window Frame",
                name=f"{PREFIX}LEFT_WINDOW_{idx + 1:02d}",
                x=-2930.0 - idx * 360.0,
                y=1510.0 - (idx % 2) * 90.0,
                parm1=24,
                parm2=58,
                parm3=24,
                scale_x=36.0 + idx * 2.2,
                scale_y=10.0 + idx * 0.7,
            )
        )
    for idx in range(16):
        left.append(
            ModelPlacement(
                template="Candy Canes",
                name=f"{PREFIX}LEFT_CANE_SET_{idx + 1:02d}",
                x=-2780.0 - idx * 225.0,
                y=210.0 + (idx % 4) * 34.0,
                parm1=10,
                parm2=56,
                x2=265.0,
                y2=-7.0,
                direction=("L" if idx % 2 == 0 else "R"),
            )
        )
    for idx in range(16):
        left.append(
            ModelPlacement(
                template="Arches",
                name=f"{PREFIX}LEFT_ARCH_{idx + 1:02d}",
                x=-2860.0 - idx * 210.0,
                y=510.0 + (idx % 3) * 38.0,
                parm1=8,
                parm2=72,
                x2=210.0 + idx * 7.0,
                y2=-4.5,
                direction=("R" if idx % 2 == 0 else "L"),
            )
        )
    for idx in range(8):
        left.append(
            ModelPlacement(
                template="wreath 1 2 white",
                name=f"{PREFIX}LEFT_CIRCLE_{idx + 1:02d}",
                x=-3220.0 - idx * 260.0,
                y=1260.0 - (idx % 3) * 90.0,
                display_as="Circle",
                string_type="RGB Nodes",
            )
        )
    for idx in range(12):
        left.append(
            ModelPlacement(
                template="Single Line-5",
                name=f"{PREFIX}LEFT_ROOFLINE_{idx + 1:02d}",
                x=-2600.0 - idx * 330.0,
                y=760.0 + (idx % 4) * 30.0,
                parm2=220 + idx * 24,
                x2=360.0 + idx * 22.0,
                y2=-130.0 + (idx % 3) * 42.0,
                direction=("L" if idx % 2 == 0 else "R"),
            )
        )
    for idx in range(10):
        left.append(
            ModelPlacement(
                template="Poly Line",
                name=f"{PREFIX}LEFT_TUNNEL_LINE_{idx + 1:02d}",
                x=-3180.0 - idx * 245.0,
                y=336.0 + idx * 20.0,
                parm2=140 + idx * 16,
                direction=("R" if idx % 2 == 0 else "L"),
                scale_x=1.0 + idx * 0.1,
                scale_y=1.0 + idx * 0.08,
            )
        )
    for idx in range(12):
        left.append(
            ModelPlacement(
                template=("Tree-3", "Tree", "Tree-2")[idx % 3],
                name=f"{PREFIX}LEFT_TREE_{idx + 1:02d}",
                x=-2850.0 - idx * 330.0,
                y=1710.0 - (idx % 4) * 65.0,
                parm1=20 + (idx % 3) * 2,
                parm2=94 + idx * 4,
                scale_x=2.4 + (idx % 3) * 0.16,
                scale_y=2.3 + (idx % 4) * 0.15,
            )
        )
    for idx in range(10):
        left.append(
            ModelPlacement(
                template="Star-2",
                name=f"{PREFIX}LEFT_STAR_{idx + 1:02d}",
                x=-3000.0 - idx * 340.0,
                y=1940.0 + (idx % 2) * 22.0,
                parm2=62 + (idx % 4) * 8,
                scale_x=9.4 + (idx % 3) * 1.4,
                scale_y=9.1 + (idx % 2) * 1.3,
            )
        )
    return right, left, brand


def run() -> int:
    if not LAYOUT_PATH.exists():
        raise SystemExit(f"Layout file not found: {LAYOUT_PATH}")

    if not BACKUP_PATH.exists():
        BACKUP_PATH.write_bytes(LAYOUT_PATH.read_bytes())
        print(f"Backup saved: {BACKUP_PATH}")

    tree = ET.parse(LAYOUT_PATH)
    root = tree.getroot()
    models_el = root.find("models")
    groups_el = root.find("modelGroups")
    if models_el is None:
        raise SystemExit("Layout has no <models> section.")
    if groups_el is None:
        groups_el = ET.SubElement(root, "modelGroups")

    existing_models = list(models_el)
    template_map = {model.attrib.get("name", "").strip(): model for model in existing_models if model.attrib.get("name", "").strip()}

    required = [
        "Spinner",
        "Sphere",
        "Arches",
        "Candy Canes",
        "Tree",
        "Tree-2",
        "Tree-3",
        "Matrix",
        "Matrix-2",
        "Matrix-3",
        "Matrix-4",
        "Window Frame",
        "Single Line-5",
        "Poly Line",
        "Star-2",
        "wreath 1 2 white",
    ]
    missing = [name for name in required if name not in template_map]
    if missing:
        raise SystemExit("Missing required template models: " + ", ".join(missing))

    # Remove prior generated neighbor models/groups for idempotent runs.
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

    right, left, brand = build_showcase_placements()
    all_new = right + left + brand
    channel_cursor = next_start_channel(list(models_el))

    created_names: list[str] = []
    for placement in all_new:
        template = template_map[placement.template]
        model = clone_model(template, placement, channel_cursor)
        models_el.append(model)
        created_names.append(placement.name)
        channel_cursor += estimate_channels(dict(model.attrib)) + 9

    right_names = [item.name for item in right] + [item.name for item in brand if item.name.startswith(f"{PREFIX}RIGHT_")]
    left_names = [item.name for item in left]
    brand_names = [item.name for item in brand]
    spinner_names = [item.name for item in all_new if "SPINNER" in item.name or "HELIX_SPIN" in item.name]
    singing_face_names = [item.name for item in all_new if "SINGING_FACE" in item.name]
    matrix_names = [item.name for item in all_new if "MATRIX" in item.name or item.name.endswith(("_H", "_E", "_L", "_I", "_X"))]
    arch_names = [item.name for item in all_new if "_ARCH_" in item.name]
    tree_names = [item.name for item in all_new if "_TREE_" in item.name]

    groups_el.append(make_group(f"{PREFIX}RIGHT_NEIGHBOR", right_names, center_for(right + brand)))
    groups_el.append(make_group(f"{PREFIX}LEFT_NEIGHBOR", left_names, center_for(left)))
    groups_el.append(make_group(f"{PREFIX}ICON_AND_BRAND", brand_names, center_for(brand)))
    groups_el.append(make_group(f"{PREFIX}CHAOS_SPINNERS", spinner_names, center_for([item for item in all_new if item.name in spinner_names])))
    groups_el.append(make_group(f"{PREFIX}SINGING_FACES", singing_face_names, center_for([item for item in all_new if item.name in singing_face_names])))
    groups_el.append(make_group(f"{PREFIX}MATRIX_DISTRICT", matrix_names, center_for([item for item in all_new if item.name in matrix_names])))
    groups_el.append(make_group(f"{PREFIX}ARCH_RIVER", arch_names, center_for([item for item in all_new if item.name in arch_names])))
    groups_el.append(make_group(f"{PREFIX}MEGA_FOREST", tree_names, center_for([item for item in all_new if item.name in tree_names])))
    groups_el.append(make_group(f"{PREFIX}ALL_MODELS", created_names, center_for(all_new)))

    try:
        ET.indent(tree, space="  ")
    except Exception:
        pass
    tree.write(LAYOUT_PATH, encoding="utf-8", xml_declaration=True)
    print(f"Neighbor showcase layout saved: {LAYOUT_PATH}")
    print(f"Generated models: {len(created_names)}")
    print(f"Group additions: 9")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
