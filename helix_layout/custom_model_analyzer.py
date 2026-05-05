from __future__ import annotations

from core import model_parser as xmp


def analyze_custom_model(model: xmp.Model) -> dict[str, object]:
    return {
        "name": model.name,
        "is_custom_like": "custom" in (model.display_as or "").lower() or "snowman" in model.name.lower(),
        "pixel_count": model.total_pixels,
        "has_submodels": bool(model.submodels),
        "geometry_points": len(model.geometry_points),
    }
