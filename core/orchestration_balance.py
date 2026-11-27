"""Role ownership and section budgets for the live placement path.

Engines still propose effects. These checks decide whether a proposal may
land, so piano overlays, vocal faces, and busy accent passes cannot paint
models they do not own or fill a quiet section.

The fuller PlacementSession from the governor branch is not imported here.
This tree has no MusicalContext, and a second show director is not added.
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
