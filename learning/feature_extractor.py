from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, field
from typing import Any, Mapping

from core import self_improving_scoring as scoring


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(round(float(value)))
    except Exception:
        return default


def _bucket(value: float, cuts: tuple[float, float], labels: tuple[str, str, str]) -> str:
    if value < cuts[0]:
        return labels[0]
    if value < cuts[1]:
        return labels[1]
    return labels[2]


def tempo_bucket(tempo_bpm: float) -> str:
    if tempo_bpm <= 0:
        return "unknown_tempo"
    if tempo_bpm < 86:
        return "slow_tempo"
    if tempo_bpm < 118:
        return "medium_tempo"
    if tempo_bpm < 150:
        return "fast_tempo"
    return "very_fast_tempo"


@dataclass(frozen=True)
class VisualFeatures:
    effect_types_used: dict[str, int] = field(default_factory=dict)
    layer_combinations: dict[str, int] = field(default_factory=dict)
    color_palette_transitions: dict[str, int] = field(default_factory=dict)
    spatial_motion_patterns: dict[str, int] = field(default_factory=dict)
    density_over_time: list[dict[str, Any]] = field(default_factory=list)
    repetition_frequency: float = 0.0
    contrast_levels: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MusicalContext:
    tempo: float = 0.0
    tempo_bucket: str = "unknown_tempo"
    energy_curve: list[dict[str, Any]] = field(default_factory=list)
    section_types: dict[str, int] = field(default_factory=dict)
    dominant_elements: dict[str, int] = field(default_factory=dict)
    emotion_profile: dict[str, float] = field(default_factory=dict)
    genre_hint: str = "unknown"
    style_hint: str = "unknown"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ExtractedSequenceFeatures:
    visual: VisualFeatures
    musical: MusicalContext
    score_summary: dict[str, float]
    source_policy: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "visual": self.visual.to_dict(),
            "musical": self.musical.to_dict(),
            "score_summary": dict(self.score_summary),
            "source_policy": dict(self.source_policy),
        }


def _placement_effect_counts(payload: Mapping[str, Any]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for key, count in ((payload.get("placements") or {}) or {}).items():
        name = str(key or "unknown").lower()
        if "strobe" in name or "flash" in name:
            family = "strobe_burst"
        elif "sweep" in name or "wave" in name or "chase" in name:
            family = "motion_sweep"
        elif "chorus" in name or "hook" in name:
            family = "hook_accent"
        elif "matrix" in name or "shader" in name:
            family = "matrix_texture"
        elif "face" in name or "vocal" in name:
            family = "focal_highlight"
        else:
            family = name[:48] or "unknown"
        counts[family] += _safe_int(count, 0)
    for effect in (((payload.get("effect_layering") or {}) or {}).get("layered_effects") or []):
        if isinstance(effect, Mapping):
            counts[str(effect.get("effect", "unknown")).lower()] += 1
    return counts


def _layer_combinations(payload: Mapping[str, Any]) -> Counter[str]:
    combos: Counter[str] = Counter()
    for effect in (((payload.get("effect_layering") or {}) or {}).get("layered_effects") or []):
        if not isinstance(effect, Mapping):
            continue
        role = str(effect.get("layer_role", effect.get("layer", "motion")) or "motion").lower()
        blend = str(effect.get("blend_mode", "normal") or "normal").lower()
        combos[f"{role}+{blend}"] += 1
    for log in (((payload.get("effect_layering") or {}) or {}).get("layering_logs") or []):
        if isinstance(log, Mapping) and log.get("action") in {"composited", "promoted_and_composited"}:
            combos["composited_overflow"] += 1
    runtime = (payload.get("runtime_tuning") or {}) or {}
    mode = str(runtime.get("layering_mode", "") or "").lower()
    if mode:
        combos[f"mode:{mode}"] += 1
    return combos


def _palette_transitions(payload: Mapping[str, Any]) -> Counter[str]:
    transitions: Counter[str] = Counter()
    runtime = (payload.get("runtime_tuning") or {}) or {}
    palette_mode = str(runtime.get("palette_mode", "template") or "template").lower()
    transitions[f"palette_mode:{palette_mode}"] += 1
    polish = (payload.get("polish") or {}) or {}
    swaps = _safe_int(polish.get("palette_swaps", 0), 0)
    if swaps:
        transitions["palette_swaps"] += swaps
    style = (payload.get("style_profile") or {}) or {}
    for palette in style.get("color_palettes", []) or []:
        if isinstance(palette, list):
            transitions[f"style_palette:{len(palette)}_colors"] += 1
    return transitions


def _spatial_patterns(payload: Mapping[str, Any]) -> Counter[str]:
    patterns: Counter[str] = Counter()
    spatial_payload = (payload.get("spatial_mapping") or payload.get("spatial_mapping_engine") or {}) or {}
    for item in spatial_payload.get("mapping_logs", []) or []:
        if not isinstance(item, Mapping):
            continue
        category = str(item.get("mapped_category", "unknown") or "unknown").lower()
        effect = str(item.get("effect", "unknown") or "unknown").lower()
        source = str(item.get("source", "unknown") or "unknown").lower()
        patterns[f"{source}:{category}:{effect}"] += 1
    coverage = (spatial_payload.get("coverage_visualization") or {}).get("coverage_by_type", {}) or {}
    for category, count in coverage.items():
        if _safe_int(count, 0) > 0:
            patterns[f"coverage:{str(category).lower()}"] += _safe_int(count, 0)
    matrix = (payload.get("matrix_intelligence") or {}) or {}
    for section in (((matrix.get("matrix_shader_config") or {}) or {}).get("per_section") or []):
        if isinstance(section, Mapping):
            shader = str(section.get("recommended_shader", "") or "").lower()
            if shader:
                patterns[f"shader:{shader}"] += 1
    return patterns


def _section_scores(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    audit_final = ((payload.get("audit") or {}).get("final") or {}) or {}
    sections = audit_final.get("section_scores") or []
    out: list[dict[str, Any]] = []
    for idx, section in enumerate(sections[:96]):
        if not isinstance(section, Mapping):
            continue
        energy = clamp01(_safe_float(section.get("energy", 0.0), 0.0))
        density = clamp01(_safe_float(section.get("density", 0.0), 0.0))
        out.append(
            {
                "index": idx,
                "section": str(section.get("label", "section") or "section").lower(),
                "energy_bucket": _bucket(energy, (0.34, 0.72), ("low", "medium", "high")),
                "density_bucket": _bucket(density, (0.34, 0.72), ("sparse", "balanced", "dense")),
                "coverage_bucket": _bucket(clamp01(_safe_float(section.get("coverage_ratio", 0.0))), (0.35, 0.72), ("narrow", "moderate", "wide")),
            }
        )
    return out


def _dominant_elements(payload: Mapping[str, Any]) -> Counter[str]:
    counts: Counter[str] = Counter()
    band = (payload.get("band_sync") or payload.get("snowman_band") or {}) or {}
    for item in (band.get("timeline") or band.get("state_frames") or [])[:128]:
        if isinstance(item, Mapping):
            focus = str(item.get("primary_focus", item.get("focus", "")) or "").lower()
            if focus:
                counts[focus] += 1
            for feature in item.get("dominant_features", []) or []:
                counts[str(feature).lower()] += 1
    advanced = (payload.get("advanced_audio") or {}) or {}
    for key in ("dominant_band", "dominant_element"):
        if advanced.get(key):
            counts[str(advanced[key]).lower()] += 1
    return counts


def _emotion_profile(payload: Mapping[str, Any]) -> dict[str, float]:
    emotion = (payload.get("emotion_state") or payload.get("vocal_emotion") or {}) or {}
    if isinstance(emotion.get("profile"), Mapping):
        return {str(key).lower(): clamp01(_safe_float(value)) for key, value in emotion["profile"].items()}
    if emotion.get("emotion_type"):
        return {str(emotion.get("emotion_type")).lower(): clamp01(_safe_float(emotion.get("intensity", 0.7), 0.7))}
    advanced = (payload.get("advanced_audio") or {}) or {}
    mood = str(advanced.get("mood_hint", "neutral") or "neutral").lower()
    return {mood: 0.6} if mood else {"neutral": 0.5}


def extract_features_from_payload(payload: Mapping[str, Any], *, require_helix_generated: bool = True) -> ExtractedSequenceFeatures:
    if require_helix_generated and not scoring.is_helix_generated_payload(dict(payload)):
        raise ValueError("learning feature extraction requires a Helix-generated payload watermark")

    score = scoring.score_sequence(dict(payload))
    advanced = (payload.get("advanced_audio") or {}) or {}
    tempo = _safe_float(advanced.get("tempo_bpm", advanced.get("tempo", 0.0)), 0.0)
    section_density = _section_scores(payload)
    section_counts: Counter[str] = Counter(section["section"] for section in section_density)
    energy_curve = [
        {"index": item["index"], "section": item["section"], "energy_bucket": item["energy_bucket"]}
        for item in section_density
    ]
    quality = (payload.get("quality") or {}) or {}
    audit_final = ((payload.get("audit") or {}).get("final") or {}) or {}

    visual = VisualFeatures(
        effect_types_used=dict(_placement_effect_counts(payload)),
        layer_combinations=dict(_layer_combinations(payload)),
        color_palette_transitions=dict(_palette_transitions(payload)),
        spatial_motion_patterns=dict(_spatial_patterns(payload)),
        density_over_time=section_density,
        repetition_frequency=clamp01(_safe_float(quality.get("dominant_family_ratio", 0.0), 0.0)),
        contrast_levels={
            "visual_coherence": round(score.metrics.get("visual_coherence", 0.0), 4),
            "energy_balance": round(score.metrics.get("energy_balance", 0.0), 4),
            "clutter": round(clamp01(_safe_float(audit_final.get("clutter_ratio", 0.0), 0.0)), 4),
        },
    )
    musical = MusicalContext(
        tempo=round(tempo, 4),
        tempo_bucket=tempo_bucket(tempo),
        energy_curve=energy_curve,
        section_types=dict(section_counts),
        dominant_elements=dict(_dominant_elements(payload)),
        emotion_profile=_emotion_profile(payload),
        genre_hint=str(advanced.get("genre_hint", "unknown") or "unknown").lower(),
        style_hint=str(((payload.get("style_profile") or {}) or {}).get("name", advanced.get("genre_hint", "unknown")) or "unknown").lower(),
    )
    return ExtractedSequenceFeatures(
        visual=visual,
        musical=musical,
        score_summary={"total_score": round(score.total_score, 4), **{key: round(value, 4) for key, value in score.metrics.items()}},
        source_policy={"helix_generated_only": True, "stores_full_sequences": False},
    )
