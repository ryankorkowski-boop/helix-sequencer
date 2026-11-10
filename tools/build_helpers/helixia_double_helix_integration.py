from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from models.helixia_double_helix import build_giant_double_helix
from tools.build_helpers.helixia import build_helixia_layout


DOUBLE_HELIX_LOT_ID = "giant_double_helix"
DOUBLE_HELIX_GROUP = "HX_LOT_GIANT_DOUBLE_HELIX"


def build_double_helix_special_lot(double_helix: dict[str, Any]) -> dict[str, Any]:
    """Return the Helixia special-lot record for the giant double helix.

    This is intentionally geometry-backed but xLights-placeholder-safe: the
    canonical Helixia xLights generator should skip it until the dedicated 3D
    custom-model exporter is added.
    """
    return {
        "lot_id": DOUBLE_HELIX_LOT_ID,
        "display_name": "Giant Lighted Double Helix",
        "world_x_ft": 0.0,
        "world_y_ft": -18.0,
        "world_z_ft": 0.0,
        "model_types": ["custom", "line", "sphere", "matrix"],
        "geometry_only": True,
        "xlights_placeholder_safe": True,
        "contains": [
            "HELIXIA_GIANT_DOUBLE_HELIX",
            "HELIXIA_DNA_STRAND_A",
            "HELIXIA_DNA_STRAND_B",
            "HELIXIA_DNA_RUNGS",
            "HELIXIA_DNA_TOP_INPUT",
            "HELIXIA_DNA_BOTTOM_OUTPUT",
        ],
        "visual_role": "central_identity_landmark",
        "height_ft": double_helix["config"]["height_ft"],
        "radius_ft": double_helix["config"]["radius_ft"],
        "bounds_ft": dict(double_helix["bounds_ft"]),
        "narrative": "Audio enters the top input zone, spirals through DNA strands and rungs, then resolves into lights-out output at the base.",
        "submodels": sorted(double_helix["submodels"]),
    }


def inject_double_helix_into_helixia_payload(payload: dict[str, Any], double_helix: dict[str, Any] | None = None) -> dict[str, Any]:
    """Inject the giant double helix into an existing Helixia manifest payload."""
    double_helix = double_helix or build_giant_double_helix()
    lot = build_double_helix_special_lot(double_helix)
    payload = dict(payload)
    special_lots = [lot_item for lot_item in list(payload.get("special_lots", []) or []) if lot_item.get("lot_id") != DOUBLE_HELIX_LOT_ID]
    special_lots.append(lot)
    payload["special_lots"] = special_lots
    payload["giant_double_helix"] = double_helix
    requirements = dict(payload.get("requirements_satisfied", {}) or {})
    requirements["giant_double_helix_centerpiece_present"] = True
    requirements["giant_double_helix_geometry_backed"] = bool(double_helix.get("validation", {}).get("has_two_equal_strands"))
    payload["requirements_satisfied"] = requirements

    intelligence = dict(payload.get("layout_intelligence", {}) or {})
    special_intelligence = [item for item in list(intelligence.get("special_lots", []) or []) if item.get("lot_id") != DOUBLE_HELIX_LOT_ID]
    special_intelligence.append(
        {
            "lot_id": DOUBLE_HELIX_LOT_ID,
            "display_name": lot["display_name"],
            "world_position_ft": [lot["world_x_ft"], lot["world_y_ft"], lot["world_z_ft"]],
            "model_types": lot["model_types"],
            "families": ["custom_props", "lines", "spheres", "matrices"],
            "roles": ["hero", "motion", "performer_or_special", "structure"],
            "stage_zone": True,
            "legacy_control_zone": False,
            "contains": lot["contains"],
            "geometry_only": True,
        }
    )
    intelligence["special_lots"] = special_intelligence
    performer_models = dict(intelligence.get("performer_models", {}) or {})
    performer_models["giant_double_helix"] = [
        "HELIXIA_GIANT_DOUBLE_HELIX",
        "HELIXIA_DNA_STRAND_A",
        "HELIXIA_DNA_STRAND_B",
        "HELIXIA_DNA_RUNGS",
        "HELIXIA_DNA_TOP_INPUT",
        "HELIXIA_DNA_BOTTOM_OUTPUT",
    ]
    intelligence["performer_models"] = performer_models
    required_groups = list(dict.fromkeys([*list(intelligence.get("required_groups", []) or []), DOUBLE_HELIX_GROUP]))
    intelligence["required_groups"] = required_groups
    readability = dict(intelligence.get("two_dimensional_readability", {}) or {})
    readability["double_helix_uses_central_vertical_landmark"] = True
    intelligence["two_dimensional_readability"] = readability
    payload["layout_intelligence"] = intelligence
    return payload


def build_helixia_layout_with_double_helix(
    output_dir: str | Path,
    *,
    village_rows: int = 3,
    village_cols: int = 4,
    use_helixville4_band_model_specs: bool = False,
) -> dict[str, Any]:
    """Build Helixia/Helixville4 and inject the giant double helix manifest lot."""
    out_dir = Path(output_dir)
    payload = build_helixia_layout(
        out_dir,
        village_rows=village_rows,
        village_cols=village_cols,
        use_helixville4_band_model_specs=use_helixville4_band_model_specs,
    )
    payload = inject_double_helix_into_helixia_payload(payload)
    (out_dir / "helixia_manifest.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    notes_path = out_dir / "HELIXIA_LAYOUT_NOTES.txt"
    existing_notes = notes_path.read_text(encoding="utf-8") if notes_path.exists() else ""
    notes_path.write_text(
        existing_notes
        + "Giant Lighted Double Helix manifest integration is enabled as geometry-backed, xLights-placeholder-safe centerpiece.\n",
        encoding="utf-8",
    )
    return payload
