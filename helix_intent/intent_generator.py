from __future__ import annotations

from helix_intent.visual_intent import VisualIntent


def generate_visual_intents(section_plans: list[dict[str, object]]) -> list[VisualIntent]:
    intents: list[VisualIntent] = []
    for idx, section in enumerate(section_plans):
        name = str(section.get("name", "verse"))
        if name in {"chorus", "final_chorus"}:
            intent_type = "bloom"
            trigger = "chorus_entry"
            spatial = "center_out"
            density = "full"
            emotion = "bright"
            target_roles = ["center", "upper", "hero_prop", "whole_house"]
        elif name in {"intro", "outro"}:
            intent_type = "color_wash"
            trigger = "section_change"
            spatial = "per_model"
            density = "sparse"
            emotion = "calm"
            target_roles = ["background", "matrix", "roofline"]
        elif name in {"bridge", "breakdown"}:
            intent_type = "transition"
            trigger = "section_change"
            spatial = "outside_in"
            density = "medium"
            emotion = "tense"
            target_roles = ["middle", "background", "arches"]
        else:
            intent_type = "trail"
            trigger = "vocal_phrase"
            spatial = "follow_melody_path"
            density = "medium"
            emotion = "dramatic"
            target_roles = ["center", "vocal_prop", "matrix"]
        intents.append(
            VisualIntent(
                id=f"intent_{idx + 1:03d}",
                start_time=float(section.get("start_time", 0.0)),
                end_time=float(section.get("end_time", 0.0)),
                intent_type=intent_type,
                musical_trigger=trigger,
                spatial_behavior=spatial,
                target_roles=target_roles,
                density_level=density,
                emotional_role=emotion,
                color_strategy=str(section.get("palette_hint", "adaptive_palette")),
                brightness_strategy=str(section.get("brightness_budget", "balanced")),
                curve_strategy="section_envelope",
                render_style_hint="per_preview" if spatial in {"center_out", "outside_in"} else "per_model",
                confidence=0.72,
            )
        )
    return intents
