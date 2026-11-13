"""Two native xLights prop variants for a high-roof delivery van concept.

These are editable design-unit layouts, not measured RAM ProMaster CAD or
roadworthy fabrication drawings. Actual Helix/xLights rendering is a separate
verification gate. Both variants use genuine Garden/Structures model families.
"""
from __future__ import annotations

from collections import Counter

from models.approval_layouts import allocate, structures
from models.ultimate_showcase import Garden
from models.parade_float import build as build_extreme_float

PALETTE = ("#62F0FF", "#FF6DD6", "#FFE49C")
VARIANTS = ("clean_matrix_van", "extreme_skeleton_van")


def build_clean_van(plan=None, *, duration=None):
    """Low-density readable sign + actual xLights arches, trees, paths and stars."""
    g = Garden(
        title="Drastic Measures — Clean Matrix Delivery Van",
        slug="drastic_measures_clean_matrix_van",
        palette=PALETTE,
        description="High-roof white delivery van: clean signage and recognizable xLights props.",
    )
    s = structures(g)
    # The following is an artistic coordinate frame, NOT actual vehicle dimensions.
    # Keep the center clear for a high-contrast native pixel brand sign.
    for side in (-1, 1):
        x = side * 43
        for y in (5, 38, 55):
            s.path("VAN_SIDE_OUTLINE", [(x, y, -70), (x, y, 70)],
                   "EDGE_HIGHLIGHTS", 0, count=130)
        for z in (-70, 70):
            s.path("VAN_CORNER", [(x, 5, z), (x, 55, z)],
                   "EDGE_HIGHLIGHTS", 0, count=65)
        for index, z in enumerate((-48, -16, 16, 48)):
            s.arch((side * 22, 55, z), width=15, height=16,
                   color=index, zone="ROOF_ARCHES")
        for index, z in enumerate((-56, 56)):
            s.tree(side * 36, z, 19, 6, color=index)
        for index, z in enumerate((-42, 0, 42)):
            s.starburst((side * 44, 64, z), 6, color=index,
                        zone="SNOWFLAKES")
    # Native RGB mesh planes: side-facing pixel signs, not composited artwork.
    for side in (-1, 1):
        s.mesh("BREWERY_RGB_MATRIX", (side * 45, 8, 0), 1, 38,
               "BRAND_MATRIX", 0, wave=0, yaw=0)
    from models.brewery_branding import add_sign, add_screw_press_emblem
    add_sign(g, "DRASTIC MEASURES", name="CLEAN_SIDE_L",
             pos=(-46, 24, 0), plane="zy", size=.74)
    add_sign(g, "DRASTIC MEASURES", name="CLEAN_SIDE_R",
             pos=(46, 24, 0), plane="zy", size=.74)
    add_sign(g, "BREWING WADENA MN", name="CLEAN_REAR",
             pos=(0, 15, -76), plane="xy", size=.80)
    add_screw_press_emblem(g)
    for model in g.models:
        model.attrs.update(BlackTransparency="100", PixelSize="8", Antialias="1")
        model.details.setdefault("parade_layer", model.zone)
        model.details.setdefault("source_display_floor", .20)
        model.details.setdefault("musical_role", "guitarist")
    from tools.source_role_routing import configure_source_routes
    configure_source_routes(g.models)
    return allocate(g), None


def build_extreme_van(plan=None, *, duration=None):
    """Full native Helix 3D prop arrangement, including four skeletons."""
    return build_extreme_float(plan=plan, duration=duration)


def build(variant="clean_matrix_van", plan=None, *, duration=None):
    if variant == "clean_matrix_van":
        return build_clean_van(plan=plan, duration=duration)
    if variant == "extreme_skeleton_van":
        return build_extreme_van(plan=plan, duration=duration)
    raise ValueError(f"Unknown van variant: {variant}")


def inventory(variant="clean_matrix_van"):
    garden, _ = build(variant)
    return {
        "variant": variant,
        "models": len(garden.models),
        "pixels": sum(len(m.points) for m in garden.models),
        "zones": dict(sorted(Counter(m.zone for m in garden.models).items())),
        "native_editable_design": True,
        "vehicle_geometry_verified": False,
        "native_video_verified": False,
    }
