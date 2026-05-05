from __future__ import annotations


def estimate_render_cost(pixel_count: int, layer_count: int, render_style: str) -> float:
    style_factor = 1.15 if render_style == "per_preview" else 1.0
    return round(min(1.0, (pixel_count / 1500.0) * max(1, layer_count) * style_factor), 4)
