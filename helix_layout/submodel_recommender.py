from __future__ import annotations

from core import model_parser as xmp


def recommend_submodels(model: xmp.Model) -> list[str]:
    kind = (model.type or model.display_as or "").lower()
    if "tree" in kind:
        return ["bottom_band", "middle_band", "top_band", "vertical_slice_left", "vertical_slice_right", "spiral_lane"]
    if "matrix" in kind:
        return ["lyric_zone", "face_zone", "background_zone", "border_zone", "particle_field"]
    if "arch" in kind:
        return ["left_half", "right_half", "center", "chase_lane", "waveform_lane"]
    if "spinner" in kind or "star" in kind:
        return ["center", "arms", "rings", "clockwise_order", "counterclockwise_order"]
    name = model.name.lower()
    if "snowman" in name:
        return ["mouth", "eyes", "body", "instrument_zone"]
    return ["center", "left_half", "right_half"]
