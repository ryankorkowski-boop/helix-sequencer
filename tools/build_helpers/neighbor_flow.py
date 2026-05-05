from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Iterable

from core import model_parser as xmp


def _family_key(model: xmp.Model) -> str:
    semantic = (model.type or "").strip().lower()
    if semantic == "tree":
        norm = xmp.normalize_name(model.name)
        return "gt" if "garage" in norm else "mega"
    if semantic == "star":
        return "stars"
    if semantic in {"circle", "wreath"}:
        return "sphere"
    if semantic in {"icicle", "window", "channelblock", "multipoint"}:
        return "line"
    if semantic == "cane":
        return "canes_combo"
    return semantic


@dataclass
class NeighborGraph:
    routes: dict[str, list[str]] = field(default_factory=dict)
    adjacency: dict[str, list[str]] = field(default_factory=dict)
    families: dict[str, list[str]] = field(default_factory=dict)

    def seed_targets(self, family: str | None = None, *, limit: int | None = None) -> list[str]:
        if family and family in self.routes:
            ordered = self.routes[family][:]
        else:
            ordered = []
            for family_key in sorted(self.routes):
                ordered.extend(self.routes[family_key])
        if limit is None:
            return ordered
        cap = max(0, int(limit))
        if cap == 0:
            return []
        return ordered[:cap]

    def as_dict(self) -> dict[str, object]:
        return {
            "routes": self.routes,
            "adjacency": self.adjacency,
            "families": self.families,
        }


def build_neighbor_graph(
    parsed_layout: xmp.ParsedLayout | None,
    *,
    available_names: Iterable[str] | None = None,
) -> NeighborGraph:
    if parsed_layout is None:
        return NeighborGraph()

    allowed = {name for name in available_names} if available_names is not None else None
    family_points: dict[str, list[tuple[float, float, str]]] = defaultdict(list)

    for model in parsed_layout.models.values():
        if model.is_submodel:
            continue
        if allowed is not None and model.name not in allowed:
            continue
        family = _family_key(model)
        if not family or family == "group":
            continue
        center_x, center_y, _center_z = model.center()
        family_points[family].append((center_x, center_y, model.name))

    routes: dict[str, list[str]] = {}
    adjacency: dict[str, list[str]] = {}
    families: dict[str, list[str]] = {}
    for family, points in family_points.items():
        if len(points) <= 1:
            ordered = [name for _x, _y, name in points]
        else:
            span_x = max(point[0] for point in points) - min(point[0] for point in points)
            span_y = max(point[1] for point in points) - min(point[1] for point in points)
            if span_x >= span_y:
                points.sort(key=lambda point: (point[0], point[1], point[2].lower()))
            else:
                points.sort(key=lambda point: (point[1], point[0], point[2].lower()))
            ordered = [name for _x, _y, name in points]
        routes[family] = ordered
        families[family] = ordered[:]
        for index, name in enumerate(ordered):
            neighbors: list[str] = []
            if index > 0:
                neighbors.append(ordered[index - 1])
            if index + 1 < len(ordered):
                neighbors.append(ordered[index + 1])
            adjacency[name] = neighbors
    return NeighborGraph(routes=routes, adjacency=adjacency, families=families)


def expand_neighbor_targets(
    graph: NeighborGraph | None,
    seeds: Iterable[str],
    *,
    depth: int = 1,
    limit: int = 6,
) -> list[str]:
    if graph is None:
        return []
    frontier = [seed for seed in seeds if seed]
    seen = set(frontier)
    out: list[str] = []
    for _depth in range(max(1, int(depth))):
        next_frontier: list[str] = []
        for name in frontier:
            for neighbor in graph.adjacency.get(name, []):
                if neighbor in seen:
                    continue
                seen.add(neighbor)
                out.append(neighbor)
                next_frontier.append(neighbor)
                if len(out) >= max(1, int(limit)):
                    return out
        frontier = next_frontier
        if not frontier:
            break
    return out[: max(1, int(limit))]
