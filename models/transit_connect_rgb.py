"""Simple Ford Transit Connect RGB strip-outline owner-review layout.

Coordinates are artistic design units, not measured vehicle dimensions.
The D/M logo is sampled from the owner's traced brewery mark.
"""
from __future__ import annotations
import numpy as np
from models.ultimate_showcase import Garden
from models.approval_layouts import allocate, structures
from models.brewery_branding import owner_logo_mask

def build(plan=None, *, duration=None):
    g = Garden(title="Drastic Measures — Transit Connect RGB Outlines",
               slug="drastic_measures_transit_connect_rgb",
               palette=("#47DBFF", "#FFB84F", "#FF5BB9"),
               description="Minimal RGB strip body contours and illuminated D/M logo")
    s = structures(g)
    # Front = positive Z. Profile captures short hood and compact van cabin.
    for side in (-1, 1):
        x = side * 34
        lines = {
            "ROOF_STRIP": [(x, 49, -69), (x, 49, 36), (x, 46, 44)],
            "WINDSHIELD_EDGE": [(x, 46, 44), (x, 28, 53)],
            "HOOD_EDGE": [(x, 28, 53), (x, 26, 69)],
            "BELTLINE_STRIP": [(x, 25, -69), (x, 25, 53)],
            "LOWER_BODY_STRIP": [(x, 9, -69), (x, 9, 69)],
            "REAR_VERTICAL": [(x, 9, -69), (x, 49, -69)],
            "FRONT_VERTICAL": [(x, 9, 69), (x, 26, 69)],
            "SLIDING_DOOR_EDGE": [(x, 10, -15), (x, 43, -15)],
        }
        for name, coords in lines.items():
            s.path(name, coords, "BODY_OUTLINE", 0, count=80)
        # A single clean logo contour on each flank, without an RGB matrix.
        mask = owner_logo_mask()
        up = np.zeros_like(mask); up[1:] = mask[:-1]
        down = np.zeros_like(mask); down[:-1] = mask[1:]
        left = np.zeros_like(mask); left[:, 1:] = mask[:, :-1]
        right = np.zeros_like(mask); right[:, :-1] = mask[:, 1:]
        edge = mask & ~(up & down & left & right)
        rr, cc = np.where(edge & (np.indices(mask.shape)[0] % 2 == 0))
        points = [(side * 35, 15 + (145 - float(r)) * .19,
                   -39 + (float(c) - 55.5) * .31) for r, c in zip(rr, cc)]
        g.custom("DM_PRESS_LOGO_" + ("L" if side < 0 else "R"), points,
                 "BREWERY_EMBLEM", "Owner-traced D/M mark as simple RGB outline",
                 ["#FFB84F"] * len(points),
                 {"LOGO_OUTLINE": list(range(1, len(points) + 1))},
                 details={"brand_emblem": True, "musical_role": "guitarist",
                          "parade_layer": "BREWERY_EMBLEM",
                          "source_display_floor": .45})
    for m in g.models:
        m.attrs.update(BlackTransparency="100", PixelSize="8", Antialias="1")
        m.details.setdefault("musical_role", "guitarist")
        m.details.setdefault("parade_layer", m.zone)
        m.details.setdefault("source_display_floor", .18)
    from tools.source_role_routing import configure_source_routes
    configure_source_routes(g.models)
    return allocate(g), None
