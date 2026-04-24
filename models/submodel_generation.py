from __future__ import annotations

from collections import defaultdict

from models.grid_canvas import DrawableModelTemplate


def detect_overlapping_regions(model: DrawableModelTemplate) -> list[str]:
    by_coord: dict[tuple[int, int], list[str]] = defaultdict(list)
    for name, region in model.all_regions().items():
        for coord in region.coordinates:
            by_coord[coord].append(name)
    issues: list[str] = []
    for coord, names in sorted(by_coord.items()):
        unique = sorted(set(names))
        if len(unique) <= 1:
            continue
        # Body/head overlap and alternate mouth-shape overlap are expected:
        # mouth shapes are exclusive face-definition targets, not simultaneously lit regions.
        non_context = [name for name in unique if name not in {"head", "mouth_area"} and not (name.startswith("mouth_") and name != "mouth_area")]
        mouth_names = [name for name in unique if name.startswith("mouth_") and name != "mouth_area"]
        if mouth_names and non_context:
            issues.append(f"{model.id}: coordinate {coord} shared by mouth and non-face regions {', '.join(unique)}")
    return issues


def validate_model(model: DrawableModelTemplate) -> list[str]:
    issues: list[str] = []
    required = {
        "head",
        "mouth_A",
        "mouth_E",
        "mouth_I",
        "mouth_O",
        "mouth_U",
        "mouth_MBP",
        "left_arm",
        "right_arm",
        "body_top",
        "body_bottom",
        "mouth_all",
        "band_body_core",
    }
    missing = sorted(required - set(model.submodels))
    if missing:
        issues.append(f"{model.id}: missing submodels {', '.join(missing)}")
    head = set(model.base_regions.get("head").coordinates if "head" in model.base_regions else [])
    for name, region in model.mouth_regions.items():
        if not region.coordinates:
            issues.append(f"{model.id}: empty mouth shape {name}")
        outside = [coord for coord in region.coordinates if coord not in head]
        if outside:
            issues.append(f"{model.id}: {name} has {len(outside)} pixels outside head bounds")
    for name, submodel in model.submodels.items():
        if not submodel.included_coordinates:
            issues.append(f"{model.id}: empty submodel {name}")
    issues.extend(detect_overlapping_regions(model))
    return issues


def xlights_mapping_hints(model: DrawableModelTemplate) -> dict[str, object]:
    return {
        "model_id": model.id,
        "custom_model_hint": {
            "node_order": "row_major_top_left_1_based",
            "width": model.canvas.width,
            "height": model.canvas.height,
            "xmodel_ready": False,
            "intermediate_json_ready": True,
        },
        "submodels": {
            name: {
                "intended_as_submodel": True,
                "node_ids": [model.canvas.node_id(coord) for coord in submodel.included_coordinates],
                "coordinate_count": len(submodel.included_coordinates),
                "category": submodel.category,
                "sequencing_tags": submodel.sequencing_tags,
                "audio_stem_tags": submodel.audio_stem_tags,
                "xlights_usage": (
                    "Faces effect mouth target"
                    if submodel.category == "mouth"
                    else "Reactive drum submodel"
                    if submodel.category == "drum"
                    else "Instrument/body submodel"
                ),
            }
            for name, submodel in model.submodels.items()
        },
        "face_definition_hint": {
            "style": "Matrix or Node Ranges",
            "mouth_targets": ["mouth_A", "mouth_E", "mouth_I", "mouth_O", "mouth_U", "mouth_MBP"],
            "preferred_next_step": "Generate xLights face definition from mouth submodel node ids.",
        },
    }
