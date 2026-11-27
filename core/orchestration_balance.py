"""Role ownership and section budgets for the live placement path.

Engines still propose effects. These checks decide whether a proposal may
land, so piano overlays, vocal faces, and busy accent passes cannot paint
models they do not own or fill a quiet section.

The fuller PlacementSession from the governor branch is not imported here.
This tree has no MusicalContext, and a second show director is not added.

This module also exposes a small, dependency-free gate for callers that want
to restrain unsupported accent placements without changing their scheduler.
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


# The live engine still owns timing, priority, and xLights serialization.
# These lightweight gates do not introduce the incompatible MusicalContext
# dependency from the earlier unified-intelligence branch.
DEDICATED_PERFORMER_ROLES = frozenset({"piano", "singer", "percussion"})


def accent_target_allowed(model_name: str, label: str, *, layout_has_piano: bool, layout_has_singer: bool) -> bool:
    """Prevent generic effects from overwriting named performers.

    No-piano and no-singer layouts retain their historical yard fallbacks.
    Never infer a performer from a generic house, arch, or matrix name.
    """
    role = model_role(model_name)
    lane = label_lane(label)
    if lane == "piano_overlay":
        return allows_piano_overlay(model_name, layout_has_piano=layout_has_piano)
    if lane == "vocal":
        return allows_vocal(model_name, label, layout_has_singer=layout_has_singer)
    if lane in {"overlay", "flash"} and role in DEDICATED_PERFORMER_ROLES:
        return False
    return True


def restrained_accent_budget(section: str, *, quiet: bool = False, density: float = 1.0) -> tuple[int, int]:
    """Return overlay/flash caps for a section; quiet audio never flashes.

    These are maximum *accepted* accent counts, not a target number to fill.
    A higher density cannot override a quiet passage.
    """
    if quiet:
        return (1, 0)
    overlay = overlay_cap_per_second(section)
    if density <= 0.25:
        overlay = min(overlay, 3)
    return (overlay, flash_cap_per_window(section))

# A display-wide fan-out is not a musical cue. Preserve deliberate focal
# families even when a very large layout has thousands of available models.
_FAMILY_CAP_FLOOR = 5
_FAMILY_CAP_CEILING = 12
_FAMILY_CAP_STEP_MODELS = 60


def family_cap_for_layout(model_count: int, available_families: int = 0) -> int:
    """Bound simultaneously active *families* without capping individual pixels."""
    extra = max(0, (max(0, int(model_count)) - 40) // _FAMILY_CAP_STEP_MODELS)
    cap = min(_FAMILY_CAP_CEILING, _FAMILY_CAP_FLOOR + extra)
    if available_families > 0:
        cap = min(cap, int(available_families))
    return max(1, cap)


def vu_cap_for_section(model_count: int) -> int:
    """Green VU is a selective meter, never a full-show white/green wash."""
    return max(24, min(120, max(0, int(model_count)) // 6))


def section_instance_key(parts: list, start_ms: int) -> str:
    """Give each detected section its own family budget, even repeated verses."""
    t_ms = max(0, int(start_ms))
    for idx, part in enumerate(parts):
        if part.start_ms <= t_ms < part.end_ms:
            return f"{idx}:{part.label}"
    if parts:
        return f"{len(parts)-1}:{parts[-1].label}"
    return "0:VERSE"


def intersects_quiet_window(start_ms: int, end_ms: int, windows: list[tuple[int, int]]) -> bool:
    """Restrain accents that overlap silence, not only those starting inside."""
    start_ms = max(0, int(start_ms))
    end_ms = max(start_ms + 1, int(end_ms))
    return any(a < end_ms and b > start_ms for a, b in windows)


class ShowDirectionBudget:
    """Admit family accents with deterministic, section-local focus.

    The gate commits only after a real effect placement succeeds. Rejected
    placements cannot consume family or VU capacity.
    """

    def __init__(self, model_count: int, available_families: int = 0) -> None:
        self.model_count = max(0, int(model_count))
        self.family_cap = family_cap_for_layout(self.model_count, available_families)
        self.vu_cap = vu_cap_for_section(self.model_count)
        self._families: dict[str, list[str]] = {}
        self._vu: dict[str, int] = {}
        self.held = {"family": 0, "support": 0, "vu": 0}

    def _decision(self, *, section: str, family: str, label: str) -> str | None:
        section_key = section or "SONG"
        family_key = (family or "").strip().lower()
        label_key = (label or "").lower()
        if "green_vu" in label_key and self._vu.get(section_key, 0) >= self.vu_cap:
            return "vu"
        if not family_key:
            return None
        admitted = self._families.get(section_key, [])
        if family_key not in admitted and len(admitted) >= self.family_cap:
            return "family"
        if "_support" in label_key and self.model_count < 180 and admitted and family_key != admitted[0]:
            return "support"
        return None

    def can_allow(self, *, section: str, family: str, label: str) -> bool:
        """Read-only admission check, safe before conflict resolution."""
        return self._decision(section=section, family=family, label=label) is None

    def record(self, *, section: str, family: str, label: str) -> None:
        """Commit capacity only after a successful placement."""
        section_key = section or "SONG"
        family_key = (family or "").strip().lower()
        if "green_vu" in (label or "").lower():
            self._vu[section_key] = self._vu.get(section_key, 0) + 1
        if family_key:
            admitted = self._families.setdefault(section_key, [])
            if family_key not in admitted:
                admitted.append(family_key)

    def allow(self, *, section: str, family: str, label: str) -> bool:
        """Backward-compatible check-and-record for direct callers."""
        reason = self._decision(section=section, family=family, label=label)
        if reason is not None:
            self.held[reason] += 1
            return False
        self.record(section=section, family=family, label=label)
        return True

    def reject(self, *, section: str, family: str, label: str) -> None:
        """Account for a declined proposal without spending a slot."""
        reason = self._decision(section=section, family=family, label=label)
        if reason is not None:
            self.held[reason] += 1
