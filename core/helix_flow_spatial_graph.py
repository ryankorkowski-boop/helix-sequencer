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


def build_spatial_graph(*, layout_path: Path = DEFAULT_LAYOUT, model_names: tuple[str, ...] = ()) -> SpatialGraph:
    nodes = parse_xlights_spatial_nodes(layout_path, model_names=model_names or None)
    if model_names and len(nodes) != len(model_names):
        found = {node.name for node in nodes}
        missing = tuple(name for name in model_names if name not in found)
        nodes = tuple(nodes) + fallback_spatial_nodes(missing)
    if not nodes and model_names:
        nodes = fallback_spatial_nodes(model_names)
    return SpatialGraph(nodes=tuple(sorted(nodes, key=lambda node: node.name)))
