from __future__ import annotations

import math
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class VisibleBandModel:
    name: str
    width: int
    height: int
    x: float
    y: float
    z: float
    submodels: tuple[tuple[str, int], ...]
    role: str


VISIBLE_BAND_MODELS: tuple[VisibleBandModel, ...] = (
    VisibleBandModel(
        "HX_SNOWMAN_BASSIST_BODY",
        52,
        80,
        260.0,
        -30.0,
        18.0,
        (
            ("HX_SNOWMAN_BASSIST_HEAD", 40),
            ("HX_SNOWMAN_BASSIST_FACE", 18),
            ("HX_SNOWMAN_BASSIST_HAT", 20),
            ("HX_SNOWMAN_BASSIST_SCARF", 20),
            ("HX_SNOWMAN_BASSIST_TORSO", 72),
            ("HX_SNOWMAN_BASSIST_ARMS", 44),
            ("HX_SNOWMAN_BASSIST_BUTTONS", 9),
        ),
        "body",
    ),
    VisibleBandModel(
        "HX_SNOWMAN_BASSIST_INSTRUMENT",
        62,
        78,
        278.0,
        -30.0,
        20.0,
        (
            ("HX_SNOWMAN_BASSIST_BASS_BODY", 112),
            ("HX_SNOWMAN_BASSIST_BASS_NECK", 56),
            ("HX_SNOWMAN_BASSIST_BASS_SCROLL", 18),
            ("HX_SNOWMAN_BASSIST_BASS_STRINGS", 76),
            ("HX_SNOWMAN_BASSIST_PLUCK_ZONE", 28),
            ("HX_SNOWMAN_BASSIST_BASS_BRIDGE", 18),
        ),
        "bass",
    ),
    VisibleBandModel(
        "HX_SNOWMAN_DRUMMER_BODY",
        54,
        78,
        330.0,
        -36.0,
        18.0,
        (
            ("HX_SNOWMAN_DRUMMER_HEAD", 40),
            ("HX_SNOWMAN_DRUMMER_FACE", 18),
            ("HX_SNOWMAN_DRUMMER_HAT", 20),
            ("HX_SNOWMAN_DRUMMER_SCARF", 20),
            ("HX_SNOWMAN_DRUMMER_TORSO", 72),
            ("HX_SNOWMAN_DRUMMER_ARMS", 54),
            ("HX_SNOWMAN_DRUMMER_BUTTONS", 9),
        ),
        "body",
    ),
    VisibleBandModel(
        "HX_SNOWMAN_DRUMMER_INSTRUMENT",
        90,
        72,
        330.0,
        -58.0,
        16.0,
        (
            ("HX_SNOWMAN_DRUMMER_KICK", 72),
            ("HX_SNOWMAN_DRUMMER_SNARE", 28),
            ("HX_SNOWMAN_DRUMMER_TOM", 44),
            ("HX_SNOWMAN_DRUMMER_CYMBALS", 44),
            ("HX_SNOWMAN_DRUMMER_HI_HAT", 24),
            ("HX_SNOWMAN_DRUMMER_STICKS", 24),
        ),
        "drums",
    ),
    VisibleBandModel(
        "HX_SNOWMAN_GUITARIST_BODY",
        52,
        80,
        400.0,
        -30.0,
        18.0,
        (
            ("HX_SNOWMAN_GUITARIST_HEAD", 40),
            ("HX_SNOWMAN_GUITARIST_FACE", 18),
            ("HX_SNOWMAN_GUITARIST_HAT", 20),
            ("HX_SNOWMAN_GUITARIST_SCARF", 20),
            ("HX_SNOWMAN_GUITARIST_TORSO", 72),
            ("HX_SNOWMAN_GUITARIST_ARMS", 44),
            ("HX_SNOWMAN_GUITARIST_BUTTONS", 9),
        ),
        "body",
    ),
    VisibleBandModel(
        "HX_SNOWMAN_GUITARIST_INSTRUMENT",
        64,
        74,
        416.0,
        -30.0,
        20.0,
        (
            ("HX_SNOWMAN_GUITARIST_GUITAR_BODY", 62),
            ("HX_SNOWMAN_GUITARIST_GUITAR_NECK", 40),
            ("HX_SNOWMAN_GUITARIST_GUITAR_STRINGS", 72),
            ("HX_SNOWMAN_GUITARIST_STRUM_ZONE", 24),
        ),
        "guitar",
    ),
    VisibleBandModel(
        "HX_SNOWMAN_SINGER_BODY",
        54,
        86,
        305.0,
        18.0,
        22.0,
        (
            ("HX_SNOWMAN_SINGER_HEAD", 44),
            ("HX_SNOWMAN_SINGER_FACE", 18),
            ("HX_SNOWMAN_SINGER_MOUTH", 16),
            ("HX_SNOWMAN_SINGER_HAT", 20),
            ("HX_SNOWMAN_SINGER_SCARF", 20),
            ("HX_SNOWMAN_SINGER_TORSO", 78),
            ("HX_SNOWMAN_SINGER_ARMS", 54),
            ("HX_SNOWMAN_SINGER_BUTTONS", 9),
        ),
        "body",
    ),
    VisibleBandModel(
        "HX_SNOWMAN_SINGER_INSTRUMENT",
        34,
        82,
        330.0,
        18.0,
        24.0,
        (("HX_SNOWMAN_SINGER_MICROPHONE", 26), ("HX_SNOWMAN_SINGER_MIC_STAND", 32)),
        "microphone",
    ),
    VisibleBandModel(
        "HX_SNOWMAN_SINGER_FEMALE_BODY",
        56,
        86,
        360.0,
        18.0,
        22.0,
        (
            ("HX_SNOWMAN_SINGER_FEMALE_HEAD", 44),
            ("HX_SNOWMAN_SINGER_FEMALE_FACE", 18),
            ("HX_SNOWMAN_SINGER_FEMALE_MOUTH", 16),
            ("HX_SNOWMAN_SINGER_FEMALE_BOW", 20),
            ("HX_SNOWMAN_SINGER_FEMALE_SCARF", 20),
            ("HX_SNOWMAN_SINGER_FEMALE_TORSO", 78),
            ("HX_SNOWMAN_SINGER_FEMALE_ARMS", 54),
            ("HX_SNOWMAN_SINGER_FEMALE_BUTTONS", 9),
        ),
        "body",
    ),
    VisibleBandModel(
        "HX_SNOWMAN_SINGER_FEMALE_INSTRUMENT",
        34,
        82,
        386.0,
        18.0,
        24.0,
        (("HX_SNOWMAN_SINGER_FEMALE_MICROPHONE", 26), ("HX_SNOWMAN_SINGER_FEMALE_MIC_STAND", 32)),
        "microphone",
    ),
)


def _blank_grid(width: int, height: int) -> list[list[str]]:
    return [["." for _ in range(width)] for _ in range(height)]


def _put(grid: list[list[str]], x: int, y: int, value: int) -> None:
    if 0 <= y < len(grid) and 0 <= x < len(grid[y]):
        grid[y][x] = str(value)


def _ellipse_points(cx: float, cy: float, rx: float, ry: float, count: int) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    for idx in range(count):
        angle = math.tau * idx / max(1, count)
        out.append((int(round(cx + math.cos(angle) * rx)), int(round(cy + math.sin(angle) * ry))))
    return out


def _line_points(x1: float, y1: float, x2: float, y2: float, count: int) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    for idx in range(count):
        ratio = 0.0 if count <= 1 else idx / (count - 1)
        out.append((int(round(x1 + (x2 - x1) * ratio)), int(round(y1 + (y2 - y1) * ratio))))
    return out


def _points_for_count(
    seed_points: list[tuple[int, int]],
    width: int,
    height: int,
    count: int,
    used: set[tuple[int, int]],
) -> list[tuple[int, int]]:
    """Return exactly count visible, non-overlapping points when the grid permits."""
    points: list[tuple[int, int]] = []
    seen = set(used)
    for x, y in seed_points:
        if 0 <= x < width and 0 <= y < height and (x, y) not in seen:
            seen.add((x, y))
            points.append((x, y))
            if len(points) == count:
                return points

    if seed_points:
        cx = sum(x for x, _ in seed_points) / len(seed_points)
        cy = sum(y for _, y in seed_points) / len(seed_points)
    else:
        cx = width * 0.5
        cy = height * 0.5
    candidates = [(x, y) for y in range(height) for x in range(width) if (x, y) not in seen]
    candidates.sort(key=lambda p: ((p[0] - cx) ** 2 + (p[1] - cy) ** 2, p[1], p[0]))
    for point in candidates:
        points.append(point)
        if len(points) == count:
            return points
    return points


def _body_points(name: str, width: int, height: int, submodel: str, count: int) -> list[tuple[int, int]]:
    cx = width * 0.5
    if submodel.endswith("_HEAD"):
        return _ellipse_points(cx, height * 0.22, width * 0.18, height * 0.11, count)
    if submodel.endswith("_FACE"):
        return _ellipse_points(cx, height * 0.23, width * 0.09, height * 0.05, count)
    if submodel.endswith("_MOUTH"):
        return _ellipse_points(cx, height * 0.27, width * 0.07, height * 0.025, count)
    if submodel.endswith("_HAT"):
        return _line_points(cx - width * 0.18, height * 0.10, cx + width * 0.18, height * 0.10, count)
    if submodel.endswith("_BOW"):
        return _ellipse_points(cx + width * 0.15, height * 0.10, width * 0.10, height * 0.05, count)
    if submodel.endswith("_SCARF"):
        return _line_points(cx - width * 0.24, height * 0.36, cx + width * 0.24, height * 0.37, count)
    if submodel.endswith("_TORSO"):
        return _ellipse_points(cx, height * 0.58, width * 0.26, height * 0.24, count)
    if submodel.endswith("_ARMS"):
        half = max(2, count // 2)
        left = _line_points(cx - width * 0.16, height * 0.42, cx - width * 0.44, height * 0.56, half)
        right = _line_points(cx + width * 0.16, height * 0.42, cx + width * 0.44, height * 0.30, count - half)
        return left + right
    if submodel.endswith("_BUTTONS"):
        return _line_points(cx, height * 0.45, cx, height * 0.72, count)
    return _ellipse_points(cx, height * 0.50, width * 0.18, height * 0.18, count)


def _instrument_points(role: str, width: int, height: int, submodel: str, count: int) -> list[tuple[int, int]]:
    cx = width * 0.5
    if role == "drums":
        if submodel.endswith("_KICK"):
            return _ellipse_points(cx, height * 0.62, width * 0.18, height * 0.19, count)
        if submodel.endswith("_SNARE"):
            return _ellipse_points(width * 0.30, height * 0.52, width * 0.11, height * 0.08, count)
        if submodel.endswith("_TOM"):
            left = _ellipse_points(width * 0.45, height * 0.42, width * 0.08, height * 0.07, count // 2)
            right = _ellipse_points(width * 0.60, height * 0.42, width * 0.08, height * 0.07, count - len(left))
            return left + right
        if submodel.endswith("_CYMBALS"):
            left = _ellipse_points(width * 0.22, height * 0.26, width * 0.13, height * 0.04, count // 2)
            right = _ellipse_points(width * 0.78, height * 0.26, width * 0.13, height * 0.04, count - len(left))
            return left + right
        if submodel.endswith("_HI_HAT"):
            return _ellipse_points(width * 0.22, height * 0.42, width * 0.10, height * 0.03, count)
        if submodel.endswith("_STICKS"):
            return _line_points(width * 0.36, height * 0.12, width * 0.58, height * 0.36, count // 2) + _line_points(
                width * 0.68, height * 0.12, width * 0.48, height * 0.36, count - (count // 2)
            )
    if role == "bass":
        if "BODY" in submodel:
            return _ellipse_points(width * 0.45, height * 0.62, width * 0.18, height * 0.25, count)
        if "NECK" in submodel:
            return _line_points(width * 0.50, height * 0.10, width * 0.50, height * 0.58, count)
        if "SCROLL" in submodel:
            return _ellipse_points(width * 0.50, height * 0.09, width * 0.10, height * 0.06, count)
        if "STRINGS" in submodel:
            rows = 4
            points: list[tuple[int, int]] = []
            base = count // rows
            for row in range(rows):
                n = base + (1 if row < count % rows else 0)
                x = width * (0.45 + row * 0.035)
                points.extend(_line_points(x, height * 0.14, x, height * 0.84, n))
            return points
        if "PLUCK_ZONE" in submodel:
            return _ellipse_points(width * 0.55, height * 0.56, width * 0.09, height * 0.08, count)
        if "BRIDGE" in submodel:
            return _line_points(width * 0.34, height * 0.72, width * 0.62, height * 0.72, count)
    if role == "guitar":
        if "BODY" in submodel:
            return _ellipse_points(width * 0.36, height * 0.66, width * 0.20, height * 0.20, count)
        if "NECK" in submodel:
            return _line_points(width * 0.50, height * 0.48, width * 0.92, height * 0.16, count)
        if "STRINGS" in submodel:
            rows = 6
            points: list[tuple[int, int]] = []
            base = count // rows
            for row in range(rows):
                n = base + (1 if row < count % rows else 0)
                points.extend(_line_points(width * 0.28, height * (0.58 + row * 0.035), width * 0.90, height * (0.18 + row * 0.012), n))
            return points
        if "PLUCK_ZONE" in submodel or "STRUM_ZONE" in submodel:
            return _ellipse_points(width * 0.39, height * 0.60, width * 0.10, height * 0.07, count)
    if role == "microphone":
        if submodel.endswith("_MICROPHONE"):
            return _ellipse_points(width * 0.50, height * 0.20, width * 0.12, height * 0.08, count)
        if submodel.endswith("_MIC_STAND"):
            return _line_points(width * 0.50, height * 0.26, width * 0.50, height * 0.88, count)
    return _ellipse_points(cx, height * 0.50, width * 0.16, height * 0.12, count)


def custom_model_for_visible_band(model: VisibleBandModel) -> str:
    grid = _blank_grid(model.width, model.height)
    cursor = 1
    used: set[tuple[int, int]] = set()
    for submodel, count in model.submodels:
        if model.role == "body":
            seed_points = _body_points(model.name, model.width, model.height, submodel, count)
        else:
            seed_points = _instrument_points(model.role, model.width, model.height, submodel, count)
        points = _points_for_count(seed_points, model.width, model.height, count, used)
        for x, y in points:
            _put(grid, x, y, cursor)
            used.add((x, y))
            cursor += 1
    return ";".join(",".join(row) for row in grid)


def _line_ranges(model: VisibleBandModel) -> list[tuple[str, int, int]]:
    cursor = 1
    ranges: list[tuple[str, int, int]] = []
    for name, count in model.submodels:
        ranges.append((name, cursor, cursor + count - 1))
        cursor += count
    return ranges


def _add_visible_band_model(models_el: ET.Element, spec: VisibleBandModel) -> ET.Element:
    return ET.SubElement(
        models_el,
        "model",
        {
            "name": spec.name,
            "DisplayAs": "Custom",
            "WorldPosX": f"{spec.x:.3f}",
            "WorldPosY": f"{spec.y:.3f}",
            "WorldPosZ": f"{spec.z:.3f}",
            "X2": "24.000",
            "Y2": "18.000",
            "Z2": "0.000",
            "StartChannel": "1",
            "StringType": "RGB Nodes",
        },
    )


def upgrade_visible_band_models(layout_path: Path, *, create_missing: bool = False) -> dict[str, object]:
    tree = ET.parse(layout_path)
    root = tree.getroot()
    models_el = root.find("models")
    if models_el is None:
        models_el = ET.SubElement(root, "models")
    by_name = {model.attrib.get("name", ""): model for model in root.findall(".//model")}
    upgraded: list[str] = []
    missing: list[str] = []
    for spec in VISIBLE_BAND_MODELS:
        model = by_name.get(spec.name)
        if model is None:
            if not create_missing:
                missing.append(spec.name)
                continue
            model = _add_visible_band_model(models_el, spec)
            by_name[spec.name] = model
        model.attrib.update(
            {
                "DisplayAs": "Custom",
                "LayoutGroup": "Default",
                "Controller": "No Controller",
                "WorldPosX": f"{spec.x:.3f}",
                "WorldPosY": f"{spec.y:.3f}",
                "WorldPosZ": f"{spec.z:.3f}",
                "X2": f"{spec.width * 0.72:.3f}",
                "Y2": f"{spec.height * 0.72:.3f}",
                "Z2": "0.000",
                "StringType": "RGB Nodes",
                "StartSide": "B",
                "Dir": "L",
                "Antialias": "1",
                "PixelSize": "3",
                "Transparency": "0",
                "parm1": str(spec.width),
                "parm2": str(spec.height),
                "parm3": "1",
                "versionNumber": "7",
                "CustomWidth": str(spec.width),
                "CustomHeight": str(spec.height),
                "CustomModel": custom_model_for_visible_band(spec),
                "CustomModelCompressed": "",
                "HelixVisibleBandUpgrade": "split_models_v1",
            }
        )
        for child in list(model):
            if child.tag == "subModel":
                model.remove(child)
        for submodel, start, end in _line_ranges(spec):
            ET.SubElement(model, "subModel", {"name": submodel, "line0": f"{start}-{end}", "HelixPixelCount": str(end - start + 1)})
        if model.find("ControllerConnection") is None:
            ET.SubElement(model, "ControllerConnection")
        upgraded.append(spec.name)
    tree.write(layout_path, encoding="utf-8", xml_declaration=True)
    return {"layout": str(layout_path), "upgraded": upgraded, "missing": missing}
