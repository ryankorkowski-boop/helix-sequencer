"""Role ownership and section budgets for the live placement path.

Engines still propose effects. This module decides whether a proposal is
allowed to land, so piano overlays, vocal faces, and busy accent passes
cannot paint models they do not own or fill a quiet section.
"""

from __future__ import annotations


def model_role(name: str) -> str:
    """Advisory role from a model or group name. First specific match wins."""
    norm = " ".join(name.replace("_", " ").replace("-", " ").lower().split())
    if "piano" in norm or "keyboard" in norm:
        return "piano"
    if any(token in norm for token in ("drummer", "snare", "hi hat", "hihat", "cymbal")):
        return "percussion"
    if any(token in norm for token in ("singer", "singing face", "phoneme", "mouth", "talking head")):
        return "singer"
    if any(token in norm for token in ("guitarist", "guitar", "bassist", "cactus", "tubeman")):
        return "character"
    if any(token in norm for token in ("mega tree", "spiral tree", "double helix", "fib tree", "helix")):
        return "hero"
    if "arch" in norm:
        return "arch"
    if any(token in norm for token in ("matrix", "panel", "screen")):
        return "matrix"
    if any(token in norm for token in ("roofline", "roof line", "window", "eaves", "house")):
        return "house"
    return "fill"


def label_lane(label: str) -> str:
    """Which engine a placement label belongs to."""
    text = (label or "").lower()
    if any(token in text for token in ("polyphonic", "player_piano", "piano_lights")):
        return "piano_overlay"
    if any(token in text for token in ("lyric_mouth", "mouth_sync", "snowman_face", "lyric_text")):
        return "vocal"
    if text.startswith("pixel_") or any(
        token in text
        for token in ("birdsong", "multiband", "audio_reactive", "intensity_wave", "spatial_chase")
    ):
        return "overlay"
    if "drop_flash" in text or text.endswith("_flash"):
        return "flash"
    return "primary"


def layout_has_role(names: list[str], role: str) -> bool:
    return any(model_role(name) == role for name in names)


def allows_piano_overlay(model_name: str, *, layout_has_piano: bool) -> bool:
    """Keep note-echo overlays on piano models when the layout has a piano.

    Layouts with no piano keep the old yard-as-keyboard behavior.
    """
    if not layout_has_piano:
        return True
    return model_role(model_name) == "piano"


def allows_vocal(model_name: str, label: str, *, layout_has_singer: bool) -> bool:
    if label_lane(label) != "vocal" or not layout_has_singer:
        return True
    role = model_role(model_name)
    if "text" in (label or "").lower():
        return role in {"singer", "matrix"}
    return role == "singer"


def overlay_cap_per_second(part: str) -> int:
    """How many accent-engine hits a section may accept in one second."""
    name = (part or "").upper()
    if name == "CHORUS":
        return 14
    if name == "PRECHORUS":
        return 9
    if name == "OUTRO":
        return 11
    return 5


def flash_cap_per_window(part: str) -> int:
    name = (part or "").upper()
    if name in {"CHORUS", "OUTRO"}:
        return 2
    return 1


def family_for_role(role: str) -> str | None:
    """Pool family override. None means leave DisplayAs classification alone."""
    return {
        "piano": "notes",
        "singer": "talking_heads",
        "percussion": "band",
        "character": "band",
        "hero": "mega",
        "arch": "arch",
        "matrix": "matrix",
    }.get(role)

from core.cooperative_intelligence import (
    LANE_TO_ROLE,
    ROLE_PRIORITY_ORDER,
    infer_spatial_zone,
    select_soft_brightness,
    select_xlights_blend_mode,
)


def priority_for_lane(lane: str, *, is_climax: bool = False) -> int:
    """Cooperative priority score so high-value hits win budget slots."""
    role = LANE_TO_ROLE.get(lane, "motion")
    base_score = ROLE_PRIORITY_ORDER.get(role, 25)
    return base_score + (10 if is_climax else 0)


def cooperative_layer_blend(effect_name: str, label: str, layer_index: int) -> str:
    """Choose native xLights layer blend method for an engine proposal."""
    role = LANE_TO_ROLE.get(label_lane(label), "motion")
    return select_xlights_blend_mode(effect_name, role, layer_index)


def cooperative_brightness_scale(label: str, part: str, *, enabled: bool = True) -> int:
    """Soft brightness layering keeping the full yard vibrant and dimensional."""
    role = LANE_TO_ROLE.get(label_lane(label), "motion")
    return select_soft_brightness(role, part, enabled=enabled)


def spatial_zone_for_model(model_name: str) -> str:
    """Spatial call-and-response zone inferred from model name."""
    return infer_spatial_zone(model_name)
