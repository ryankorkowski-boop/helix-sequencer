from __future__ import annotations

import math
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Sequence

from core import model_parser as xmp


LAYOUT_CAPABILITY_2D = "2d"
LAYOUT_CAPABILITY_25D = "2.5d"
LAYOUT_CAPABILITY_3D = "3d"

_CAPABILITY_ORDER = {
    LAYOUT_CAPABILITY_2D: 0,
    LAYOUT_CAPABILITY_25D: 1,
    LAYOUT_CAPABILITY_3D: 2,
}
_EPSILON = 1e-6


@dataclass(frozen=True)
class FrontProjector:
    view: str = "front"
    horizontal_axis: str = "x"
    vertical_axis: str = "y"
    depth_axis: str = "z"

    def project_xyz(self, point: tuple[float, float, float]) -> tuple[float, float]:
        return (float(point[0]), float(point[1]))


@dataclass(frozen=True)
class LayoutCapabilityReport:
    capability: str
    model_count: int
    horizontal_span: float
    vertical_span: float
    depth_span: float
    depth_ratio: float
    depth_layer_count: int
    layered_model_ratio: float
    volumetric_model_ratio: float


@dataclass(frozen=True)
class SceneNode:
    name: str
    kind: str
    center_xyz: tuple[float, float, float]
    extents_xyz: tuple[float, float, float]
    projected_xy: tuple[float, float]
    bounds_xyz: tuple[float, float, float, float, float, float]
    projected_bounds_xy: tuple[float, float, float, float]
    projected_outline_xy: tuple[tuple[float, float], ...]
    tags: tuple[str, ...]
    groups: tuple[str, ...]


@dataclass(frozen=True)
class SpatialEffectRoute:
    family: str
    capability: str
    primitive: str
    distance_mode: str
    axis: str | None = None
    path_strategy: str | None = None
    fallback_family: str | None = None
    flat_equivalent: str | None = None


@dataclass(frozen=True)
class SpatialScene:
    path: Path | None
    capability: str
    capability_report: LayoutCapabilityReport
    nodes: dict[str, SceneNode]
    group_nodes: dict[str, SceneNode]
    groups: dict[str, tuple[str, ...]]
    aliases: dict[str, str]
    projector: FrontProjector = field(default_factory=FrontProjector)

    def node_for(self, name: str) -> SceneNode | None:
        normalized = xmp.normalize_name(name)
        actual = self.aliases.get(normalized)
        if actual:
            return self.nodes.get(actual) or self.group_nodes.get(actual)
        for pool in (self.nodes, self.group_nodes):
            for node_name, node in pool.items():
                if xmp.normalize_name(node_name) == normalized:
                    return node
        return None

    def projected_coordinate_map(self, available_names: Iterable[str]) -> dict[str, tuple[float, float]]:
        out: dict[str, tuple[float, float]] = {}
        for name in available_names:
            node = self.node_for(name)
            if node is not None:
                out[name] = node.projected_xy
        return out

    def xyz_coordinate_map(self, available_names: Iterable[str]) -> dict[str, tuple[float, float, float]]:
        out: dict[str, tuple[float, float, float]] = {}
        for name in available_names:
            node = self.node_for(name)
            if node is not None:
                out[name] = node.center_xyz
        return out


def normalize_spatial_family(name: str) -> str:
    normalized = xmp.normalize_name(name).replace("/", " ")
    aliases = {
        "wave": "wave_propagation",
        "wave propagation": "wave_propagation",
        "radial": "radial_burst",
        "radial burst": "radial_burst",
        "height": "height_mapping",
        "height mapping": "height_mapping",
        "proximity": "proximity_activation",
        "proximity activation": "proximity_activation",
        "trajectory": "trajectory_travel",
        "trajectory travel": "trajectory_travel",
        "travel": "trajectory_travel",
        "orbit": "orbit_rotation",
        "rotation": "orbit_rotation",
        "orbit rotation": "orbit_rotation",
        "depth": "depth_sweep",
        "depth sweep": "depth_sweep",
    }
    return aliases.get(normalized, normalized.replace(" ", "_"))


_ROUTE_TABLE: dict[str, dict[str, SpatialEffectRoute]] = {
    "wave_propagation": {
        LAYOUT_CAPABILITY_3D: SpatialEffectRoute(
            family="wave_propagation",
            capability=LAYOUT_CAPABILITY_3D,
            primitive="directional_wave",
            distance_mode="xyz",
            axis="x",
            path_strategy="axis_sort",
            fallback_family="wave_propagation",
            flat_equivalent="projected_wave_propagation",
        ),
        LAYOUT_CAPABILITY_25D: SpatialEffectRoute(
            family="wave_propagation",
            capability=LAYOUT_CAPABILITY_25D,
            primitive="directional_wave",
            distance_mode="xyz",
            axis="x",
            path_strategy="axis_sort",
            fallback_family="wave_propagation",
            flat_equivalent="projected_wave_propagation",
        ),
        LAYOUT_CAPABILITY_2D: SpatialEffectRoute(
            family="wave_propagation",
            capability=LAYOUT_CAPABILITY_2D,
            primitive="directional_wave",
            distance_mode="projected_xy",
            axis="x",
            path_strategy="axis_sort",
            fallback_family="wave_propagation",
            flat_equivalent="projected_wave_propagation",
        ),
    },
    "radial_burst": {
        LAYOUT_CAPABILITY_3D: SpatialEffectRoute(
            family="radial_burst",
            capability=LAYOUT_CAPABILITY_3D,
            primitive="radial_field",
            distance_mode="xyz",
            path_strategy="radial_out",
            fallback_family="radial_burst",
            flat_equivalent="projected_radial_burst",
        ),
        LAYOUT_CAPABILITY_25D: SpatialEffectRoute(
            family="radial_burst",
            capability=LAYOUT_CAPABILITY_25D,
            primitive="radial_field",
            distance_mode="xyz",
            path_strategy="radial_out",
            fallback_family="radial_burst",
            flat_equivalent="projected_radial_burst",
        ),
        LAYOUT_CAPABILITY_2D: SpatialEffectRoute(
            family="radial_burst",
            capability=LAYOUT_CAPABILITY_2D,
            primitive="radial_field",
            distance_mode="projected_xy",
            path_strategy="radial_out",
            fallback_family="radial_burst",
            flat_equivalent="projected_radial_burst",
        ),
    },
    "height_mapping": {
        LAYOUT_CAPABILITY_3D: SpatialEffectRoute(
            family="height_mapping",
            capability=LAYOUT_CAPABILITY_3D,
            primitive="directional_wave",
            distance_mode="xyz",
            axis="y",
            path_strategy="axis_sort",
            fallback_family="height_mapping",
            flat_equivalent="projected_height_mapping",
        ),
        LAYOUT_CAPABILITY_25D: SpatialEffectRoute(
            family="height_mapping",
            capability=LAYOUT_CAPABILITY_25D,
            primitive="directional_wave",
            distance_mode="xyz",
            axis="y",
            path_strategy="axis_sort",
            fallback_family="height_mapping",
            flat_equivalent="projected_height_mapping",
        ),
        LAYOUT_CAPABILITY_2D: SpatialEffectRoute(
            family="height_mapping",
            capability=LAYOUT_CAPABILITY_2D,
            primitive="directional_wave",
            distance_mode="projected_xy",
            axis="y",
            path_strategy="axis_sort",
            fallback_family="height_mapping",
            flat_equivalent="projected_height_mapping",
        ),
    },
    "proximity_activation": {
        LAYOUT_CAPABILITY_3D: SpatialEffectRoute(
            family="proximity_activation",
            capability=LAYOUT_CAPABILITY_3D,
            primitive="proximity",
            distance_mode="xyz",
            fallback_family="proximity_activation",
            flat_equivalent="projected_proximity_activation",
        ),
        LAYOUT_CAPABILITY_25D: SpatialEffectRoute(
            family="proximity_activation",
            capability=LAYOUT_CAPABILITY_25D,
            primitive="proximity",
            distance_mode="xyz",
            fallback_family="proximity_activation",
            flat_equivalent="projected_proximity_activation",
        ),
        LAYOUT_CAPABILITY_2D: SpatialEffectRoute(
            family="proximity_activation",
            capability=LAYOUT_CAPABILITY_2D,
            primitive="proximity",
            distance_mode="projected_xy",
            fallback_family="proximity_activation",
            flat_equivalent="projected_proximity_activation",
        ),
    },
    "trajectory_travel": {
        LAYOUT_CAPABILITY_3D: SpatialEffectRoute(
            family="trajectory_travel",
            capability=LAYOUT_CAPABILITY_3D,
            primitive="path_travel",
            distance_mode="xyz",
            path_strategy="nearest_neighbor",
            fallback_family="trajectory_travel",
            flat_equivalent="projected_trajectory_travel",
        ),
        LAYOUT_CAPABILITY_25D: SpatialEffectRoute(
            family="trajectory_travel",
            capability=LAYOUT_CAPABILITY_25D,
            primitive="path_travel",
            distance_mode="xyz",
            path_strategy="nearest_neighbor",
            fallback_family="trajectory_travel",
            flat_equivalent="projected_trajectory_travel",
        ),
        LAYOUT_CAPABILITY_2D: SpatialEffectRoute(
            family="trajectory_travel",
            capability=LAYOUT_CAPABILITY_2D,
            primitive="path_travel",
            distance_mode="projected_xy",
            path_strategy="nearest_neighbor",
            fallback_family="trajectory_travel",
            flat_equivalent="projected_trajectory_travel",
        ),
    },
    "orbit_rotation": {
        LAYOUT_CAPABILITY_3D: SpatialEffectRoute(
            family="orbit_rotation",
            capability=LAYOUT_CAPABILITY_3D,
            primitive="path_travel",
            distance_mode="xyz",
            path_strategy="orbit_xz",
            fallback_family="orbit_rotation",
            flat_equivalent="projected_orbit_rotation",
        ),
        LAYOUT_CAPABILITY_25D: SpatialEffectRoute(
            family="orbit_rotation",
            capability=LAYOUT_CAPABILITY_25D,
            primitive="path_travel",
            distance_mode="xyz",
            path_strategy="orbit_xz",
            fallback_family="orbit_rotation",
            flat_equivalent="projected_orbit_rotation",
        ),
        LAYOUT_CAPABILITY_2D: SpatialEffectRoute(
            family="orbit_rotation",
            capability=LAYOUT_CAPABILITY_2D,
            primitive="path_travel",
            distance_mode="projected_xy",
            path_strategy="orbit_xy",
            fallback_family="orbit_rotation",
            flat_equivalent="projected_orbit_rotation",
        ),
    },
    "depth_sweep": {
        LAYOUT_CAPABILITY_3D: SpatialEffectRoute(
            family="depth_sweep",
            capability=LAYOUT_CAPABILITY_3D,
            primitive="directional_wave",
            distance_mode="xyz",
            axis="z",
            path_strategy="axis_sort",
            fallback_family="height_mapping",
            flat_equivalent="front_view_height_mapping",
        ),
        LAYOUT_CAPABILITY_25D: SpatialEffectRoute(
            family="depth_sweep",
            capability=LAYOUT_CAPABILITY_25D,
            primitive="directional_wave",
            distance_mode="xyz",
            axis="z",
            path_strategy="axis_sort",
            fallback_family="height_mapping",
            flat_equivalent="front_view_height_mapping",
        ),
        LAYOUT_CAPABILITY_2D: SpatialEffectRoute(
            family="depth_sweep",
            capability=LAYOUT_CAPABILITY_2D,
            primitive="directional_wave",
            distance_mode="projected_xy",
            axis="y",
            path_strategy="axis_sort",
            fallback_family="height_mapping",
            flat_equivalent="front_view_height_mapping",
        ),
    },
}


def route_spatial_effect(family: str, capability: str | SpatialScene) -> SpatialEffectRoute:
    normalized = normalize_spatial_family(family)
    cap = capability.capability if isinstance(capability, SpatialScene) else capability
    cap_key = cap if cap in _CAPABILITY_ORDER else LAYOUT_CAPABILITY_2D
    family_routes = _ROUTE_TABLE.get(normalized)
    if not family_routes:
        return _ROUTE_TABLE["trajectory_travel"][cap_key]
    return family_routes.get(cap_key, family_routes[LAYOUT_CAPABILITY_2D])


def _quantize_depth(value: float) -> float:
    return round(float(value) / 12.0) * 12.0


def _downsample_points(points: Sequence[tuple[float, float, float]], limit: int = 96) -> list[tuple[float, float, float]]:
    if len(points) <= limit:
        return [tuple(point) for point in points]
    if limit <= 1:
        return [tuple(points[0])]
    step = float(len(points) - 1) / float(limit - 1)
    return [tuple(points[int(round(step * idx))]) for idx in range(limit)]


def _model_points(model: xmp.Model) -> list[tuple[float, float, float]]:
    if model.geometry_points:
        return _downsample_points(model.geometry_points)
    try:
        pixels = model.virtual_pixel_map()
    except Exception:
        pixels = []
    if pixels:
        sampled = _downsample_points([(point.x, point.y, point.z) for point in pixels])
        if sampled:
            return sampled
    if model.coordinates is not None and model.end_coordinates is not None and model.coordinates != model.end_coordinates:
        return [model.coordinates, model.end_coordinates]
    if model.coordinates is not None:
        return [model.coordinates]
    return [(0.0, 0.0, 0.0)]


def _bounds_from_points(points: Sequence[tuple[float, float, float]]) -> tuple[float, float, float, float, float, float]:
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    zs = [point[2] for point in points]
    return (min(xs), min(ys), min(zs), max(xs), max(ys), max(zs))


def _center_from_points(points: Sequence[tuple[float, float, float]]) -> tuple[float, float, float]:
    count = max(1, len(points))
    return (
        sum(point[0] for point in points) / count,
        sum(point[1] for point in points) / count,
        sum(point[2] for point in points) / count,
    )


def _projected_outline(points: Sequence[tuple[float, float, float]], projector: FrontProjector) -> tuple[tuple[float, float], ...]:
    projected = [projector.project_xyz(point) for point in points]
    if projected:
        return tuple(projected)
    return ((0.0, 0.0),)


def _projected_bounds(points: Sequence[tuple[float, float]], fallback: tuple[float, float]) -> tuple[float, float, float, float]:
    if not points:
        return (fallback[0], fallback[1], fallback[0], fallback[1])
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return (min(xs), min(ys), max(xs), max(ys))


def _extent_tuple(bounds: tuple[float, float, float, float, float, float]) -> tuple[float, float, float]:
    return (
        max(0.0, bounds[3] - bounds[0]),
        max(0.0, bounds[4] - bounds[1]),
        max(0.0, bounds[5] - bounds[2]),
    )


def _node_tags(model: xmp.Model) -> tuple[str, ...]:
    tags = {
        "model",
        xmp.normalize_name(model.type),
        xmp.normalize_name(model.display_as),
        xmp.normalize_name(model.orientation or ""),
        xmp.normalize_name(model.color_family or ""),
        "pixel" if model.is_pixel_model() else "single_point",
        "rgb" if model.is_rgb_capable() else "single_color" if model.is_single_color() else "ac",
        "submodel" if model.is_submodel else "root",
    }
    return tuple(sorted(tag for tag in tags if tag))


def _group_membership(parsed_layout: xmp.ParsedLayout) -> dict[str, tuple[str, ...]]:
    membership: dict[str, list[str]] = {}
    for group_name, group in parsed_layout.groups.items():
        for member_name in group.models:
            membership.setdefault(member_name, []).append(group_name)
            resolved = parsed_layout.model_for(member_name)
            if resolved is not None and resolved.name != member_name:
                membership.setdefault(resolved.name, []).append(group_name)
    return {name: tuple(sorted(dict.fromkeys(groups))) for name, groups in membership.items()}


def _scene_bounds(nodes: Sequence[SceneNode]) -> tuple[float, float, float, float, float, float]:
    if not nodes:
        return (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    return (
        min(node.bounds_xyz[0] for node in nodes),
        min(node.bounds_xyz[1] for node in nodes),
        min(node.bounds_xyz[2] for node in nodes),
        max(node.bounds_xyz[3] for node in nodes),
        max(node.bounds_xyz[4] for node in nodes),
        max(node.bounds_xyz[5] for node in nodes),
    )


def detect_layout_capability(nodes: Iterable[SceneNode]) -> LayoutCapabilityReport:
    model_nodes = [node for node in nodes if node.kind == "model"]
    horizontal_span = 0.0
    vertical_span = 0.0
    depth_span = 0.0
    if model_nodes:
        xs = [node.center_xyz[0] for node in model_nodes]
        ys = [node.center_xyz[1] for node in model_nodes]
        zs = [node.center_xyz[2] for node in model_nodes]
        horizontal_span = max(0.0, max(xs) - min(xs))
        vertical_span = max(0.0, max(ys) - min(ys))
        depth_span = max(0.0, max(zs) - min(zs))
    planar_span = max(horizontal_span, vertical_span, 1.0)
    depth_ratio = depth_span / planar_span
    model_count = len(model_nodes)

    if not model_nodes:
        return LayoutCapabilityReport(
            capability=LAYOUT_CAPABILITY_2D,
            model_count=0,
            horizontal_span=horizontal_span,
            vertical_span=vertical_span,
            depth_span=depth_span,
            depth_ratio=depth_ratio,
            depth_layer_count=0,
            layered_model_ratio=0.0,
            volumetric_model_ratio=0.0,
        )

    depth_layers = {_quantize_depth(node.center_xyz[2]) for node in model_nodes if abs(node.center_xyz[2]) > _EPSILON}
    layered_count = sum(1 for node in model_nodes if abs(node.center_xyz[2]) > 1.0)
    volumetric_count = sum(1 for node in model_nodes if node.extents_xyz[2] > 6.0)
    layered_ratio = layered_count / float(max(1, model_count))
    volumetric_ratio = volumetric_count / float(max(1, model_count))

    if depth_span <= 1.0 and len(depth_layers) <= 1 and layered_ratio < 0.10:
        capability = LAYOUT_CAPABILITY_2D
    elif (depth_ratio >= 0.25 and layered_ratio >= 0.35 and len(depth_layers) >= 3) or (volumetric_ratio >= 0.20 and depth_span > 12.0):
        capability = LAYOUT_CAPABILITY_3D
    elif depth_ratio >= 0.05 or layered_ratio >= 0.10 or len(depth_layers) >= 2:
        capability = LAYOUT_CAPABILITY_25D
    else:
        capability = LAYOUT_CAPABILITY_2D

    return LayoutCapabilityReport(
        capability=capability,
        model_count=model_count,
        horizontal_span=horizontal_span,
        vertical_span=vertical_span,
        depth_span=depth_span,
        depth_ratio=depth_ratio,
        depth_layer_count=len(depth_layers),
        layered_model_ratio=layered_ratio,
        volumetric_model_ratio=volumetric_ratio,
    )


def build_scene(
    parsed_layout: xmp.ParsedLayout,
    *,
    projector: FrontProjector | None = None,
) -> SpatialScene:
    active_projector = projector or FrontProjector()
    membership = _group_membership(parsed_layout)
    model_nodes: dict[str, SceneNode] = {}
    aliases = dict(parsed_layout.aliases)

    for model_name, model in parsed_layout.models.items():
        points = _model_points(model)
        bounds = _bounds_from_points(points)
        center = _center_from_points(points)
        outline = _projected_outline(points, active_projector)
        projected_center = active_projector.project_xyz(center)
        projected_bounds = _projected_bounds(outline, projected_center)
        model_nodes[model_name] = SceneNode(
            name=model_name,
            kind="model",
            center_xyz=center,
            extents_xyz=_extent_tuple(bounds),
            projected_xy=projected_center,
            bounds_xyz=bounds,
            projected_bounds_xy=projected_bounds,
            projected_outline_xy=outline,
            tags=_node_tags(model),
            groups=membership.get(model_name, ()),
        )
        aliases[xmp.normalize_name(model_name)] = model_name
        for alias in model.aliases:
            aliases[xmp.normalize_name(alias)] = model_name

    group_nodes: dict[str, SceneNode] = {}
    groups: dict[str, tuple[str, ...]] = {}
    for group_name, group in parsed_layout.groups.items():
        members: list[str] = []
        member_nodes: list[SceneNode] = []
        for raw_member in group.models:
            resolved = parsed_layout.model_for(raw_member)
            member_name = resolved.name if resolved is not None else raw_member
            if member_name in model_nodes:
                members.append(member_name)
                member_nodes.append(model_nodes[member_name])
        groups[group_name] = tuple(members)
        if member_nodes:
            bounds = (
                min(node.bounds_xyz[0] for node in member_nodes),
                min(node.bounds_xyz[1] for node in member_nodes),
                min(node.bounds_xyz[2] for node in member_nodes),
                max(node.bounds_xyz[3] for node in member_nodes),
                max(node.bounds_xyz[4] for node in member_nodes),
                max(node.bounds_xyz[5] for node in member_nodes),
            )
            center = (
                sum(node.center_xyz[0] for node in member_nodes) / len(member_nodes),
                sum(node.center_xyz[1] for node in member_nodes) / len(member_nodes),
                sum(node.center_xyz[2] for node in member_nodes) / len(member_nodes),
            )
            outline_xyz = [
                (bounds[0], bounds[1], center[2]),
                (bounds[0], bounds[4], center[2]),
                (bounds[3], bounds[4], center[2]),
                (bounds[3], bounds[1], center[2]),
            ]
        else:
            gx = group.coordinates[0] if group.coordinates is not None else 0.0
            gy = group.coordinates[1] if group.coordinates is not None else 0.0
            center = (gx, gy, 0.0)
            bounds = (gx, gy, 0.0, gx, gy, 0.0)
            outline_xyz = [(gx, gy, 0.0)]
        outline = _projected_outline(outline_xyz, active_projector)
        projected_center = active_projector.project_xyz(center)
        group_nodes[group_name] = SceneNode(
            name=group_name,
            kind="group",
            center_xyz=center,
            extents_xyz=_extent_tuple(bounds),
            projected_xy=projected_center,
            bounds_xyz=bounds,
            projected_bounds_xy=_projected_bounds(outline, projected_center),
            projected_outline_xy=outline,
            tags=("group",),
            groups=(),
        )
        aliases[xmp.normalize_name(group_name)] = group_name

    report = detect_layout_capability(model_nodes.values())
    return SpatialScene(
        path=parsed_layout.path,
        capability=report.capability,
        capability_report=report,
        nodes=model_nodes,
        group_nodes=group_nodes,
        groups=groups,
        aliases=aliases,
        projector=active_projector,
    )


@lru_cache(maxsize=8)
def _load_scene_cached(path_str: str, mtime_ns: int) -> SpatialScene:
    return build_scene(xmp.parse_layout(Path(path_str)))


def load_scene(layout_path: Path) -> SpatialScene:
    resolved = layout_path.resolve()
    stat = resolved.stat()
    return _load_scene_cached(str(resolved), int(stat.st_mtime_ns))


def _projected_center(scene: SpatialScene, names: Sequence[str]) -> tuple[float, float]:
    coords = [scene.node_for(name).projected_xy for name in names if scene.node_for(name) is not None]
    if not coords:
        return (0.0, 0.0)
    return (
        sum(point[0] for point in coords) / len(coords),
        sum(point[1] for point in coords) / len(coords),
    )


def _xyz_center(scene: SpatialScene, names: Sequence[str]) -> tuple[float, float, float]:
    coords = [scene.node_for(name).center_xyz for name in names if scene.node_for(name) is not None]
    if not coords:
        return (0.0, 0.0, 0.0)
    return (
        sum(point[0] for point in coords) / len(coords),
        sum(point[1] for point in coords) / len(coords),
        sum(point[2] for point in coords) / len(coords),
    )


def _distance_xy(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


def _distance_xyz(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2)


def _axis_value(node: SceneNode, axis: str, distance_mode: str) -> float:
    if axis == "z":
        return float(node.center_xyz[2])
    if distance_mode == "projected_xy":
        return float(node.projected_xy[0] if axis == "x" else node.projected_xy[1])
    if axis == "y":
        return float(node.center_xyz[1])
    return float(node.center_xyz[0])


def _ordered_available_nodes(scene: SpatialScene, names: Iterable[str]) -> list[SceneNode]:
    ordered: list[SceneNode] = []
    seen: set[str] = set()
    for name in names:
        node = scene.node_for(name)
        if node is None:
            continue
        key = node.name.lower()
        if key in seen:
            continue
        seen.add(key)
        ordered.append(node)
    return ordered


def _nearest_neighbor_order(
    nodes: list[SceneNode],
    *,
    distance_mode: str,
    start_hint: tuple[float, float] | None = None,
) -> list[str]:
    if len(nodes) < 2:
        return [node.name for node in nodes]
    remaining = nodes[:]
    if start_hint is None:
        start = min(remaining, key=lambda node: (node.projected_xy[0], node.projected_xy[1], node.name.lower()))
    else:
        start = min(remaining, key=lambda node: _distance_xy(node.projected_xy, start_hint))
    ordered = [start]
    remaining.remove(start)
    while remaining:
        current = ordered[-1]
        if distance_mode == "xyz":
            next_node = min(remaining, key=lambda node: _distance_xyz(node.center_xyz, current.center_xyz))
        else:
            next_node = min(remaining, key=lambda node: _distance_xy(node.projected_xy, current.projected_xy))
        ordered.append(next_node)
        remaining.remove(next_node)
    return [node.name for node in ordered]


def order_names_for_family(
    scene: SpatialScene,
    names: Iterable[str],
    family: str,
    *,
    path_style: str | None = None,
    reverse: bool = False,
) -> list[str]:
    nodes = _ordered_available_nodes(scene, names)
    if len(nodes) < 2:
        return [node.name for node in nodes]

    route = route_spatial_effect(family, scene)
    style = xmp.normalize_name(path_style or "")
    if style == "left to right":
        ordered = sorted(nodes, key=lambda node: (node.projected_xy[0], node.projected_xy[1], node.name.lower()))
    elif style == "top to bottom":
        ordered = sorted(nodes, key=lambda node: (node.projected_xy[1], node.projected_xy[0], node.name.lower()))
    elif style == "radial out":
        if route.distance_mode == "xyz":
            center = _xyz_center(scene, [node.name for node in nodes])
            ordered = sorted(nodes, key=lambda node: (_distance_xyz(node.center_xyz, center), node.name.lower()))
        else:
            center_xy = _projected_center(scene, [node.name for node in nodes])
            ordered = sorted(nodes, key=lambda node: (_distance_xy(node.projected_xy, center_xy), node.name.lower()))
    elif style == "group to group":
        center_xy = _projected_center(scene, [node.name for node in nodes])
        quadrants: dict[int, list[SceneNode]] = {0: [], 1: [], 2: [], 3: []}
        for node in nodes:
            x_value, y_value = node.projected_xy
            quadrant = 0
            if x_value >= center_xy[0] and y_value >= center_xy[1]:
                quadrant = 1
            elif x_value < center_xy[0] and y_value >= center_xy[1]:
                quadrant = 2
            elif x_value < center_xy[0] and y_value < center_xy[1]:
                quadrant = 3
            quadrants[quadrant].append(node)
        ordered = []
        for quadrant in (0, 1, 2, 3):
            ordered.extend(sorted(quadrants[quadrant], key=lambda node: node.name.lower()))
    elif style == "random walk":
        ordered = [scene.node_for(name) for name in _nearest_neighbor_order(nodes, distance_mode=route.distance_mode)]
        ordered = [node for node in ordered if node is not None]
    elif style == "wave":
        xs = [node.projected_xy[0] for node in nodes]
        min_x, max_x = min(xs), max(xs)
        span = max(0.001, max_x - min_x)
        ordered = sorted(
            nodes,
            key=lambda node: (
                node.projected_xy[0],
                math.sin(((node.projected_xy[0] - min_x) / span) * math.pi * 2.0) + node.projected_xy[1] * 0.04,
                node.name.lower(),
            ),
        )
    elif route.path_strategy == "orbit_xz":
        center_xyz = _xyz_center(scene, [node.name for node in nodes])
        ordered = sorted(
            nodes,
            key=lambda node: (
                math.atan2(node.center_xyz[2] - center_xyz[2], node.center_xyz[0] - center_xyz[0]),
                node.center_xyz[1],
                node.name.lower(),
            ),
        )
    elif route.path_strategy == "orbit_xy":
        center_xy = _projected_center(scene, [node.name for node in nodes])
        ordered = sorted(
            nodes,
            key=lambda node: (
                math.atan2(node.projected_xy[1] - center_xy[1], node.projected_xy[0] - center_xy[0]),
                node.name.lower(),
            ),
        )
    elif route.path_strategy == "nearest_neighbor":
        ordered = [scene.node_for(name) for name in _nearest_neighbor_order(nodes, distance_mode=route.distance_mode)]
        ordered = [node for node in ordered if node is not None]
    else:
        ordered = sorted(
            nodes,
            key=lambda node: (
                _axis_value(node, route.axis or "x", route.distance_mode),
                node.projected_xy[0],
                node.projected_xy[1],
                node.name.lower(),
            ),
        )

    ordered_names = [node.name for node in ordered]
    if reverse:
        ordered_names.reverse()
    return ordered_names


def radial_field(
    scene: SpatialScene,
    origin: str | tuple[float, float, float],
    *,
    family: str = "radial_burst",
    names: Iterable[str] | None = None,
    radius: float | None = None,
) -> dict[str, float]:
    route = route_spatial_effect(family, scene)
    nodes = _ordered_available_nodes(scene, names or scene.nodes.keys())
    if not nodes:
        return {}
    if isinstance(origin, str):
        origin_node = scene.node_for(origin)
        if origin_node is None:
            return {}
        origin_xyz = origin_node.center_xyz
        origin_xy = origin_node.projected_xy
    else:
        origin_xyz = origin
        origin_xy = scene.projector.project_xyz(origin_xyz)

    if radius is None:
        span = max(
            scene.capability_report.horizontal_span,
            scene.capability_report.vertical_span,
            scene.capability_report.depth_span if route.distance_mode == "xyz" else 0.0,
            1.0,
        )
        radius = max(1.0, span * 0.35)

    scores: dict[str, float] = {}
    for node in nodes:
        distance = _distance_xyz(node.center_xyz, origin_xyz) if route.distance_mode == "xyz" else _distance_xy(node.projected_xy, origin_xy)
        scores[node.name] = max(0.0, 1.0 - (distance / max(radius, 0.001)))
    return scores


def proximity_activation(
    scene: SpatialScene,
    origin: str | tuple[float, float, float],
    *,
    names: Iterable[str] | None = None,
    radius: float | None = None,
) -> dict[str, float]:
    return radial_field(scene, origin, family="proximity_activation", names=names, radius=radius)


def directional_wave(
    scene: SpatialScene,
    *,
    family: str = "wave_propagation",
    names: Iterable[str] | None = None,
    axis: str | None = None,
    progress: float = 0.0,
    width: float | None = None,
) -> dict[str, float]:
    route = route_spatial_effect(family, scene)
    nodes = _ordered_available_nodes(scene, names or scene.nodes.keys())
    if not nodes:
        return {}
    axis_key = axis or route.axis or "x"
    values = [_axis_value(node, axis_key, route.distance_mode) for node in nodes]
    lo = min(values)
    hi = max(values)
    span = max(0.001, hi - lo)
    center_value = lo + span * max(0.0, min(1.0, progress))
    wave_width = width if width is not None else max(span / max(3.0, math.sqrt(len(nodes))), 1.0)
    scores: dict[str, float] = {}
    for node in nodes:
        distance = abs(_axis_value(node, axis_key, route.distance_mode) - center_value)
        scores[node.name] = max(0.0, 1.0 - (distance / max(wave_width, 0.001)))
    return scores


def path_travel(
    scene: SpatialScene,
    names: Iterable[str],
    *,
    family: str = "trajectory_travel",
    progress: float = 0.0,
    width: float | None = None,
) -> dict[str, float]:
    route = route_spatial_effect(family, scene)
    ordered_names = order_names_for_family(scene, names, family)
    nodes = [scene.node_for(name) for name in ordered_names]
    nodes = [node for node in nodes if node is not None]
    if not nodes:
        return {}
    if len(nodes) == 1:
        return {nodes[0].name: 1.0}

    cumulative = [0.0]
    total = 0.0
    for idx in range(1, len(nodes)):
        prev = nodes[idx - 1]
        current = nodes[idx]
        segment = _distance_xyz(prev.center_xyz, current.center_xyz) if route.distance_mode == "xyz" else _distance_xy(prev.projected_xy, current.projected_xy)
        total += segment
        cumulative.append(total)
    if total <= 0.0001:
        return {node.name: 1.0 if idx == 0 else 0.0 for idx, node in enumerate(nodes)}

    travel_width = width if width is not None else max(total / max(3.0, len(nodes) - 1), 1.0)
    focus = total * max(0.0, min(1.0, progress))
    scores: dict[str, float] = {}
    for node, distance in zip(nodes, cumulative):
        scores[node.name] = max(0.0, 1.0 - (abs(distance - focus) / max(travel_width, 0.001)))
    return scores
