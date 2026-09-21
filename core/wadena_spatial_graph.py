"""Deterministic landmark graph for Wadena-style spatial choreography.

This graph is deliberately independent of electrical channel truth. It gives the
sequencer a small, named physical vocabulary so musical events can travel across
real display landmarks instead of selecting arbitrary model numbers.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import hypot


@dataclass(frozen=True)
class Landmark:
    name: str
    x: float
    y: float
    role: str
    neighbors: tuple[str, ...] = ()

    def distance_to(self, other: "Landmark") -> float:
        return hypot(self.x - other.x, self.y - other.y)


WADENA_LANDMARKS: tuple[Landmark, ...] = (
    Landmark("LEFT_TREE", 122.0, 302.0, "perimeter", ("BLVD_LEFT", "WREATH")),
    Landmark("BLVD_LEFT", 120.0, 62.0, "boulevard", ("LEFT_TREE", "BLVD_CENTER", "WREATH")),
    Landmark("BLVD_CENTER", 644.0, 11.0, "boulevard", ("BLVD_LEFT", "BLVD_RIGHT", "WREATH")),
    Landmark("BLVD_RIGHT", 999.0, -26.0, "boulevard", ("BLVD_CENTER", "RIGHT_LINDEN", "WREATH")),
    Landmark("RIGHT_LINDEN", 1290.0, 391.0, "perimeter", ("BLVD_RIGHT", "WREATH")),
    Landmark("WREATH", 556.0, 340.0, "hero", ("LEFT_TREE", "BLVD_LEFT", "BLVD_CENTER", "BLVD_RIGHT", "RIGHT_LINDEN", "GARAGE_SNOWFLAKE")),
    Landmark("GARAGE_SNOWFLAKE", 666.0, 342.0, "punctuation", ("WREATH", "ROOF_SNOWFLAKE")),
    Landmark("ROOF_SNOWFLAKE", 855.0, 469.0, "punctuation", ("GARAGE_SNOWFLAKE", "RIGHT_LINDEN")),
    Landmark("FRONT_IMPACT", 621.0, 372.0, "impact", ("WREATH", "RIGHT_IMPACT")),
    Landmark("RIGHT_IMPACT", 1279.0, 239.0, "impact", ("RIGHT_LINDEN", "FRONT_IMPACT")),
)


class WadenaSpatialGraph:
    """Named physical topology with deterministic route generation."""

    def __init__(self, landmarks: tuple[Landmark, ...] = WADENA_LANDMARKS) -> None:
        self.landmarks = landmarks
        self.by_name = {item.name: item for item in landmarks}

    def route(self, start: str, end: str) -> tuple[str, ...]:
        """Return a deterministic shortest hop route between landmarks."""
        if start not in self.by_name or end not in self.by_name:
            return ()
        if start == end:
            return (start,)
        frontier: list[tuple[str, ...]] = [(start,)]
        seen = {start}
        while frontier:
            path = frontier.pop(0)
            for nxt in sorted(self.by_name[path[-1]].neighbors):
                if nxt in seen:
                    continue
                candidate = path + (nxt,)
                if nxt == end:
                    return candidate
                seen.add(nxt)
                frontier.append(candidate)
        return ()

    def order(self, direction: str) -> tuple[str, ...]:
        """Return a stable landmark order for common spatial gestures."""
        items = self.landmarks
        if direction == "right_to_left":
            return tuple(item.name for item in sorted(items, key=lambda i: (-i.x, i.y, i.name)))
        if direction == "center_out":
            hero = self.by_name["WREATH"]
            return tuple(item.name for item in sorted(items, key=lambda i: (hero.distance_to(i), i.name)))
        if direction == "out_to_center":
            hero = self.by_name["WREATH"]
            return tuple(item.name for item in sorted(items, key=lambda i: (-hero.distance_to(i), i.name)))
        if direction == "bottom_up":
            return tuple(item.name for item in sorted(items, key=lambda i: (i.y, i.x, i.name)))
        return tuple(item.name for item in sorted(items, key=lambda i: (i.x, i.y, i.name)))


def wadena_spatial_graph() -> WadenaSpatialGraph:
    return WadenaSpatialGraph()
