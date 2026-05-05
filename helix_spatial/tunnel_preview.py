from __future__ import annotations


def build_tunnel_preview(points: list[tuple[float, float, float]]) -> dict[str, object]:
    return {
        "point_count": len(points),
        "trajectory": [{"x": point[0], "y": point[1], "z": point[2]} for point in points[:64]],
        "future_lookahead_markers": list(range(min(8, len(points)))),
    }
