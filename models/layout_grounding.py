from __future__ import annotations

from copy import deepcopy
from typing import Any, Iterable, Mapping


GROUNDING_SCHEMA = "helix.layout_grounding.v1"
GROUND_PLANE_Z_FT = 0.0


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _point_z(point: Mapping[str, Any]) -> float:
    if "z" in point:
        return _safe_float(point.get("z"))
    if "world_z_ft" in point:
        return _safe_float(point.get("world_z_ft"))
    if "anchor_z_ft" in point:
        return _safe_float(point.get("anchor_z_ft"))
    return 0.0


def geometry_bounds(points: Iterable[Mapping[str, Any]]) -> dict[str, float]:
    """Return simple XYZ bounds for points using x/y/z or world_*_ft keys."""
    point_list = list(points)
    if not point_list:
        return {
            "min_x_ft": 0.0,
            "max_x_ft": 0.0,
            "min_y_ft": 0.0,
            "max_y_ft": 0.0,
            "min_z_ft": 0.0,
            "max_z_ft": 0.0,
            "height_ft": 0.0,
        }
    xs = [_safe_float(point.get("x", point.get("world_x_ft", point.get("anchor_x_ft", 0.0)))) for point in point_list]
    ys = [_safe_float(point.get("y", point.get("world_y_ft", point.get("anchor_y_ft", 0.0)))) for point in point_list]
    zs = [_point_z(point) for point in point_list]
    return {
        "min_x_ft": round(min(xs), 3),
        "max_x_ft": round(max(xs), 3),
        "min_y_ft": round(min(ys), 3),
        "max_y_ft": round(max(ys), 3),
        "min_z_ft": round(min(zs), 3),
        "max_z_ft": round(max(zs), 3),
        "height_ft": round(max(zs) - min(zs), 3),
    }


def align_points_to_ground(points: Iterable[Mapping[str, Any]], *, ground_z_ft: float = GROUND_PLANE_Z_FT) -> list[dict[str, Any]]:
    """Return point dictionaries shifted so their lowest z/world_z_ft equals ground_z_ft."""
    copied = [dict(point) for point in points]
    if not copied:
        return []
    current_min_z = min(_point_z(point) for point in copied)
    offset = ground_z_ft - current_min_z
    aligned: list[dict[str, Any]] = []
    for point in copied:
        item = dict(point)
        if "z" in item:
            item["z"] = round(_safe_float(item.get("z")) + offset, 3)
        if "world_z_ft" in item:
            item["world_z_ft"] = round(_safe_float(item.get("world_z_ft")) + offset, 3)
        if "anchor_z_ft" in item:
            item["anchor_z_ft"] = round(_safe_float(item.get("anchor_z_ft")) + offset, 3)
        if "z" not in item and "world_z_ft" not in item and "anchor_z_ft" not in item:
            item["world_z_ft"] = round(ground_z_ft, 3)
        aligned.append(item)
    return aligned


def align_model_to_ground(model: Mapping[str, Any], *, ground_z_ft: float = GROUND_PLANE_Z_FT) -> dict[str, Any]:
    """Return a model placement normalized to the ground plane.

    Models with point clouds are shifted by their lowest point. Simple placement
    records without points get their anchor z snapped to ground unless marked as
    intentionally elevated.
    """
    result = deepcopy(dict(model))
    intentionally_elevated = bool(result.get("intentionally_elevated", False))
    points = list(result.get("points", []) or [])
    if points and not intentionally_elevated:
        aligned_points = align_points_to_ground(points, ground_z_ft=ground_z_ft)
        result["points"] = aligned_points
        bounds = geometry_bounds(aligned_points)
        result["anchor_z_ft"] = round(ground_z_ft, 3)
        result["min_z_ft"] = bounds["min_z_ft"]
        result["max_z_ft"] = bounds["max_z_ft"]
        result["height_ft"] = bounds["height_ft"]
    elif not intentionally_elevated:
        height_ft = max(0.0, _safe_float(result.get("height_ft", result.get("visual_height_ft", 0.0))))
        result["anchor_z_ft"] = round(ground_z_ft, 3)
        result["min_z_ft"] = round(ground_z_ft, 3)
        result["max_z_ft"] = round(ground_z_ft + height_ft, 3)
        result["height_ft"] = round(height_ft, 3)
    else:
        anchor_z = _safe_float(result.get("anchor_z_ft", result.get("world_z_ft", ground_z_ft)))
        height_ft = max(0.0, _safe_float(result.get("height_ft", result.get("visual_height_ft", 0.0))))
        result["anchor_z_ft"] = round(anchor_z, 3)
        result["min_z_ft"] = round(anchor_z, 3)
        result["max_z_ft"] = round(anchor_z + height_ft, 3)
        result["height_ft"] = round(height_ft, 3)
    result["ground_plane_z_ft"] = round(ground_z_ft, 3)
    result["grounded"] = not intentionally_elevated and round(result.get("min_z_ft", ground_z_ft), 3) == round(ground_z_ft, 3)
    result["grounding_schema"] = GROUNDING_SCHEMA
    return result


def validate_ground_alignment(models: Iterable[Mapping[str, Any]], *, ground_z_ft: float = GROUND_PLANE_Z_FT) -> dict[str, Any]:
    """Validate that all non-elevated models are aligned to the ground plane."""
    model_list = list(models)
    floating = []
    negative = []
    for model in model_list:
        model_id = str(model.get("model_id", model.get("name", "unknown")))
        if bool(model.get("intentionally_elevated", False)):
            continue
        min_z = _safe_float(model.get("min_z_ft", model.get("anchor_z_ft", ground_z_ft)))
        if round(min_z, 3) != round(ground_z_ft, 3):
            floating.append(model_id)
        if min_z < ground_z_ft - 0.001:
            negative.append(model_id)
    return {
        "schema": GROUNDING_SCHEMA,
        "ground_plane_z_ft": round(ground_z_ft, 3),
        "model_count": len(model_list),
        "floating_grounded_models": floating,
        "negative_grounded_models": negative,
        "all_grounded_models_on_ground": not floating,
        "no_grounded_models_below_ground": not negative,
    }
