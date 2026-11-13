"""Editable illuminated brewery signage and 3D brewery prop geometry.

All branding letters are native xLights Custom pixels, not image overlays.
No unofficial logo is reproduced: this is plain-text concept branding.
"""
from __future__ import annotations
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont


def _letter_points(text, *, x=0, y=0, z=0, scale=.65, plane="xy"):
    font = ImageFont.truetype("DejaVuSans-Bold.ttf", 18)
    box = font.getbbox(text)
    w = box[2] - box[0] + 4
    h = box[3] - box[1] + 4
    image = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(image)
    draw.text((2 - box[0], 2 - box[1]), text, 255, font=font)
    occupied = np.argwhere(np.asarray(image) > 128)
    if len(occupied) == 0:
        raise ValueError("Empty brewery signage")
    coords = []
    for row, col in occupied:
        offset = (float(col) - (w - 1) / 2) * scale
        high = (float(h - 1 - row)) * scale
        if plane == "xy":
            coords.append((x + offset, y + high, z))
        elif plane == "zy":
            coords.append((x, y + high, z + offset))
        else:
            raise ValueError(plane)
    return np.asarray(coords)


def add_sign(g, text, *, name, pos, plane="xy", size=1., color="#FFD38A"):
    points = _letter_points(text, x=pos[0], y=pos[1], z=pos[2],
                            scale=.60 * size, plane=plane)
    model = g.custom(name, points, "BRAND_SIGNAGE",
                     "Always readable physical brewery pixel lettering",
                     [color] * len(points),
                     {"LETTERS": list(range(1, len(points) + 1))},
                     details={"brand_sign": True, "musical_role": "guitarist",
                              "parade_layer": "BRAND_SIGNAGE",
                              "source_display_floor": .52,
                              "always_readable": True})
    model.attrs.update(PixelSize="10", Antialias="1",
                       BlackTransparency="100")
    return model


def add_brewery_details(g):
    """Build real xLights editable illuminated tanks, rings, kegs and pipes."""
    from models.approval_layouts import structures
    s = structures(g)
    start = len(g.models)
    for side in (-1, 1):
        x = side * 43
        for z in (-50, -35):
            for level in (10, 20, 30, 38):
                s.ring("BREW_KETTLE_HOOP", (x, level, z), 5.4, 5.4,
                       "BREWERY_PROPS", int(level / 10), plane="xz", count=65)
            for dx in (-5, 5):
                s.path("BREW_TANK_WALL",
                       [(x + dx, 10, z), (x + dx, 38, z)],
                       "BREWERY_PROPS", 1, count=60)
            s.path("BREW_TANK_PIPE",
                   [(x, 39, z), (x, 44, z), (x - side * 7, 44, z + 5)],
                   "BREWERY_PROPS", 0, count=90)
        for z in (37, 53):
            for level in (4, 9, 14):
                s.ring("KEG_RING", (x, level, z), 4.8, 4.8, "BREWERY_PROPS",
                       int(level / 4), plane="xz", count=60)
        # A suspended hop cone silhouette composed of independently rendered
        # loops; prevents confusion with fake proprietary trademark artwork.
        for i in range(4):
            ypos = 39 + i * 2.5
            s.ring("HOP_PETAL", (x, ypos, 65), 2.5 + i * .5, 1.9,
                   "BREWERY_PROPS", i, plane="xy", count=45)
    for m in g.models[start:]:
        m.zone = "BREWERY_PROPS"
        m.details.update(musical_role="bassist",
                         parade_layer="BREWERY_PROPS",
                         spatial_axis="y", source_display_floor=.31)
        m.attrs.update(BlackTransparency="100", PixelSize="8", Antialias="1")


def add_brewery_signage(g):
    # Physical front/rear and both long sides. X/z positions are design units,
    # not a street-legal vehicle dimension.
    signs = [
        ("DRASTIC MEASURES", "HX_BRAND_FRONT", (0, 3, 82), "xy", .85),
        ("BREWERY WADENA MN", "HX_BRAND_REAR", (0, 3, -82), "xy", .83),
        ("DRASTIC MEASURES BREWERY", "HX_BRAND_SIDE_L", (-54, 5, 0), "zy", .74),
        ("DRASTIC MEASURES BREWERY", "HX_BRAND_SIDE_R", (54, 5, 0), "zy", .74),
    ]
    for text, name, pos, plane, scale in signs:
        add_sign(g, text, name=name, pos=pos, plane=plane, size=scale)
    add_brewery_details(g)
