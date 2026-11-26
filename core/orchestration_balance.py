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


# One extra family per 60 models past a 40-model yard, never above 12.
_FAMILY_CAP_FLOOR = 5
_FAMILY_CAP_CEILING = 12
_FAMILY_CAP_STEP_MODELS = 60

SECTION_FOCAL_FAMILY = {
    "INTRO": "mega",
    "VERSE": "arch",
    "PRECHORUS": "line",
    "CHORUS": "mega",
    "BRIDGE": "matrix",
    "BREAKDOWN": "sphere",
    "DROP": "mega",
    "OUTRO": "stars",
    "FINALE": "mega",
}

SECTION_MOTION = {
    "INTRO": "bottom_up",
    "VERSE": "left_to_right",
    "PRECHORUS": "center_outward",
    "CHORUS": "sweep",
    "BRIDGE": "call_and_response",
    "BREAKDOWN": "wave_handoff",
    "DROP": "center_outward",
    "OUTRO": "radial",
    "FINALE": "radial",
}


def normalize_show_family(family: str) -> str:
    text = " ".join((family or "").replace("_", " ").lower().split()).replace(" ", "_")
    return {
        "north_canes": "canes_combo",
        "south_canes": "canes_combo",
        "snowflakes": "stars",
    }.get(text, text)


def family_cap_for_layout(model_count: int, available_families: int = 0) -> int:
    """How many prop families a section may light at once.

    Small shows stay at 5. Large layouts earn more, up to 12, and never more
    families than the layout actually contains.
    """
    extra = max(0, (max(0, int(model_count)) - 40) // _FAMILY_CAP_STEP_MODELS)
    cap = min(_FAMILY_CAP_CEILING, _FAMILY_CAP_FLOOR + extra)
    if int(available_families) > 0:
        cap = min(cap, int(available_families))
    return max(1, cap)


def vu_cap_for_section(model_count: int) -> int:
    """Green-VU hits allowed in one section. Grows with the yard, stays a meter."""
    return max(24, min(120, max(0, int(model_count)) // 6))


class ShowDirectionBudget:
    """Admission gate for family fan-out, keyboard support lanes, and VU wash.

    Held placements are not recorded as validation rejections. The engine
    should not propose them in the first place; this only refuses the ones
    that still arrive.
    """

    def __init__(self, model_count: int, available_families: int = 0) -> None:
        self.model_count = max(0, int(model_count))
        self.family_cap = family_cap_for_layout(self.model_count, available_families)
        self.vu_cap = vu_cap_for_section(self.model_count)
        self._families: dict[str, list[str]] = {}
        self._vu: dict[str, int] = {}
        self.held = {"family": 0, "support": 0, "vu": 0}

    def focal_family(self, section: str) -> str:
        key = section or "SONG"
        admitted = self._families.get(key, [])
        planned = SECTION_FOCAL_FAMILY.get((section or "").upper(), "")
        if planned and planned in admitted:
            return planned
        if admitted:
            return admitted[0]
        return planned

    def motion_for(self, section: str) -> str:
        return SECTION_MOTION.get((section or "").upper(), "sweep")

    def allow(self, *, section: str, family: str, label: str) -> bool:
        section_key = section or "SONG"
        family_key = normalize_show_family(family)
        label_key = (label or "").lower()
        if "green_vu" in label_key:
            return self._allow_vu(section_key, family_key)
        if not family_key:
            return True
        admitted = self._families.setdefault(section_key, [])
        if family_key not in admitted:
            if len(admitted) >= self.family_cap:
                self.held["family"] += 1
                return False
            admitted.append(family_key)
        if "_support" in label_key and not self._support_allowed(section_key, family_key):
            self.held["support"] += 1
            return False
        return True

    def _allow_vu(self, section_key: str, family_key: str) -> bool:
        used = self._vu.get(section_key, 0)
        if used >= self.vu_cap:
            self.held["vu"] += 1
            return False
        focal = self.focal_family(section_key)
        meter_families = {focal, "mega", "line", "gt"} - {""}
        if family_key and focal and family_key not in meter_families:
            self.held["vu"] += 1
            return False
        self._vu[section_key] = used + 1
        if family_key:
            admitted = self._families.setdefault(section_key, [])
            if family_key not in admitted and len(admitted) < self.family_cap:
                admitted.append(family_key)
        return True

    def _support_allowed(self, section_key: str, family_key: str) -> bool:
        """Support lanes stay on the focal family.

        Yards of 180+ models may also keep support on one companion family.
        """
        planned = SECTION_FOCAL_FAMILY.get(section_key.upper(), "")
        focal = planned or self.focal_family(section_key)
        allowed = {focal} if focal else set()
        if self.model_count >= 180:
            for name in self._families.get(section_key, []):
                if name != focal:
                    allowed.add(name)
                    break
        if not allowed:
            return True
        return family_key in allowed

