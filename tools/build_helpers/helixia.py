from __future__ import annotations

import json
import shutil
import xml.etree.ElementTree as ET
from copy import deepcopy
from pathlib import Path
from typing import Any

from tools.write_helixville4_band_assets import write_band_assets

ROOT = Path(__file__).resolve().parents[2]
COMMITTED_LAYOUT_DIR = ROOT / "helixville4"

MEGATREE_CONFIGS: list[str] = [
    "mega_360",
    "mega_180",
    "mega_90",
    "mega_pixel_strip",
    "mega_dense_matrix",
    "mega_sparse_outline",
]

NATIVE_XLIGHTS_MODEL_TYPES: list[str] = [
    "arch",
    "tree",
    "matrix",
    "line",
    "candy_cane",
    "circle",
    "sphere",
    "star",
    "spinner",
    "icicles",
    "window_frame",
    "dmx",
    "custom",
]

ROLE_BY_MODEL_TYPE: dict[str, str] = {
    "arch": "travel",
    "tree": "hero",
    "matrix": "detail_surface",
    "line": "structure",
    "candy_cane": "rhythm",
    "circle": "accent",
    "sphere": "mood",
    "star": "accent",
    "spinner": "motion",
    "icicles": "texture",
    "window_frame": "structure",
    "dmx": "legacy_control",
    "custom": "performer_or_special",
}

FAMILY_BY_MODEL_TYPE: dict[str, str] = {
    "arch": "travel_props",
    "tree": "trees",
    "matrix": "matrices",
    "line": "lines",
    "candy_cane": "canes",
    "circle": "circles",
    "sphere": "spheres",
    "star": "stars",
    "spinner": "spinners",
    "icicles": "icicles",
    "window_frame": "windows",
    "dmx": "legacy_control",
    "custom": "custom_props",
}

BAND_MODELS: dict[str, list[str]] = {
    "HX_SNOWMAN_SINGER": ["HX_SNOWMAN_SINGER_MOUTH_PHONEME"],
    "HX_SNOWMAN_SINGER_FEMALE": ["HX_SNOWMAN_SINGER_FEMALE_CALL_RESPONSE"],
    "HX_SNOWMAN_GUITARIST": ["HX_SNOWMAN_GUITARIST_STRUM_ZONE"],
    "HX_SNOWMAN_BASSIST": ["HX_SNOWMAN_BASSIST_PLUCK_ZONE"],
    "HX_SNOWMAN_DRUMMER": [
        "HX_SNOWMAN_DRUMMER_HAT",
        "HX_SNOWMAN_DRUMMER_HEAD",
        "HX_SNOWMAN_DRUMMER_FACE",
        "HX_SNOWMAN_DRUMMER_TORSO",
        "HX_SNOWMAN_DRUMMER_BUTTONS",
        "HX_SNOWMAN_DRUMMER_LEFT_ARM",
        "HX_SNOWMAN_DRUMMER_RIGHT_ARM",
        "HX_SNOWMAN_DRUMMER_LEFT_STICK",
        "HX_SNOWMAN_DRUMMER_RIGHT_STICK",
        "HX_SNOWMAN_DRUMMER_KICK",
        "HX_SNOWMAN_DRUMMER_SNARE",
        "HX_SNOWMAN_DRUMMER_SNARE_RIM",
        "HX_SNOWMAN_DRUMMER_TOM_LEFT",
        "HX_SNOWMAN_DRUMMER_TOM_RIGHT",
        "HX_SNOWMAN_DRUMMER_FLOOR_TOM",
        "HX_SNOWMAN_DRUMMER_HI_HAT",
        "HX_SNOWMAN_DRUMMER_CRASH_CYMBAL",
        "HX_SNOWMAN_DRUMMER_RIDE_CYMBAL",
    ],
}


def _manifest() -> dict[str, Any]:
    return json.loads((COMMITTED_LAYOUT_DIR / "helixia_manifest.json").read_text(encoding="utf-8"))


def _count_xml(layout_path: Path) -> dict[str, int]:
    root = ET.parse(layout_path).getroot()
    return {
        "model_count": len(root.findall(".//model")),
        "group_count": len(root.findall(".//modelGroup")),
    }


def _lot_meta(lot_id: str, model_types: list[str]) -> dict[str, Any]:
    return {
        "lot_id": lot_id,
        "model_types": list(model_types),
        "families": sorted({FAMILY_BY_MODEL_TYPE.get(t, "unknown") for t in model_types}),
        "roles": sorted({ROLE_BY_MODEL_TYPE.get(t, "support") for t in model_types}),
        "stage_zone": lot_id in {"snowman_band_stage", "dj_radio_booth"},
        "legacy_control_zone": lot_id in {"ac_all_white", "ac_rwg"},
    }


def _layout_intelligence(payload: dict[str, Any]) -> dict[str, Any]:
    houses = payload.get("village_grid", {}).get("houses", []) or []
    specials = payload.get("special_lots", []) or []
    trees = payload.get("fibonacci_tree_lot", {}).get("trees", []) or []
    coverage = payload.get("native_model_coverage", {}) or {}
    return {
        "schema": "helixia.layout_intelligence.v1",
        "role_by_model_type": dict(ROLE_BY_MODEL_TYPE),
        "family_by_model_type": dict(FAMILY_BY_MODEL_TYPE),
        "house_lots": [
            _lot_meta(str(h.get("lot_id", "")), list(h.get("model_types", []) or []))
            | {
                "style_id": h.get("style_id"),
                "style_name": h.get("style_name"),
                "grid_row": h.get("grid_row"),
                "grid_col": h.get("grid_col"),
                "world_position_ft": [
                    float(h.get("world_x_ft", 0.0)),
                    float(h.get("world_y_ft", 0.0)),
                    float(h.get("world_z_ft", 0.0)),
                ],
            }
            for h in houses
        ],
        "special_lots": [
            _lot_meta(str(l.get("lot_id", "")), list(l.get("model_types", []) or []))
            | {
                "display_name": l.get("display_name"),
                "world_position_ft": [float(l.get("world_x_ft", 0.0)), float(l.get("world_y_ft", 0.0)), 0.0],
                "contains": list(l.get("contains", []) or []),
            }
            for l in specials
        ],
        "fibonacci_tree_lot": {
            "role": "hero_spiral",
            "family": "trees",
            "tree_count": len(trees),
            "center_tree": "HX_FIB_FIB_TREE_CENTER",
        },
        "performer_models": {
            "snowman_band": [
                "HX_SNOWMAN_BASSIST_BODY",
                "HX_SNOWMAN_BASSIST_INSTRUMENT",
                "HX_SNOWMAN_GUITARIST_BODY",
                "HX_SNOWMAN_GUITARIST_INSTRUMENT",
                "HX_SNOWMAN_DRUMMER_BODY",
                "HX_SNOWMAN_DRUMMER_INSTRUMENT",
                "HX_SNOWMAN_SINGER_BODY",
                "HX_SNOWMAN_SINGER_INSTRUMENT",
                "HX_SNOWMAN_SINGER_FEMALE_BODY",
                "HX_SNOWMAN_SINGER_FEMALE_INSTRUMENT",
            ],
            "cactus_tubeman": ["HX_CACTUS_BODY", "HX_CACTUS_FACE", "HX_TUBEMAN_BODY", "HX_TUBEMAN_ARMS", "HX_DJ_BOOTH"],
        },
        "required_groups": [
            "HELIXIA_ALL",
            "HELIXIA_HOUSES",
            "HELIXIA_STAGE",
            "HELIXIA_SPECIAL_LOTS",
            "HX_FAMILY_MATRIX",
            "HX_FAMILY_CUSTOM",
            "HX_FAMILY_TREE",
            "HX_FAMILY_ARCH",
            "HX_LOT_SNOWMAN_BAND_STAGE",
            "HX_LOT_DJ_RADIO_BOOTH",
        ],
        "coverage_complete": all(bool(v) for v in coverage.values()),
        "two_dimensional_readability": {
            "houses_use_grid": True,
            "performers_use_stage_zone": True,
            "hero_trees_use_separate_lot": True,
        },
    }


def _write_notes(out_dir: Path, use_specs: bool) -> None:
    notes = "Helixia layout scaffold generated.\nGenerated xlights_rgbeffects.xml contains deterministic placeholder models for Helixia v1.\n"
    if use_specs:
        notes += "Helixville4 spec-driven snowman band models are enabled.\nBand background SVG assets were written to band_assets/.\n"
    (out_dir / "HELIXIA_LAYOUT_NOTES.txt").write_text(notes, encoding="utf-8")


def _add_band_specs(layout_path: Path) -> None:
    tree = ET.parse(layout_path)
    root = tree.getroot()
    models_el = root.find("models") or ET.SubElement(root, "models")
    groups_el = root.find("modelGroups") or ET.SubElement(root, "modelGroups")
    start = 900000
    for idx, (model_name, submodels) in enumerate(BAND_MODELS.items()):
        model = ET.SubElement(
            models_el,
            "model",
            {
                "name": model_name,
                "DisplayAs": "Custom",
                "WorldPosX": f"{250 + idx * 28:.3f}",
                "WorldPosY": f"{-52 - idx * 8:.3f}",
                "WorldPosZ": "12.000",
                "StartChannel": str(start + idx * 100),
                "StringType": "RGB Nodes",
                "parm1": "12",
                "parm2": "12",
                "CustomWidth": "12",
                "CustomHeight": "12",
            },
        )
        for submodel_name in submodels:
            ET.SubElement(model, "subModel", {"name": submodel_name, "line0": "1-4"})
    members = ",".join(BAND_MODELS)
    ET.SubElement(groups_el, "modelGroup", {"name": "HX_SNOWMAN_BAND", "models": members})
    ET.SubElement(groups_el, "modelGroup", {"name": "HX_SNOWMAN_VOCALS", "models": "HX_SNOWMAN_SINGER,HX_SNOWMAN_SINGER_FEMALE"})
    ET.SubElement(groups_el, "modelGroup", {"name": "HX_SNOWMAN_INSTRUMENTS", "models": "HX_SNOWMAN_GUITARIST,HX_SNOWMAN_BASSIST,HX_SNOWMAN_DRUMMER"})
    tree.write(layout_path, encoding="utf-8", xml_declaration=True)


def build_helixia_layout(
    output_dir: str | Path,
    *,
    village_rows: int = 3,
    village_cols: int = 4,
    use_helixville4_band_model_specs: bool = False,
) -> dict[str, Any]:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    layout_path = out_dir / "xlights_rgbeffects.xml"
    shutil.copyfile(COMMITTED_LAYOUT_DIR / "xlights_rgbeffects.xml", layout_path)

    payload = deepcopy(_manifest())
    payload["village_grid"]["rows"] = village_rows
    payload["village_grid"]["cols"] = village_cols
    payload["use_helixville4_band_model_specs"] = bool(use_helixville4_band_model_specs)
    payload["layout_intelligence"] = _layout_intelligence(payload)

    if use_helixville4_band_model_specs:
        _add_band_specs(layout_path)
        payload["band_assets"] = write_band_assets(out_dir / "band_assets")

    counts = _count_xml(layout_path)
    payload["xlights_layout"] = dict(payload.get("xlights_layout", {}))
    payload["xlights_layout"].update(counts)
    payload["xlights_layout"]["output_layout"] = str(layout_path)
    payload["xlights_layout"]["band_model_specs_enabled"] = bool(use_helixville4_band_model_specs)

    _write_notes(out_dir, bool(use_helixville4_band_model_specs))
    (out_dir / "helixia_manifest.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload
