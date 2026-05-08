from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence

from models.helixville4_band_assets import HELIXVILLE4_BAND_ASSETS, BandModelAsset


MODEL_KIND_BY_SUBMODEL_SUFFIX: tuple[tuple[str, str], ...] = (
    ("MOUTH_PHONEME", "phoneme"),
    ("MICROPHONE", "vocal_prop"),
    ("MIC_STAND", "vocal_prop"),
    ("GUITAR", "instrument"),
    ("BASS", "instrument"),
    ("STRUM_ZONE", "instrument_articulation"),
    ("PLUCK_ZONE", "instrument_articulation"),
    ("FRET_HAND", "instrument_articulation"),
    ("KICK", "drum"),
    ("SNARE", "drum"),
    ("TOM", "drum"),
    ("HI_HAT", "drum"),
    ("CYMBALS", "drum"),
    ("STICKS", "drum"),
    ("LEFT_ARM", "body_motion"),
    ("RIGHT_ARM", "body_motion"),
    ("HAIR", "body_detail"),
    ("FACE", "face"),
    ("HEAD", "body"),
    ("TORSO", "body"),
    ("BUTTONS", "body_detail"),
    ("HAT", "body_detail"),
)


def classify_submodel(submodel: str) -> str:
    upper = submodel.upper()
    for suffix, kind in MODEL_KIND_BY_SUBMODEL_SUFFIX:
        if upper.endswith(suffix) or f"_{suffix}_" in upper:
            return kind
    return "outline"


def _segment_bounds(asset: BandModelAsset, submodel: str) -> dict[str, float]:
    points = [point for segment in asset.outline_segments if segment.submodel == submodel for point in segment.points]
    if not points:
        return {"min_x": 0.0, "min_y": 0.0, "max_x": 0.0, "max_y": 0.0}
    return {
        "min_x": round(min(point.x for point in points), 3),
        "min_y": round(min(point.y for point in points), 3),
        "max_x": round(max(point.x for point in points), 3),
        "max_y": round(max(point.y for point in points), 3),
    }


def build_model_spec_for_asset(asset: BandModelAsset) -> dict[str, Any]:
    submodels: list[dict[str, Any]] = []
    for index, submodel in enumerate(asset.submodel_order, start=1):
        segment_names = [segment.name for segment in asset.outline_segments if segment.submodel == submodel]
        submodels.append(
            {
                "name": submodel,
                "kind": classify_submodel(submodel),
                "segment_names": segment_names,
                "bounds_px": _segment_bounds(asset, submodel),
                "node_order": index,
            }
        )
    return {
        "model_name": asset.model_prefix,
        "member_id": asset.member_id,
        "display_name": asset.display_name,
        "display_as": "Custom",
        "background_svg": f"{asset.asset_id}.svg",
        "width_px": asset.width_px,
        "height_px": asset.height_px,
        "submodel_count": len(submodels),
        "submodels": submodels,
    }


def build_helixville4_band_model_specs() -> dict[str, Any]:
    models = [build_model_spec_for_asset(asset) for asset in HELIXVILLE4_BAND_ASSETS]
    return {
        "schema": "helixville4.band_model_specs.v1",
        "scope": "xlights_ready_model_and_submodel_specifications",
        "model_count": len(models),
        "models": models,
        "groups": {
            "HX_SNOWMAN_BAND": [model["model_name"] for model in models],
            "HX_SNOWMAN_VOCALS": [model["model_name"] for model in models if "singer" in str(model["member_id"])],
            "HX_SNOWMAN_INSTRUMENTS": [model["model_name"] for model in models if "singer" not in str(model["member_id"])],
        },
    }


def write_helixville4_band_model_specs(output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(build_helixville4_band_model_specs(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build xLights-ready Helixville4 band model/submodel specs from outline assets.")
    parser.add_argument("--output", type=Path, default=Path("test_runs/helixville4_band_model_specs.json"))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    path = write_helixville4_band_model_specs(args.output)
    print(json.dumps({"output": str(path)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
