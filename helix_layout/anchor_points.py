from __future__ import annotations

from core import spatial_scene


def detect_anchor_points(scene: spatial_scene.SpatialScene) -> dict[str, tuple[float, float, float]]:
    nodes = list(scene.nodes.values())
    if not nodes:
        return {"center": (0.0, 0.0, 0.0)}
    xs = [node.center_xyz[0] for node in nodes]
    ys = [node.center_xyz[1] for node in nodes]
    zs = [node.center_xyz[2] for node in nodes]
    center = (sum(xs) / len(xs), sum(ys) / len(ys), sum(zs) / len(zs))
    return {
        "center": center,
        "visual_center": center,
        "bottom_center": (center[0], min(ys), center[2]),
        "top_center": (center[0], max(ys), center[2]),
        "left_edge": (min(xs), center[1], center[2]),
        "right_edge": (max(xs), center[1], center[2]),
        "front_center": (center[0], center[1], min(zs)),
        "back_center": (center[0], center[1], max(zs)),
        "audience_focus": (center[0], min(ys), min(zs)),
    }
