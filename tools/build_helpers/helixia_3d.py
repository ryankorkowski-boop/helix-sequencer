from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from models.layout_grounding import GROUND_PLANE_Z_FT, align_model_to_ground, validate_ground_alignment
from tools.build_helpers.helixia_double_helix_integration import build_helixia_layout_with_double_helix


HELIXIA_3D_SCHEMA = "helixia.layout3d.v1"
DEFAULT_HELIXIA_3D_OUTPUT = "helixia_3d_manifest.json"


MODEL_TYPE_DIMENSIONS: dict[str, tuple[float, float, float]] = {
    "arch": (28.0, 8.0, 12.0),
    "tree": (18.0, 18.0, 28.0),
    "matrix": (28.0, 4.0, 16.0),
    "line": (36.0, 2.0, 3.0),
    "candy_cane": (5.0, 5.0, 8.0),
    "circle": (16.0, 4.0, 16.0),
    "sphere": (12.0, 12.0, 12.0),
    "star": (14.0, 4.0, 14.0),
    "spinner": (18.0, 4.0, 18.0),
    "icicles": (34.0, 3.0, 8.0),
    "window_frame": (18.0, 4.0, 12.0),
    "dmx": (4.0, 4.0, 2.0),
    "custom": (18.0, 8.0, 14.0),
}


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _dims_for_model_type(model_type: str) -> tuple[float, float, float]:
    return MODEL_TYPE_DIMENSIONS.get(model_type, MODEL_TYPE_DIMENSIONS["custom"])


def _placed_model(
    *,
    model_id: str,
    lot_id: str,
    model_type: str,
    anchor_x_ft: float,
    anchor_y_ft: float,
    index: int = 0,
    stage_zone: bool = False,
) -> dict[str, Any]:
    width, depth, height = _dims_for_model_type(model_type)
    offset_x = (index - 1) * max(width * 0.75, 8.0)
    model = {
        "model_id": model_id,
        "lot_id": lot_id,
        "model_type": model_type,
        "anchor_x_ft": round(anchor_x_ft + offset_x, 3),
        "anchor_y_ft": round(anchor_y_ft, 3),
        "anchor_z_ft": GROUND_PLANE_Z_FT,
        "width_ft": width,
        "depth_ft": depth,
        "height_ft": height,
        "stage_zone": stage_zone,
        "intentionally_elevated": False,
    }
    return align_model_to_ground(model)


def _house_models(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    models: list[dict[str, Any]] = []
    for house in payload.get("village_grid", {}).get("houses", []) or []:
        lot_id = str(house.get("lot_id", "house"))
        for idx, model_type in enumerate(list(house.get("model_types", []) or [])):
            models.append(
                _placed_model(
                    model_id=f"HX3D_{lot_id}_{model_type}",
                    lot_id=lot_id,
                    model_type=str(model_type),
                    anchor_x_ft=_safe_float(house.get("world_x_ft")),
                    anchor_y_ft=_safe_float(house.get("world_y_ft")),
                    index=idx,
                )
            )
    return models


def _fibonacci_models(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    models: list[dict[str, Any]] = []
    for tree in payload.get("fibonacci_tree_lot", {}).get("trees", []) or []:
        height = _safe_float(tree.get("height_ft"), 20.0)
        item = {
            "model_id": f"HX3D_FIB_{tree.get('tree_id')}",
            "lot_id": "fibonacci_tree_lot",
            "model_type": "tree",
            "anchor_x_ft": _safe_float(tree.get("world_x_ft")),
            "anchor_y_ft": _safe_float(tree.get("world_y_ft")),
            "anchor_z_ft": GROUND_PLANE_Z_FT,
            "width_ft": max(8.0, height * 0.45),
            "depth_ft": max(8.0, height * 0.45),
            "height_ft": height,
            "stage_zone": False,
            "intentionally_elevated": False,
        }
        models.append(align_model_to_ground(item))
    return models


def _special_lot_models(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    models: list[dict[str, Any]] = []
    for lot in payload.get("special_lots", []) or []:
        lot_id = str(lot.get("lot_id", "special"))
        if lot_id == "giant_double_helix":
            continue
        stage_zone = bool("stage" in lot_id or "dj" in lot_id)
        for idx, model_type in enumerate(list(lot.get("model_types", []) or [])):
            models.append(
                _placed_model(
                    model_id=f"HX3D_{lot_id}_{model_type}",
                    lot_id=lot_id,
                    model_type=str(model_type),
                    anchor_x_ft=_safe_float(lot.get("world_x_ft")),
                    anchor_y_ft=_safe_float(lot.get("world_y_ft")),
                    index=idx,
                    stage_zone=stage_zone,
                )
            )
    return models


def _double_helix_model(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    geometry = payload.get("giant_double_helix")
    if not geometry:
        return None
    points = [
        {
            "point_id": point["node_id"],
            "x": _safe_float(point.get("world_x_ft")),
            # Current helix geometry uses world_y_ft as vertical height; convert to canonical z.
            "y": 0.0,
            "z": _safe_float(point.get("world_y_ft")),
            "strand": point.get("strand"),
            "phase": point.get("phase"),
        }
        for point in list(geometry.get("strand_a", []) or []) + list(geometry.get("strand_b", []) or [])
    ]
    model = {
        "model_id": "HELIXIA_GIANT_DOUBLE_HELIX",
        "lot_id": "giant_double_helix",
        "model_type": "custom_3d_landmark",
        "anchor_x_ft": 0.0,
        "anchor_y_ft": -18.0,
        "anchor_z_ft": GROUND_PLANE_Z_FT,
        "width_ft": round(_safe_float(geometry.get("config", {}).get("radius_ft"), 24.0) * 2.0, 3),
        "depth_ft": round(_safe_float(geometry.get("config", {}).get("radius_ft"), 24.0) * 2.0, 3),
        "height_ft": _safe_float(geometry.get("config", {}).get("height_ft"), 112.0),
        "points": points,
        "stage_zone": True,
        "intentionally_elevated": False,
        "base_contact_mode": "lowest_point",
    }
    grounded = align_model_to_ground(model)
    grounded["submodels"] = sorted(geometry.get("submodels", {}))
    return grounded


def _derive_2d_projection(models: list[Mapping[str, Any]]) -> dict[str, Any]:
    footprints = []
    for model in models:
        width = _safe_float(model.get("width_ft"), 0.0)
        depth = _safe_float(model.get("depth_ft"), 0.0)
        x = _safe_float(model.get("anchor_x_ft"), 0.0)
        y = _safe_float(model.get("anchor_y_ft"), 0.0)
        footprints.append(
            {
                "model_id": model.get("model_id"),
                "lot_id": model.get("lot_id"),
                "x_ft": round(x, 3),
                "y_ft": round(y, 3),
                "width_ft": round(width, 3),
                "depth_ft": round(depth, 3),
                "footprint_area_sqft": round(max(0.0, width * depth), 3),
            }
        )
    if not footprints:
        bounds = {"min_x_ft": 0.0, "max_x_ft": 0.0, "min_y_ft": 0.0, "max_y_ft": 0.0}
    else:
        bounds = {
            "min_x_ft": round(min(item["x_ft"] for item in footprints), 3),
            "max_x_ft": round(max(item["x_ft"] for item in footprints), 3),
            "min_y_ft": round(min(item["y_ft"] for item in footprints), 3),
            "max_y_ft": round(max(item["y_ft"] for item in footprints), 3),
        }
    return {
        "schema": "helixia.layout3d_projection2d.v1",
        "source": "derived_from_3d_anchors",
        "footprints": footprints,
        "bounds_ft": bounds,
        "readability": {
            "projection_is_derived_from_3d": True,
            "houses_preserve_grid": True,
            "special_lots_preserve_world_positions": True,
            "double_helix_uses_central_landmark_footprint": any(
                item["model_id"] == "HELIXIA_GIANT_DOUBLE_HELIX" for item in footprints
            ),
        },
    }


def build_helixia_3d_layout(
    output_dir: str | Path,
    *,
    village_rows: int = 3,
    village_cols: int = 4,
    use_helixville4_band_model_specs: bool = False,
) -> dict[str, Any]:
    """Build a grounded 3D Helixia layout manifest.

    The 3D manifest is the source of truth: 2D is derived as a footprint
    projection. Every non-elevated model is snapped to z=0.
    """
    out_dir = Path(output_dir)
    helixia_payload = build_helixia_layout_with_double_helix(
        out_dir,
        village_rows=village_rows,
        village_cols=village_cols,
        use_helixville4_band_model_specs=use_helixville4_band_model_specs,
    )
    models = [
        *_house_models(helixia_payload),
        *_fibonacci_models(helixia_payload),
        *_special_lot_models(helixia_payload),
    ]
    double_helix = _double_helix_model(helixia_payload)
    if double_helix:
        models.append(double_helix)
    grounding = validate_ground_alignment(models)
    projection = _derive_2d_projection(models)
    stage_models = [model for model in models if model.get("stage_zone")]
    payload = {
        "schema": HELIXIA_3D_SCHEMA,
        "layout_id": "helixia_v1_3d",
        "layout_name": "Helixia 3D Grounded Layout (Helixville4)",
        "ground_plane_z_ft": GROUND_PLANE_Z_FT,
        "source_layout_id": helixia_payload.get("layout_id"),
        "models": models,
        "stage_zones": {
            "model_count": len(stage_models),
            "model_ids": [model["model_id"] for model in stage_models],
        },
        "projection_2d": projection,
        "grounding": grounding,
        "validation": {
            "all_grounded_models_on_ground": grounding["all_grounded_models_on_ground"],
            "no_grounded_models_below_ground": grounding["no_grounded_models_below_ground"],
            "has_double_helix": any(model["model_id"] == "HELIXIA_GIANT_DOUBLE_HELIX" for model in models),
            "double_helix_grounded": any(
                model["model_id"] == "HELIXIA_GIANT_DOUBLE_HELIX" and model["grounded"] and model["min_z_ft"] == 0.0
                for model in models
            ),
            "projection_is_derived_from_3d": projection["readability"]["projection_is_derived_from_3d"],
            "has_stage_models": bool(stage_models),
            "has_house_models": any(str(model.get("lot_id", "")).startswith("house_") for model in models),
        },
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / DEFAULT_HELIXIA_3D_OUTPUT).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload
