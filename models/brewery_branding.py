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




# Compressed 112 x 146 monochrome shape traced from the owner-supplied
# November 12, 2025 Drastic Measures Brewing Facebook screenshot.
# The source crop excludes the Facebook UI, background and tree silhouettes.
# Exact logo source, unlike hand-drawn approximation; downsampling is a
# physical pixel-density choice. No logo redistribution license inferred.
_LOGO_MASK_B64 = (
"eNqt1Ttu3DAQAFDKLNQElssUAXSFlK4sH8VHcJnCWMlw4dJH8FFCI0VKX4GAL6CSBriccIbkkGOttgqBxeotf7P8jJQ6W8alPv_QYK5Zh6gH1gwAYU-61Y3op_TRfBdS_0FQdZHU18CoLEJOCOiPswyNWMoqmnpULzruzWGzVDtMXJapzh_VlUFJWBmqRqEhT5jU5wmTdI47qdvIslQOZi5Df5HbSCdNKdC81lI5UNaRFO5alboAVQOEmVoKHW3WtDQtoVGfFYpGqrNFpm0p9WLafqRPkw5RErAsfq0n9WyxuxOyWX_jw0CLY4pwo0bTJVGZzmhG_Vk3wuWEosHhzrK8UKD_UQQYXdUiZPDDsnGDqlYhFzcd9ZE1N_KN8LzEk5oVH7v4Q9EET7Fr1rcRnsHeqqTLHmJgJmt4CgM8sowbg-b51vvJDSyvwNHqfuBah7hLU1XcFyiri3rblYbHRh10u1LRuLfvmGiCeqhSN-pXI6V-Cl0lveR0FRXP4OvyVXRequgSo37ToV3LfVB8Ijc6KL4P8cYdxP2Tt5EOqjcnb7ir4szgRdbwIqMUWVbNRF5kKS8y2FY113mRB30NM2vmbOprKEm6ZmGfJjCsseZrT4MEVaRLSiZxusasOHJi1yLpDxlBvBCcaGjahunNMbUNuZtq65ZT77jz2i__ABsPQFI"
)


def owner_logo_mask():
    """Decode the traced press-shaped D/M exactly as provided by the owner."""
    import base64
    import zlib
    payload = _LOGO_MASK_B64 + "=" * (-len(_LOGO_MASK_B64) % 4)
    packed = zlib.decompress(base64.urlsafe_b64decode(payload))
    image = np.unpackbits(np.frombuffer(packed, dtype=np.uint8))
    if image.size != 112 * 146:
        raise ValueError("Brewery logo mask was truncated or changed")
    return image.reshape(146, 112).astype(bool)


def add_screw_press_emblem(g):
    """Make actual screenshot-traced brand silhouette from native xLights nodes.

    The physical pixel sample retains all contour nodes and a sparse interior
    illumination lattice. A second inset contour creates modest parallax depth.
    This is a native xLights Custom model, never an image/video overlay.
    """
    m = owner_logo_mask()
    up = np.zeros_like(m); up[1:] = m[:-1]
    down = np.zeros_like(m); down[:-1] = m[1:]
    left = np.zeros_like(m); left[:, 1:] = m[:, :-1]
    right = np.zeros_like(m); right[:, :-1] = m[:, 1:]
    edge = m & ~(up & down & left & right)
    rr, cc = np.indices(m.shape)
    fill = m & ~edge & (rr % 4 == 0) & (cc % 4 == 0)
    parts = {}
    points = []
    def layer(name, selected, depth):
        indices = np.argwhere(selected)
        ids = []
        for row, col in indices:
            # Image origin is top-left; xLights Y is vertical.
            x = (float(col) - 55.5) * .26
            y = 34 + (145 - float(row)) * .26
            z = depth
            ids.append(len(points) + 1)
            points.append((x, y, z))
        parts[name] = ids
    layer("PRESS_SILHOUETTE", edge, 88)
    layer("PRESS_FILL", fill, 88)
    layer("PRESS_DEPTH", edge & ((rr + cc) % 3 == 0), 85)
    g.custom("HX_DRASTIC_PRESS_DM_LOGO", points, "BREWERY_EMBLEM",
             "Source-traced screw press D / inner M in 3D illuminated pixels",
             ["#FFE6AA"] * len(points), parts,
             details={"brand_emblem": True, "brand_reference": "owner_facebook_screenshot_2025_11_12",
                      "brand_trace_kind": "binary_pixel_source_trace",
                      "trace_size": [112, 146], "musical_role": "guitarist",
                      "parade_layer": "BREWERY_EMBLEM",
                      "original_logo_nodes": len(points),
                      "source_display_floor": .55,
                      "mechanical_artwork_engineering_verified": False})
    result = g.models[-1]
    result.attrs.update(BlackTransparency="100", PixelSize="10", Antialias="1")


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
    add_screw_press_emblem(g)
