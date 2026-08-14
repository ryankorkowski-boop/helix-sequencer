from __future__ import annotations

"""Bridge Helix's canonical SpatialScene into a renderer-friendly 3D scene.

The bridge deliberately does not invent geometry. It consumes the same
WorldPos/scene data used by spatial orchestration and exposes a stable
representation for preview renderers. 2D layouts remain valid and are marked
as a fallback instead of silently pretending to be 3D.
"""

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from core import spatial_scene


@dataclass(frozen=True)
class RenderNode3D:
    name: str
    kind: str
    position: tuple[float, float, float]
    size: tuple[float, float, float]
    bounds: tuple[float, float, float, float, float, float]
    projected_xy: tuple[float, float]
    tags: tuple[str, ...]
    groups: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["position"] = list(self.position)
        data["size"] = list(self.size)
        data["bounds"] = list(self.bounds)
        data["projected_xy"] = list(self.projected_xy)
        return data


@dataclass(frozen=True)
class SpatialRenderScene:
    capability: str
    is_true_3d: bool
    nodes: tuple[RenderNode3D, ...]
    bounds: tuple[float, float, float, float, float, float]

    def to_dict(self) -> dict[str, Any]:
        return {
            "capability": self.capability,
            "is_true_3d": self.is_true_3d,
            "bounds": list(self.bounds),
            "nodes": [node.to_dict() for node in self.nodes],
        }


def build_render_scene(scene: spatial_scene.SpatialScene) -> SpatialRenderScene:
    """Convert a SpatialScene without losing its Z coordinate."""
    model_nodes = [
        node for node in scene.nodes.values()
        if node.kind == "model" and "root" in node.tags
    ]
    model_nodes.sort(key=lambda node: node.name.lower())

    if model_nodes:
        bounds = (
            min(node.bounds_xyz[0] for node in model_nodes),
            min(node.bounds_xyz[1] for node in model_nodes),
            min(node.bounds_xyz[2] for node in model_nodes),
            max(node.bounds_xyz[3] for node in model_nodes),
            max(node.bounds_xyz[4] for node in model_nodes),
            max(node.bounds_xyz[5] for node in model_nodes),
        )
    else:
        bounds = (0.0, 0.0, 0.0, 1.0, 1.0, 1.0)

    nodes = tuple(
        RenderNode3D(
            name=node.name,
            kind=node.kind,
            position=node.center_xyz,
            size=node.extents_xyz,
            bounds=node.bounds_xyz,
            projected_xy=node.projected_xy,
            tags=node.tags,
            groups=node.groups,
        )
        for node in model_nodes
    )

    return SpatialRenderScene(
        capability=scene.capability,
        is_true_3d=scene.capability == spatial_scene.LAYOUT_CAPABILITY_3D,
        nodes=nodes,
        bounds=bounds,
    )


def build_render_scene_from_layout(layout_path: Path) -> SpatialRenderScene:
    """Build the canonical render scene directly from an xLights layout."""
    scene = spatial_scene.load_scene(layout_path)
    return build_render_scene(scene)


def validate_true_3d(render_scene: SpatialRenderScene) -> tuple[bool, str]:
    """Return whether the scene contains meaningful depth for 3D rendering."""
    if not render_scene.nodes:
        return False, "scene contains no root model nodes"
    if not render_scene.is_true_3d:
        return False, f"layout capability is {render_scene.capability!r}, not '3d'"
    z_span = render_scene.bounds[5] - render_scene.bounds[2]
    if z_span <= 1e-6:
        return False, "3D scene has zero Z span"
    return True, "true 3D scene"
