#!/usr/bin/env python3
"""Clean-room 12-panel showcase layouts, simplest LOR yard through a singing band.

Synthetic geometry and hobbyist model names. No imported show data.
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
OUT_DIR = ROOT / "fixtures" / "showcase12"

FACE = {
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
FACE_SUBS = [("Mouth", "1-24"), ("Eyes", "25-48")]


def line(x1, y1, x2, y2, z=0.0, steps=2):
    return [
        (x1 + (x2 - x1) * i / (steps - 1), y1 + (y2 - y1) * i / (steps - 1), z)
        for i in range(steps)
    ]


def rect(x, y, w, h, z=0.0):
    return [(x, y, z), (x + w, y, z), (x + w, y + h, z), (x, y + h, z), (x, y, z)]


def arc_section(cx, cy, width, height, sec, secs, steps=7):
    pts = []
    for i in range(steps):
        t = (sec - 1 + i / (steps - 1)) / secs
        ang = math.pi * (1.0 - t)
        pts.append((cx + math.cos(ang) * width / 2.0, cy + math.sin(ang) * height, 0.0))
    return pts


def ellipse(cx, cy, rx, ry, z=0.0, steps=16):
    return [
        (cx + math.cos(math.tau * i / steps) * rx, cy + math.sin(math.tau * i / steps) * ry, z)
        for i in range(steps + 1)
    ]


def star_poly(cx, cy, r, tips=5):
    pts = []
    for i in range(tips * 2):
        radius = r if i % 2 == 0 else r * 0.42
        ang = -math.pi / 2.0 + math.pi * i / tips
        pts.append((cx + math.cos(ang) * radius, cy + math.sin(ang) * radius, 0.0))
    pts.append(pts[0])
    return pts


def tree_outline(x, y, w, h):
    return [(x, y, 0), (x - w / 2, y, 0), (x, y + h, 0), (x + w / 2, y, 0), (x, y, 0)]


def cane(x, y, h=90.0, w=28.0):
    pts = [(x, y, 0.0), (x, y + h * 0.72, 0.0)]
    for i in range(8):
        ang = math.pi * i / 7.0
        pts.append((x + math.sin(ang) * w, y + h * 0.72 + (1.0 - math.cos(ang)) * w, 0.0))
    return pts


def spiral(cx, cy, radius, height, turns, steps=48):
    pts = []
    for i in range(steps):
        t = i / (steps - 1)
        ang = turns * math.tau * t
        r = radius * (0.15 + 0.85 * t)
        pts.append((cx + math.cos(ang) * r, cy + t * height, math.sin(ang) * r * 0.35))
    return pts


def helix(cx, cy, radius, height, turns, phase, steps=48):
    pts = []
    for i in range(steps):
        t = i / (steps - 1)
        ang = turns * math.tau * t + phase
        pts.append((cx + math.cos(ang) * radius, cy + t * height, math.sin(ang) * radius))
    return pts


def matrix_grid(x, y, w, h, cols, rows):
    pts = []
    for r in range(rows):
        yy = y + h * r / max(1, rows - 1)
        xs = range(cols) if r % 2 == 0 else range(cols - 1, -1, -1)
        for c in xs:
            pts.append((x + w * c / max(1, cols - 1), yy, 0.0))
    return pts


def face_points(cx, cy, scale=1.0):
    pts = []
    for i in range(24):
        t = i / 23
        ang = math.pi * (0.15 + 0.7 * t)
        pts.append((cx + math.cos(ang) * 16 * scale, cy - 8 * scale - math.sin(ang) * 8 * scale, 0.0))
    for side in (-1, 1):
        for i in range(12):
            ang = math.tau * i / 12
            pts.append(
                (
                    cx + side * 10 * scale + math.cos(ang) * 5 * scale,
                    cy + 8 * scale + math.sin(ang) * 3 * scale,
                    0.0,
                )
            )
    return pts


class Layout:
    def __init__(self, layout_id, title, tier, summary):
        self.layout_id = layout_id
        self.title = title
        self.tier = tier
        self.summary = summary
        self.models = []
        self.groups = []
        self.silhouette: list[dict] = []
        self._channel = 1

    def add(self, name, display, points, *, rgb=False, pixels=1, color="#FFFFFF", string_type=None, extra=None, face=None, submodels=None):
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        zs = [p[2] for p in points]
        cx, cy, cz = sum(xs) / len(xs), sum(ys) / len(ys), sum(zs) / len(zs)
        local = [(p[0] - cx, p[1] - cy, p[2] - cz) for p in points]
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
                "width": max(max(xs) - min(xs), 4.0),
                "height": max(max(ys) - min(ys), 4.0),
                "rgb": rgb,
                "pixels": max(1, pixels),
                "color": color,
                "string_type": string_type or ("RGB Nodes" if rgb else "Single Color Intensity"),
                "extra": extra or {},
                "face": face,
                "submodels": submodels or [],
                "protocol": "ws2811" if rgb else "LOR Optimised",
                "start": start,
                "channels": count,
            }
        )
        return name

    def group(self, name, members):
        clean = [member for member in members if member]
        if clean:
            self.groups.append((name, clean))

    @property
    def channel_count(self):
        return self._channel - 1

    def names(self):
        return [model["name"] for model in self.models]


# One dimmable channel. Without these, the parser treats the rectangle's vertices as pixels.
AC_WINDOW = {"TopNodes": "1", "SideNodes": "0", "BottomNodes": "0"}


def ac(layout, name, points, color_name, hex_color, display="Single Line", extra=None):
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
        string_type=f"Single Color {color_name}",
        extra=attrs,
    )


def rgb(layout, name, display, points, pixels, color, extra=None, face=None, submodels=None):
    attrs = {"parm1": "1", "parm2": str(pixels)}
    if extra:
        attrs.update(extra)
    return layout.add(
        name,
        display,
        points,
        rgb=True,
        pixels=pixels,
        color=color,
        extra=attrs,
        face=face,
        submodels=submodels,
    )


def add_face(layout, name, cx, cy, scale=1.0):
    return rgb(
        layout,
        name,
        "Poly Line",
        face_points(cx, cy, scale),
        48,
        "#FFD0A8",
        face=FACE,
        submodels=FACE_SUBS,
    )


def build_ac16():
    layout = Layout("s01_ac16", "LOR 16 House", "ac", "16-channel LOR house: outline, four mini trees, wreath, door, and a flood.")
    red, green, white = "#FF0000", "#00FF00", "#FFFFFF"
    ac(layout, "Roofline", line(80, 560, 1120, 600, steps=8), "White", white)
    ac(layout, "Eaves", line(100, 500, 1100, 500, steps=6), "Red", red)
    ac(layout, "Door Outline", rect(560, 280, 80, 140), "White", white)
    ac(layout, "Window Frame 1", rect(360, 420, 110, 80), "White", white, "Window Frame", AC_WINDOW)
    ac(layout, "Window Frame 2", rect(760, 420, 110, 80), "White", white, "Window Frame", AC_WINDOW)
    for i, x in enumerate((220, 420, 780, 980), start=1):
        ac(layout, f"Mini Tree {i}", tree_outline(x, 220, 50, 100), "Green", green, "Tree Flat")
    ac(layout, "Wreath 1", ellipse(600, 470, 28, 28, steps=12), "Green", green)
    ac(layout, "Bush 1", ellipse(180, 160, 40, 18, steps=8), "Green", green)
    ac(layout, "Star 1", star_poly(600, 640, 28), "White", white, "Star")
    ac(layout, "Arch 1", arc_section(300, 140, 180, 90, 1, 1), "White", white, "Poly Line")
    ac(layout, "Arch 2", arc_section(900, 140, 180, 90, 1, 1), "White", white, "Poly Line")
    ac(layout, "Candy Cane 1", cane(700, 180), "Red", red, "Candy Canes")
    ac(layout, "Flood Light 1", line(640, 80, 700, 80), "White", white)
    if layout.channel_count != 16:
        raise RuntimeError(layout.channel_count)
    layout.group("Whole House", layout.names())
    layout.group("All Mini Trees", [f"Mini Tree {i}" for i in range(1, 5)])
    layout.group("All Arches", ["Arch 1", "Arch 2"])
    return layout


def build_ac_count(channel_count, layout_id, title, summary):
    layout = Layout(layout_id, title, "ac", summary)
    red, green, white = "#FF0000", "#00FF00", "#FFFFFF"
    colors = [("Red", red), ("Green", green), ("White", white)]
    n = 0

    def take(name, points, color_name, hex_color, display="Single Line", extra=None):
        nonlocal n
        if layout.channel_count >= channel_count:
            return
        ac(layout, name, points, color_name, hex_color, display, extra)
        n += 1

    take("Roofline", line(60, 580, 1180, 620, steps=8), "White", white)
    take("Eaves", line(80, 520, 1160, 520, steps=8), "Red", red)
    take("Door Outline", rect(560, 260, 90, 150), "White", white)
    take("Garage Outline", rect(860, 250, 200, 160), "White", white)
    for i, x in enumerate((180, 300, 420, 980, 1100), start=1):
        take(f"Window Frame {i}", rect(x, 400, 80, 60), "White", white, "Window Frame", AC_WINDOW)
    for i in range(1, 13):
        take(f"Mini Tree {i}", tree_outline(80 + i * 85, 180, 40, 90), "Green", green, "Tree Flat")
    for i in range(1, 9):
        take(f"Arch {i}", arc_section(120 + i * 130, 120, 110, 70, 1, 1), "White", white, "Poly Line")
    for i in range(1, 17):
        cname, hex_color = colors[i % 3]
        take(f"Candy Cane {i}", cane(70 + (i % 16) * 70, 160 + (i // 16) * 20), cname, hex_color, "Candy Canes")
    for i in range(1, 9):
        take(f"Wreath {i}", ellipse(140 + i * 120, 460, 22, 22, steps=10), "Green", green)
    for i in range(1, 9):
        take(f"Bush {i}", ellipse(100 + i * 130, 140, 28, 14, steps=8), "Green", green)
    take("Star 1", star_poly(600, 680, 30), "White", white, "Star")
    take("Flood Light 1", line(500, 70, 560, 70), "White", white)
    take("Flood Light 2", line(700, 70, 760, 70), "White", white)
    i = 1
    while layout.channel_count < channel_count:
        cname, hex_color = colors[i % 3]
        col = (i - 1) % 32
        row = (i - 1) // 32
        take(f"Stake Light {i}", line(40 + col * 36, 40 + row * 18, 40 + col * 36, 70 + row * 18), cname, hex_color)
        i += 1
        if i > 400:
            break
    if layout.channel_count != channel_count:
        raise RuntimeError(f"{layout_id} has {layout.channel_count} channels")
    layout.group("Whole House", layout.names())
    layout.group("All Mini Trees", [name for name in layout.names() if name.startswith("Mini Tree")])
    layout.group("All Arches", [name for name in layout.names() if name.startswith("Arch")])
    return layout


def porch_rgb():
    layout = Layout("s04_rgb_porch", "Pixel Porch", "rgb", "First RGB yard: roofline, windows, door, and six pixel mini trees.")
    rgb(layout, "Roofline", "Poly Line", line(80, 560, 1120, 600, steps=8), 80, "#FFB000")
    rgb(layout, "Eaves", "Poly Line", line(100, 500, 1100, 500, steps=6), 60, "#FF4FA3")
    rgb(layout, "Door Outline", "Poly Line", rect(560, 280, 90, 150), 40, "#F4F1DE")
    rgb(layout, "Window Frame 1", "Window Frame", rect(340, 420, 120, 90), 36, "#7AA2FF", {"parm1": "1", "parm2": "36"})
    rgb(layout, "Window Frame 2", "Window Frame", rect(780, 420, 120, 90), 36, "#7AA2FF", {"parm1": "1", "parm2": "36"})
    trees = []
    for i, x in enumerate((180, 320, 460, 760, 900, 1040), start=1):
        trees.append(rgb(layout, f"Mini Tree {i}", "Tree Flat", tree_outline(x, 180, 48, 110), 50, "#39E07A", {"parm1": "5", "parm2": "10"}))
    rgb(layout, "Bush 1", "Poly Line", ellipse(160, 140, 36, 16, steps=12), 24, "#2EC4B6")
    rgb(layout, "Star 1", "Star", star_poly(600, 660, 26), 30, "#FFE56B", {"parm1": "1", "parm2": "30", "parm3": "5"})
    layout.group("Whole House", layout.names())
    layout.group("All Mini Trees", trees)
    return layout


def arches_faces():
    layout = Layout("s05_arches_faces", "Arches And A Face", "rgb", "Arches, two spinners, candy canes, and one Boscoyo-style singing face.")
    rgb(layout, "Roofline", "Poly Line", line(60, 580, 1180, 610, steps=8), 90, "#FFB000")
    arches = []
    for i, cx in enumerate((220, 480, 760, 1040), start=1):
        for sec in (1, 2):
            arches.append(
                rgb(layout, f"Arch {i} Sec {sec}", "Poly Line", arc_section(cx, 150, 200, 100, sec, 2), 24, "#3DDCFF")
            )
    spins = [
        rgb(layout, "Spinner 1", "Spinner", star_poly(300, 360, 40, tips=6), 72, "#FF7A3C", {"parm1": "1", "parm2": "12", "ArmsPerString": "6", "NodesPerArm": "12"}),
        rgb(layout, "Spinner 2", "Spinner", star_poly(900, 360, 40, tips=6), 72, "#FF7A3C", {"parm1": "1", "parm2": "12", "ArmsPerString": "6", "NodesPerArm": "12"}),
    ]
    canes = [rgb(layout, f"Candy Cane {i}", "Candy Canes", cane(160 + i * 140, 200), 12, "#FF4FA3") for i in range(1, 5)]
    add_face(layout, "Singing Face 1", 600, 430, 1.3)
    for i, x in enumerate((140, 1060), start=1):
        rgb(layout, f"Mini Tree {i}", "Tree Flat", tree_outline(x, 200, 50, 120), 40, "#39E07A", {"parm1": "4", "parm2": "10"})
    layout.group("Whole House", layout.names())
    layout.group("All Arches", arches)
    layout.group("All Spinners", spins)
    layout.group("All Candy Canes", canes)
    return layout


def pixel_yard():
    layout = Layout("s06_pixel_yard", "Pixel Yard", "rgb", "Busier yard: arches, spinners, two singing faces, and a singing-tree face.")
    rgb(layout, "Roofline", "Poly Line", line(40, 600, 1200, 640, steps=10), 120, "#FFB000")
    rgb(layout, "Eaves", "Poly Line", line(60, 540, 1180, 540, steps=8), 80, "#9AE6B4")
    arches = []
    for i, cx in enumerate((180, 420, 780, 1040), start=1):
        for sec in (1, 2, 3):
            arches.append(rgb(layout, f"Arch {i} Sec {sec}", "Poly Line", arc_section(cx, 130, 180, 90, sec, 3), 18, "#3DDCFF"))
    spins = [
        rgb(layout, f"Spinner {i}", "Spinner", star_poly(200 + i * 250, 340, 36, tips=8), 64, "#FF7A3C", {"parm1": "1", "parm2": "8", "ArmsPerString": "8", "NodesPerArm": "8"})
        for i in range(1, 4)
    ]
    add_face(layout, "Singing Face 1", 460, 460, 1.2)
    add_face(layout, "Singing Face 2", 760, 460, 1.1)
    add_face(layout, "Singing Tree Face 1", 180, 430, 1.0)
    rgb(layout, "Pixel Tree 1", "Tree Flat", tree_outline(180, 180, 70, 160), 80, "#39E07A", {"parm1": "8", "parm2": "10"})
    rgb(layout, "Matrix 1", "Horiz Matrix", matrix_grid(520, 200, 160, 100, 16, 8), 128, "#7AA2FF", {"parm1": "16", "parm2": "8"})
    for i in range(1, 5):
        rgb(layout, f"Mini Tree {i}", "Tree Flat", tree_outline(360 + i * 140, 160, 40, 90), 40, "#2EC4B6", {"parm1": "4", "parm2": "10"})
    layout.group("Whole House", layout.names())
    layout.group("All Arches", arches)
    layout.group("All Spinners", spins)
    layout.group("All Matrices", ["Matrix 1"])
    return layout


def mega_start():
    layout = Layout("s07_mega_yard", "Mega Tree Yard", "rgb", "One 360 mega tree with a star, arches, a spinner, a singing face, and a strip matrix.")
    mega = rgb(layout, "Mega Tree", "Tree 360", tree_outline(240, 80, 180, 420), 16 * 40, "#C77DFF", {"parm1": "16", "parm2": "40"})
    star = rgb(layout, "Star 1", "Star", star_poly(240, 540, 36), 40, "#FFE56B", {"parm1": "1", "parm2": "40", "parm3": "5"})
    arches = []
    for i, cx in enumerate((560, 820, 1060), start=1):
        for sec in (1, 2):
            arches.append(rgb(layout, f"Arch {i} Sec {sec}", "Poly Line", arc_section(cx, 140, 200, 110, sec, 2), 24, "#3DDCFF"))
    spin = rgb(layout, "Spinner 1", "Spinner", star_poly(700, 360, 50, tips=6), 72, "#FF7A3C", {"parm1": "1", "parm2": "12", "ArmsPerString": "6", "NodesPerArm": "12"})
    add_face(layout, "Singing Face 1", 920, 400, 1.4)
    matrix = rgb(layout, "Matrix 1", "Horiz Matrix", matrix_grid(480, 220, 200, 80, 20, 4), 80, "#7AA2FF", {"parm1": "20", "parm2": "4"})
    rgb(layout, "Roofline", "Poly Line", line(400, 600, 1200, 620, steps=8), 80, "#FFB000")
    layout.group("Whole House", layout.names())
    layout.group("Mega Tree Group", [mega, star])
    layout.group("All Arches", arches)
    layout.group("All Spinners", [spin])
    layout.group("All Matrices", [matrix])
    return layout


def busy_rgb():
    layout = Layout("s08_busy_rgb", "Busy Pixel Show", "rgb", "Dense arches, four spinners, two singing-tree faces, two singing faces, and windows.")
    rgb(layout, "Roofline", "Poly Line", line(20, 620, 1240, 650, steps=12), 140, "#FFB000")
    arches = []
    for i, cx in enumerate((140, 360, 620, 880, 1100), start=1):
        for sec in (1, 2, 3):
            arches.append(rgb(layout, f"Arch {i} Sec {sec}", "Poly Line", arc_section(cx, 120, 160, 80, sec, 3), 16, "#3DDCFF"))
    spins = [
        rgb(layout, f"Spinner {i}", "Spinner", star_poly(160 + i * 220, 320, 34, tips=8), 64, "#FF7A3C", {"parm1": "1", "parm2": "8", "ArmsPerString": "8", "NodesPerArm": "8"})
        for i in range(1, 5)
    ]
    add_face(layout, "Singing Face 1", 480, 480, 1.1)
    add_face(layout, "Singing Face 2", 760, 480, 1.1)
    add_face(layout, "Singing Tree Face 1", 200, 460, 1.0)
    add_face(layout, "Singing Tree Face 2", 1040, 460, 1.0)
    rgb(layout, "Pixel Tree 1", "Tree Flat", tree_outline(200, 180, 60, 150), 60, "#39E07A", {"parm1": "6", "parm2": "10"})
    rgb(layout, "Pixel Tree 2", "Tree Flat", tree_outline(1040, 180, 60, 150), 60, "#39E07A", {"parm1": "6", "parm2": "10"})
    rgb(layout, "Window Frame 1", "Window Frame", rect(400, 400, 90, 70), 28, "#F4F1DE")
    rgb(layout, "Window Frame 2", "Window Frame", rect(700, 400, 90, 70), 28, "#F4F1DE")
    layout.group("Whole House", layout.names())
    layout.group("All Arches", arches)
    layout.group("All Spinners", spins)
    return layout


def mega_grove():
    layout = Layout("s09_mega_grove", "Mega Grove", "ultra", "Two 360 mega trees with stars, singing-tree faces, a spiral tree, and arches.")
    megas = []
    stars = []
    for i, x in enumerate((260, 980), start=1):
        megas.append(rgb(layout, f"Mega Tree {i}" if i > 1 else "Mega Tree", "Tree 360", tree_outline(x, 60, 200, 460), 16 * 36, "#C77DFF", {"parm1": "16", "parm2": "36"}))
        stars.append(rgb(layout, f"Star {i}", "Star", star_poly(x, 560, 34), 35, "#FFE56B", {"parm1": "1", "parm2": "35", "parm3": "5"}))
    spiral_tree = rgb(layout, "Spiral Tree 1", "Tree 360", spiral(620, 80, 70, 360, 4.0, steps=60), 12 * 30, "#67E8F9", {"parm1": "12", "parm2": "30"})
    add_face(layout, "Singing Tree Face 1", 620, 200, 1.2)
    add_face(layout, "Singing Tree Face 2", 500, 420, 0.9)
    arches = []
    for i, cx in enumerate((450, 790), start=1):
        for sec in (1, 2, 3):
            arches.append(rgb(layout, f"Arch {i} Sec {sec}", "Poly Line", arc_section(cx, 80, 180, 70, sec, 3), 18, "#3DDCFF"))
    layout.group("Whole House", layout.names())
    layout.group("Mega Tree Group", megas + stars)
    layout.group("All Spirals", [spiral_tree])
    layout.group("All Arches", arches)
    return layout


def helix_tunnel():
    layout = Layout("s10_helix_tunnel", "Helix Tunnel", "ultra", "Double helix, spirals, a concentric tunnel, and dense spinners.")
    helix_a = rgb(layout, "Double Helix 1 A", "Single Line", helix(360, 80, 50, 420, 5.0, 0.0, steps=80), 160, "#E879F9")
    helix_b = rgb(layout, "Double Helix 1 B", "Single Line", helix(360, 80, 50, 420, 5.0, math.pi, steps=80), 160, "#67E8F9")
    spirals = [
        rgb(layout, f"Spiral Tree {i}", "Tree 360", spiral(700 + i * 160, 60, 55, 300, 3.5, steps=50), 10 * 24, "#67E8F9", {"parm1": "10", "parm2": "24"})
        for i in range(1, 3)
    ]
    rings = [
        rgb(layout, f"Ring {i}", "Circle", ellipse(200, 300, 40 + i * 28, 24 + i * 16, z=(4 - i) * 20, steps=20), 36 + i * 8, "#5EEAD4", {"parm1": "1", "parm2": str(36 + i * 8)})
        for i in range(1, 5)
    ]
    spins = [
        rgb(layout, f"Spinner {i}", "Spinner", star_poly(140 + i * 180, 560, 32, tips=8), 64, "#FF7A3C", {"parm1": "1", "parm2": "8", "ArmsPerString": "8", "NodesPerArm": "8"})
        for i in range(1, 6)
    ]
    arches = [rgb(layout, f"Arch 1 Sec {sec}", "Poly Line", arc_section(1000, 200, 220, 140, sec, 3), 24, "#3DDCFF") for sec in (1, 2, 3)]
    layout.group("Whole House", layout.names())
    layout.group("All Helixes", [helix_a, helix_b])
    layout.group("All Spirals", spirals)
    layout.group("Tunnel", rings)
    layout.group("All Spinners", spins)
    layout.group("All Arches", arches)
    return layout


def matrix_wall():
    layout = Layout("s11_matrix_wall", "Matrix Wall", "ultra", "A 40x20 panel matrix, two pixel-strip matrices, and three singing faces.")
    wall = rgb(layout, "Matrix 1", "Horiz Matrix", matrix_grid(80, 180, 720, 360, 40, 20), 40 * 20, "#7AA2FF", {"parm1": "40", "parm2": "20"})
    strips = [
        rgb(layout, "Matrix 2", "Horiz Matrix", matrix_grid(860, 360, 280, 80, 28, 4), 112, "#5EEAD4", {"parm1": "28", "parm2": "4"}),
        rgb(layout, "Matrix 3", "Horiz Matrix", matrix_grid(860, 220, 280, 80, 28, 4), 112, "#E879F9", {"parm1": "28", "parm2": "4"}),
    ]
    add_face(layout, "Singing Face 1", 980, 120, 1.3)
    add_face(layout, "Singing Face 2", 200, 80, 1.0)
    add_face(layout, "Singing Face 3", 500, 80, 1.0)
    rgb(layout, "Roofline", "Poly Line", line(40, 580, 1200, 600, steps=8), 80, "#FFB000")
    layout.group("Whole House", layout.names())
    layout.group("All Matrices", [wall, *strips])
    return layout


def band_stage():
    layout = Layout(
        "s12_band_stage",
        "Snowman Band Stage",
        "ultra",
        "Snowman band with singing faces, stage, backdrop matrix, drums, singing-tree faces, and a mega tree.",
    )
    mega = rgb(layout, "Mega Tree", "Tree 360", tree_outline(140, 40, 140, 360), 12 * 30, "#C77DFF", {"parm1": "12", "parm2": "30"})
    star = rgb(layout, "Star 1", "Star", star_poly(140, 430, 28), 30, "#FFE56B", {"parm1": "1", "parm2": "30", "parm3": "5"})
    stage = rgb(layout, "Stage", "Poly Line", rect(280, 80, 720, 40), 80, "#F8C8DC")
    backdrop = rgb(layout, "Backdrop Matrix", "Horiz Matrix", matrix_grid(300, 140, 680, 220, 34, 12), 34 * 12, "#7AA2FF", {"parm1": "34", "parm2": "12"})
    add_face(layout, "Singing Face Lead", 620, 400, 1.5)
    add_face(layout, "Singing Face Guitar", 900, 340, 1.15)
    add_face(layout, "Singing Face Bass", 360, 340, 1.15)
    add_face(layout, "Singing Face Drummer", 1080, 300, 1.0)
    rgb(layout, "Snowman Lead", "Poly Line", ellipse(620, 300, 36, 50, steps=16), 40, "#F8C8DC")
    rgb(layout, "Snowman Guitar", "Poly Line", ellipse(900, 250, 30, 42, steps=14), 32, "#F8C8DC")
    rgb(layout, "Snowman Bass", "Poly Line", ellipse(360, 250, 30, 42, steps=14), 32, "#F8C8DC")
    rgb(layout, "Guitar", "Single Line", line(860, 220, 980, 360, steps=8), 24, "#F6AD55")
    rgb(layout, "Bass Guitar", "Single Line", line(300, 220, 420, 360, steps=8), 24, "#F6AD55")
    drums = [
        ("HX_SNOWMAN_DRUMMER_KICK", ellipse(1040, 160, 26, 14, steps=8), 16),
        ("HX_SNOWMAN_DRUMMER_SNARE", ellipse(1100, 210, 16, 8, steps=8), 12),
        ("HX_SNOWMAN_DRUMMER_TOM_1", ellipse(1060, 240, 12, 8, steps=8), 10),
        ("HX_SNOWMAN_DRUMMER_TOM_2", ellipse(1120, 240, 12, 8, steps=8), 10),
        ("HX_SNOWMAN_DRUMMER_TOM_3", ellipse(1050, 270, 10, 6, steps=6), 8),
        ("HX_SNOWMAN_DRUMMER_TOM_4", ellipse(1130, 270, 10, 6, steps=6), 8),
        ("HX_SNOWMAN_DRUMMER_HI_HAT", line(1000, 300, 1040, 320, steps=4), 8),
        ("HX_SNOWMAN_DRUMMER_CYMBAL_LEFT", ellipse(990, 340, 18, 5, steps=8), 12),
        ("HX_SNOWMAN_DRUMMER_CYMBAL_RIGHT", ellipse(1160, 340, 18, 5, steps=8), 12),
    ]
    for name, points, pixels in drums:
        rgb(layout, name, "Poly Line", points, pixels, "#F6AD55")
    add_face(layout, "Singing Tree Face 1", 1180, 180, 0.9)
    rgb(layout, "Pixel Tree 1", "Tree Flat", tree_outline(1180, 60, 50, 120), 40, "#39E07A", {"parm1": "4", "parm2": "10"})
    layout.group("Whole House", layout.names())
    layout.group("Mega Tree Group", [mega, star])
    layout.group("All Matrices", [backdrop])
    layout.group("Stage Group", [stage, "Snowman Lead", "Snowman Guitar", "Snowman Bass"])
    return layout


BUILDERS = [
    build_ac16,
    lambda: build_ac_count(64, "s02_ac64", "LOR 64 Yard", "64-channel LOR yard: house outline, arches, canes, wreaths, and stake lights."),
    lambda: build_ac_count(256, "s03_ac256", "LOR 256 Show", "256-channel AC show: the same LOR vocabulary expanded across the whole yard."),
    porch_rgb,
    arches_faces,
    pixel_yard,
    mega_start,
    busy_rgb,
    mega_grove,
    helix_tunnel,
    matrix_wall,
    band_stage,
]


def write_layout_xml(layout: Layout, path: Path) -> None:
    root = ET.Element("xrgb")
    root.append(ET.Comment(" Helix showcase12 fixture. Synthetic geometry. No imported show data. "))
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
            "ScaleX": "1.0000",
            "ScaleY": "1.0000",
            "ScaleZ": "1.0000",
            "versionNumber": "7",
            "StartChannel": str(spec["start"]),
            "NumPoints": str(len(spec["local"])),
            "PointData": ",".join(f"{x:.4f},{y:.4f},{z:.4f}" for x, y, z in spec["local"]),
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
        ET.SubElement(groups, "modelGroup", {"name": name, "models": ",".join(members), "layout": "minimalGrid", "GridSize": "400", "LayoutGroup": "Default"})
    path.parent.mkdir(parents=True, exist_ok=True)
    ET.indent(root, space="  ")
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


def write_template(layout: Layout, path: Path) -> None:
    root = ET.Element("xsequence", {"BaseChannel": "0", "ChanCtrlBasic": "0", "ChanCtrlColor": "0", "FixedPointTiming": "1", "ModelBlending": "true"})
    head = ET.SubElement(root, "head")
    for tag, text in (
        ("version", "2026.01"),
        ("author", "Helix showcase12"),
        ("comment", "Clean-room empty template."),
        ("sequenceTiming", "50 ms"),
        ("sequenceType", "Media"),
        ("mediaFile", ""),
        ("sequenceDuration", "35.000"),
    ):
        ET.SubElement(head, tag).text = text
    ET.SubElement(root, "nextid").text = "1"
    palettes = ET.SubElement(root, "ColorPalettes")
    ET.SubElement(palettes, "ColorPalette").text = "C_BUTTON_Palette1=#FFFFFF,C_CHECKBOX_Palette1=1"
    ET.SubElement(palettes, "ColorPalette").text = "C_BUTTON_Palette1=#FF0000,C_BUTTON_Palette2=#00FF00,C_CHECKBOX_Palette1=1,C_CHECKBOX_Palette2=1"
    display = ET.SubElement(root, "DisplayElements")
    ET.SubElement(display, "Element", {"collapsed": "0", "type": "timing", "name": "Beats", "visible": "1", "active": "1"})
    ET.SubElement(display, "Element", {"collapsed": "0", "type": "model", "name": "Bench Palette", "visible": "1"})
    effects = ET.SubElement(root, "ElementEffects")
    timing = ET.SubElement(effects, "Element", {"type": "timing", "name": "Beats"})
    ET.SubElement(timing, "EffectLayer")
    layer = ET.SubElement(ET.SubElement(effects, "Element", {"type": "model", "name": "Bench Palette"}), "EffectLayer")
    samples = [
        ("On", "0", "50", "0", "E_TEXTCTRL_Eff_On_Start=100,E_TEXTCTRL_Eff_On_End=100"),
        ("Bars", "50", "100", "0", ""),
        ("Wave", "100", "150", "0", ""),
        ("Faces", "150", "200", "0", "E_CHOICE_Faces_FaceDefinition=NodeRange,E_CHOICE_Faces_TimingTrack=Phonemes,E_CHOICE_Faces_Eyes=Auto"),
    ]
    for name, start, end, palette, settings in samples:
        attrib = {"name": name, "startTime": start, "endTime": end, "palette": palette}
        if settings:
            attrib["settings"] = settings
        ET.SubElement(layer, "Effect", attrib)
    ET.SubElement(root, "lastView").text = "0"
    path.parent.mkdir(parents=True, exist_ok=True)
    ET.indent(root, space="  ")
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


def main() -> int:
    from tools.showcase12.houses import BUILDERS

    manifest = []
    for builder in BUILDERS:
        layout = builder()
        folder = OUT_DIR / layout.layout_id
        write_layout_xml(layout, folder / "xlights_rgbeffects.xml")
        write_template(layout, folder / "template.xsq")
        if layout.silhouette:
            (folder / "house.json").write_text(
                json.dumps({"polygons": layout.silhouette}, indent=2) + "\n",
                encoding="utf-8",
            )
        pixels = sum(model["pixels"] for model in layout.models)
        manifest.append(
            {
                "id": layout.layout_id,
                "title": layout.title,
                "tier": layout.tier,
                "summary": layout.summary,
                "layout": str((folder / "xlights_rgbeffects.xml").relative_to(ROOT)),
                "template": str((folder / "template.xsq").relative_to(ROOT)),
                "channels": layout.channel_count,
                "pixels": pixels,
                "props": layout.names(),
            }
        )
        print(f"{layout.layout_id:16} {layout.channel_count:6} ch  {pixels:5} px  {layout.title}")
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
