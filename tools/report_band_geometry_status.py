from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from models.helixville4_performer_runtime import HELIXVILLE4_PERFORMERS


DEFAULT_MANIFEST = Path("fixtures/band_geometry/geometry_manifest.json")


def load_geometry_manifest(path: str | Path = DEFAULT_MANIFEST) -> dict[str, Any]:
    manifest_path = Path(path)
    if not manifest_path.exists():
        return {"models": {}}
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def build_band_geometry_status(manifest_path: str | Path = DEFAULT_MANIFEST) -> dict[str, Any]:
    manifest = load_geometry_manifest(manifest_path)
    models = manifest.get("models", {})

    performers: list[dict[str, Any]] = []
    for performer in HELIXVILLE4_PERFORMERS:
        entry = models.get(performer.model_name, {})
        declared_submodels = set(entry.get("submodels", []))
        expected_submodels = set(performer.submodels)
        missing_submodels = sorted(expected_submodels - declared_submodels)

        performers.append(
            {
                "performer_id": performer.performer_id,
                "model_name": performer.model_name,
                "geometry_proven": bool(entry.get("asset_path")) and not missing_submodels,
                "asset_path": entry.get("asset_path"),
                "expected_submodel_count": len(expected_submodels),
                "declared_submodel_count": len(declared_submodels),
                "missing_submodel_count": len(missing_submodels),
                "missing_submodels": missing_submodels,
            }
        )

    missing_models = [p["model_name"] for p in performers if not p["asset_path"]]
    incomplete_models = [p["model_name"] for p in performers if p["missing_submodel_count"]]

    return {
        "schema": "helix.band_geometry_status.v1",
        "manifest_path": str(manifest_path),
        "accepted_model_count": len(HELIXVILLE4_PERFORMERS),
        "geometry_complete": not missing_models and not incomplete_models,
        "missing_geometry_models": missing_models,
        "incomplete_submodel_models": incomplete_models,
        "performers": performers,
    }


if __name__ == "__main__":
    print(json.dumps(build_band_geometry_status(), indent=2))
