"""Realistic front-elevation houses for the 12-panel showcase.

Coordinates are inches, y up. The street is at the bottom of the preview and
the house sits at the back of the yard, the way an xLights layout is drawn.
"""

from __future__ import annotations

import math


FT = 12.0
SPACING = 3.0  # inches between RGB nodes


def _g():
    from tools.showcase12 import generate_layouts as g

    return g


def length(points) -> float:
    total = 0.0
    for a, b in zip(points, points[1:]):
        total += math.dist(a[:2], b[:2])
    return total


def nodes(points, spacing=SPACING, minimum=8) -> int:
    return max(minimum, int(round(length(points) / spacing)))


def line(x1, y1, x2, y2, steps=2):
    return [
        (x1 + (x2 - x1) * i / (steps - 1), y1 + (y2 - y1) * i / (steps - 1), 0.0)
        for i in range(max(2, steps))
    ]


def rect(x, y, w, h):
    return [(x, y, 0.0), (x + w, y, 0.0), (x + w, y + h, 0.0), (x, y + h, 0.0), (x, y, 0.0)]


def ellipse(cx, cy, rx, ry, steps=18):
    return [
        (cx + math.cos(math.tau * i / steps) * rx, cy + math.sin(math.tau * i / steps) * ry, 0.0)
        for i in range(steps + 1)
    ]


def cone_wrap(cx, base_y, height, radius, turns=5.0, steps=64):
    """Evergreen wrapped from the tip down to the skirt."""
    pts = []
    for i in range(steps):
        t = i / (steps - 1)
        ang = turns * math.tau * t
        r = radius * t
        pts.append((cx + math.cos(ang) * r, base_y + height * (1.0 - t), 0.0))
    return pts


def tree_fan(cx, base_y, height, radius, strings, nodes_each):
    """Front view of a cone mega tree: each string from the topper to the skirt."""
    pts = []
    for s in range(strings):
        ang = math.pi * (s / max(1, strings - 1) - 0.5)  # -90..90 degrees across the front
        # Spread strings across the visible skirt, not a full circle.
        bx = cx + math.sin(ang) * radius
        for n in range(nodes_each):
            t = n / max(1, nodes_each - 1)
            pts.append((cx + (bx - cx) * t, base_y + height * (1.0 - t), 0.0))
    return pts


def shrub(cx, cy, w, h):
    return ellipse(cx, cy, w / 2, h / 2, steps=14)


def cane(x, y, h=42.0, w=14.0):
    pts = [(x, y, 0.0), (x, y + h * 0.72, 0.0)]
    for i in range(8):
        ang = math.pi * i / 7.0
        pts.append((x + math.sin(ang) * w, y + h * 0.72 + (1.0 - math.cos(ang)) * w, 0.0))
    return pts


def arch(cx, base_y, width, height, steps=16):
    pts = []
    for i in range(steps):
        t = i / (steps - 1)
        ang = math.pi * (1.0 - t)
        pts.append((cx + math.cos(ang) * width / 2.0, base_y + math.sin(ang) * height, 0.0))
    return pts


class Yard:
    """A house front plus the yard in front of it."""

    def __init__(self, layout, *, left, right, wall_base, wall_top, peak, peak_x=None):
        self.layout = layout
        self.left = left
        self.right = right
        self.wall_base = wall_base
        self.wall_top = wall_top
        self.peak = peak
        self.peak_x = peak_x if peak_x is not None else (left + right) / 2
        self.over = 18  # 18 inch overhang
        layout.silhouette = []

    def poly(self, kind, points):
        self.layout.silhouette.append({"kind": kind, "points": [[p[0], p[1]] for p in points]})

    def shell(self, wings=True):
        """Center-gable wall and roof. Wings stay at eave height."""
        L, R, B, E, P, X = self.left, self.right, self.wall_base, self.wall_top, self.peak, self.peak_x
        gable_l, gable_r = X - 90, X + 90
        mass = [(L, B), (R, B), (R, E), (gable_r, E), (X, P), (gable_l, E), (L, E)]
        self.poly("wall", mass)
        roof = [(L - self.over, E), (gable_l, E), (X, P + 8), (gable_r, E), (R + self.over, E)]
        self.poly("roof", roof)
        self.poly("ground", [(40, 20), (R + 220, 20), (R + 180, B - 30), (L - 140, B - 30)])
        return {
            "eave_left": line(L - self.over, E, gable_l, E, steps=8),
            "rake_left": line(gable_l, E, X, P, steps=8),
            "rake_right": line(X, P, gable_r, E, steps=8),
            "eave_right": line(gable_r, E, R + self.over, E, steps=8),
            "ridge": line(X, P, X, P + 6, steps=2),
        }

    def opening(self, x, y, w, h):
        self.poly("opening", [(x, y), (x + w, y), (x + w, y + h), (x, y + h)])
        return rect(x, y, w, h)

    def ac(self, name, points, color_name, hex_color, display="Poly Line", extra=None):
        return _g().ac(self.layout, name, points, color_name, hex_color, display, extra)

    def rgb_line(self, name, points, color, display="Poly Line", extra=None, minimum=8):
        count = nodes(points, minimum=minimum)
        return _g().rgb(self.layout, name, display, points, count, color, extra)

    def window_ac(self, name, x, y, w, h):
        self.opening(x, y, w, h)
        return self.ac(name, rect(x, y, w, h), "White", "#FFFFFF", "Window Frame", _g().AC_WINDOW)

    def window_rgb(self, name, x, y, w, h):
        self.opening(x, y, w, h)
        return self.rgb_line(name, rect(x, y, w, h), "#F4F1DE", minimum=12)

    def door(self, name, x, y, w, h, rgb=False):
        self.opening(x, y, w, h)
        pts = rect(x, y, w, h)
        if rgb:
            return self.rgb_line(name, pts, "#F8E7C9", minimum=16)
        return self.ac(name, pts, "White", "#FFFFFF")

    def garage(self, name, x, y, w, h, rgb=False):
        self.opening(x, y, w, h)
        pts = rect(x, y, w, h)
        if rgb:
            return self.rgb_line(name, pts, "#E8EEF2", minimum=24)
        return self.ac(name, pts, "White", "#FFFFFF")

    def evergreen(self, name, cx, base, height, radius, rgb=False, color="#39E07A"):
        pts = cone_wrap(cx, base, height, radius, turns=4.5, steps=48)
        if rgb:
            return self.rgb_line(name, pts, color, minimum=40)
        return self.ac(name, pts, "Green", color, "Poly Line")

    def bush(self, name, cx, base, w=36, h=28, rgb=False):
        pts = shrub(cx, base + h / 2, w, h)
        if rgb:
            return self.rgb_line(name, pts, "#2EC4B6", minimum=16)
        return self.ac(name, pts, "Green", "#00AA44")

    def path_stakes(self, prefix, x0, x1, y, count, rgb=False):
        names = []
        for i in range(count):
            x = x0 + (x1 - x0) * i / max(1, count - 1)
            pts = line(x, y, x, y + 18, steps=2)
            label = f"{prefix} {i + 1}"
            if rgb:
                self.rgb_line(label, pts, "#FFF4D0", minimum=6)
            else:
                self.ac(label, pts, "White", "#FFFFFF")
            names.append(label)
        return names


def _finish(layout, groups):
    layout.group("Whole House", layout.names())
    for name, members in groups:
        layout.group(name, [m for m in members if m])
    return layout


def build_ac16():
    g = _g()
    layout = g.Layout(
        "s01_ac16",
        "LOR 16 Ranch",
        "ac",
        "40-foot one-story ranch: center gable, garage, three windows, foundation shrubs, and two yard evergreens.",
    )
    yard = Yard(layout, left=240, right=720, wall_base=300, wall_top=420, peak=510)
    edges = yard.shell()
    red, green, white = "#FF0000", "#00FF00", "#FFFFFF"
    yard.ac("Eave Left", edges["eave_left"], "White", white)
    yard.ac("Gable Rake Left", edges["rake_left"], "Red", red)
    yard.ac("Gable Rake Right", edges["rake_right"], "Green", green)
    yard.ac("Eave Right", edges["eave_right"], "White", white)
    yard.ac("Garage Door", yard.opening(270, 300, 150, 84), "White", white)
    yard.ac("Front Door", yard.opening(456, 300, 40, 84), "Red", red)
    yard.window_ac("Window Frame 1", 560, 340, 40, 48)
    yard.window_ac("Window Frame 2", 630, 340, 40, 48)
    yard.ac("Porch Rail", line(430, 300, 520, 300, steps=6), "White", white)
    yard.bush("Bush 1", 400, 268)
    yard.bush("Bush 2", 560, 268)
    yard.evergreen("Mini Tree 1", 140, 150, 96, 36)
    yard.evergreen("Mini Tree 2", 840, 140, 110, 42)
    yard.ac("Wreath 1", ellipse(476, 360, 14, 16, steps=12), "Green", green)
    yard.ac("Candy Cane 1", cane(430, 160), "Red", red, "Candy Canes")
    yard.ac("Mailbox", line(90, 80, 90, 150, steps=2) + line(90, 150, 130, 150, steps=2), "White", white)
    if layout.channel_count != 16:
        raise RuntimeError(f"s01 has {layout.channel_count} channels")
    return _finish(layout, [("All Mini Trees", ["Mini Tree 1", "Mini Tree 2"])])


def build_ac64():
    g = _g()
    layout = g.Layout(
        "s02_ac64",
        "LOR 64 Colonial",
        "ac",
        "Two-story colonial: upper and lower windows, porch columns, dormer, fence, and a walk of candy canes.",
    )
    yard = Yard(layout, left=220, right=760, wall_base=280, wall_top=520, peak=640)
    # Two-story mass: eave at 520, peak 640.
    L, R, B, E, P = 220, 760, 280, 520, 640
    X = 490
    layout.silhouette = []
    yard.poly("ground", [(30, 16), (980, 16), (900, 250), (80, 250)])
    yard.poly("wall", [(L, B), (R, B), (R, E), (X + 80, E), (X, P), (X - 80, E), (L, E)])
    yard.poly("roof", [(L - 16, E), (X - 80, E), (X, P + 10), (X + 80, E), (R + 16, E)])
    yard.poly("wall", [(X - 36, E), (X + 36, E), (X + 36, E + 36), (X, E + 70), (X - 36, E + 36)])  # dormer
    red, green, white = "#FF0000", "#00FF00", "#FFFFFF"
    colors = [("Red", red), ("Green", green), ("White", white)]
    runs = [
        ("Eave Left", line(L - 16, E, X - 80, E, steps=6), "White", white),
        ("Gable Rake Left", line(X - 80, E, X, P, steps=8), "Red", red),
        ("Ridge", line(X - 10, P, X + 10, P, steps=2), "White", white),
        ("Gable Rake Right", line(X, P, X + 80, E, steps=8), "Green", green),
        ("Eave Right", line(X + 80, E, R + 16, E, steps=6), "White", white),
        ("Dormer Rake Left", line(X - 36, E + 28, X, E + 70, steps=4), "Red", red),
        ("Dormer Rake Right", line(X, E + 70, X + 36, E + 28, steps=4), "Green", green),
        ("Fascia Upper", line(L, E - 8, R, E - 8, steps=8), "White", white),
    ]
    for name, pts, cname, hex_color in runs:
        yard.ac(name, pts, cname, hex_color)
    yard.garage("Garage Door", 246, B, 140, 84)
    yard.door("Front Door", 470, B, 42, 90)
    # First and second floor windows.
    for i, x in enumerate((250, 340, 560, 650)):
        yard.window_ac(f"Window Frame {i + 1}", x, 330, 36, 48)
    for i, x in enumerate((250, 340, 470, 560, 650)):
        yard.window_ac(f"Window Frame {i + 5}", x, 450, 36, 44)
    yard.ac("Porch Column 1", line(440, B, 440, B + 96, steps=3), "White", white)
    yard.ac("Porch Column 2", line(540, B, 540, B + 96, steps=3), "White", white)
    yard.ac("Porch Rail", line(400, B + 8, 580, B + 8, steps=8), "White", white)
    yard.ac("Wreath 1", ellipse(491, B + 55, 14, 16, steps=12), "Green", green)
    for i, x in enumerate((150, 180, 860, 900)):
        yard.evergreen(f"Mini Tree {i + 1}", x, 150 + (i % 2) * 20, 90 + (i % 3) * 16, 34)
    for i, x in enumerate((300, 400, 600, 700)):
        yard.bush(f"Bush {i + 1}", x, 250)
    yard.ac("Mailbox", line(70, 70, 70, 140, steps=2), "White", white)
    yard.ac("Fence Left", line(40, 200, 140, 210, steps=8), "White", white)
    yard.ac("Fence Right", line(860, 210, 980, 200, steps=8), "White", white)
    for i in range(8):
        cname, hex_color = colors[i % 3]
        yard.ac(f"Candy Cane {i + 1}", cane(360 + i * 28, 120), cname, hex_color, "Candy Canes")
    # Walk and drive stakes to reach 64.
    i = 1
    while layout.channel_count < 64:
        cname, hex_color = colors[i % 3]
        x = 80 + ((i - 1) % 24) * 36
        y = 50 + ((i - 1) // 24) * 28
        yard.ac(f"Stake Light {i}", line(x, y, x, y + 16, steps=2), cname, hex_color)
        i += 1
    if layout.channel_count != 64:
        raise RuntimeError(layout.channel_count)
    return _finish(layout, [("All Mini Trees", [f"Mini Tree {n}" for n in range(1, 5)])])


def build_ac256():
    g = _g()
    layout = g.Layout(
        "s03_ac256",
        "LOR 256 Estate",
        "ac",
        "Wide two-story with three gables: every window, eave, and stake on its own AC channel.",
    )
    yard = Yard(layout, left=180, right=980, wall_base=260, wall_top=500, peak=640, peak_x=580)
    L, R, B, E = 180, 980, 260, 500
    layout.silhouette = []
    yard.poly("ground", [(20, 12), (1180, 12), (1100, 230), (60, 230)])
    yard.poly("drive", [(200, 16), (420, 16), (460, 250), (240, 250)])
    # Three gables.
    peaks = [(320, 600), (580, 660), (840, 600)]
    wall = [(L, B), (R, B), (R, E)]
    for px, py in reversed(peaks):
        wall.append((px + 70, E))
        wall.append((px, py))
        wall.append((px - 70, E))
    wall.append((L, E))
    yard.poly("wall", wall)
    roof = [(L - 16, E)]
    for px, py in peaks:
        roof.extend([(px - 70, E), (px, py + 8), (px + 70, E)])
    roof.append((R + 16, E))
    yard.poly("roof", roof)
    red, green, white = "#FF0000", "#00FF00", "#FFFFFF"
    colors = [("Red", red), ("Green", green), ("White", white)]
    n = 1

    def add(name, pts, cname, hex_color, display="Poly Line"):
        nonlocal n
        yard.ac(name, pts, cname, hex_color, display)
        n += 1

    add("Eave Front", line(L - 16, E, R + 16, E, steps=12), "White", white)
    for i, (px, py) in enumerate(peaks, start=1):
        add(f"Gable {i} Rake Left", line(px - 70, E, px, py, steps=6), "Red", red)
        add(f"Gable {i} Rake Right", line(px, py, px + 70, E, steps=6), "Green", green)
        add(f"Ridge {i}", line(px - 8, py, px + 8, py, steps=2), "White", white)
    # Two floors of windows across the facade.
    win = 1
    for floor_y in (300, 420):
        for x in range(210, 940, 70):
            if layout.channel_count >= 256:
                break
            yard.window_ac(f"Window Frame {win}", x, floor_y, 36, 46)
            win += 1
    yard.garage("Garage Door", 200, B, 160, 84)
    yard.door("Front Door", 540, B, 44, 92)
    yard.ac("Porch Column 1", line(510, B, 510, B + 100, steps=3), "White", white)
    yard.ac("Porch Column 2", line(610, B, 610, B + 100, steps=3), "White", white)
    yard.ac("Porch Rail", line(470, B + 6, 660, B + 6, steps=8), "White", white)
    for i, x in enumerate(range(80, 160, 20)):
        yard.evergreen(f"Mini Tree {i + 1}", x, 140, 100, 36)
    for i, x in enumerate(range(1040, 1160, 30)):
        yard.evergreen(f"Mini Tree {i + 5}", x, 130, 90, 32)
    for i, x in enumerate(range(240, 960, 80)):
        yard.bush(f"Bush {i + 1}", x, 230)
    yard.ac("Mailbox", line(50, 60, 50, 130, steps=2), "White", white)
    yard.ac("Fence", line(20, 180, 160, 190, steps=10), "White", white)
    for i in range(12):
        cname, hex_color = colors[i % 3]
        yard.ac(f"Candy Cane {i + 1}", cane(430 + i * 22, 100), cname, hex_color, "Candy Canes")
    i = 1
    while layout.channel_count < 256:
        cname, hex_color = colors[i % 3]
        col = (i - 1) % 40
        row = (i - 1) // 40
        yard.ac(
            f"Stake Light {i}",
            line(30 + col * 28, 30 + row * 22, 30 + col * 28, 46 + row * 22, steps=2),
            cname,
            hex_color,
        )
        i += 1
    if layout.channel_count != 256:
        raise RuntimeError(layout.channel_count)
    return _finish(layout, [])


def _rgb_ranch(layout_id, title, summary, tier="rgb"):
    g = _g()
    layout = g.Layout(layout_id, title, tier, summary)
    yard = Yard(layout, left=240, right=720, wall_base=300, wall_top=420, peak=510)
    edges = yard.shell()
    roof = "#FFB000"
    for name, key in (
        ("Eave Left", "eave_left"),
        ("Gable Rake Left", "rake_left"),
        ("Gable Rake Right", "rake_right"),
        ("Eave Right", "eave_right"),
    ):
        yard.rgb_line(name, edges[key], roof, minimum=40)
    yard.garage("Garage Door", 270, 300, 150, 84, rgb=True)
    yard.door("Front Door", 456, 300, 40, 84, rgb=True)
    yard.window_rgb("Window Frame 1", 560, 340, 40, 48)
    yard.window_rgb("Window Frame 2", 630, 340, 40, 48)
    yard.rgb_line("Porch Rail", line(430, 300, 520, 300, steps=8), "#F8E7C9", minimum=16)
    yard.bush("Bush 1", 400, 268, rgb=True)
    yard.bush("Bush 2", 680, 268, rgb=True)
    yard.evergreen("Mini Tree 1", 140, 150, 108, 40, rgb=True)
    yard.evergreen("Mini Tree 2", 840, 140, 120, 44, rgb=True)
    yard.rgb_line("Wreath 1", ellipse(476, 360, 14, 16, steps=16), "#39E07A", minimum=16)
    return yard


def build_pixel_porch():
    layout_yard = _rgb_ranch(
        "s04_rgb_porch",
        "Pixel Ranch",
        "Same 40-foot ranch in pixels: roofline, garage, windows, and two wrapped evergreens at 3-inch spacing.",
    )
    layout = layout_yard.layout
    layout_yard.rgb_line("Walkway", line(476, 300, 476, 40, steps=12), "#FFF4D0", minimum=30)
    return _finish(layout, [("All Mini Trees", ["Mini Tree 1", "Mini Tree 2"])])


def build_arches_faces():
    yard = _rgb_ranch(
        "s05_arches_faces",
        "Colonial With Arches",
        "Ranch front plus three yard arches, two spinners, candy canes, and a porch singing face.",
    )
    layout = yard.layout
    arches = []
    for i, cx in enumerate((300, 480, 680)):
        arches.append(yard.rgb_line(f"Arch {i + 1}", arch(cx, 80, 140, 90), "#3DDCFF", minimum=30))
    spins = []
    for i, cx in enumerate((180, 820)):
        spins.append(
            _g().rgb(
                layout,
                f"Spinner {i + 1}",
                "Spinner",
                ellipse(cx, 160, 24, 8, steps=8),
                8 * 12,
                "#FF7A3C",
                {"parm1": "1", "parm2": "12", "ArmsPerString": "8", "NodesPerArm": "12"},
            )
        )
    for i in range(6):
        yard.rgb_line(f"Candy Cane {i + 1}", cane(380 + i * 36, 50), "#FF4FA3", minimum=12)
    _g().add_face(layout, "Singing Face 1", 476, 390, 1.6)
    return _finish(layout, [("All Arches", arches), ("All Spinners", spins), ("All Mini Trees", ["Mini Tree 1", "Mini Tree 2"])])


def build_pixel_yard():
    yard = _rgb_ranch(
        "s06_pixel_yard",
        "Pixel Yard",
        "Ranch with four arches, three spinners, two singing faces, and a singing tree in the side yard.",
    )
    layout = yard.layout
    arches = [yard.rgb_line(f"Arch {i}", arch(260 + i * 120, 70, 110, 80), "#3DDCFF", minimum=28) for i in range(1, 5)]
    spins = []
    for i, cx in enumerate((120, 500, 880)):
        spins.append(
            _g().rgb(
                layout,
                f"Spinner {i + 1}",
                "Spinner",
                ellipse(cx, 150, 22, 8, steps=8),
                8 * 10,
                "#FF7A3C",
                {"parm1": "1", "parm2": "10", "ArmsPerString": "8", "NodesPerArm": "10"},
            )
        )
    _g().add_face(layout, "Singing Face 1", 430, 390, 1.4)
    _g().add_face(layout, "Singing Face 2", 560, 390, 1.4)
    yard.evergreen("Pixel Tree 1", 980, 160, 140, 50, rgb=True, color="#39E07A")
    _g().add_face(layout, "Singing Tree Face 1", 980, 250, 1.2)
    _matrix(layout, "Matrix 1", 270, 312, 140, 70, 20, 8)
    return _finish(
        layout,
        [
            ("All Arches", arches),
            ("All Spinners", spins),
            ("All Matrices", ["Matrix 1"]),
            ("All Mini Trees", ["Mini Tree 1", "Mini Tree 2"]),
        ],
    )


def _matrix(layout, name, x, y, w, h, cols, rows, color="#7AA2FF"):
    pts = [
        (x, y, 0.0),
        (x + w, y, 0.0),
        (x + w, y + h, 0.0),
        (x, y + h, 0.0),
        (x, y, 0.0),
    ]
    return _g().rgb(
        layout,
        name,
        "Horiz Matrix",
        pts,
        cols * rows,
        color,
        {"parm1": str(cols), "parm2": str(rows)},
    )


def _mega(layout, name, cx, base, height, radius, strings, per_string):
    pts = tree_fan(cx, base, height, radius, strings, nodes_each=per_string)
    return _g().rgb(layout, name, "Poly Line", pts, strings * per_string, "#C77DFF")


def build_mega_yard():
    yard = _rgb_ranch(
        "s07_mega_yard",
        "Mega Tree Ranch",
        "Ranch with a 16-foot 16-string mega tree and star in the front yard, plus a porch matrix and a singing face.",
    )
    layout = yard.layout
    mega = _mega(layout, "Mega Tree", 120, 80, 16 * FT, 6 * FT, 16, 50)
    star = yard.rgb_line("Star 1", ellipse(120, 80 + 16 * FT, 18, 18, steps=10), "#FFE56B", minimum=24)
    _matrix(layout, "Matrix 1", 430, 308, 160, 48, 24, 6)
    _g().add_face(layout, "Singing Face 1", 620, 390, 1.5)
    arches = [yard.rgb_line(f"Arch {i}", arch(360 + i * 160, 60, 140, 86), "#3DDCFF", minimum=30) for i in range(1, 3)]
    return _finish(layout, [("Mega Tree Group", [mega, star]), ("All Matrices", ["Matrix 1"]), ("All Arches", arches)])


def build_busy():
    yard = _rgb_ranch(
        "s08_busy_rgb",
        "Busy Two-Story",
        "Taller facade, four arches, four spinners, singing faces on the porch, and two singing trees.",
    )
    layout = yard.layout
    # Raise the read of a second floor with another window row and a fascia.
    yard.rgb_line("Fascia Upper", line(240, 470, 720, 470, steps=10), "#FFB000", minimum=40)
    for i, x in enumerate((280, 400, 560, 640)):
        yard.window_rgb(f"Window Up {i + 1}", x, 430, 36, 40)
    arches = [yard.rgb_line(f"Arch {i}", arch(200 + i * 150, 50, 120, 78), "#3DDCFF", minimum=28) for i in range(1, 5)]
    spins = []
    for i, cx in enumerate((100, 320, 640, 900)):
        spins.append(
            _g().rgb(
                layout,
                f"Spinner {i + 1}",
                "Spinner",
                ellipse(cx, 130, 20, 8, steps=8),
                64,
                "#FF7A3C",
                {"parm1": "1", "parm2": "8", "ArmsPerString": "8", "NodesPerArm": "8"},
            )
        )
    _g().add_face(layout, "Singing Face 1", 450, 400, 1.3)
    _g().add_face(layout, "Singing Face 2", 540, 400, 1.3)
    yard.evergreen("Pixel Tree 1", 40, 160, 130, 46, rgb=True)
    yard.evergreen("Pixel Tree 2", 1000, 150, 150, 52, rgb=True)
    _g().add_face(layout, "Singing Tree Face 1", 40, 250, 1.1)
    _g().add_face(layout, "Singing Tree Face 2", 1000, 250, 1.1)
    return _finish(layout, [("All Arches", arches), ("All Spinners", spins)])


def build_mega_grove():
    g = _g()
    layout = g.Layout(
        "s09_mega_grove",
        "Two-Gable Mega Grove",
        "ultra",
        "Wide house with two gables, two 16-20 ft mega trees with stars, a spiral evergreen, and singing-tree faces.",
    )
    yard = Yard(layout, left=280, right=860, wall_base=280, wall_top=430, peak=540, peak_x=420)
    L, R, B, E = 280, 860, 280, 430
    layout.silhouette = []
    yard.poly("ground", [(20, 16), (1100, 16), (1020, 250), (40, 250)])
    yard.poly(
        "wall",
        [(L, B), (R, B), (R, E), (700, E), (780, 560), (860, E), (560, E), (480, 540), (400, E), (L, E)],
    )
    yard.poly("roof", [(L - 16, E), (400, E), (480, 548), (560, E), (700, E), (780, 568), (R + 16, E)])
    for name, pts in (
        ("Eave Left", line(L - 16, E, 400, E, steps=8)),
        ("Gable 1 Rake Left", line(400, E, 480, 540, steps=6)),
        ("Gable 1 Rake Right", line(480, 540, 560, E, steps=6)),
        ("Eave Mid", line(560, E, 700, E, steps=6)),
        ("Gable 2 Rake Left", line(700, E, 780, 560, steps=6)),
        ("Gable 2 Rake Right", line(780, 560, R + 16, E, steps=6)),
    ):
        yard.rgb_line(name, pts, "#FFB000", minimum=36)
    yard.garage("Garage Door", 300, B, 150, 84, rgb=True)
    yard.door("Front Door", 500, B, 42, 88, rgb=True)
    yard.window_rgb("Window Frame 1", 620, 320, 40, 48)
    yard.window_rgb("Window Frame 2", 700, 320, 40, 48)
    yard.window_rgb("Window Frame 3", 780, 330, 36, 44)
    mega_a = _mega(layout, "Mega Tree", 140, 70, 16 * FT, 6 * FT, 16, 48)
    mega_b = _mega(layout, "Mega Tree 2", 1020, 60, 20 * FT, 7 * FT, 20, 50)
    star_a = yard.rgb_line("Star 1", ellipse(140, 70 + 16 * FT, 16, 16, steps=8), "#FFE56B", minimum=16)
    star_b = yard.rgb_line("Star 2", ellipse(1020, 60 + 20 * FT, 18, 18, steps=8), "#FFE56B", minimum=16)
    spiral = yard.rgb_line("Spiral Tree 1", cone_wrap(1180, 80, 14 * FT, 48, turns=6, steps=80), "#67E8F9", minimum=80)
    g.add_face(layout, "Singing Tree Face 1", 140, 180, 1.2)
    g.add_face(layout, "Singing Tree Face 2", 1020, 200, 1.3)
    arches = [yard.rgb_line(f"Arch {i}", arch(360 + i * 160, 60, 130, 84), "#3DDCFF", minimum=30) for i in range(1, 4)]
    return _finish(
        layout,
        [
            ("Mega Tree Group", [mega_a, mega_b, star_a, star_b]),
            ("All Spirals", [spiral]),
            ("All Arches", arches),
        ],
    )


def build_helix_yard():
    g = _g()
    layout = g.Layout(
        "s10_helix_tunnel",
        "Driveway Helix",
        "ultra",
        "House on the street, with a driveway of arches, two helix-wrapped trees, and a row of spinners.",
    )
    yard = Yard(layout, left=360, right=900, wall_base=320, wall_top=440, peak=530)
    edges = yard.shell()
    for key in ("eave_left", "rake_left", "rake_right", "eave_right"):
        yard.rgb_line(key.replace("_", " ").title(), edges[key], "#FFB000", minimum=36)
    yard.garage("Garage Door", 390, 320, 150, 84, rgb=True)
    yard.door("Front Door", 620, 320, 40, 84, rgb=True)
    yard.window_rgb("Window Frame 1", 720, 360, 40, 48)
    yard.window_rgb("Window Frame 2", 790, 360, 40, 48)
    # Driveway arch tunnel, a real display, not floating rings.
    arches = [yard.rgb_line(f"Arch {i}", arch(180, 40 + i * 36, 200 - i * 10, 110), "#3DDCFF", minimum=36) for i in range(1, 5)]
    helix_a = yard.rgb_line("Double Helix 1 A", cone_wrap(1040, 80, 16 * FT, 36, turns=5, steps=70), "#E879F9", minimum=70)
    helix_b = yard.rgb_line(
        "Double Helix 1 B",
        [(x + 8, y, z) for x, y, z in cone_wrap(1040, 80, 16 * FT, 36, turns=5, steps=70)],
        "#67E8F9",
        minimum=70,
    )
    spins = []
    for i in range(5):
        spins.append(
            g.rgb(
                layout,
                f"Spinner {i + 1}",
                "Spinner",
                ellipse(260 + i * 90, 200, 18, 8, steps=8),
                48,
                "#FF7A3C",
                {"parm1": "1", "parm2": "8", "ArmsPerString": "6", "NodesPerArm": "8"},
            )
        )
    return _finish(layout, [("All Arches", arches), ("All Helixes", [helix_a, helix_b]), ("All Spinners", spins)])


def build_matrix_wall():
    g = _g()
    layout = g.Layout(
        "s11_matrix_wall",
        "Garage Matrix House",
        "ultra",
        "Two-story house whose garage door is a pixel matrix, plus window-strip matrices and three singing faces.",
    )
    yard = Yard(layout, left=300, right=920, wall_base=280, wall_top=500, peak=620)
    L, R, B, E, P = 300, 920, 280, 500, 620
    layout.silhouette = []
    yard.poly("ground", [(40, 16), (1100, 16), (1000, 240), (80, 240)])
    yard.poly("wall", [(L, B), (R, B), (R, E), ((L + R) / 2 + 80, E), ((L + R) / 2, P), ((L + R) / 2 - 80, E), (L, E)])
    yard.poly("roof", [(L - 16, E), ((L + R) / 2, P + 8), (R + 16, E)])
    yard.rgb_line("Eave Left", line(L - 16, E, (L + R) / 2 - 80, E, steps=8), "#FFB000", minimum=36)
    yard.rgb_line("Gable Rake Left", line((L + R) / 2 - 80, E, (L + R) / 2, P, steps=8), "#FFB000", minimum=36)
    yard.rgb_line("Gable Rake Right", line((L + R) / 2, P, (L + R) / 2 + 80, E, steps=8), "#FFB000", minimum=36)
    yard.rgb_line("Eave Right", line((L + R) / 2 + 80, E, R + 16, E, steps=8), "#FFB000", minimum=36)
    # Garage door matrix, about 8 ft by 7 ft at 3 inch cells: 32 x 28 is heavy; use 32 x 16.
    wall = _matrix(layout, "Matrix 1", 330, B, 8 * FT, 7 * FT, 32, 16)
    strips = [
        _matrix(layout, "Matrix 2", 560, 430, 3 * FT, 4 * FT, 16, 8, "#5EEAD4"),
        _matrix(layout, "Matrix 3", 680, 430, 3 * FT, 4 * FT, 16, 8, "#E879F9"),
    ]
    yard.door("Front Door", 800, B, 42, 90, rgb=True)
    yard.window_rgb("Window Frame 1", 560, 320, 36, 48)
    g.add_face(layout, "Singing Face 1", 200, 360, 1.5)
    g.add_face(layout, "Singing Face 2", 1040, 340, 1.4)
    g.add_face(layout, "Singing Face 3", 610, 200, 1.2)
    yard.rgb_line("Roofline", line(40, 560, 200, 560, steps=4), "#FFB000", minimum=20)
    return _finish(layout, [("All Matrices", [wall, *strips])])


def build_band():
    g = _g()
    layout = g.Layout(
        "s12_band_stage",
        "Yard Stage And House",
        "ultra",
        "The ranch stays on the left. A real stage sits in the side yard with snowmen, a backdrop matrix, drums, and a mega tree.",
    )
    yard = Yard(layout, left=80, right=520, wall_base=300, wall_top=420, peak=510, peak_x=300)
    edges = yard.shell()
    for key in ("eave_left", "rake_left", "rake_right", "eave_right"):
        yard.rgb_line(key.replace("_", " ").title(), edges[key], "#FFB000", minimum=30)
    yard.door("Front Door", 280, 300, 40, 84, rgb=True)
    yard.window_rgb("Window Frame 1", 380, 340, 40, 48)
    yard.window_rgb("Window Frame 2", 450, 340, 40, 48)
    # Stage deck in the right yard.
    layout.silhouette.append(
        {"kind": "stage", "points": [[620, 160], [1100, 160], [1100, 200], [620, 200]]}
    )
    stage = yard.rgb_line("Stage", rect(620, 160, 480, 40), "#F8C8DC", minimum=40)
    backdrop = _matrix(layout, "Backdrop Matrix", 640, 200, 440, 200, 34, 12)
    g.add_face(layout, "Singing Face Lead", 860, 340, 1.7)
    g.add_face(layout, "Singing Face Guitar", 1040, 300, 1.3)
    g.add_face(layout, "Singing Face Bass", 700, 300, 1.3)
    g.add_face(layout, "Singing Face Drummer", 1120, 280, 1.15)
    yard.rgb_line("Snowman Lead", ellipse(860, 250, 28, 40, steps=16), "#F8C8DC", minimum=24)
    yard.rgb_line("Snowman Guitar", ellipse(1040, 240, 24, 34, steps=14), "#F8C8DC", minimum=20)
    yard.rgb_line("Snowman Bass", ellipse(700, 240, 24, 34, steps=14), "#F8C8DC", minimum=20)
    yard.rgb_line("Guitar", line(1000, 230, 1100, 340, steps=6), "#F6AD55", minimum=16)
    yard.rgb_line("Bass Guitar", line(640, 230, 740, 330, steps=6), "#F6AD55", minimum=16)
    drums = [
        ("HX_SNOWMAN_DRUMMER_KICK", ellipse(1160, 190, 26, 14, steps=8), 16),
        ("HX_SNOWMAN_DRUMMER_SNARE", ellipse(1200, 230, 16, 8, steps=8), 12),
        ("HX_SNOWMAN_DRUMMER_TOM_1", ellipse(1170, 260, 12, 8, steps=6), 10),
        ("HX_SNOWMAN_DRUMMER_TOM_2", ellipse(1220, 260, 12, 8, steps=6), 10),
        ("HX_SNOWMAN_DRUMMER_TOM_3", ellipse(1164, 290, 10, 6, steps=6), 8),
        ("HX_SNOWMAN_DRUMMER_TOM_4", ellipse(1230, 290, 10, 6, steps=6), 8),
        ("HX_SNOWMAN_DRUMMER_HI_HAT", line(1130, 300, 1160, 330, steps=4), 8),
        ("HX_SNOWMAN_DRUMMER_CYMBAL_LEFT", ellipse(1120, 340, 16, 5, steps=8), 12),
        ("HX_SNOWMAN_DRUMMER_CYMBAL_RIGHT", ellipse(1260, 340, 16, 5, steps=8), 12),
    ]
    for name, pts, count in drums:
        g.rgb(layout, name, "Poly Line", pts, count, "#F6AD55")
    mega = _mega(layout, "Mega Tree", 1320, 80, 18 * FT, 6.5 * FT, 18, 46)
    star = yard.rgb_line("Star 1", ellipse(1320, 80 + 18 * FT, 16, 16, steps=8), "#FFE56B", minimum=16)
    g.add_face(layout, "Singing Tree Face 1", 1320, 200, 1.15)
    yard.evergreen("Mini Tree 1", 40, 160, 100, 36, rgb=True)
    return _finish(
        layout,
        [
            ("Mega Tree Group", [mega, star]),
            ("All Matrices", [backdrop]),
            ("Stage Group", [stage, "Snowman Lead", "Snowman Guitar", "Snowman Bass"]),
        ],
    )


BUILDERS = [
    build_ac16,
    build_ac64,
    build_ac256,
    build_pixel_porch,
    build_arches_faces,
    build_pixel_yard,
    build_mega_yard,
    build_busy,
    build_mega_grove,
    build_helix_yard,
    build_matrix_wall,
    build_band,
]
