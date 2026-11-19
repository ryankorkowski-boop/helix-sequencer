from __future__ import annotations

import math
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path


DEFAULT_LAYOUT = Path("xlights_rgbeffects.xml")


@dataclass(frozen=True)
class SpatialNode:
    name: str
    x: float
    y: float
    z: float

    def distance_to(self, other: "SpatialNode") -> float:
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2 + (self.z - other.z) ** 2)


@dataclass(frozen=True)
class SpatialGraph:
    nodes: tuple[SpatialNode, ...]

    @property
    def by_name(self) -> dict[str, SpatialNode]:
        return {node.name: node for node in self.nodes}

    def ordered_for_direction(self, direction: str) -> tuple[SpatialNode, ...]:
        if direction == "right_to_left":
            return tuple(sorted(self.nodes, key=lambda node: (-node.x, node.y, node.z, node.name)))
        if direction == "center_out":
            cx = sum(node.x for node in self.nodes) / max(1, len(self.nodes))
            cy = sum(node.y for node in self.nodes) / max(1, len(self.nodes))
            cz = sum(node.z for node in self.nodes) / max(1, len(self.nodes))
            return tuple(sorted(self.nodes, key=lambda node: ((node.x - cx) ** 2 + (node.y - cy) ** 2 + (node.z - cz) ** 2, node.name)))
        if direction == "bottom_up":
            return tuple(sorted(self.nodes, key=lambda node: (node.z, node.y, node.x, node.name)))
        if direction == "top_down":
            return tuple(sorted(self.nodes, key=lambda node: (-node.z, node.y, node.x, node.name)))
        return tuple(sorted(self.nodes, key=lambda node: (node.x, node.y, node.z, node.name)))

    def nearest_neighbors(self, model_name: str, count: int = 3) -> tuple[str, ...]:
        lookup = self.by_name
        if model_name not in lookup:
            return ()
        origin = lookup[model_name]
        neighbors = sorted(
            (node for node in self.nodes if node.name != model_name),
            key=lambda node: (origin.distance_to(node), node.name),
        )
        return tuple(node.name for node in neighbors[:count])


def _float(value: str | None) -> float:
    try:
        return float(value or 0.0)
    except ValueError:
        return 0.0


def parse_xlights_spatial_nodes(layout_path: Path = DEFAULT_LAYOUT, *, model_names: tuple[str, ...] | None = None) -> tuple[SpatialNode, ...]:
    if not layout_path.exists():
        return ()
    root = ET.parse(layout_path).getroot()
    allowed = set(model_names or ())
    nodes: list[SpatialNode] = []
    for model in root.findall(".//model"):
        name = model.attrib.get("name")
        if not name:
            continue
        if allowed and name not in allowed:
            continue
        nodes.append(
            SpatialNode(
                name=name,
                x=_float(model.attrib.get("WorldPosX")),
                y=_float(model.attrib.get("WorldPosY")),
                z=_float(model.attrib.get("WorldPosZ")),
            )
        )
    return tuple(sorted(nodes, key=lambda node: node.name))


def fallback_spatial_nodes(model_names: tuple[str, ...]) -> tuple[SpatialNode, ...]:
    if not model_names:
        return ()
    midpoint = (len(model_names) - 1) / 2.0
    nodes = []
    for index, name in enumerate(model_names):
        x = round((index - midpoint) * 10.0, 6)
        y = round((index % 5) * 6.0, 6)
        z = round((index // 5) * 4.0, 6)
        nodes.append(SpatialNode(name=name, x=x, y=y, z=z))
    return tuple(nodes)


def grouping_spatial_nodes(layout_path: Path) -> tuple[SpatialNode, ...]:
    """3D nodes for submodels and groups, including groups nested inside groups.

    Model nodes stay on WorldPos so existing layout reads do not move.
    A submodel uses the centroid of the node range sliced from the parent
    PointData. A group uses the mean of its expanded member centers.
    """
    from core.model_parser import parse_layout

    if not layout_path.exists():
        return ()
    layout = parse_layout(layout_path)
    nodes: list[SpatialNode] = []
    for model in layout.models.values():
        if not model.is_submodel:
            continue
        x, y, z = model.center()
        nodes.append(SpatialNode(name=model.name, x=x, y=y, z=z))
    for group in layout.groups.values():
        centers: list[tuple[float, float, float]] = []
        for member in layout.expand_group_members(group.name):
            model = layout.model_for(member)
            if model is not None:
                centers.append(model.center())
        if not centers and group.coordinates is not None:
            centers.append((group.coordinates[0], group.coordinates[1], 0.0))
        if not centers:
            continue
        count = float(len(centers))
        nodes.append(
            SpatialNode(
                name=group.name,
                x=sum(point[0] for point in centers) / count,
                y=sum(point[1] for point in centers) / count,
                z=sum(point[2] for point in centers) / count,
            )
        )
    return tuple(nodes)


def route_names_by_axis(graph: SpatialGraph, names: tuple[str, ...] | list[str], axis: str = "x") -> tuple[str, ...]:
    """Order props by a real spatial axis. Names with no node stay at the end."""
    lookup = graph.by_name
    present = [name for name in names if name in lookup]
    missing = [name for name in names if name not in lookup]
    present.sort(key=lambda name: (getattr(lookup[name], axis), lookup[name].y, name))
    return tuple(present + missing)


def build_spatial_graph(*, layout_path: Path = DEFAULT_LAYOUT, model_names: tuple[str, ...] = ()) -> SpatialGraph:
    nodes = parse_xlights_spatial_nodes(layout_path, model_names=model_names or None)
    if model_names and len(nodes) != len(set(model_names)):
        found = {node.name for node in nodes}
        missing = tuple(name for name in model_names if name not in found)
        nodes = tuple(nodes) + fallback_spatial_nodes(missing)
    elif layout_path.exists():
        found = {node.name for node in nodes}
        extra = tuple(node for node in grouping_spatial_nodes(layout_path) if node.name not in found)
        nodes = tuple(nodes) + extra
    if not nodes and model_names:
        nodes = fallback_spatial_nodes(model_names)
    return SpatialGraph(nodes=tuple(sorted(nodes, key=lambda node: node.name)))
