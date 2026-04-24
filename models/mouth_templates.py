from __future__ import annotations

from models.grid_canvas import Coord, MouthShapeTemplate


MOUTH_ALIASES = {
    "mouth_A": ["A", "AH", "AA", "AE"],
    "mouth_E": ["E", "EH", "EE"],
    "mouth_I": ["I", "IH", "Y"],
    "mouth_O": ["O", "OH", "OW"],
    "mouth_U": ["U", "UW", "OO"],
    "mouth_MBP": ["M", "B", "P", "MBP"],
}


def _ellipse(width: int, height: int, cx: float, cy: float, rx: float, ry: float, *, fill: bool = True) -> set[Coord]:
    coords: set[Coord] = set()
    for y in range(height):
        for x in range(width):
            value = ((x - cx) / max(rx, 0.001)) ** 2 + ((y - cy) / max(ry, 0.001)) ** 2
            if (value <= 1.0) if fill else (0.68 <= value <= 1.18):
                coords.add((x, y))
    return coords


def _line(width: int, y: int, x0: int, x1: int, thickness: int = 1) -> set[Coord]:
    coords: set[Coord] = set()
    for yy in range(y - thickness // 2, y + thickness // 2 + 1):
        for x in range(x0, x1 + 1):
            coords.add((x, yy))
    return coords


def default_mouth_box(canvas_size: int = 64, scale: float = 1.0) -> tuple[int, int]:
    base_w = 18 if canvas_size >= 64 else 14 if canvas_size >= 48 else 10
    base_h = 12 if canvas_size >= 64 else 9 if canvas_size >= 48 else 7
    return max(5, int(round(base_w * scale))), max(3, int(round(base_h * scale)))


def generate_mouth_shape(name: str, box_width: int, box_height: int) -> MouthShapeTemplate:
    w = max(3, int(box_width))
    h = max(3, int(box_height))
    cx = (w - 1) / 2.0
    cy = (h - 1) / 2.0
    if name == "mouth_A":
        coords = _ellipse(w, h, cx, cy, max(2.0, w * 0.28), max(2.0, h * 0.45), fill=True)
        tags = ["tall", "open", "oval"]
    elif name == "mouth_E":
        coords = _ellipse(w, h, cx, cy, max(2.0, w * 0.42), max(1.5, h * 0.28), fill=True)
        tags = ["wide", "open"]
    elif name == "mouth_I":
        coords = _ellipse(w, h, cx, cy + h * 0.08, max(2.0, w * 0.38), max(1.0, h * 0.16), fill=True)
        tags = ["narrow", "smile"]
    elif name == "mouth_O":
        coords = _ellipse(w, h, cx, cy, max(2.0, min(w, h) * 0.34), max(2.0, min(w, h) * 0.34), fill=True)
        tags = ["round", "open"]
    elif name == "mouth_U":
        coords = _ellipse(w, h, cx, cy, max(1.5, w * 0.22), max(1.5, h * 0.30), fill=True)
        tags = ["narrow", "rounded"]
    elif name == "mouth_MBP":
        coords = _line(w, int(round(cy)), max(0, int(w * 0.20)), min(w - 1, int(w * 0.80)), thickness=max(1, h // 8))
        tags = ["closed", "line"]
    else:
        raise ValueError(f"Unknown mouth shape: {name}")
    clean = sorted((x, y) for x, y in coords if 0 <= x < w and 0 <= y < h)
    xs = [x for x, _ in clean] or [0]
    ys = [y for _, y in clean] or [0]
    return MouthShapeTemplate(
        name=name,
        phoneme_aliases=MOUTH_ALIASES[name],
        coordinates=clean,
        bounding_box=(min(xs), min(ys), max(xs), max(ys)),
        style_tags=tags,
    )


def generate_mouth_library(canvas_size: int = 64, scale: float = 1.0) -> dict[str, MouthShapeTemplate]:
    box = default_mouth_box(canvas_size, scale)
    return {name: generate_mouth_shape(name, *box) for name in MOUTH_ALIASES}


def place_mouth_shape(
    shape: MouthShapeTemplate,
    *,
    anchor: Coord,
    box_width: int,
    box_height: int,
    offset: Coord = (0, 0),
) -> list[Coord]:
    ax, ay = anchor
    ox, oy = offset
    left = int(round(ax - box_width / 2 + ox))
    top = int(round(ay - box_height / 2 + oy))
    return sorted({(left + x, top + y) for x, y in shape.coordinates})
