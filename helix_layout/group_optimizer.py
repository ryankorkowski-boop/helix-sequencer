from __future__ import annotations

from core import spatial_scene


def optimize_group_order(names: list[str], scene: spatial_scene.SpatialScene, ordering: str) -> list[str]:
    coords = scene.projected_coordinate_map(names)
    if ordering == "left_to_right":
        return sorted(names, key=lambda name: (coords.get(name, (0.0, 0.0))[0], name.lower()))
    if ordering == "right_to_left":
        return sorted(names, key=lambda name: (-coords.get(name, (0.0, 0.0))[0], name.lower()))
    if ordering == "bottom_to_top":
        return sorted(names, key=lambda name: (coords.get(name, (0.0, 0.0))[1], name.lower()))
    if ordering == "top_to_bottom":
        return sorted(names, key=lambda name: (-coords.get(name, (0.0, 0.0))[1], name.lower()))
    if ordering == "center_out":
        xs = [value[0] for value in coords.values()] or [0.0]
        ys = [value[1] for value in coords.values()] or [0.0]
        cx = sum(xs) / len(xs)
        cy = sum(ys) / len(ys)
        return sorted(names, key=lambda name: ((coords.get(name, (cx, cy))[0] - cx) ** 2 + (coords.get(name, (cx, cy))[1] - cy) ** 2, name.lower()))
    return names[:]
