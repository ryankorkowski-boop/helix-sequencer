from __future__ import annotations


def sample_field(field: object, points: list[tuple[float, float, float]]) -> list[float]:
    return [float(getattr(field, "sample")(point)) for point in points]
