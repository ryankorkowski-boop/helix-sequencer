from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from typing import Any, Iterable, Mapping, Sequence

from core import spatial_scene
from core.sequence_context import SequenceContext, clamp01


MODEL_CATEGORIES = ("tree", "arch", "matrix", "face", "ac")


@dataclass(frozen=True)
class SpatialPoint:
    x: float
    y: float
    z: float = 0.0
    weight: float = 1.0
    timestamp_ms: int | None = None


@dataclass(frozen=True)
class SpatialTrajectory:
    name: str
    points: tuple[SpatialPoint, ...]
    start_ms: int = 0
    end_ms: int = 1000
    energy: float = 0.5


@dataclass(frozen=True)
class EnergyField:
    center: SpatialPoint
    radius: float = 0.25
    strength: float = 0.75
    start_ms: int = 0
    end_ms: int = 500


@dataclass(frozen=True)
class NormalizedSpatialPoint:
    x: float
    y: float
    z: float
    weight: float = 1.0
    timestamp_ms: int | None = None


@dataclass(frozen=True)
class MappedEffect:
    model: str
    model_type: str
    effect: str
    start_ms: int
    end_ms: int
    layer: str
    intensity: float
    normalized_position: tuple[float, float, float]
    parameters: dict[str, Any] = field(default_factory=dict)
    source: str = "spatial"

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["normalized_position"] = list(self.normalized_position)
        return data


@dataclass(frozen=True)
class SpatialMappingPlan:
    effects: list[MappedEffect]
    mapping_logs: list[dict[str, Any]]
    coverage_visualization: dict[str, Any]
    fallback_logs: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "effects": [effect.to_dict() for effect in self.effects],
            "mapping_logs": self.mapping_logs,
            "coverage_visualization": self.coverage_visualization,
            "fallback_logs": self.fallback_logs,
        }


def _point_from(value: Any) -> SpatialPoint:
    if isinstance(value, SpatialPoint):
        return value
    if isinstance(value, Mapping):
        return SpatialPoint(
            x=float(value.get("x", 0.0)),
            y=float(value.get("y", 0.0)),
            z=float(value.get("z", 0.0)),
            weight=float(value.get("weight", value.get("intensity", 1.0))),
            timestamp_ms=value.get("timestamp_ms"),
        )
    seq = list(value or [])
    return SpatialPoint(
        x=float(seq[0]) if len(seq) > 0 else 0.0,
        y=float(seq[1]) if len(seq) > 1 else 0.0,
        z=float(seq[2]) if len(seq) > 2 else 0.0,
        weight=float(seq[3]) if len(seq) > 3 else 1.0,
    )


def _scene_model_nodes(scene: spatial_scene.SpatialScene) -> list[spatial_scene.SceneNode]:
    return [node for node in scene.nodes.values() if node.kind == "model" and "root" in node.tags]


def _axis_bounds(scene: spatial_scene.SpatialScene) -> tuple[float, float, float, float, float, float]:
    nodes = _scene_model_nodes(scene)
    if not nodes:
        return (0.0, 1.0, 0.0, 1.0, 0.0, 1.0)
    return (
        min(node.bounds_xyz[0] for node in nodes),
        max(node.bounds_xyz[3] for node in nodes),
        min(node.bounds_xyz[1] for node in nodes),
        max(node.bounds_xyz[4] for node in nodes),
        min(node.bounds_xyz[2] for node in nodes),
        max(node.bounds_xyz[5] for node in nodes),
    )


def _normalize_axis(value: float, low: float, high: float) -> float:
    span = max(0.0001, high - low)
    return clamp01((value - low) / span)


def normalize_point(point: Any, scene: spatial_scene.SpatialScene) -> NormalizedSpatialPoint:
    raw = _point_from(point)
    x0, x1, y0, y1, z0, z1 = _axis_bounds(scene)
    already_normalized = all(0.0 <= value <= 1.0 for value in (raw.x, raw.y, raw.z))
    if already_normalized:
        return NormalizedSpatialPoint(raw.x, raw.y, raw.z, clamp01(raw.weight), raw.timestamp_ms)
    return NormalizedSpatialPoint(
        x=_normalize_axis(raw.x, x0, x1),
        y=_normalize_axis(raw.y, y0, y1),
        z=_normalize_axis(raw.z, z0, z1),
        weight=clamp01(raw.weight),
        timestamp_ms=raw.timestamp_ms,
    )


def normalize_spatial_data(
    scene: spatial_scene.SpatialScene,
    *,
    points: Iterable[Any] = (),
    trajectories: Iterable[SpatialTrajectory | Mapping[str, Any]] = (),
    energy_fields: Iterable[EnergyField | Mapping[str, Any]] = (),
) -> dict[str, Any]:
    normalized_points = [normalize_point(point, scene) for point in points]
    normalized_trajectories: list[SpatialTrajectory] = []
    for item in trajectories:
        if isinstance(item, SpatialTrajectory):
            raw = item
        else:
            raw_points = tuple(_point_from(point) for point in item.get("points", ()))
            raw = SpatialTrajectory(
                name=str(item.get("name", "trajectory")),
                points=raw_points,
                start_ms=int(item.get("start_ms", 0)),
                end_ms=int(item.get("end_ms", 1000)),
                energy=float(item.get("energy", 0.5)),
            )
        normalized_trajectories.append(
            SpatialTrajectory(
                name=raw.name,
                points=tuple(
                    SpatialPoint(p.x, p.y, p.z, p.weight, p.timestamp_ms)
                    for p in (normalize_point(point, scene) for point in raw.points)
                ),
                start_ms=raw.start_ms,
                end_ms=raw.end_ms,
                energy=raw.energy,
            )
        )
    normalized_fields: list[EnergyField] = []
    for item in energy_fields:
        if isinstance(item, EnergyField):
            raw_field = item
        else:
            raw_field = EnergyField(
                center=_point_from(item.get("center", (0.5, 0.5, 0.0))),
                radius=float(item.get("radius", 0.25)),
                strength=float(item.get("strength", 0.75)),
                start_ms=int(item.get("start_ms", 0)),
                end_ms=int(item.get("end_ms", 500)),
            )
        center = normalize_point(raw_field.center, scene)
        normalized_fields.append(
            EnergyField(
                center=SpatialPoint(center.x, center.y, center.z, center.weight, center.timestamp_ms),
                radius=clamp01(raw_field.radius),
                strength=clamp01(raw_field.strength),
                start_ms=raw_field.start_ms,
                end_ms=raw_field.end_ms,
            )
        )
    return {"points": normalized_points, "trajectories": normalized_trajectories, "energy_fields": normalized_fields}


def _node_category(node: spatial_scene.SceneNode) -> str:
    name = node.name.lower()
    tags = set(node.tags)
    groups = " ".join(node.groups).lower()
    haystack = f"{name} {groups} {' '.join(tags)}"
    if "face" in haystack or "mouth" in haystack or "eye" in haystack:
        return "face"
    if "matrix" in tags:
        return "matrix"
    if "tree" in tags:
        return "tree"
    if "arch" in tags:
        return "arch"
    if "ac" in tags or "single_color" in tags or "channelblock" in tags or "flood" in tags:
        return "ac"
    return "matrix" if "custom" in tags else "ac"


def categorize_models(scene: spatial_scene.SpatialScene) -> dict[str, list[spatial_scene.SceneNode]]:
    buckets = {category: [] for category in MODEL_CATEGORIES}
    for node in _scene_model_nodes(scene):
        category = _node_category(node)
        buckets.setdefault(category, []).append(node)
    for category in buckets:
        buckets[category].sort(key=lambda node: (node.center_xyz[0], node.center_xyz[1], node.name.lower()))
    return buckets


def _node_normalized(node: spatial_scene.SceneNode, scene: spatial_scene.SpatialScene) -> tuple[float, float, float]:
    x0, x1, y0, y1, z0, z1 = _axis_bounds(scene)
    return (
        _normalize_axis(node.center_xyz[0], x0, x1),
        _normalize_axis(node.center_xyz[1], y0, y1),
        _normalize_axis(node.center_xyz[2], z0, z1),
    )


def _distance(a: Sequence[float], b: Sequence[float], depth_weight: float = 0.45) -> float:
    return math.sqrt(((a[0] - b[0]) ** 2) + ((a[1] - b[1]) ** 2) + (((a[2] - b[2]) * depth_weight) ** 2))


def _nearest_node(
    scene: spatial_scene.SpatialScene,
    point: NormalizedSpatialPoint,
    candidates: Sequence[spatial_scene.SceneNode],
) -> spatial_scene.SceneNode | None:
    if not candidates:
        return None
    target = (point.x, point.y, point.z)
    return min(candidates, key=lambda node: (_distance(_node_normalized(node, scene), target), node.name.lower()))


def _fallback_candidates(
    buckets: Mapping[str, list[spatial_scene.SceneNode]],
    category: str,
) -> tuple[str, list[spatial_scene.SceneNode]]:
    fallback_order = {
        "tree": ("matrix", "arch", "ac", "face"),
        "arch": ("tree", "matrix", "ac", "face"),
        "matrix": ("tree", "arch", "face", "ac"),
        "face": ("matrix", "tree", "arch", "ac"),
        "ac": ("arch", "tree", "matrix", "face"),
    }
    for fallback in fallback_order.get(category, MODEL_CATEGORIES):
        candidates = buckets.get(fallback, [])
        if candidates:
            return fallback, candidates
    for fallback, candidates in buckets.items():
        if candidates:
            return fallback, candidates
    return category, []


def _adapt_effect(category: str, point: NormalizedSpatialPoint, source: str, style: Mapping[str, Any]) -> tuple[str, str, dict[str, Any]]:
    density = clamp01(float(style.get("effect_density", 0.62) or 0.62))
    motion_style = str(style.get("motion_style", "clean_hook_motion") or "clean_hook_motion")
    depth_offset_ms = int(round(point.z * (180 - (density * 70))))
    if category == "tree":
        return (
            "Spirals" if point.weight >= 0.55 else "SingleStrand",
            "motion",
            {
                "vertical_position": round(point.y, 4),
                "spiral_turns": max(1, int(round(2 + point.z * 4))),
                "direction": "up" if point.y >= 0.5 else "down",
                "depth_timing_offset_ms": depth_offset_ms,
                "motion_style": motion_style,
            },
        )
    if category == "arch":
        return (
            "Wave",
            "motion",
            {
                "horizontal_position": round(point.x, 4),
                "wave_phase": round(point.x, 4),
                "crest_height": round(point.y, 4),
                "depth_timing_offset_ms": depth_offset_ms,
                "motion_style": motion_style,
            },
        )
    if category == "matrix":
        return (
            "Shader" if point.weight >= 0.62 else "Pictures",
            "base",
            {
                "projection_x": round(point.x, 4),
                "projection_y": round(1.0 - point.y, 4),
                "zoom": round(0.8 + point.z * 0.55, 4),
                "shader_hint": "waveform_2d.glsl" if source == "trajectory" else "radial_pulse.glsl",
                "motion_style": motion_style,
            },
        )
    if category == "face":
        return (
            "On",
            "accent",
            {
                "focal_highlight": round(point.weight, 4),
                "vertical_focus": round(point.y, 4),
                "expression_hint": "open" if point.weight >= 0.65 else "soft",
                "depth_timing_offset_ms": depth_offset_ms,
            },
        )
    return (
        "On",
        "accent",
        {
            "gate_strength": round(point.weight, 4),
            "gate_position": round(point.x, 4),
            "depth_timing_offset_ms": depth_offset_ms,
            "rhythmic_gating": True,
        },
    )


def _effect_for_point(
    scene: spatial_scene.SpatialScene,
    point: NormalizedSpatialPoint,
    *,
    category: str,
    buckets: Mapping[str, list[spatial_scene.SceneNode]],
    start_ms: int,
    duration_ms: int,
    source: str,
    style: Mapping[str, Any],
    logs: list[dict[str, Any]],
    fallbacks: list[dict[str, Any]],
) -> MappedEffect | None:
    actual_category = category
    candidates = buckets.get(category, [])
    if not candidates:
        actual_category, candidates = _fallback_candidates(buckets, category)
        fallbacks.append({"requested": category, "used": actual_category, "reason": "missing_model_category"})
    node = _nearest_node(scene, point, candidates)
    if node is None:
        fallbacks.append({"requested": category, "used": None, "reason": "layout_has_no_models"})
        return None
    effect_name, layer, parameters = _adapt_effect(actual_category, point, source, style)
    offset = int(parameters.get("depth_timing_offset_ms", 0))
    mapped = MappedEffect(
        model=node.name,
        model_type=actual_category,
        effect=effect_name,
        start_ms=max(0, int(start_ms + offset)),
        end_ms=max(int(start_ms + offset) + 40, int(start_ms + offset + duration_ms)),
        layer=layer,
        intensity=round(clamp01((point.weight * 0.78) + (point.z * 0.22)), 4),
        normalized_position=(round(point.x, 4), round(point.y, 4), round(point.z, 4)),
        parameters=parameters,
        source=source,
    )
    logs.append(
        {
            "source": source,
            "requested_category": category,
            "mapped_category": actual_category,
            "model": node.name,
            "normalized_point": list(mapped.normalized_position),
            "effect": effect_name,
        }
    )
    return mapped


def _trajectory_effects(
    scene: spatial_scene.SpatialScene,
    trajectory: SpatialTrajectory,
    *,
    buckets: Mapping[str, list[spatial_scene.SceneNode]],
    style: Mapping[str, Any],
    logs: list[dict[str, Any]],
    fallbacks: list[dict[str, Any]],
) -> list[MappedEffect]:
    if not trajectory.points:
        return []
    effects: list[MappedEffect] = []
    span = max(1, trajectory.end_ms - trajectory.start_ms)
    point_count = max(1, len(trajectory.points))
    categories = ("matrix", "tree", "arch") if point_count > 2 else ("arch", "tree")
    for idx, point in enumerate(trajectory.points):
        ratio = 0.0 if point_count == 1 else idx / float(point_count - 1)
        category = categories[idx % len(categories)]
        effect = _effect_for_point(
            scene,
            NormalizedSpatialPoint(point.x, point.y, point.z, point.weight, point.timestamp_ms),
            category=category,
            buckets=buckets,
            start_ms=trajectory.start_ms + int(round(span * ratio)),
            duration_ms=max(90, int(round(span / point_count))),
            source="trajectory",
            style=style,
            logs=logs,
            fallbacks=fallbacks,
        )
        if effect is not None:
            effects.append(effect)
    return effects


def _energy_field_effects(
    scene: spatial_scene.SpatialScene,
    field: EnergyField,
    *,
    buckets: Mapping[str, list[spatial_scene.SceneNode]],
    style: Mapping[str, Any],
    logs: list[dict[str, Any]],
    fallbacks: list[dict[str, Any]],
) -> list[MappedEffect]:
    effects: list[MappedEffect] = []
    all_nodes = [node for nodes in buckets.values() for node in nodes]
    center = (field.center.x, field.center.y, field.center.z)
    ranked = sorted(
        all_nodes,
        key=lambda node: (_distance(_node_normalized(node, scene), center), node.name.lower()),
    )
    limit = max(1, min(8, int(round(2 + (field.strength * 6)))))
    for node in ranked[:limit]:
        node_pos = _node_normalized(node, scene)
        distance = _distance(node_pos, center)
        if distance > max(0.08, field.radius * 1.8) and len(effects) >= 1:
            continue
        point = NormalizedSpatialPoint(node_pos[0], node_pos[1], node_pos[2], clamp01(field.strength * (1.0 - min(0.9, distance))), None)
        category = _node_category(node)
        effect = _effect_for_point(
            scene,
            point,
            category=category,
            buckets=buckets,
            start_ms=field.start_ms,
            duration_ms=max(80, field.end_ms - field.start_ms),
            source="energy_field",
            style=style,
            logs=logs,
            fallbacks=fallbacks,
        )
        if effect is not None:
            effects.append(effect)
    return effects


def coverage_visualization(effects: Sequence[MappedEffect], *, width: int = 12, height: int = 6) -> dict[str, Any]:
    grid = [["." for _ in range(max(1, width))] for _ in range(max(1, height))]
    by_type = {category: 0 for category in MODEL_CATEGORIES}
    models = set()
    for effect in effects:
        x = min(width - 1, max(0, int(round(effect.normalized_position[0] * (width - 1)))))
        y = min(height - 1, max(0, int(round((1.0 - effect.normalized_position[1]) * (height - 1)))))
        grid[y][x] = "#"
        by_type[effect.model_type] = by_type.get(effect.model_type, 0) + 1
        models.add(effect.model)
    return {
        "grid": ["".join(row) for row in grid],
        "covered_models": sorted(models),
        "coverage_by_type": by_type,
        "effect_count": len(effects),
    }


def build_mapping_plan(
    scene: spatial_scene.SpatialScene,
    *,
    points: Iterable[Any] = (),
    trajectories: Iterable[SpatialTrajectory | Mapping[str, Any]] = (),
    energy_fields: Iterable[EnergyField | Mapping[str, Any]] = (),
    context: SequenceContext | None = None,
    start_ms: int = 0,
    point_duration_ms: int = 240,
) -> SpatialMappingPlan:
    normalized = normalize_spatial_data(scene, points=points, trajectories=trajectories, energy_fields=energy_fields)
    buckets = categorize_models(scene)
    style = (context.style_profile if context is not None else {}) or {}
    logs: list[dict[str, Any]] = []
    fallbacks: list[dict[str, Any]] = []
    effects: list[MappedEffect] = []

    point_categories = ("tree", "arch", "matrix", "face", "ac")
    for idx, point in enumerate(normalized["points"]):
        category = point_categories[idx % len(point_categories)]
        effect = _effect_for_point(
            scene,
            point,
            category=category,
            buckets=buckets,
            start_ms=point.timestamp_ms if point.timestamp_ms is not None else start_ms + idx * max(40, point_duration_ms // 3),
            duration_ms=point_duration_ms,
            source="point",
            style=style,
            logs=logs,
            fallbacks=fallbacks,
        )
        if effect is not None:
            effects.append(effect)

    for trajectory in normalized["trajectories"]:
        effects.extend(_trajectory_effects(scene, trajectory, buckets=buckets, style=style, logs=logs, fallbacks=fallbacks))

    for field in normalized["energy_fields"]:
        effects.extend(_energy_field_effects(scene, field, buckets=buckets, style=style, logs=logs, fallbacks=fallbacks))

    visualization = coverage_visualization(effects)
    plan = SpatialMappingPlan(effects=effects, mapping_logs=logs, coverage_visualization=visualization, fallback_logs=fallbacks)
    if context is not None:
        context.update_spatial_features(
            {
                "layout_capability": scene.capability,
                "mapped_effect_count": len(effects),
                "coverage_by_type": visualization["coverage_by_type"],
            }
        )
        context.add_debug("spatial_mapping_engine", "mapping_plan_built", plan.to_dict())
    return plan
