from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

from models.grid_canvas import DrawableModelTemplate
from models.mouth_templates import generate_mouth_library
from models.snowman_geometry import build_band_templates, model_summary
from models.submodel_generation import validate_model, xlights_mapping_hints


def model_export_payload(model: DrawableModelTemplate) -> dict[str, object]:
    payload = model.to_dict()
    payload["validation"] = {"issues": validate_model(model)}
    payload["xlights_mapping_hints"] = xlights_mapping_hints(model)
    payload["summary"] = model_summary(model)
    return payload


def mouth_library_payload(canvas_size: int = 64) -> dict[str, object]:
    library = generate_mouth_library(canvas_size)
    return {
        "schema": "helix.snowman_band.mouth_library.v1",
        "canvas_size": canvas_size,
        "mouth_shapes": {name: shape.to_dict() for name, shape in library.items()},
        "xlights_hint": "Use these shape coordinate sets to generate Faces effect mouth targets as node ranges or matrix regions.",
    }


def write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def export_band_pack(output_dir: Path, canvas_size: int = 64) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    models = build_band_templates(canvas_size)
    exported: dict[str, object] = {}
    for role, model in models.items():
        path = output_dir / f"{model.id}.json"
        payload = model_export_payload(model)
        write_json(path, payload)
        exported[role] = {"path": str(path), "summary": payload["summary"], "validation": payload["validation"]}
    mouth_path = output_dir / f"snowman_band_mouth_library_{canvas_size}.json"
    write_json(mouth_path, mouth_library_payload(canvas_size))
    combined = {
        "schema": "helix.snowman_band.model_pack.v1",
        "canvas_size": canvas_size,
        "models": {role: model_export_payload(model) for role, model in models.items()},
        "mouth_library": mouth_library_payload(canvas_size),
        "xlights_notes": {
            "custom_model": "Convert row-major coordinates/node ids to xModel custom model strings.",
            "submodels": "Export each SubmodelTemplate included_coordinates as xLights submodel node ranges.",
            "faces": "Node Ranges or Matrix style is the best next step; Single Node is too limited for expressive mouths.",
            "manual_work": "Final visual polish, exact xModel node wiring, and xLights face-definition UI checks may still be needed.",
        },
    }
    combined_path = output_dir / f"snowman_band_pack_{canvas_size}.json"
    write_json(combined_path, combined)
    return {"output_dir": str(output_dir), "combined_path": str(combined_path), "mouth_library_path": str(mouth_path), "models": exported}
