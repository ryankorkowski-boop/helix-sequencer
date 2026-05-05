from __future__ import annotations

from helix_intent.visual_intent import RenderStylePlan, VisualIntent


def decide_render_style(intent: VisualIntent, render_buffer: dict[str, float | str], *, is_ac: bool = False) -> RenderStylePlan:
    if is_ac:
        style = "single_line"
    elif intent.spatial_behavior in {"center_out", "outside_in", "front_to_back", "back_to_front"}:
        style = "per_preview"
    elif intent.spatial_behavior in {"left_to_right", "right_to_left", "bottom_up", "top_down"}:
        style = "per_model_per_preview"
    else:
        style = "per_model"
    readability = float(render_buffer.get("visual_readability", 0.5))
    direction = 0.86 if style in {"per_preview", "per_model_per_preview"} else 0.62
    density = 0.82 if intent.density_level in {"medium", "full"} else 0.64
    cost = 1.0 - float(render_buffer.get("render_cost", 0.5))
    fit = 0.82 if not is_ac else 0.74
    return RenderStylePlan(
        visual_intent_id=intent.id,
        render_style=style,
        readability_score=round(readability, 4),
        direction_preservation_score=round(direction, 4),
        density_match_score=round(density, 4),
        render_cost_score=round(cost, 4),
        layout_fit_score=round(fit, 4),
        rationale=f"Selected {style} for {intent.spatial_behavior} on {'AC' if is_ac else 'pixel'} target.",
    )
