from __future__ import annotations

from core import model_parser as xmp


def simulate_render_buffer(model: xmp.Model) -> dict[str, float | str]:
    width = max(1, int(model.strings or 1))
    height = max(1, int(model.nodes_per_string or model.total_pixels or 1))
    aspect_ratio = round(width / max(1, height), 4)
    density = round(min(1.0, model.total_pixels / 400.0), 4)
    readability = round(0.35 + min(0.55, density * 0.6), 4)
    return {
        "aspect_ratio": aspect_ratio,
        "render_surface_shape": "wide" if aspect_ratio > 1.25 else "tall" if aspect_ratio < 0.8 else "balanced",
        "pixel_density": density,
        "visible_direction": str(model.orientation or "front"),
        "stretching_risk": round(max(0.0, abs(aspect_ratio - 1.0) * 0.35), 4),
        "detail_loss": round(max(0.0, 0.7 - density), 4),
        "visual_readability": readability,
        "render_cost": round(min(1.0, model.total_pixels / 1200.0), 4),
    }
