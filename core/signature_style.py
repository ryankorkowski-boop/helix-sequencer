from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence


KEY_PALETTES = {
    "C": ("#ffffff", "#ff4d8d", "#4cc9f0"),
    "C#": ("#e9ddff", "#6c4cff", "#00d4ff"),
    "D": ("#fff2b8", "#ff8a3d", "#2e9f82"),
    "D#": ("#ffd6e7", "#b5179e", "#55dde0"),
    "E": ("#fff8dc", "#00ff85", "#3a86ff"),
    "F": ("#f8f7f2", "#c7a76c", "#8da9c4"),
    "F#": ("#d7f7ff", "#2bd9ff", "#7f52ff"),
    "G": ("#ffd166", "#ef476f", "#06d6a0"),
    "G#": ("#f1e8ff", "#9b5de5", "#00f5d4"),
    "A": ("#ffcf4a", "#ff4f5e", "#1f5f8b"),
    "A#": ("#f7f3d6", "#0f6f78", "#6be7c8"),
    "B": ("#e0fbfc", "#5a6cff", "#ff9f1c"),
}

SECTION_TREATMENTS = {
    "intro": ("soft_reveal", 0.62, "cool"),
    "verse": ("identity_hold", 0.72, "balanced"),
    "pre-chorus": ("lift_tint", 0.82, "warm"),
    "buildup": ("lift_tint", 0.86, "warm"),
    "chorus": ("signature_bright", 1.0, "warm"),
    "post-chorus": ("afterglow", 0.92, "warm"),
    "drop": ("impact_flash_guarded", 1.0, "contrast"),
    "bridge": ("color_pivot", 0.7, "cool"),
    "breakdown": ("negative_space", 0.52, "cool"),
    "outro": ("memory_fade", 0.56, "cool"),
}


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        out = float(value)
    except Exception:
        return default
    if out != out:
        return default
    return out


def _get(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, Mapping):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _label(scene: Any) -> str:
    return str(_get(scene, "section_label", _get(scene, "label", "section")) or "section").lower().replace("_", "-")


def _scene_id(scene: Any, index: int) -> str:
    return str(_get(scene, "scene_id", f"scene_{index + 1:02d}") or f"scene_{index + 1:02d}")


def _start_ms(scene: Any) -> int:
    return max(0, int(_get(scene, "start_ms", 0) or 0))


def _end_ms(scene: Any) -> int:
    start = _start_ms(scene)
    return max(start + 1, int(_get(scene, "end_ms", start + 1) or (start + 1)))


def _energy(scene: Any) -> float:
    return _clamp01(_safe_float(_get(scene, "energy", 0.5), 0.5))


def _normalize_key(song_key: str | None) -> str:
    raw = str(song_key or "").strip().replace("major", "").replace("minor", "").strip()
    if not raw:
        return "C"
    root = raw.split()[0].replace("b", "#")
    aliases = {
        "Db": "C#",
        "Eb": "D#",
        "Gb": "F#",
        "Ab": "G#",
        "Bb": "A#",
    }
    return aliases.get(root, root if root in KEY_PALETTES else "C")


def key_for_midi(midi_value: int | float | None) -> str:
    try:
        value = int(round(float(midi_value)))
    except Exception:
        return "C"
    names = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
    return names[value % 12]


def _stable_unit(seed: str) -> float:
    digest = hashlib.sha256(seed.encode("utf-8", errors="ignore")).hexdigest()
    return int(digest[:8], 16) / 0xFFFFFFFF


def _shift_palette(base: Sequence[str], label: str, treatment: str) -> tuple[str, ...]:
    colors = list(base[:3]) or list(KEY_PALETTES["C"])
    if label in {"breakdown", "bridge", "outro", "intro"}:
        return tuple(colors[1:] + colors[:1])
    if treatment in {"signature_bright", "impact_flash_guarded"}:
        return tuple((colors[0], colors[2], "#ffffff"))
    if treatment == "afterglow":
        return tuple((colors[2], colors[0], colors[1]))
    return tuple(colors)


@dataclass(frozen=True)
class SectionPalette:
    scene_id: str
    section_label: str
    palette_name: str
    colors: tuple[str, ...]
    treatment: str
    brightness_scale: float
    temperature_bias: str

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["colors"] = list(self.colors)
        return data


@dataclass(frozen=True)
class HumanizationRule:
    scene_id: str
    timing_offset_ms: int
    brightness_modulation: float
    decay_curve: str
    seed: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ShowProfile:
    name: str
    brand_palette: tuple[str, ...]
    pacing_style: str
    motion_intensity_bias: float
    complexity_ceiling: int
    palette_mode: str

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["brand_palette"] = list(self.brand_palette)
        return data


@dataclass(frozen=True)
class SignatureStylePlan:
    song_key: str
    key_palette: tuple[str, ...]
    section_palettes: tuple[SectionPalette, ...]
    humanization: tuple[HumanizationRule, ...]
    show_profile: ShowProfile
    consistency_rules: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "helix.signature_style.v1",
            "song_key": self.song_key,
            "key_palette": list(self.key_palette),
            "section_palettes": [palette.to_dict() for palette in self.section_palettes],
            "humanization": [rule.to_dict() for rule in self.humanization],
            "show_profile": self.show_profile.to_dict(),
            "consistency_rules": list(self.consistency_rules),
        }


def _section_palette(scene: Any, index: int, key_palette: Sequence[str]) -> SectionPalette:
    label = _label(scene)
    treatment, brightness_scale, temperature = SECTION_TREATMENTS.get(label, ("identity_hold", 0.72, "balanced"))
    colors = _shift_palette(key_palette, label, treatment)
    energy = _energy(scene)
    return SectionPalette(
        scene_id=_scene_id(scene, index),
        section_label=label,
        palette_name=f"{label.replace('-', '_')}_{treatment}",
        colors=colors,
        treatment=treatment,
        brightness_scale=round(_clamp01(float(brightness_scale) * (0.78 + energy * 0.28)), 4),
        temperature_bias=temperature,
    )


def _humanization(scene: Any, index: int) -> HumanizationRule:
    scene_id = _scene_id(scene, index)
    start = _start_ms(scene)
    end = _end_ms(scene)
    label = _label(scene)
    energy = _energy(scene)
    seed = f"{scene_id}:{start}:{end}:{label}"
    timing = int(round((_stable_unit(seed + ':timing') - 0.5) * (18 + energy * 20)))
    brightness = 0.018 + _stable_unit(seed + ":brightness") * (0.035 + energy * 0.035)
    if label in {"drop", "chorus"}:
        decay = "fast_attack_controlled_release"
    elif label in {"intro", "outro", "breakdown"}:
        decay = "soft_breathing_decay"
    else:
        decay = "musical_ease_in_out"
    return HumanizationRule(
        scene_id=scene_id,
        timing_offset_ms=timing,
        brightness_modulation=round(_clamp01(brightness), 4),
        decay_curve=decay,
        seed=seed,
    )


def _pacing_style(scenes: Sequence[Any], genre_hint: str, mood_hint: str) -> str:
    energies = [_energy(scene) for scene in scenes]
    avg = sum(energies) / float(max(1, len(energies)))
    span = (max(energies) - min(energies)) if energies else 0.0
    genre = genre_hint.lower()
    mood = mood_hint.lower()
    if "edm" in genre or avg >= 0.72:
        return "bold_payoff_cycles"
    if span >= 0.42:
        return "cinematic_arc"
    if "ambient" in genre or mood in {"calm", "melancholic"}:
        return "restrained_breathing"
    return "hook_forward"


def _complexity_ceiling(scenes: Sequence[Any], runtime_tuning: Mapping[str, Any] | None) -> int:
    requested = int(round(_safe_float((runtime_tuning or {}).get("max_layers_per_prop", 3), 3.0)))
    energies = [_energy(scene) for scene in scenes]
    avg = sum(energies) / float(max(1, len(energies)))
    ceiling = requested
    if avg >= 0.78:
        ceiling += 1
    if any(_label(scene) in {"breakdown", "intro", "outro"} for scene in scenes):
        ceiling = min(ceiling, requested)
    return max(2, min(5, ceiling))


def _workspace_palette(workspace_history: Mapping[str, Any] | None) -> tuple[str, ...]:
    pool = list((workspace_history or {}).get("palette_pool", []) or [])
    for item in pool:
        if not item:
            continue
        colors = [part.strip() for part in str(item).replace(";", ",").split(",") if part.strip().startswith("#")]
        if len(colors) >= 2:
            return tuple(colors[:3])
    return ()


def _show_profile(
    scenes: Sequence[Any],
    *,
    key_palette: Sequence[str],
    runtime_tuning: Mapping[str, Any] | None,
    workspace_history: Mapping[str, Any] | None,
    genre_hint: str,
    mood_hint: str,
) -> ShowProfile:
    history_palette = _workspace_palette(workspace_history)
    palette = history_palette or tuple(key_palette[:3])
    if len(palette) < 3:
        palette = tuple(list(palette) + list(key_palette))[:3]
    energies = [_energy(scene) for scene in scenes]
    avg = sum(energies) / float(max(1, len(energies)))
    palette_mode = str((runtime_tuning or {}).get("palette_mode", "template") or "template")
    return ShowProfile(
        name="helix_signature_show_profile",
        brand_palette=tuple(palette[:3]),
        pacing_style=_pacing_style(scenes, genre_hint, mood_hint),
        motion_intensity_bias=round(_clamp01(0.42 + avg * 0.5), 4),
        complexity_ceiling=_complexity_ceiling(scenes, runtime_tuning),
        palette_mode=palette_mode,
    )


def build_signature_style_plan(
    scenes: Sequence[Any],
    *,
    song_key: str | None = None,
    runtime_tuning: Mapping[str, Any] | None = None,
    workspace_history: Mapping[str, Any] | None = None,
    genre_hint: str = "unknown",
    mood_hint: str = "neutral",
) -> SignatureStylePlan:
    normalized_key = _normalize_key(song_key)
    key_palette = KEY_PALETTES.get(normalized_key, KEY_PALETTES["C"])
    section_palettes = tuple(_section_palette(scene, idx, key_palette) for idx, scene in enumerate(scenes))
    humanization = tuple(_humanization(scene, idx) for idx, scene in enumerate(scenes))
    show_profile = _show_profile(
        scenes,
        key_palette=key_palette,
        runtime_tuning=runtime_tuning,
        workspace_history=workspace_history,
        genre_hint=genre_hint,
        mood_hint=mood_hint,
    )
    return SignatureStylePlan(
        song_key=normalized_key,
        key_palette=tuple(key_palette),
        section_palettes=section_palettes,
        humanization=humanization,
        show_profile=show_profile,
        consistency_rules=(
            "reuse brand_palette across all major callbacks",
            "shift section palettes by treatment instead of introducing unrelated colors",
            "apply deterministic timing and brightness humanization below the visual mud threshold",
            "keep complexity at or below the show profile ceiling except for scored payoff moments",
        ),
    )
