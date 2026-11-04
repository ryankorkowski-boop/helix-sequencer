#!/usr/bin/env python3
"""Generate clean-room xLights layout fixtures for the Helix layout test bench.

The fixtures are synthetic. They use common hobbyist model types and names so
the master profile can discover arches, canes, trees, faces, and groups.
They do not copy any existing show, sequence, or copyrighted layout.
"""

from __future__ import annotations

import json
import math
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core import model_parser as xmp  # noqa: E402


OUT_DIR = ROOT / "fixtures" / "layout_bench"

# Preview tint that does not collide with the parser's exact red/green/white checks.
RGB_TINT = {
    "roof": "#FFB000",
    "arch": "#3DDCFF",
    "cane": "#FF4FA3",
    "tree": "#39E07A",
    "mini": "#2EC4B6",
    "window": "#F4F1DE",
    "matrix": "#7AA2FF",
    "star": "#FFE56B",
    "flake": "#D6E4FF",
    "mega": "#C77DFF",
    "spin": "#FF7A3C",
    "ring": "#5EEAD4",
    "face": "#FFD0A8",
    "helix": "#E879F9",
    "spiral": "#67E8F9",
    "stage": "#F8C8DC",
    "flood": "#B8F2FF",
    "line": "#9AE6B4",
    "drum": "#F6AD55",
}


def _pts(*pairs: tuple[float, float, float]) -> list[tuple[float, float, float]]:
    return [(float(x), float(y), float(z)) for x, y, z in pairs]


def line(x1: float, y1: float, x2: float, y2: float, z: float = 0.0, steps: int = 2) -> list[tuple[float, float, float]]:
    return [
        (x1 + (x2 - x1) * i / (steps - 1), y1 + (y2 - y1) * i / (steps - 1), z)
        for i in range(steps)
    ]


def rect(x: float, y: float, w: float, h: float, z: float = 0.0) -> list[tuple[float, float, float]]:
    return _pts(
        (x, y, z),
        (x + w, y, z),
        (x + w, y + h, z),
        (x, y + h, z),
        (x, y, z),
    )


def arc(cx: float, cy: float, width: float, height: float, steps: int = 9) -> list[tuple[float, float, float]]:
    pts = []
    for i in range(steps):
        t = i / (steps - 1)
        ang = math.pi * (1.0 - t)
        pts.append((cx + math.cos(ang) * width / 2.0, cy + math.sin(ang) * height, 0.0))
    return pts


def arc_section(cx: float, cy: float, width: float, height: float, sec: int, secs: int, steps: int = 7) -> list[tuple[float, float, float]]:
    pts = []
    for i in range(steps):
        t = (sec - 1 + i / (steps - 1)) / secs
        ang = math.pi * (1.0 - t)
        pts.append((cx + math.cos(ang) * width / 2.0, cy + math.sin(ang) * height, 0.0))
    return pts


def ellipse(cx: float, cy: float, rx: float, ry: float, z: float = 0.0, steps: int = 24) -> list[tuple[float, float, float]]:
    return [
        (cx + math.cos(math.tau * i / steps) * rx, cy + math.sin(math.tau * i / steps) * ry, z)
        for i in range(steps + 1)
    ]


def star_poly(cx: float, cy: float, r: float, tips: int = 5) -> list[tuple[float, float, float]]:
    pts = []
    for i in range(tips * 2):
        radius = r if i % 2 == 0 else r * 0.42
        ang = -math.pi / 2.0 + math.pi * i / tips
        pts.append((cx + math.cos(ang) * radius, cy + math.sin(ang) * radius, 0.0))
    pts.append(pts[0])
    return pts


def snowflake(cx: float, cy: float, r: float) -> list[tuple[float, float, float]]:
    pts: list[tuple[float, float, float]] = []
    for arm in range(6):
        ang = math.tau * arm / 6.0
        dx, dy = math.cos(ang), math.sin(ang)
        px, py = -dy, dx
        pts.extend(
            [
                (cx, cy, 0.0),
                (cx + dx * r, cy + dy * r, 0.0),
                (cx + dx * r * 0.62 + px * r * 0.22, cy + dy * r * 0.62 + py * r * 0.22, 0.0),
                (cx + dx * r * 0.62, cy + dy * r * 0.62, 0.0),
                (cx + dx * r * 0.62 - px * r * 0.22, cy + dy * r * 0.62 - py * r * 0.22, 0.0),
                (cx + dx * r, cy + dy * r, 0.0),
                (cx, cy, 0.0),
            ]
        )
    return pts


def cane(x: float, y: float, h: float = 90.0, w: float = 28.0) -> list[tuple[float, float, float]]:
    pts = [(x, y, 0.0), (x, y + h * 0.72, 0.0)]
    for i in range(8):
        ang = math.pi * i / 7.0
        pts.append((x + math.sin(ang) * w, y + h * 0.72 + (1.0 - math.cos(ang)) * w, 0.0))
    return pts


def spiral(cx: float, cy: float, radius: float, height: float, turns: float, z: float = 0.0, steps: int = 72) -> list[tuple[float, float, float]]:
    pts = []
    for i in range(steps):
        t = i / (steps - 1)
        ang = turns * math.tau * t
        r = radius * (0.12 + 0.88 * t)
        pts.append((cx + math.cos(ang) * r, cy + t * height, z + math.sin(ang) * r * 0.35))
    return pts


def helix(cx: float, cy: float, radius: float, height: float, turns: float, phase: float, steps: int = 64) -> list[tuple[float, float, float]]:
    pts = []
    for i in range(steps):
        t = i / (steps - 1)
        ang = turns * math.tau * t + phase
        pts.append((cx + math.cos(ang) * radius, cy + t * height, math.sin(ang) * radius))
    return pts


def tree_outline(x: float, y: float, w: float, h: float) -> list[tuple[float, float, float]]:
    return _pts(
        (x, y, 0),
        (x - w / 2, y, 0),
        (x, y + h, 0),
        (x + w / 2, y, 0),
        (x, y, 0),
    )


def matrix_grid(x: float, y: float, w: float, h: float, cols: int, rows: int) -> list[tuple[float, float, float]]:
    pts: list[tuple[float, float, float]] = []
    rows = max(2, min(rows, 18))
    cols = max(2, min(cols, 24))
    for r in range(rows):
        yy = y + h * r / (rows - 1)
        xs = range(cols) if r % 2 == 0 else range(cols - 1, -1, -1)
        for c in xs:
            pts.append((x + w * c / (cols - 1), yy, 0.0))
    return pts


def snowman(cx: float, cy: float, scale: float = 1.0) -> list[tuple[float, float, float]]:
    pts: list[tuple[float, float, float]] = []
    pts.extend(ellipse(cx, cy + 28 * scale, 34 * scale, 28 * scale, steps=18))
    pts.extend(ellipse(cx, cy + 78 * scale, 22 * scale, 18 * scale, steps=14))
    pts.extend(ellipse(cx, cy + 112 * scale, 14 * scale, 12 * scale, steps=12))
    return pts


def face_path(cx: float, cy: float, scale: float = 1.0) -> list[tuple[float, float, float]]:
    """Mouth samples first, then eyes, then the head, so NodeRange submodels land on features."""
    pts: list[tuple[float, float, float]] = []
    for i in range(24):
        t = i / 23
        ang = math.pi * (0.15 + 0.7 * t)
        pts.append((cx + math.cos(ang) * 16 * scale, cy - 8 * scale - math.sin(ang) * 8 * scale, 0.0))
    pts.extend(ellipse(cx - 10 * scale, cy + 8 * scale, 6 * scale, 4 * scale, steps=11))
    pts.extend(ellipse(cx + 10 * scale, cy + 8 * scale, 6 * scale, 4 * scale, steps=11))
    pts.extend(ellipse(cx, cy, 28 * scale, 34 * scale, steps=28))
    return pts


class Layout:
    def __init__(self, layout_id: str, title: str, tier: str, summary: str) -> None:
        self.layout_id = layout_id
        self.title = title
        self.tier = tier
        self.summary = summary
        self.models: list[dict] = []
        self.groups: list[tuple[str, list[str]]] = []
        self._channel = 1

    def add(
        self,
        name: str,
        display: str,
        points: list[tuple[float, float, float]],
        *,
        rgb: bool = False,
        pixels: int = 1,
        color: str = "#FFFFFF",
        string_type: str | None = None,
        extra: dict[str, str] | None = None,
        face: dict[str, str] | None = None,
        submodels: list[tuple[str, str]] | None = None,
        protocol: str | None = None,
    ) -> str:
        if not points:
            raise ValueError(f"{name} has no geometry")
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        zs = [p[2] for p in points]
        cx = sum(xs) / len(xs)
        cy = sum(ys) / len(ys)
        cz = sum(zs) / len(zs)
        local = [(p[0] - cx, p[1] - cy, p[2] - cz) for p in points]
        width = max(xs) - min(xs)
        height = max(ys) - min(ys)
        channels_each = 3 if rgb else 1
        start = self._channel
        count = max(1, pixels) * channels_each
        self._channel += count
        self.models.append(
            {
                "name": name,
                "display": display,
                "cx": cx,
                "cy": cy,
                "cz": cz,
                "local": local,
                "width": max(width, 4.0),
                "height": max(height, 4.0),
                "rgb": rgb,
                "pixels": max(1, pixels),
                "color": color,
                "string_type": string_type or ("RGB Nodes" if rgb else "Single Color Intensity"),
                "extra": extra or {},
                "face": face,
                "submodels": submodels or [],
                "protocol": protocol or ("ws2811" if rgb else "LOR Optimised"),
                "start": start,
                "channels": count,
            }
        )
        return name

    def group(self, name: str, members: list[str]) -> None:
        clean = [member for member in members if member]
        if len(clean) >= 1:
            self.groups.append((name, clean))

    @property
    def channel_count(self) -> int:
        return self._channel - 1

    def names(self) -> list[str]:
        return [model["name"] for model in self.models]


def _single(color_name: str, hex_color: str) -> str:
    return f"Single Color {color_name}"


def add_ac_strand(layout: Layout, name: str, points: list[tuple[float, float, float]], color_name: str, hex_color: str, display: str = "Single Line", extra: dict[str, str] | None = None) -> str:
    attrs = {"parm1": "1", "parm2": "1", "parm3": "1"}
    if extra:
        attrs.update(extra)
    return layout.add(
        name,
        display,
        points,
        rgb=False,
        pixels=1,
        color=hex_color,
        string_type=_single(color_name, hex_color),
        extra=attrs,
    )


def build_ac(channel_count: int) -> Layout:
    titles = {
        16: ("ac16_lor", "AC 16 LOR", "A 16-channel LOR-style yard: one dimmable channel per prop."),
        32: ("ac32_house", "AC 32 House", "A 32-channel AC house with segmented arches, canes, and a second window."),
        64: ("ac64_yard", "AC 64 Yard", "A 64-channel AC yard with color stacks, more arch sections, and path lights."),
    }
    layout_id, title, summary = titles[channel_count]
    layout = Layout(layout_id, title, "ac", summary)
    red, green, white = "#FF0000", "#00FF00", "#FFFFFF"

    def roof(y: float, name: str, color_name: str, hex_color: str) -> str:
        return add_ac_strand(layout, name, line(80, y, 1120, y + 36, steps=8), color_name, hex_color)

    def mini(i: int, x: float) -> str:
        return add_ac_strand(layout, f"Mini Tree {i}", tree_outline(x, 250, 54, 110), "Green", green, display="Tree Flat", extra={"parm1": "1", "parm2": "1"})

    def arch_seg(arch: int, sec: int, secs: int, cx: float) -> str:
        return add_ac_strand(
            layout,
            f"Arch {arch} Sec {sec}",
            arc_section(cx, 150, 220, 120, sec, secs),
            "White",
            white,
            display="Poly Line",
            extra={"parm1": "1", "parm2": "1", "parm3": "1", "NumPoints": "7"},
        )

    roof_models = [
        roof(560, "Roofline Red", "Red", red),
        roof(548, "Roofline Green", "Green", green),
        roof(536, "Roofline White", "White", white),
    ]
    trees = [mini(i, 180 + (i - 1) * 70) for i in range(1, 5)]
    arches = [arch_seg(1, 1, 2, 260), arch_seg(1, 2, 2, 260), arch_seg(2, 1, 2, 860), arch_seg(2, 2, 2, 860)]
    window = add_ac_strand(
        layout,
        "Window Frame 1",
        rect(470, 430, 110, 80),
        "White",
        white,
        display="Window Frame",
        extra={"TopNodes": "1", "SideNodes": "0", "BottomNodes": "0", "parm1": "1", "parm2": "1"},
    )
    door = add_ac_strand(layout, "Door Outline", rect(620, 300, 70, 130), "White", white)
    bush = add_ac_strand(layout, "Bush 1", ellipse(160, 150, 36, 18, steps=10), "Green", green)
    star = add_ac_strand(layout, "Star 1", star_poly(980, 620, 36), "White", white, display="Star", extra={"parm1": "1", "parm2": "1", "parm3": "5", "ScaleX": "3.6", "ScaleY": "3.6"})
    flood = add_ac_strand(layout, "Flood Light 1", line(700, 80, 760, 80), "White", white)
    core = roof_models + trees + arches + [window, door, bush, star, flood]
    if len(core) != 16:
        raise RuntimeError(f"AC core expected 16 props, got {len(core)}")

    extra: list[str] = []
    if channel_count >= 32:
        extra.extend(
            [
                arch_seg(3, 1, 2, 480),
                arch_seg(3, 2, 2, 480),
                arch_seg(4, 1, 2, 1040),
                arch_seg(4, 2, 2, 1040),
                add_ac_strand(layout, "Candy Cane 1", cane(300, 180), "Red", red, display="Candy Cane", extra={"NumCanes": "1", "NodesPerCane": "1", "parm1": "1", "parm2": "1"}),
                add_ac_strand(layout, "Candy Cane 2", cane(360, 180), "White", white, display="Candy Cane", extra={"NumCanes": "1", "NodesPerCane": "1", "parm1": "1", "parm2": "1"}),
                add_ac_strand(layout, "Candy Cane 3", cane(760, 180), "Red", red, display="Candy Cane", extra={"NumCanes": "1", "NodesPerCane": "1", "parm1": "1", "parm2": "1"}),
                add_ac_strand(layout, "Candy Cane 4", cane(820, 180), "White", white, display="Candy Cane", extra={"NumCanes": "1", "NodesPerCane": "1", "parm1": "1", "parm2": "1"}),
                add_ac_strand(layout, "Window Frame 2", rect(800, 430, 90, 70), "White", white, display="Window Frame", extra={"TopNodes": "1", "SideNodes": "0", "BottomNodes": "0", "parm1": "1", "parm2": "1"}),
                add_ac_strand(layout, "Garage Outline", rect(860, 280, 180, 150), "White", white),
                add_ac_strand(layout, "Bush 2", ellipse(430, 140, 30, 16, steps=8), "Green", green),
                add_ac_strand(layout, "Bush 3", ellipse(980, 140, 30, 16, steps=8), "Green", green),
                mini(5, 520),
                mini(6, 680),
                add_ac_strand(layout, "Stake Light 1", line(240, 60, 240, 100), "White", white),
                add_ac_strand(layout, "Icicles", line(120, 500, 1080, 520, steps=12), "White", white, display="Icicles", extra={"NumStrings": "1", "LightsPerString": "1", "parm1": "1", "parm2": "1"}),
            ]
        )
    if channel_count >= 64:
        extra.extend(
            [
                roof(500, "Roofline Lower Red", "Red", red),
                roof(488, "Roofline Lower Green", "Green", green),
                roof(476, "Roofline Lower White", "White", white),
                add_ac_strand(layout, "Eaves Red", line(100, 450, 1100, 450, steps=6), "Red", red),
                add_ac_strand(layout, "Eaves Green", line(100, 438, 1100, 438, steps=6), "Green", green),
                add_ac_strand(layout, "Eaves White", line(100, 426, 1100, 426, steps=6), "White", white),
                arch_seg(1, 3, 4, 260),
                arch_seg(1, 4, 4, 260),
                arch_seg(2, 3, 4, 860),
                arch_seg(2, 4, 4, 860),
                arch_seg(3, 3, 4, 480),
                arch_seg(3, 4, 4, 480),
                arch_seg(4, 3, 4, 1040),
                arch_seg(4, 4, 4, 1040),
                add_ac_strand(layout, "Candy Cane 5", cane(430, 170, 70, 22), "Red", red, display="Candy Cane", extra={"NumCanes": "1", "NodesPerCane": "1", "parm1": "1", "parm2": "1"}),
                add_ac_strand(layout, "Candy Cane 6", cane(500, 170, 70, 22), "Green", green, display="Candy Cane", extra={"NumCanes": "1", "NodesPerCane": "1", "parm1": "1", "parm2": "1"}),
                add_ac_strand(layout, "Candy Cane 7", cane(900, 170, 70, 22), "Red", red, display="Candy Cane", extra={"NumCanes": "1", "NodesPerCane": "1", "parm1": "1", "parm2": "1"}),
                add_ac_strand(layout, "Candy Cane 8", cane(970, 170, 70, 22), "White", white, display="Candy Cane", extra={"NumCanes": "1", "NodesPerCane": "1", "parm1": "1", "parm2": "1"}),
                mini(7, 80),
                mini(8, 1140),
                add_ac_strand(layout, "Window Frame 3", rect(250, 430, 80, 60), "White", white, display="Window Frame", extra={"TopNodes": "1", "SideNodes": "0", "BottomNodes": "0", "parm1": "1", "parm2": "1"}),
                add_ac_strand(layout, "Star 2", star_poly(180, 640, 28), "White", white, display="Star", extra={"parm1": "1", "parm2": "1", "parm3": "5", "ScaleX": "2.8", "ScaleY": "2.8"}),
                add_ac_strand(layout, "Star 3", star_poly(620, 650, 28), "Red", red, display="Star", extra={"parm1": "1", "parm2": "1", "parm3": "5", "ScaleX": "2.8", "ScaleY": "2.8"}),
                add_ac_strand(layout, "Flood Light 2", line(1040, 80, 1100, 80), "Green", green),
                add_ac_strand(layout, "Door Wreath", ellipse(655, 400, 22, 22, steps=12), "Green", green, display="Circle", extra={"parm1": "1", "parm2": "1", "parm3": "1", "ScaleX": "2.2", "ScaleY": "2.2"}),
                add_ac_strand(layout, "Bush 4", ellipse(700, 130, 26, 14, steps=8), "Green", green),
                add_ac_strand(layout, "Column 1", line(400, 280, 400, 520), "White", white),
                add_ac_strand(layout, "Column 2", line(760, 280, 760, 520), "White", white),
                add_ac_strand(layout, "Up Light 1", line(540, 70, 580, 70), "Red", red),
                add_ac_strand(layout, "Garage Tree 1", tree_outline(960, 300, 40, 80), "Green", green, display="Tree Flat", extra={"parm1": "1", "parm2": "1"}),
                add_ac_strand(layout, "Path Lights", line(200, 40, 1000, 40, steps=10), "White", white),
                add_ac_strand(layout, "Snowflake 1", snowflake(760, 600, 26), "White", white, display="Custom", extra={"CustomWidth": "1", "CustomHeight": "1", "parm1": "1", "parm2": "1"}),
            ]
        )
    if len(layout.models) != channel_count:
        raise RuntimeError(f"{layout_id} built {len(layout.models)} props, expected {channel_count}")

    names = layout.names()
    layout.group("Whole House", names)
    layout.group("All Red", [name for name in names if "Red" in name or name.endswith(" Red")])
    layout.group("All Green", [name for name in names if "Green" in name])
    layout.group("All White", [name for name in names if "White" in name])
    layout.group("All Arches", [name for name in names if name.startswith("Arch ")])
    layout.group("All Mini Trees", [name for name in names if name.startswith("Mini Tree")])
    canes = [name for name in names if "Cane" in name]
    if canes:
        layout.group("All Canes", canes)
    layout.group("All Stars", [name for name in names if name.startswith("Star")])
    return layout


def _rgb(layout: Layout, name: str, display: str, points: list[tuple[float, float, float]], pixels: int, tint: str, extra: dict[str, str] | None = None, **kwargs) -> str:
    return layout.add(name, display, points, rgb=True, pixels=pixels, color=tint, extra=extra, **kwargs)


def build_pixel_starter() -> Layout:
    layout = Layout("pixel_starter", "Pixel Starter", "pixel", "Small pixel yard: arches, canes, mini trees, roofline, one window, a matrix, and a star.")
    roof = _rgb(layout, "Roofline", "Poly Line", line(60, 560, 1140, 600, steps=16), 150, RGB_TINT["roof"], {"parm1": "1", "parm2": "150", "NumPoints": "16"})
    arches = []
    for sec in range(1, 5):
        arches.append(
            _rgb(
                layout,
                f"Arch 1 Sec {sec}",
                "Poly Line",
                arc_section(420, 160, 360, 150, sec, 4),
                40,
                RGB_TINT["arch"],
                {"parm1": "1", "parm2": "40", "NumPoints": "7"},
            )
        )
    canes = [
        _rgb(layout, f"Candy Cane {i}", "Candy Cane", cane(640 + i * 48, 170, 100, 26), 36, RGB_TINT["cane"], {"NumCanes": "1", "NodesPerCane": "36", "parm1": "1", "parm2": "36"})
        for i in range(1, 5)
    ]
    trees = [
        _rgb(layout, f"Mini Tree {i}", "Tree Flat", tree_outline(140 + i * 90, 250, 70, 140), 6 * 25, RGB_TINT["mini"], {"parm1": "6", "parm2": "25"})
        for i in range(1, 4)
    ]
    window = _rgb(
        layout,
        "Window Frame 1",
        "Window Frame",
        rect(860, 400, 140, 100),
        30 + 40 * 2 + 30,
        RGB_TINT["window"],
        {"TopNodes": "30", "SideNodes": "40", "BottomNodes": "30"},
    )
    matrix = _rgb(layout, "Matrix 1", "Horiz Matrix", matrix_grid(860, 250, 160, 90, 16, 8), 16 * 8, RGB_TINT["matrix"], {"parm1": "16", "parm2": "8"})
    star = _rgb(layout, "Star 1", "Star", star_poly(1040, 640, 42), 50, RGB_TINT["star"], {"parm1": "1", "parm2": "50", "parm3": "5", "ScaleX": "4.2", "ScaleY": "4.2"})
    layout.group("Whole House", layout.names())
    layout.group("All Arches", arches)
    layout.group("All Canes", canes)
    layout.group("All Mini Trees", trees)
    layout.group("Roofline", [roof])
    layout.group("All Stars", [star])
    layout.group("All Windows", [window])
    return layout


def build_pixel_classic() -> Layout:
    layout = Layout(
        "pixel_classic",
        "Pixel Classic House",
        "pixel",
        "Full hobbyist pixel house: mega tree, matrix, arches, north and south canes, mini trees, windows, stars, and snowflakes.",
    )
    mega = _rgb(layout, "Mega Tree", "Tree 360", tree_outline(180, 180, 220, 420), 16 * 50, RGB_TINT["mega"], {"parm1": "16", "parm2": "50"})
    matrix = _rgb(layout, "Matrix 1", "Horiz Matrix", matrix_grid(860, 300, 220, 140, 20, 12), 32 * 16, RGB_TINT["matrix"], {"parm1": "32", "parm2": "16"})
    roof = _rgb(layout, "Roofline", "Poly Line", line(40, 620, 1180, 650, steps=20), 200, RGB_TINT["roof"], {"parm1": "1", "parm2": "200"})
    icicles = _rgb(layout, "Icicles", "Icicles", line(60, 560, 1160, 575, steps=18), 40 * 8, RGB_TINT["flake"], {"parm1": "40", "parm2": "8", "NumStrings": "40", "LightsPerString": "8"})
    windows = [
        _rgb(layout, "Window Frame 1", "Window Frame", rect(480, 430, 120, 90), 24 + 36 * 2 + 24, RGB_TINT["window"], {"TopNodes": "24", "SideNodes": "36", "BottomNodes": "24"}),
        _rgb(layout, "Window Frame 2", "Window Frame", rect(660, 430, 120, 90), 24 + 36 * 2 + 24, RGB_TINT["window"], {"TopNodes": "24", "SideNodes": "36", "BottomNodes": "24"}),
    ]
    arches = []
    for arch, cx in ((1, 430), (2, 760)):
        for sec in range(1, 7):
            arches.append(
                _rgb(layout, f"Arch {arch} Sec {sec}", "Poly Line", arc_section(cx, 140, 280, 130, sec, 6), 36, RGB_TINT["arch"], {"parm1": "1", "parm2": "36"})
            )
    north = [
        _rgb(layout, f"North Candy Cane {i}", "Candy Cane", cane(360 + i * 28, 250, 90, 20), 32, RGB_TINT["cane"], {"NumCanes": "1", "NodesPerCane": "32", "parm1": "1", "parm2": "32"})
        for i in range(1, 9)
    ]
    south = [
        _rgb(layout, f"South Candy Cane {i}", "Candy Cane", cane(820 + (i - 1) * 28, 250, 90, 20), 32, RGB_TINT["cane"], {"NumCanes": "1", "NodesPerCane": "32", "parm1": "1", "parm2": "32"})
        for i in range(1, 9)
    ]
    trees = [
        _rgb(layout, f"Mini Tree {i}", "Tree Flat", tree_outline(470 + i * 55, 300, 48, 100), 8 * 20, RGB_TINT["mini"], {"parm1": "8", "parm2": "20"})
        for i in range(1, 7)
    ]
    stars = [
        _rgb(layout, f"Star {i}", "Star", star_poly(80 + i * 120, 680, 24), 40, RGB_TINT["star"], {"parm1": "1", "parm2": "40", "parm3": "5", "ScaleX": "2.4", "ScaleY": "2.4"})
        for i in range(1, 9)
    ]
    flakes = [
        _rgb(layout, f"Snowflake {i}", "Custom", snowflake(140 + i * 110, 590, 22), 48, RGB_TINT["flake"], {"CustomWidth": "8", "CustomHeight": "6", "parm1": "8", "parm2": "6"})
        for i in range(1, 7)
    ]
    floods = [
        _rgb(layout, "Flood Light 1", "Single Line", line(500, 70, 560, 70), 12, RGB_TINT["flood"], {"parm1": "1", "parm2": "12"}),
        _rgb(layout, "Flood Light 2", "Single Line", line(700, 70, 760, 70), 12, RGB_TINT["flood"], {"parm1": "1", "parm2": "12"}),
    ]
    layout.group("Whole House", layout.names())
    layout.group("All Arches", arches)
    layout.group("All Canes", north + south)
    layout.group("08_NORTH_CANES", north)
    layout.group("09_NOTNORTH_CANES", south)
    layout.group("All Mini Trees", trees)
    layout.group("All Stars", stars)
    layout.group("All Snowflakes", flakes)
    layout.group("All Windows", windows)
    layout.group("Mega Tree Group", [mega])
    layout.group("All Matrices", [matrix])
    layout.group("Roofline", [roof, icicles])
    layout.group("All Floods", floods)
    return layout


def build_pixel_driveway() -> Layout:
    layout = Layout("pixel_driveway", "Pixel Driveway", "pixel", "Driveway-focused pixel yard: four arches, a garage matrix, walk-line mini trees, and a mega tree.")
    mega = _rgb(layout, "Mega Tree", "Tree 360", tree_outline(160, 160, 200, 400), 24 * 40, RGB_TINT["mega"], {"parm1": "24", "parm2": "40"})
    matrix = _rgb(layout, "Matrix 1", "Horiz Matrix", matrix_grid(900, 320, 240, 150, 18, 10), 40 * 20, RGB_TINT["matrix"], {"parm1": "40", "parm2": "20"})
    roof = _rgb(layout, "Roofline", "Poly Line", line(40, 640, 1180, 660, steps=12), 160, RGB_TINT["roof"], {"parm1": "1", "parm2": "160"})
    arches = []
    for arch, cx in ((1, 360), (2, 560), (3, 760), (4, 1040)):
        for sec in range(1, 6):
            arches.append(_rgb(layout, f"Arch {arch} Sec {sec}", "Arches", arc_section(cx, 120, 160, 110, sec, 5), 30, RGB_TINT["arch"], {"NumArches": "1", "NodesPerArch": "30", "parm1": "1", "parm2": "30"}))
    trees = [
        _rgb(layout, f"Mini Tree {i}", "Tree Flat", tree_outline(300 + i * 40, 280, 36, 80), 4 * 16, RGB_TINT["mini"], {"parm1": "4", "parm2": "16"})
        for i in range(1, 9)
    ]
    canes = [
        _rgb(layout, f"Candy Cane {i}", "Candy Cane", cane(300 + i * 36, 200, 80, 18), 24, RGB_TINT["cane"], {"NumCanes": "1", "NodesPerCane": "24", "parm1": "1", "parm2": "24"})
        for i in range(1, 7)
    ]
    window = _rgb(layout, "Window Frame 1", "Window Frame", rect(980, 500, 100, 70), 16 + 24 * 2 + 16, RGB_TINT["window"], {"TopNodes": "16", "SideNodes": "24", "BottomNodes": "16"})
    star = _rgb(layout, "Star 1", "Star", star_poly(1040, 680, 30), 36, RGB_TINT["star"], {"parm1": "1", "parm2": "36", "parm3": "5", "ScaleX": "3", "ScaleY": "3"})
    layout.group("Whole House", layout.names())
    layout.group("All Arches", arches)
    layout.group("All Mini Trees", trees)
    layout.group("All Canes", canes)
    layout.group("All Stars", [star])
    layout.group("All Matrices", [matrix])
    layout.group("Mega Tree Group", [mega])
    layout.group("Roofline", [roof])
    layout.group("All Windows", [window])
    return layout


def build_pixel_windows() -> Layout:
    layout = Layout("pixel_windows", "Pixel Windows", "pixel", "Window-heavy house: four window frames, a matrix in the picture window, outline, stars, and snowflakes.")
    roof = _rgb(layout, "Roofline", "Poly Line", line(80, 640, 1120, 660, steps=10), 140, RGB_TINT["roof"], {"parm1": "1", "parm2": "140"})
    outline = _rgb(layout, "House Outline", "Poly Line", rect(120, 180, 960, 460), 220, RGB_TINT["line"], {"parm1": "1", "parm2": "220"})
    windows = []
    spots = [(180, 460), (360, 460), (760, 460), (960, 460)]
    for i, (x, y) in enumerate(spots, 1):
        windows.append(
            _rgb(layout, f"Window Frame {i}", "Window Frame", rect(x, y, 110, 90), 20 + 30 * 2 + 20, RGB_TINT["window"], {"TopNodes": "20", "SideNodes": "30", "BottomNodes": "20"})
        )
    matrix = _rgb(layout, "Matrix 1", "Horiz Matrix", matrix_grid(500, 360, 200, 180, 16, 12), 24 * 24, RGB_TINT["matrix"], {"parm1": "24", "parm2": "24"})
    stars = [
        _rgb(layout, f"Star {i}", "Star", star_poly(200 + i * 180, 690, 26), 30, RGB_TINT["star"], {"parm1": "1", "parm2": "30", "parm3": "5", "ScaleX": "2.6", "ScaleY": "2.6"})
        for i in range(1, 6)
    ]
    flakes = [
        _rgb(layout, f"Snowflake {i}", "Custom", snowflake(160 + i * 160, 600, 20), 36, RGB_TINT["flake"], {"CustomWidth": "6", "CustomHeight": "6", "parm1": "6", "parm2": "6"})
        for i in range(1, 6)
    ]
    door = _rgb(layout, "Door Outline", "Single Line", rect(560, 180, 90, 150), 80, RGB_TINT["line"], {"parm1": "1", "parm2": "80"})
    wreath = _rgb(layout, "Wreath 1", "Circle", ellipse(605, 280, 24, 24, steps=20), 40, RGB_TINT["tree"], {"parm1": "1", "parm2": "40", "parm3": "40", "ScaleX": "2.4", "ScaleY": "2.4"})
    layout.group("Whole House", layout.names())
    layout.group("All Windows", windows)
    layout.group("All Stars", stars)
    layout.group("All Snowflakes", flakes)
    layout.group("All Matrices", [matrix])
    layout.group("Roofline", [roof, outline])
    return layout


def build_pixel_corner() -> Layout:
    layout = Layout("pixel_corner", "Pixel Corner Lot", "pixel", "Corner lot: L-shaped roofline, a corner mega tree, walk arches, and a side-yard matrix.")
    front = _rgb(layout, "Roofline Front", "Poly Line", line(40, 620, 780, 640, steps=12), 120, RGB_TINT["roof"], {"parm1": "1", "parm2": "120"})
    side = _rgb(layout, "Roofline Side", "Poly Line", line(780, 640, 1100, 280, steps=12), 100, RGB_TINT["roof"], {"parm1": "1", "parm2": "100"})
    mega = _rgb(layout, "Mega Tree", "Tree 360", tree_outline(860, 300, 180, 280), 16 * 40, RGB_TINT["mega"], {"parm1": "16", "parm2": "40"})
    matrix = _rgb(layout, "Matrix 1", "Horiz Matrix", matrix_grid(980, 160, 140, 100, 14, 8), 20 * 12, RGB_TINT["matrix"], {"parm1": "20", "parm2": "12"})
    arches = []
    for sec in range(1, 7):
        arches.append(_rgb(layout, f"Arch 1 Sec {sec}", "Poly Line", arc_section(360, 140, 420, 140, sec, 6), 32, RGB_TINT["arch"], {"parm1": "1", "parm2": "32"}))
    trees = [
        _rgb(layout, f"Mini Tree {i}", "Tree Flat", tree_outline(80 + i * 70, 240, 50, 110), 6 * 18, RGB_TINT["mini"], {"parm1": "6", "parm2": "18"})
        for i in range(1, 6)
    ]
    canes = [
        _rgb(layout, f"Candy Cane {i}", "Candy Cane", cane(80 + i * 50, 160, 86, 20), 28, RGB_TINT["cane"], {"NumCanes": "1", "NodesPerCane": "28", "parm1": "1", "parm2": "28"})
        for i in range(1, 5)
    ]
    window = _rgb(layout, "Window Frame 1", "Window Frame", rect(180, 450, 130, 90), 20 + 28 * 2 + 20, RGB_TINT["window"], {"TopNodes": "20", "SideNodes": "28", "BottomNodes": "20"})
    stars = [
        _rgb(layout, f"Star {i}", "Star", star_poly(120 + i * 140, 690, 22), 28, RGB_TINT["star"], {"parm1": "1", "parm2": "28", "parm3": "5", "ScaleX": "2.2", "ScaleY": "2.2"})
        for i in range(1, 5)
    ]
    flake = _rgb(layout, "Snowflake 1", "Custom", snowflake(700, 690, 24), 36, RGB_TINT["flake"], {"CustomWidth": "6", "CustomHeight": "6", "parm1": "6", "parm2": "6"})
    layout.group("Whole House", layout.names())
    layout.group("Roofline", [front, side])
    layout.group("All Arches", arches)
    layout.group("All Mini Trees", trees)
    layout.group("All Canes", canes)
    layout.group("All Stars", stars)
    layout.group("All Snowflakes", [flake])
    layout.group("All Windows", [window])
    layout.group("Mega Tree Group", [mega])
    layout.group("All Matrices", [matrix])
    return layout


def _face(layout: Layout, name: str, cx: float, cy: float, scale: float = 1.0) -> str:
    pixels = 80
    face = {
        "Type": "NodeRange",
        "Name": "NodeRange",
        "CustomColors": "",
        "Mouth-AI": "1-4",
        "Mouth-E": "5-8",
        "Mouth-FV": "9-12",
        "Mouth-L": "13-14",
        "Mouth-MBP": "15-18",
        "Mouth-O": "19-22",
        "Mouth-U": "23",
        "Mouth-WQ": "24",
        "Mouth-etc": "21-24",
        "Mouth-rest": "15-18",
        "Eyes-Open": "25-48",
        "Eyes-Closed": "25-32",
    }
    return _rgb(
        layout,
        name,
        "Custom",
        face_path(cx, cy, scale),
        pixels,
        RGB_TINT["face"],
        {"CustomWidth": "10", "CustomHeight": "8", "parm1": "10", "parm2": "8"},
        face=face,
        submodels=[("Mouth", "1-24"), ("Eyes", "25-48")],
    )


def _drum(layout: Layout, name: str, points: list[tuple[float, float, float]], pixels: int = 12) -> str:
    return _rgb(layout, name, "Single Line", points, pixels, RGB_TINT["drum"], {"parm1": "1", "parm2": str(pixels)})


def build_band_stage() -> Layout:
    layout = Layout(
        "band_stage",
        "Snowman Band Stage",
        "band",
        "Stage with a snowman band, three singing-face props (phoneme NodeRange mouths and eyes), a backdrop matrix, and the nine drum-hit props.",
    )
    backdrop = _rgb(layout, "Matrix 1", "Horiz Matrix", matrix_grid(180, 430, 840, 200, 20, 10), 32 * 16, RGB_TINT["matrix"], {"parm1": "32", "parm2": "16"})
    truss = _rgb(layout, "Roofline", "Poly Line", line(120, 660, 1080, 660, steps=8), 80, RGB_TINT["roof"], {"parm1": "1", "parm2": "80"})
    faces = [
        _face(layout, "Singing Face 2", 280, 500, 1.1),
        _face(layout, "Singing Face 1", 600, 520, 1.45),
        _face(layout, "Singing Face 3", 920, 500, 1.1),
    ]
    singer = _rgb(layout, "Snowman Singer", "Custom", snowman(600, 180, 1.15), 64, RGB_TINT["stage"], {"CustomWidth": "8", "CustomHeight": "8", "parm1": "8", "parm2": "8"})
    bass = _rgb(layout, "Snowman Bass", "Custom", snowman(250, 160, 1.0) + line(220, 250, 180, 420, steps=6), 64, RGB_TINT["stage"], {"CustomWidth": "8", "CustomHeight": "8", "parm1": "8", "parm2": "8"})
    guitar = _rgb(layout, "Snowman Guitar", "Custom", snowman(900, 160, 1.0) + line(930, 240, 1040, 420, steps=6), 64, RGB_TINT["stage"], {"CustomWidth": "8", "CustomHeight": "8", "parm1": "8", "parm2": "8"})
    drummer = _rgb(layout, "Snowman Drummer", "Custom", snowman(1120, 200, 0.9), 48, RGB_TINT["stage"], {"CustomWidth": "8", "CustomHeight": "6", "parm1": "8", "parm2": "6"})
    kit = [
        _drum(layout, "HX_SNOWMAN_DRUMMER_KICK", ellipse(1080, 150, 28, 16, steps=10)),
        _drum(layout, "HX_SNOWMAN_DRUMMER_SNARE", ellipse(1148, 210, 18, 10, steps=8)),
        _drum(layout, "HX_SNOWMAN_DRUMMER_TOM_1", ellipse(1110, 250, 14, 10, steps=8)),
        _drum(layout, "HX_SNOWMAN_DRUMMER_TOM_2", ellipse(1175, 255, 14, 10, steps=8)),
        _drum(layout, "HX_SNOWMAN_DRUMMER_TOM_3", ellipse(1100, 290, 12, 8, steps=8)),
        _drum(layout, "HX_SNOWMAN_DRUMMER_TOM_4", ellipse(1188, 290, 12, 8, steps=8)),
        _drum(layout, "HX_SNOWMAN_DRUMMER_HI_HAT", line(1060, 300, 1100, 320, steps=4)),
        _drum(layout, "HX_SNOWMAN_DRUMMER_CYMBAL_LEFT", ellipse(1048, 340, 22, 6, steps=8)),
        _drum(layout, "HX_SNOWMAN_DRUMMER_CYMBAL_RIGHT", ellipse(1205, 340, 22, 6, steps=8)),
    ]
    floor = _rgb(layout, "Stage Floor", "Horiz Matrix", matrix_grid(160, 40, 980, 36, 20, 2), 40 * 2, RGB_TINT["stage"], {"parm1": "40", "parm2": "2"})
    floods = [
        _rgb(layout, "Flood Light 1", "Single Line", line(160, 120, 240, 150), 10, RGB_TINT["flood"], {"parm1": "1", "parm2": "10"}),
        _rgb(layout, "Flood Light 2", "Single Line", line(980, 120, 1060, 150), 10, RGB_TINT["flood"], {"parm1": "1", "parm2": "10"}),
    ]
    stars = [
        _rgb(layout, "Star 1", "Star", star_poly(200, 690, 22), 24, RGB_TINT["star"], {"parm1": "1", "parm2": "24", "parm3": "5", "ScaleX": "2.2", "ScaleY": "2.2"}),
        _rgb(layout, "Star 2", "Star", star_poly(1000, 690, 22), 24, RGB_TINT["star"], {"parm1": "1", "parm2": "24", "parm3": "5", "ScaleX": "2.2", "ScaleY": "2.2"}),
    ]
    layout.group("Whole House", layout.names())
    layout.group("Snowman Band", [singer, bass, guitar, drummer])
    layout.group("All Singing Faces", faces)
    layout.group("Drummer Kit", kit)
    layout.group("All Matrices", [backdrop, floor])
    layout.group("All Stars", stars)
    layout.group("All Floods", floods)
    layout.group("Roofline", [truss])
    return layout


def build_wow_spirals() -> Layout:
    layout = Layout("wow_spirals", "Spiral Trees", "wow", "Five spiral trees plus a ground spiral. Tree 360 models carry a spiral point path.")
    trees = []
    for i in range(1, 6):
        cx = 140 + (i - 1) * 220
        trees.append(
            _rgb(
                layout,
                f"Spiral Tree {i}",
                "Tree 360",
                spiral(cx, 80, 70 + i * 4, 460, 4.5 + i * 0.2),
                16 * 50,
                RGB_TINT["spiral"],
                {"parm1": "16", "parm2": "50"},
            )
        )
    ground = _rgb(layout, "Spiral 1", "Poly Line", spiral(600, 40, 280, 70, 3.0, steps=80), 180, RGB_TINT["helix"], {"parm1": "1", "parm2": "180"})
    star = _rgb(layout, "Star 1", "Star", star_poly(600, 620, 30), 40, RGB_TINT["star"], {"parm1": "1", "parm2": "40", "parm3": "5", "ScaleX": "3", "ScaleY": "3"})
    layout.group("Whole House", layout.names())
    layout.group("All Spirals", trees + [ground])
    layout.group("All Stars", [star])
    return layout


def build_wow_helix() -> Layout:
    layout = Layout("wow_helix", "Double Helix Towers", "wow", "Three double-helix towers. Each tower is a pair of opposing spirals.")
    towers = []
    for i, cx in enumerate((220, 600, 980), 1):
        height = 480 if i == 2 else 380
        radius = 70 if i == 2 else 52
        a = _rgb(layout, f"Double Helix {i} A", "Single Line", helix(cx, 80, radius, height, 5.0, 0.0), 160, RGB_TINT["helix"], {"parm1": "1", "parm2": "160"})
        b = _rgb(layout, f"Double Helix {i} B", "Single Line", helix(cx, 80, radius, height, 5.0, math.pi), 160, RGB_TINT["spiral"], {"parm1": "1", "parm2": "160"})
        towers.extend([a, b])
    star = _rgb(layout, "Star 1", "Star", star_poly(600, 640, 28), 36, RGB_TINT["star"], {"parm1": "1", "parm2": "36", "parm3": "5", "ScaleX": "2.8", "ScaleY": "2.8"})
    layout.group("Whole House", layout.names())
    layout.group("All Helixes", towers)
    layout.group("All Stars", [star])
    return layout


def build_wow_tunnel() -> Layout:
    layout = Layout("wow_tunnel", "Concentric Tunnel", "wow", "Eight concentric rings with increasing depth, a center spinner, and a far matrix.")
    rings = []
    for i in range(1, 9):
        radius = 40 + i * 42
        z = (8 - i) * 40
        rings.append(
            _rgb(
                layout,
                f"Ring {i}",
                "Circle",
                ellipse(600, 340, radius, radius * 0.72, z=z, steps=36),
                48 + i * 8,
                RGB_TINT["ring"],
                {"parm1": "1", "parm2": str(48 + i * 8), "parm3": str(48 + i * 8), "ScaleX": f"{radius / 10:.2f}", "ScaleY": f"{radius * 0.72 / 10:.2f}"},
            )
        )
    spinner = _rgb(layout, "Spinner 1", "Spinner", star_poly(600, 340, 36, tips=8), 8 * 16, RGB_TINT["spin"], {"parm1": "1", "parm2": "16", "ArmsPerString": "8", "NodesPerArm": "16"})
    matrix = _rgb(layout, "Matrix 1", "Horiz Matrix", matrix_grid(500, 260, 200, 160, 12, 8), 16 * 12, RGB_TINT["matrix"], {"parm1": "16", "parm2": "12"})
    layout.group("Whole House", layout.names())
    layout.group("Tunnel", rings)
    layout.group("All Spinners", [spinner])
    layout.group("All Matrices", [matrix])
    return layout


def build_wow_spinners() -> Layout:
    layout = Layout("wow_spinners", "Spinner Radial", "wow", "A radial field of spinners and pinwheels with a ring of stars.")
    spins = []
    for i in range(1, 7):
        ang = math.tau * (i - 1) / 6.0
        cx = 600 + math.cos(ang) * 280
        cy = 340 + math.sin(ang) * 180
        spins.append(
            _rgb(
                layout,
                f"Spinner {i}",
                "Spinner",
                star_poly(cx, cy, 70, tips=6),
                6 * 18,
                RGB_TINT["spin"],
                {"parm1": "1", "parm2": "18", "ArmsPerString": "6", "NodesPerArm": "18"},
            )
        )
    pin = _rgb(layout, "Pinwheel 1", "Spinner", star_poly(600, 340, 90, tips=12), 12 * 20, RGB_TINT["helix"], {"parm1": "1", "parm2": "20", "ArmsPerString": "12", "NodesPerArm": "20"})
    stars = []
    for i in range(1, 9):
        ang = math.tau * (i - 1) / 8.0
        stars.append(
            _rgb(
                layout,
                f"Star {i}",
                "Star",
                star_poly(600 + math.cos(ang) * 460, 340 + math.sin(ang) * 280, 24),
                24,
                RGB_TINT["star"],
                {"parm1": "1", "parm2": "24", "parm3": "5", "ScaleX": "2.4", "ScaleY": "2.4"},
            )
        )
    layout.group("Whole House", layout.names())
    layout.group("All Spinners", spins + [pin])
    layout.group("All Stars", stars)
    return layout


def build_wow_moire() -> Layout:
    layout = Layout("wow_moire", "Moire Matrices", "wow", "Three overlapping matrices with different grid pitches so simultaneous hits can read as moire.")
    m1 = _rgb(layout, "Matrix 1", "Horiz Matrix", matrix_grid(260, 160, 680, 420, 24, 18), 48 * 48, RGB_TINT["matrix"], {"parm1": "48", "parm2": "48"})
    m2 = _rgb(layout, "Matrix 2", "Horiz Matrix", matrix_grid(340, 210, 560, 340, 16, 14), 36 * 36, RGB_TINT["ring"], {"parm1": "36", "parm2": "36"})
    m3 = _rgb(layout, "Matrix 3", "Horiz Matrix", matrix_grid(420, 260, 400, 240, 12, 10), 24 * 24, RGB_TINT["spiral"], {"parm1": "24", "parm2": "24"})
    frame = _rgb(layout, "House Outline", "Poly Line", rect(180, 80, 840, 540), 160, RGB_TINT["line"], {"parm1": "1", "parm2": "160"})
    layout.group("Whole House", layout.names())
    layout.group("All Matrices", [m1, m2, m3])
    layout.group("Roofline", [frame])
    return layout


def build_wow_mirror() -> Layout:
    layout = Layout("wow_mirror", "Mirror Chase", "wow", "Left and right mirrored chase arrays around a center matrix and a pair of arches.")
    left = []
    right = []
    for i in range(1, 9):
        y0 = 80 + i * 60
        left.append(_rgb(layout, f"Chase L {i}", "Single Line", line(160, y0, 420, y0 + 10, steps=6), 24, RGB_TINT["arch"], {"parm1": "1", "parm2": "24"}))
        right.append(_rgb(layout, f"Chase R {i}", "Single Line", line(780, y0 + 10, 1040, y0, steps=6), 24, RGB_TINT["helix"], {"parm1": "1", "parm2": "24"}))
    arches = []
    for sec in range(1, 5):
        arches.append(_rgb(layout, f"Arch 1 Sec {sec}", "Poly Line", arc_section(300, 80, 240, 100, sec, 4), 20, RGB_TINT["arch"], {"parm1": "1", "parm2": "20"}))
        arches.append(_rgb(layout, f"Arch 2 Sec {sec}", "Poly Line", arc_section(900, 80, 240, 100, sec, 4), 20, RGB_TINT["arch"], {"parm1": "1", "parm2": "20"}))
    matrix = _rgb(layout, "Matrix 1", "Horiz Matrix", matrix_grid(470, 220, 260, 280, 14, 12), 20 * 16, RGB_TINT["matrix"], {"parm1": "20", "parm2": "16"})
    layout.group("Whole House", layout.names())
    layout.group("Mirror Left", left)
    layout.group("Mirror Right", right)
    layout.group("All Arches", arches)
    layout.group("All Matrices", [matrix])
    return layout


def build_wow_showcase() -> Layout:
    layout = Layout(
        "wow_showcase",
        "Wow Showcase",
        "wow",
        "Over-the-top mix: spiral tree, double helix, concentric rings, spinners, overlapping matrices, arches, and a mega tree.",
    )
    mega = _rgb(layout, "Mega Tree", "Tree 360", tree_outline(140, 80, 160, 300), 16 * 40, RGB_TINT["mega"], {"parm1": "16", "parm2": "40"})
    spiral_tree = _rgb(layout, "Spiral Tree 1", "Tree 360", spiral(1040, 80, 80, 320, 4.0), 12 * 40, RGB_TINT["spiral"], {"parm1": "12", "parm2": "40"})
    helix_a = _rgb(layout, "Double Helix 1 A", "Single Line", helix(600, 80, 46, 280, 4.5, 0.0), 120, RGB_TINT["helix"], {"parm1": "1", "parm2": "120"})
    helix_b = _rgb(layout, "Double Helix 1 B", "Single Line", helix(600, 80, 46, 280, 4.5, math.pi), 120, RGB_TINT["spiral"], {"parm1": "1", "parm2": "120"})
    rings = [
        _rgb(layout, f"Ring {i}", "Circle", ellipse(600, 460, 50 + i * 36, 32 + i * 22, z=(4 - i) * 30, steps=28), 40 + i * 8, RGB_TINT["ring"], {"parm1": "1", "parm2": str(40 + i * 8), "parm3": str(40 + i * 8), "ScaleX": f"{(50 + i * 36) / 10:.2f}", "ScaleY": f"{(32 + i * 22) / 10:.2f}"})
        for i in range(1, 5)
    ]
    spins = [
        _rgb(layout, "Spinner 1", "Spinner", star_poly(360, 500, 50, tips=6), 6 * 12, RGB_TINT["spin"], {"parm1": "1", "parm2": "12", "ArmsPerString": "6", "NodesPerArm": "12"}),
        _rgb(layout, "Spinner 2", "Spinner", star_poly(840, 500, 50, tips=6), 6 * 12, RGB_TINT["spin"], {"parm1": "1", "parm2": "12", "ArmsPerString": "6", "NodesPerArm": "12"}),
    ]
    matrices = [
        _rgb(layout, "Matrix 1", "Horiz Matrix", matrix_grid(430, 200, 160, 120, 12, 8), 24 * 16, RGB_TINT["matrix"], {"parm1": "24", "parm2": "16"}),
        _rgb(layout, "Matrix 2", "Horiz Matrix", matrix_grid(500, 240, 120, 90, 8, 6), 16 * 12, RGB_TINT["ring"], {"parm1": "16", "parm2": "12"}),
    ]
    arches = [
        _rgb(layout, f"Arch 1 Sec {sec}", "Poly Line", arc_section(300, 40, 200, 80, sec, 3), 18, RGB_TINT["arch"], {"parm1": "1", "parm2": "18"})
        for sec in range(1, 4)
    ]
    star = _rgb(layout, "Star 1", "Star", star_poly(600, 680, 26), 30, RGB_TINT["star"], {"parm1": "1", "parm2": "30", "parm3": "5", "ScaleX": "2.6", "ScaleY": "2.6"})
    layout.group("Whole House", layout.names())
    layout.group("All Spirals", [spiral_tree])
    layout.group("All Helixes", [helix_a, helix_b])
    layout.group("Tunnel", rings)
    layout.group("All Spinners", spins)
    layout.group("All Matrices", matrices)
    layout.group("All Arches", arches)
    layout.group("Mega Tree Group", [mega])
    layout.group("All Stars", [star])
    return layout


BUILDERS = [
    lambda: build_ac(16),
    lambda: build_ac(32),
    lambda: build_ac(64),
    build_pixel_starter,
    build_pixel_classic,
    build_pixel_driveway,
    build_pixel_windows,
    build_pixel_corner,
    build_band_stage,
    build_wow_spirals,
    build_wow_helix,
    build_wow_tunnel,
    build_wow_spinners,
    build_wow_moire,
    build_wow_mirror,
    build_wow_showcase,
]


def _point_data(local: list[tuple[float, float, float]]) -> str:
    return ",".join(f"{x:.4f},{y:.4f},{z:.4f}" for x, y, z in local)


def write_layout_xml(layout: Layout, path: Path) -> None:
    root = ET.Element("xrgb")
    root.append(ET.Comment(" Helix layout bench fixture. Synthetic geometry and hobbyist-style names. No imported show data. "))
    models = ET.SubElement(root, "models")
    for spec in layout.models:
        attrs = {
            "name": spec["name"],
            "DisplayAs": spec["display"],
            "StringType": spec["string_type"],
            "CustomColor": spec["color"],
            "TagColour": spec["color"],
            "Antialias": "1",
            "PixelSize": "2",
            "Transparency": "0",
            "LayoutGroup": "Default",
            "Dir": "L",
            "StartSide": "B",
            "WorldPosX": f"{spec['cx']:.4f}",
            "WorldPosY": f"{spec['cy']:.4f}",
            "WorldPosZ": f"{spec['cz']:.4f}",
            "X2": f"{spec['width']:.4f}",
            "Y2": f"{spec['height']:.4f}",
            "Z2": "0.0000",
            "ScaleX": f"{max(spec['width'], 8.0) / 10.0:.4f}",
            "ScaleY": f"{max(spec['height'], 8.0) / 10.0:.4f}",
            "ScaleZ": "1.0000",
            "versionNumber": "7",
            "StartChannel": str(spec["start"]),
            "NumPoints": str(len(spec["local"])),
            "PointData": _point_data(spec["local"]),
        }
        attrs.update(spec["extra"])
        el = ET.SubElement(models, "model", attrs)
        ET.SubElement(el, "ControllerConnection", {"Protocol": spec["protocol"]})
        if spec["face"]:
            ET.SubElement(el, "faceInfo", spec["face"])
        for sub_name, line0 in spec["submodels"]:
            ET.SubElement(el, "subModel", {"name": sub_name, "layout": "horizontal", "type": "ranges", "line0": line0})
    groups = ET.SubElement(root, "modelGroups")
    for name, members in layout.groups:
        xs = [spec["cx"] for spec in layout.models if spec["name"] in set(members)]
        ys = [spec["cy"] for spec in layout.models if spec["name"] in set(members)]
        centrex = f"{(sum(xs) / len(xs)):.3f}" if xs else "0"
        centrey = f"{(sum(ys) / len(ys)):.3f}" if ys else "0"
        ET.SubElement(
            groups,
            "modelGroup",
            {
                "name": name,
                "models": ",".join(members),
                "layout": "minimalGrid",
                "GridSize": "400",
                "LayoutGroup": "Default",
                "centrex": centrex,
                "centrey": centrey,
                "centreDefined": "0",
            },
        )
    settings = ET.SubElement(root, "settings")
    ET.SubElement(settings, "previewWidth", {"value": "1280"})
    ET.SubElement(settings, "previewHeight", {"value": "720"})
    ET.SubElement(settings, "backgroundBrightness", {"value": "0"})
    path.parent.mkdir(parents=True, exist_ok=True)
    ET.indent(root, space="  ")
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


def write_template(layout: Layout, path: Path) -> None:
    root = ET.Element(
        "xsequence",
        {
            "BaseChannel": "0",
            "ChanCtrlBasic": "0",
            "ChanCtrlColor": "0",
            "FixedPointTiming": "1",
            "ModelBlending": "true",
        },
    )
    head = ET.SubElement(root, "head")
    for tag, text in (
        ("version", "2026.01"),
        ("author", "Helix layout bench"),
        ("song", ""),
        ("artist", ""),
        ("album", ""),
        ("MusicURL", ""),
        ("comment", "Clean-room empty template. The engine syncs model rows from the paired xlights_rgbeffects.xml. Bench Palette exists only to seed On/Ramp effect templates and is removed by layout sync."),
        ("sequenceTiming", "50 ms"),
        ("sequenceType", "Media"),
        ("mediaFile", ""),
        ("sequenceDuration", "35.000"),
    ):
        el = ET.SubElement(head, tag)
        el.text = text
    ET.SubElement(head, "imageDir")
    ET.SubElement(root, "nextid").text = "1"
    ET.SubElement(root, "Jukebox")
    palettes = ET.SubElement(root, "ColorPalettes")
    ET.SubElement(palettes, "ColorPalette").text = "C_BUTTON_Palette1=#FFFFFF,C_BUTTON_Palette2=#FF0000,C_BUTTON_Palette3=#00FF00,C_BUTTON_Palette4=#0000FF,C_BUTTON_Palette5=#FFFF00,C_CHECKBOX_Palette1=1"
    ET.SubElement(palettes, "ColorPalette").text = "C_BUTTON_Palette1=#FF0000,C_BUTTON_Palette2=#FFFFFF,C_BUTTON_Palette3=#00FF00,C_CHECKBOX_Palette1=1,C_CHECKBOX_Palette2=1,C_CHECKBOX_Palette3=1"
    effect_db = ET.SubElement(root, "EffectDB")
    ET.SubElement(effect_db, "Effect").text = "E_TEXTCTRL_Eff_On_Start=100,E_TEXTCTRL_Eff_On_End=100"
    layers = ET.SubElement(root, "DataLayers")
    ET.SubElement(layers, "DataLayer", {"lor_params": "0", "channel_offset": "0", "num_channels": "0", "num_frames": "0", "data": "<rendered: erase-mode>", "source": "<auto-generated>", "name": "Nutcracker"})
    display = ET.SubElement(root, "DisplayElements")
    ET.SubElement(display, "Element", {"collapsed": "0", "type": "timing", "name": "Beats", "visible": "1", "views": "Master View", "active": "1"})
    ET.SubElement(display, "Element", {"collapsed": "0", "type": "model", "name": "Bench Palette", "visible": "1"})
    effects = ET.SubElement(root, "ElementEffects")
    timing = ET.SubElement(effects, "Element", {"type": "timing", "name": "Beats", "active": "1"})
    ET.SubElement(timing, "EffectLayer")
    palette_model = ET.SubElement(effects, "Element", {"type": "model", "name": "Bench Palette"})
    layer = ET.SubElement(palette_model, "EffectLayer")
    samples = [
        ("On", "0", "50", "0", "E_TEXTCTRL_Eff_On_Start=100,E_TEXTCTRL_Eff_On_End=100"),
        ("Ramp", "50", "100", "0", "E_TEXTCTRL_Eff_On_Start=0,E_TEXTCTRL_Eff_On_End=100"),
        ("Twinkle", "100", "150", "1", ""),
        ("Shimmer", "150", "200", "1", ""),
        ("Wave", "200", "250", "0", ""),
        ("Butterfly", "250", "300", "0", ""),
        ("Bars", "300", "350", "1", ""),
        ("VU Meter", "350", "400", "1", ""),
        ("Strobe", "400", "450", "0", ""),
        ("Faces", "450", "500", "0", "E_CHOICE_Faces_FaceDefinition=NodeRange,E_CHOICE_Faces_TimingTrack=Beats"),
    ]
    for name, start, end, palette, settings in samples:
        attrib = {"ref": "0", "name": name, "startTime": start, "endTime": end, "palette": palette}
        if settings:
            attrib["settings"] = settings
        ET.SubElement(layer, "Effect", attrib)
    ET.SubElement(root, "lastView").text = "0"
    path.parent.mkdir(parents=True, exist_ok=True)
    ET.indent(root, space="  ")
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


def parsed_stats(path: Path) -> dict:
    parsed = xmp.parse_layout(path)
    roots = [model for model in parsed.models.values() if not model.is_submodel]
    channels = 0
    pixels = 0
    types: dict[str, int] = {}
    for model in roots:
        pixels += model.total_pixels
        multiplier = 3 if model.is_rgb_capable() else 1
        channels += model.total_pixels * multiplier
        types[model.type] = types.get(model.type, 0) + 1
    return {
        "models": len(roots),
        "submodels": sum(1 for model in parsed.models.values() if model.is_submodel),
        "groups": len(parsed.groups),
        "pixels": pixels,
        "channels": channels,
        "types": dict(sorted(types.items())),
        "names": [model.name for model in roots],
    }


def build_all(out_dir: Path = OUT_DIR) -> list[dict]:
    manifest = []
    for builder in BUILDERS:
        layout = builder()
        folder = out_dir / layout.layout_id
        layout_path = folder / "xlights_rgbeffects.xml"
        template_path = folder / "template.xsq"
        write_layout_xml(layout, layout_path)
        write_template(layout, template_path)
        stats = parsed_stats(layout_path)
        if layout.tier == "ac" and stats["channels"] != layout.channel_count:
            raise RuntimeError(f"{layout.layout_id} parser channels {stats['channels']} != planned {layout.channel_count}")
        if stats["models"] != len(layout.models):
            raise RuntimeError(f"{layout.layout_id} parser models {stats['models']} != planned {len(layout.models)}")
        entry = {
            "id": layout.layout_id,
            "title": layout.title,
            "tier": layout.tier,
            "summary": layout.summary,
            "layout": str(layout_path.relative_to(ROOT)),
            "template": str(template_path.relative_to(ROOT)),
            "props": stats["models"],
            "submodels": stats["submodels"],
            "groups": stats["groups"],
            "group_names": [name for name, _members in layout.groups],
            "pixels": stats["pixels"],
            "channels": stats["channels"],
            "types": stats["types"],
        }
        manifest.append(entry)
        print(f"{layout.layout_id}: props={stats['models']} channels={stats['channels']} pixels={stats['pixels']} types={stats['types']}")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    build_all()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
