"""Map existing Helix/xLights models onto Wadena physical preview geometry.

This layer changes preview geometry only. It never changes XSQ channel truth.
Traditional AC props retain independent red/green/white models on coincident
physical paths.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import hypot

from core.wadena_geometry import ConeTree, Point3, SpiralTree


@dataclass(frozen=True)
class MappedPath:
    points: tuple[tuple[float, float], ...]
    kind: str


def _anchor(points: tuple[tuple[float, float], ...]) -> tuple[float, float, float]:
    if not points:
        return 0.0, 0.0, 0.0
    x0, y0 = points[0]
    x1, y1 = points[-1]
    return (x0 + x1) / 2.0, min(y0, y1), hypot(x1 - x0, y1 - y0)


def _xy(points: tuple[Point3, ...]) -> tuple[tuple[float, float], ...]:
    return tuple((p.x, p.y) for p in points)


def map_model_path(name: str, base_points: tuple[tuple[float, float], ...]) -> MappedPath | None:
    """Return a physical Wadena path for known model-name families.

    Unknown models return None so the existing xLights geometry remains the
    safe fallback. Name matching is intentionally conservative.
    """
    lowered = name.strip().lower()
    if not base_points:
        return None

    cx, bottom, span = _anchor(base_points)

    # Traditional large trees: the physical strand is a clockwise helix,
    # followed by the broad crown/downward spiral described by the reference
    # footage. Red/green/white models share the same returned path.
    if any(token in lowered for token in ("blvd", "boulevard", "linden")) or lowered.startswith("left tree"):
        height = max(28.0, span * 1.15)
        radius = max(7.0, min(26.0, height * 0.20))
        path = SpiralTree(
            center=Point3(cx, bottom, 0.0),
            height=height,
            base_radius=radius,
            up_turns=3.25,
            down_turns=1.65,
            apex_radius=radius * 1.75,
            clockwise=True,
        ).paths()[0].points
        return MappedPath(_xy(path), "spiral_tree")

    # Explicit mini/yard trees are small tapered spirals. Keep the geometry
    # local to the existing model's anchor so this does not invent a new yard
    # coordinate system.
    if "mini tree" in lowered or "minitree" in lowered or "yard tree" in lowered:
        height = max(14.0, span * 0.75)
        radius = max(4.0, min(12.0, height * 0.24))
        path = ConeTree(
            center=Point3(cx, bottom, 0.0),
            height=height,
            base_radius=radius,
            turns=2.35,
        ).paths()[0].points
        return MappedPath(_xy(path), "cone_tree")

    return None
