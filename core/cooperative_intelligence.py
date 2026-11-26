"""Cooperative Intelligence Blackboard & xLights Layer Mastering Engine.

Bridges Helix Sequencer's multi-pass intelligence director (emotional
storytelling, spatial choreography, cinematography, motif memory, and
masterpiece evaluation) directly into the live ``effect_engine.py``
placement path so every engine cooperates upstream and at render time.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence


SOFT_BRIGHTNESS_MATRIX: dict[str, dict[str, int]] = {
    "base": {"INTRO": 70, "VERSE": 74, "BRIDGE": 72, "PRECHORUS": 80, "BUILD": 82, "CHORUS": 88, "DROP": 90, "CLIMAX": 92, "FINALE": 92, "OUTRO": 76},
    "texture": {"INTRO": 72, "VERSE": 76, "BRIDGE": 75, "PRECHORUS": 82, "BUILD": 84, "CHORUS": 88, "DROP": 90, "CLIMAX": 92, "FINALE": 92, "OUTRO": 78},
    "motion": {"INTRO": 84, "VERSE": 88, "BRIDGE": 86, "PRECHORUS": 92, "BUILD": 94, "CHORUS": 96, "DROP": 98, "CLIMAX": 100, "FINALE": 100, "OUTRO": 88},
    "accent": {"INTRO": 94, "VERSE": 96, "BRIDGE": 95, "PRECHORUS": 98, "BUILD": 100, "CHORUS": 100, "DROP": 100, "CLIMAX": 100, "FINALE": 100, "OUTRO": 96},
    "focus": {"INTRO": 100, "VERSE": 100, "BRIDGE": 100, "PRECHORUS": 100, "BUILD": 100, "CHORUS": 100, "DROP": 100, "CLIMAX": 100, "FINALE": 100, "OUTRO": 100},
}

ADDITIVE_EFFECT_FAMILIES = frozenset({
    "twinkle", "sparkle", "snowflakes", "shimmer", "strobe", "fireworks",
    "lightning", "glitter", "shockwave", "ripple", "meteors",
})
UNMASK_EFFECT_FAMILIES = frozenset({
    "bars", "spirals", "pinwheel", "fan", "morph", "single strand",
    "singlestrand", "chase", "garlands", "marquees", "curtain", "wave",
})

ROLE_FADE_SECONDS: dict[str, tuple[float, float]] = {
    "base": (0.30, 0.40),
    "texture": (0.20, 0.30),
    "motion": (0.12, 0.20),
    "accent": (0.04, 0.16),
    "focus": (0.05, 0.15),
}

VIBRANT_ACCENT_ROTATION: tuple[str, ...] = (
    "#00F0FF", "#FF2BD6", "#FFD700", "#FF3B30", "#00E676", "#7C4DFF",
)

SECTION_SPATIAL_PATTERNS: dict[str, str] = {
    "INTRO": "center_out", "VERSE": "alternating_wings", "BRIDGE": "bottom_to_top",
    "PRECHORUS": "left_to_right", "BUILD": "outside_in", "CHORUS": "full_yard_burst",
    "DROP": "full_yard_burst", "CLIMAX": "full_yard_burst", "FINALE": "full_yard_burst",
    "OUTRO": "center_out",
}

ROLE_PRIORITY_ORDER: dict[str, int] = {"base": 10, "texture": 20, "motion": 35, "accent": 55, "focus": 75}
LANE_TO_ROLE: dict[str, str] = {"primary": "base", "overlay": "motion", "flash": "accent", "piano_overlay": "accent", "vocal": "focus"}


@dataclass(frozen=True)
class SectionDirective:
    name: str
    start_ms: int
    end_ms: int
    energy: float = 0.65
    spatial_pattern: str = "full_yard_burst"
    dominant_stem: str = "other"
    focal_role: str = "hero"
    preferred_blend_mode: str = "Layered"
    motif_family: str = ""
    escalation_level: int = 0
    overlay_cap_per_sec: int = 10
    flash_cap_per_window: int = 2
    max_pure_white_models: int = 12

    def contains(self, ms: int) -> bool:
        return self.start_ms <= ms < self.end_ms

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "SectionDirective":
        return cls(
            name=str(data.get("name", "VERSE")).upper(),
            start_ms=int(data.get("start_ms", 0)),
            end_ms=int(data.get("end_ms", 0)),
            energy=float(data.get("energy", 0.65)),
            spatial_pattern=str(data.get("spatial_pattern", "full_yard_burst")),
            dominant_stem=str(data.get("dominant_stem", "other")),
            focal_role=str(data.get("focal_role", "hero")),
            preferred_blend_mode=str(data.get("preferred_blend_mode", "Layered")),
            motif_family=str(data.get("motif_family", "")),
            escalation_level=int(data.get("escalation_level", 0)),
            overlay_cap_per_sec=int(data.get("overlay_cap_per_sec", 10)),
            flash_cap_per_window=int(data.get("flash_cap_per_window", 2)),
            max_pure_white_models=int(data.get("max_pure_white_models", 12)),
        )


@dataclass
class CooperativeShowBrief:
    song_duration_ms: int
    bpm: float = 120.0
    beat_grid_ms: list[int] = field(default_factory=list)
    sections: list[SectionDirective] = field(default_factory=list)
    model_zones: dict[str, str] = field(default_factory=dict)
    chorus_motif_family: str = ""
    masterpiece_score: float = 0.0
    preserve_vibrant_multcolor: bool = True
    soft_brightness_layering: bool = True
    anti_white_wash_enabled: bool = True
    max_layers_per_prop: int = 3
    metadata: dict[str, Any] = field(default_factory=dict)

    def section_for_ms(self, ms: int) -> SectionDirective:
        for sec in self.sections:
            if sec.contains(ms):
                return sec
        if self.sections:
            return self.sections[-1] if ms >= self.sections[-1].end_ms else self.sections[0]
        return SectionDirective(name="VERSE", start_ms=0, end_ms=max(1, self.song_duration_ms))

    def snap_to_beat_ms(self, ms: int, tolerance_ms: int = 65) -> int:
        if not self.beat_grid_ms:
            return ms
        lo, hi = 0, len(self.beat_grid_ms) - 1
        while lo < hi:
            mid = (lo + hi) // 2
            if self.beat_grid_ms[mid] < ms:
                lo = mid + 1
            else:
                hi = mid
        candidates = [self.beat_grid_ms[lo]]
        if lo > 0:
            candidates.append(self.beat_grid_ms[lo - 1])
        nearest = min(candidates, key=lambda b: abs(b - ms))
        return nearest if abs(nearest - ms) <= tolerance_ms else ms

    def to_dict(self) -> dict[str, Any]:
        return {
            "song_duration_ms": self.song_duration_ms,
            "bpm": self.bpm,
            "beat_grid_ms": list(self.beat_grid_ms),
            "sections": [s.to_dict() for s in self.sections],
            "model_zones": dict(self.model_zones),
            "chorus_motif_family": self.chorus_motif_family,
            "masterpiece_score": self.masterpiece_score,
            "preserve_vibrant_multcolor": self.preserve_vibrant_multcolor,
            "soft_brightness_layering": self.soft_brightness_layering,
            "anti_white_wash_enabled": self.anti_white_wash_enabled,
            "max_layers_per_prop": self.max_layers_per_prop,
            "metadata": dict(self.metadata),
        }

    def save_json(self, path: str | Path) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return target

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "CooperativeShowBrief":
        return cls(
            song_duration_ms=int(data.get("song_duration_ms", 30000)),
            bpm=float(data.get("bpm", 120.0)),
            beat_grid_ms=[int(x) for x in data.get("beat_grid_ms", [])],
            sections=[SectionDirective.from_dict(s) for s in data.get("sections", [])],
            model_zones={str(k): str(v) for k, v in data.get("model_zones", {}).items()},
            chorus_motif_family=str(data.get("chorus_motif_family", "")),
            masterpiece_score=float(data.get("masterpiece_score", 0.0)),
            preserve_vibrant_multcolor=bool(data.get("preserve_vibrant_multcolor", True)),
            soft_brightness_layering=bool(data.get("soft_brightness_layering", True)),
            anti_white_wash_enabled=bool(data.get("anti_white_wash_enabled", True)),
            max_layers_per_prop=int(data.get("max_layers_per_prop", 3)),
            metadata=dict(data.get("metadata", {})),
        )

    @classmethod
    def load_json(cls, path: str | Path) -> "CooperativeShowBrief":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


@dataclass(frozen=True)
class LayerPlacementDirective:
    target_layer_key: str
    layer_method: str
    brightness: int
    fade_in_sec: float
    fade_out_sec: float
    promoted_from_conflict: bool = False
    spatial_phase_offset_ms: int = 0
    anti_white_wash_applied: bool = False
    adjusted_palette: str | None = None
    adjusted_settings: str | None = None
    motif_reinforced: bool = False


@dataclass
class CooperativeQualityTelemetry:
    total_proposals: int = 0
    placed_primary: int = 0
    promoted_to_blend_layer: int = 0
    collisions_prevented: int = 0
    hard_drops: int = 0
    blend_modes_used: dict[str, int] = field(default_factory=dict)
    zones_activated: set[str] = field(default_factory=set)
    white_wash_interventions: int = 0
    motif_callbacks_applied: int = 0
    beat_snaps_applied: int = 0
    spatial_staggers_applied: int = 0

    def score_summary(self) -> dict[str, Any]:
        total_placed = self.placed_primary + self.promoted_to_blend_layer
        blend_ratio = self.promoted_to_blend_layer / max(1, total_placed)
        collision_save_rate = self.promoted_to_blend_layer / max(1, self.collisions_prevented + self.hard_drops)
        zone_diversity = min(1.0, len(self.zones_activated) / 5.0)
        cooperation_score = round(
            min(
                100.0,
                35.0 * min(1.0, total_placed / max(1, self.total_proposals))
                + 25.0 * min(1.0, blend_ratio * 2.5)
                + 20.0 * zone_diversity
                + 10.0 * min(1.0, collision_save_rate)
                + 10.0 * (1.0 if self.motif_callbacks_applied > 0 or self.spatial_staggers_applied > 0 else 0.5),
            ),
            2,
        )
        return {
            "total_proposals": self.total_proposals,
            "total_placed": total_placed,
            "promoted_to_blend_layer": self.promoted_to_blend_layer,
            "collisions_prevented": self.collisions_prevented,
            "hard_drops": self.hard_drops,
            "blend_modes_used": dict(self.blend_modes_used),
            "zones_activated": sorted(self.zones_activated),
            "white_wash_interventions": self.white_wash_interventions,
            "motif_callbacks_applied": self.motif_callbacks_applied,
            "beat_snaps_applied": self.beat_snaps_applied,
            "spatial_staggers_applied": self.spatial_staggers_applied,
            "cooperation_score": cooperation_score,
        }


def parse_xlights_settings(settings_str: str | None) -> dict[str, str]:
    if not settings_str:
        return {}
    parsed: dict[str, str] = {}
    for token in settings_str.split(","):
        if "=" in token:
            k, v = token.split("=", 1)
            k = k.strip()
            if k:
                parsed[k] = v.strip()
    return parsed


def format_xlights_settings(settings: Mapping[str, str]) -> str:
    return ",".join(f"{k}={v}" for k, v in settings.items())


def inject_xlights_layer_settings(
    settings_str: str | None,
    *,
    layer_method: str,
    brightness: int,
    fade_in_sec: float,
    fade_out_sec: float,
    override_existing: bool = False,
) -> str:
    parsed = parse_xlights_settings(settings_str)
    if override_existing or "T_CHOICE_LayerMethod" not in parsed:
        parsed["T_CHOICE_LayerMethod"] = layer_method
    if override_existing or "C_SLIDER_Brightness" not in parsed:
        parsed["C_SLIDER_Brightness"] = str(max(10, min(100, int(brightness))))
    if override_existing or "T_TEXTCTRL_Fadein" not in parsed:
        parsed["T_TEXTCTRL_Fadein"] = f"{max(0.0, fade_in_sec):.2f}"
    if override_existing or "T_TEXTCTRL_Fadeout" not in parsed:
        parsed["T_TEXTCTRL_Fadeout"] = f"{max(0.0, fade_out_sec):.2f}"
    return format_xlights_settings(parsed)


_PURE_WHITE_RE = re.compile(r"#(?:fff(?:fff)?|fefefe|fdfdfd|fcfcfc)\b", re.IGNORECASE)


def is_pure_white_palette(palette_str: str | None) -> bool:
    if not palette_str:
        return False
    hex_colors = re.findall(r"#[0-9a-fA-F]{6}\b", palette_str)
    if not hex_colors:
        return False
    white_count = sum(1 for c in hex_colors if _PURE_WHITE_RE.fullmatch(c))
    return white_count > 0 and (white_count / len(hex_colors)) >= 0.75


def diversify_white_palette(palette_str: str, rotation_index: int = 0) -> str:
    accent_a = VIBRANT_ACCENT_ROTATION[rotation_index % len(VIBRANT_ACCENT_ROTATION)]
    accent_b = VIBRANT_ACCENT_ROTATION[(rotation_index + 2) % len(VIBRANT_ACCENT_ROTATION)]
    parts = parse_xlights_settings(palette_str)
    if not parts:
        return (
            f"C_BUTTON_Palette1={accent_a},C_CHECKBOX_Palette1=1,"
            f"C_BUTTON_Palette2={accent_b},C_CHECKBOX_Palette2=1,"
            f"C_BUTTON_Palette3=#FFFFFF,C_CHECKBOX_Palette3=1"
        )
    parts["C_BUTTON_Palette1"] = accent_a
    parts["C_CHECKBOX_Palette1"] = "1"
    parts["C_BUTTON_Palette2"] = accent_b
    parts["C_CHECKBOX_Palette2"] = "1"
    if "C_BUTTON_Palette3" not in parts or _PURE_WHITE_RE.fullmatch(parts.get("C_BUTTON_Palette3", "")):
        parts["C_BUTTON_Palette3"] = "#FFFFFF"
        parts["C_CHECKBOX_Palette3"] = "1"
    return format_xlights_settings(parts)


def infer_spatial_zone(model_name: str, x_norm: float | None = None, y_norm: float | None = None) -> str:
    norm = " ".join(model_name.replace("_", " ").replace("-", " ").lower().split())
    if x_norm is not None:
        if x_norm < 0.33:
            return "left"
        if x_norm > 0.67:
            return "right"
        if y_norm is not None and y_norm > 0.65:
            return "upper_center"
        return "center"
    if any(tok in norm for tok in ("left", "west", " l ", " 1", " 2")):
        return "left"
    if any(tok in norm for tok in ("right", "east", " r ", " 4", " 5")):
        return "right"
    if any(tok in norm for tok in ("roof", "eave", "peak", "gutter", "sky", "star", "top")):
        return "upper_center"
    if any(tok in norm for tok in ("mega", "helix", "matrix", "singer", "band", "center", "mid")):
        return "center"
    return "perimeter"


def select_xlights_blend_mode(effect_name: str, role: str, layer_index: int) -> str:
    if layer_index <= 0 or role == "base":
        return "Normal"
    eff = (effect_name or "").strip().lower()
    if eff in ADDITIVE_EFFECT_FAMILIES:
        return "Additive"
    if eff in UNMASK_EFFECT_FAMILIES and role in {"motion", "texture"}:
        return "1 is Unmask"
    if role == "focus":
        return "Normal"
    if role == "accent":
        return "Additive" if eff in {"on", "strobe", "flash", "shockwave", "ripple"} else "Layered"
    return "Layered"


def select_soft_brightness(role: str, section_name: str, *, enabled: bool = True) -> int:
    if not enabled:
        return 100
    role_table = SOFT_BRIGHTNESS_MATRIX.get(role, SOFT_BRIGHTNESS_MATRIX["motion"])
    return role_table.get((section_name or "VERSE").upper(), 85)


def spatial_phase_offset_ms(zone: str, pattern: str, beat_ms: float) -> int:
    quarter = max(40, int(round(beat_ms * 0.25)))
    half = max(80, int(round(beat_ms * 0.50)))
    if pattern == "left_to_right":
        return {"left": 0, "center": quarter, "upper_center": quarter, "right": half, "perimeter": quarter}.get(zone, 0)
    if pattern == "center_out":
        return {"center": 0, "upper_center": 0, "left": quarter, "right": quarter, "perimeter": half}.get(zone, 0)
    if pattern == "outside_in":
        return {"left": 0, "right": 0, "perimeter": 0, "center": quarter, "upper_center": half}.get(zone, 0)
    if pattern == "alternating_wings":
        return {"left": 0, "center": 0, "right": half, "upper_center": quarter, "perimeter": quarter}.get(zone, 0)
    if pattern == "bottom_to_top":
        return {"perimeter": 0, "left": 0, "right": 0, "center": quarter, "upper_center": half}.get(zone, 0)
    return 0


class CooperativeShowDirector:
    def __init__(self, brief: CooperativeShowBrief) -> None:
        self.brief = brief
        self.telemetry = CooperativeQualityTelemetry()
        self._white_window_counts: dict[int, int] = {}
        self._chorus_motif_counts: dict[str, int] = {}
        self._rotation_counter: int = 0

    @classmethod
    def from_orchestration_and_audio(
        cls,
        *,
        song_duration_ms: int,
        bpm: float = 120.0,
        beat_grid_ms: Sequence[int] | None = None,
        audio_sections: Sequence[Mapping[str, Any]] | None = None,
        directed_intents: Sequence[Any] | None = None,
        layout_coords: Mapping[str, tuple[float, float]] | None = None,
        model_names: Sequence[str] | None = None,
        masterpiece_score: float = 0.0,
    ) -> "CooperativeShowDirector":
        duration_ms = max(1000, int(song_duration_ms))
        beats = list(beat_grid_ms or [])
        if not beats and bpm > 0:
            step = max(150, int(round(60000.0 / bpm)))
            beats = list(range(0, duration_ms, step))

        sections: list[SectionDirective] = []
        if audio_sections:
            for idx, sec in enumerate(audio_sections):
                name = str(sec.get("name") or sec.get("label") or "VERSE").upper()
                st = int(sec.get("start_ms", round(float(sec.get("start", 0.0)) * 1000)))
                en = int(sec.get("end_ms", round(float(sec.get("end", duration_ms / 1000.0)) * 1000)))
                energy = float(sec.get("energy", 0.85 if name in {"CHORUS", "DROP", "CLIMAX", "FINALE"} else 0.55))
                sections.append(
                    SectionDirective(
                        name=name,
                        start_ms=max(0, st),
                        end_ms=min(duration_ms, max(st + 250, en)),
                        energy=max(0.1, min(1.0, energy)),
                        spatial_pattern=SECTION_SPATIAL_PATTERNS.get(name, "alternating_wings"),
                        dominant_stem=str(sec.get("dominant_stem", "drums" if name in {"DROP", "CHORUS"} else "vocals")),
                        focal_role="hero" if name in {"CHORUS", "DROP", "CLIMAX", "FINALE"} else "singer",
                        preferred_blend_mode="Additive" if name in {"CHORUS", "DROP", "FINALE"} else "1 is Unmask",
                        escalation_level=idx,
                        overlay_cap_per_sec=16 if name in {"CHORUS", "DROP", "CLIMAX", "FINALE"} else (10 if name in {"PRECHORUS", "BUILD", "OUTRO"} else 6),
                        flash_cap_per_window=3 if name in {"CHORUS", "DROP", "CLIMAX", "FINALE"} else 1,
                        max_pure_white_models=16 if name in {"CHORUS", "DROP", "CLIMAX", "FINALE"} else 10,
                    )
                )
        elif directed_intents:
            for idx, intent in enumerate(directed_intents):
                name = str(getattr(intent, "section", "VERSE")).upper()
                st = int(round(float(getattr(intent, "start", 0.0)) * 1000))
                dur = int(round(float(getattr(intent, "duration", 5.0)) * 1000))
                energy = float(getattr(intent, "emotional_energy", getattr(intent, "intensity", 0.6)))
                sections.append(
                    SectionDirective(
                        name=name,
                        start_ms=max(0, st),
                        end_ms=min(duration_ms, max(st + 250, st + dur)),
                        energy=max(0.1, min(1.0, energy)),
                        spatial_pattern=SECTION_SPATIAL_PATTERNS.get(name, "alternating_wings"),
                        escalation_level=int(getattr(intent, "escalation_phase", idx)),
                        overlay_cap_per_sec=16 if name in {"CHORUS", "DROP", "CLIMAX", "FINALE"} else 8,
                        flash_cap_per_window=3 if name in {"CHORUS", "DROP", "CLIMAX", "FINALE"} else 1,
                    )
                )
        else:
            slice_ms = max(1000, duration_ms // 5)
            for idx, name in enumerate(("INTRO", "VERSE", "PRECHORUS", "CHORUS", "FINALE")):
                st = idx * slice_ms
                en = duration_ms if idx == 4 else (idx + 1) * slice_ms
                sections.append(
                    SectionDirective(
                        name=name, start_ms=st, end_ms=en,
                        energy=min(1.0, 0.35 + idx * 0.16),
                        spatial_pattern=SECTION_SPATIAL_PATTERNS[name],
                        escalation_level=idx,
                    )
                )

        model_zones: dict[str, str] = {}
        if layout_coords:
            xs = [pt[0] for pt in layout_coords.values()]
            ys = [pt[1] for pt in layout_coords.values()]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            span_x = max(1e-6, max_x - min_x)
            span_y = max(1e-6, max_y - min_y)
            for m_name, (mx, my) in layout_coords.items():
                model_zones[m_name] = infer_spatial_zone(
                    m_name, x_norm=(mx - min_x) / span_x, y_norm=(my - min_y) / span_y,
                )
        for m_name in model_names or ():
            if m_name not in model_zones:
                model_zones[m_name] = infer_spatial_zone(m_name)

        brief = CooperativeShowBrief(
            song_duration_ms=duration_ms, bpm=bpm, beat_grid_ms=beats,
            sections=sections, model_zones=model_zones,
            masterpiece_score=float(masterpiece_score),
            preserve_vibrant_multcolor=True, soft_brightness_layering=True,
            anti_white_wash_enabled=True, max_layers_per_prop=3,
        )
        return cls(brief)

    def plan_cooperative_placement(
        self,
        *,
        model_name: str,
        start_ms: int,
        end_ms: int,
        effect_name: str,
        label: str,
        requested_layer_key: str,
        available_layer_keys: Sequence[str],
        layer_has_conflict: bool,
        settings_str: str | None = None,
        palette_str: str | None = None,
        lane: str = "primary",
    ) -> LayerPlacementDirective:
        self.telemetry.total_proposals += 1
        section = self.brief.section_for_ms(start_ms)
        role = LANE_TO_ROLE.get(lane, "motion")
        zone = self.brief.model_zones.get(model_name) or infer_spatial_zone(model_name)
        self.telemetry.zones_activated.add(zone)

        chosen_layer = requested_layer_key
        promoted = False
        ordered_layers = list(available_layer_keys) or [requested_layer_key]
        layer_idx = ordered_layers.index(requested_layer_key) if requested_layer_key in ordered_layers else 0

        if layer_has_conflict and len(ordered_layers) > 1:
            self.telemetry.collisions_prevented += 1
            for cand_idx, cand_key in enumerate(ordered_layers):
                if cand_key != requested_layer_key and cand_idx > layer_idx:
                    chosen_layer = cand_key
                    layer_idx = cand_idx
                    promoted = True
                    break
            if not promoted:
                for cand_idx, cand_key in enumerate(ordered_layers):
                    if cand_key != requested_layer_key:
                        chosen_layer = cand_key
                        layer_idx = cand_idx
                        promoted = True
                        break

        if promoted:
            self.telemetry.promoted_to_blend_layer += 1
        else:
            self.telemetry.placed_primary += 1

        blend_mode = select_xlights_blend_mode(effect_name, role, layer_idx)
        self.telemetry.blend_modes_used[blend_mode] = self.telemetry.blend_modes_used.get(blend_mode, 0) + 1
        brightness = select_soft_brightness(role, section.name, enabled=self.brief.soft_brightness_layering)
        fade_in, fade_out = ROLE_FADE_SECONDS.get(role, (0.10, 0.18))

        beat_ms = 60000.0 / max(40.0, self.brief.bpm)
        stagger_ms = 0
        if role in {"motion", "texture"} and (end_ms - start_ms) >= 400:
            stagger_ms = spatial_phase_offset_ms(zone, section.spatial_pattern, beat_ms)
            if stagger_ms > 0:
                self.telemetry.spatial_staggers_applied += 1

        motif_reinforced = False
        if section.name in {"CHORUS", "CLIMAX", "FINALE"} and role in {"motion", "focus"}:
            eff_key = (effect_name or "").strip()
            if eff_key:
                self._chorus_motif_counts[eff_key] = self._chorus_motif_counts.get(eff_key, 0) + 1
                if not self.brief.chorus_motif_family:
                    self.brief.chorus_motif_family = eff_key
                elif self.brief.chorus_motif_family.lower() == eff_key.lower():
                    motif_reinforced = True
                    self.telemetry.motif_callbacks_applied += 1

        adjusted_palette = palette_str
        white_wash_applied = False
        if self.brief.anti_white_wash_enabled and is_pure_white_palette(palette_str):
            win_bucket = int(start_ms) // 500
            current_white = self._white_window_counts.get(win_bucket, 0)
            if current_white >= section.max_pure_white_models:
                adjusted_palette = diversify_white_palette(palette_str or "", self._rotation_counter)
                self._rotation_counter += 1
                white_wash_applied = True
                self.telemetry.white_wash_interventions += 1
            else:
                self._white_window_counts[win_bucket] = current_white + 1

        adjusted_settings = inject_xlights_layer_settings(
            settings_str, layer_method=blend_mode, brightness=brightness,
            fade_in_sec=fade_in, fade_out_sec=fade_out,
        )

        return LayerPlacementDirective(
            target_layer_key=chosen_layer, layer_method=blend_mode, brightness=brightness,
            fade_in_sec=fade_in, fade_out_sec=fade_out, promoted_from_conflict=promoted,
            spatial_phase_offset_ms=stagger_ms, anti_white_wash_applied=white_wash_applied,
            adjusted_palette=adjusted_palette, adjusted_settings=adjusted_settings,
            motif_reinforced=motif_reinforced,
              )
