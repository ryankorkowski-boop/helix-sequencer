from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from typing import Any, Mapping

from core.sequence_context import SequenceContext, clamp01


STYLE_NAMES = ("edm", "rock", "pop", "orchestral", "ambient", "experimental")


@dataclass(frozen=True)
class StyleProfile:
    name: str
    color_palettes: tuple[tuple[str, ...], ...]
    effect_density: float
    motion_style: str
    layer_usage: dict[str, float]
    intensity_curve: str
    transition_speed: float
    spatial_bias: dict[str, float] = field(default_factory=dict)
    performer_bias: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["color_palettes"] = [list(palette) for palette in self.color_palettes]
        return payload


@dataclass(frozen=True)
class StyleDecision:
    profile: StyleProfile
    detected_style: str
    confidence: float
    manual_override: str | None
    blends: dict[str, float]
    debug: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile": self.profile.to_dict(),
            "detected_style": self.detected_style,
            "confidence": round(self.confidence, 4),
            "manual_override": self.manual_override,
            "blends": {key: round(value, 4) for key, value in self.blends.items()},
            "debug": self.debug,
        }


STYLE_PROFILES: dict[str, StyleProfile] = {
    "edm": StyleProfile(
        name="edm",
        color_palettes=(("#00E5FF", "#7C4DFF", "#FF2BD6"), ("#00FF85", "#F9FF00", "#111111")),
        effect_density=0.88,
        motion_style="quantized_pulses",
        layer_usage={"base": 0.75, "motion": 0.95, "accent": 1.0, "texture": 0.55, "max_layers": 4.0},
        intensity_curve="sidechain_snap",
        transition_speed=0.9,
        spatial_bias={"depth_timing": 0.78, "symmetry": 0.62, "strobe_gate": 0.88},
        performer_bias={"drummer": 0.9, "environment": 0.75, "singer": 0.55},
    ),
    "rock": StyleProfile(
        name="rock",
        color_palettes=(("#FF3B30", "#FFD166", "#F8F9FA"), ("#D90429", "#2B2D42", "#EDF2F4")),
        effect_density=0.72,
        motion_style="hit_driven_sweeps",
        layer_usage={"base": 0.82, "motion": 0.75, "accent": 0.9, "texture": 0.35, "max_layers": 3.0},
        intensity_curve="attack_sustain",
        transition_speed=0.68,
        spatial_bias={"depth_timing": 0.45, "symmetry": 0.5, "strobe_gate": 0.55},
        performer_bias={"guitarist": 0.85, "drummer": 0.82, "singer": 0.65},
    ),
    "pop": StyleProfile(
        name="pop",
        color_palettes=(("#FF4D8D", "#FFD166", "#4CC9F0"), ("#FFFFFF", "#F72585", "#7209B7")),
        effect_density=0.66,
        motion_style="clean_hook_motion",
        layer_usage={"base": 0.76, "motion": 0.72, "accent": 0.72, "texture": 0.48, "max_layers": 3.0},
        intensity_curve="chorus_lift",
        transition_speed=0.72,
        spatial_bias={"depth_timing": 0.42, "symmetry": 0.78, "strobe_gate": 0.36},
        performer_bias={"singer": 0.9, "environment": 0.62, "drummer": 0.52},
    ),
    "orchestral": StyleProfile(
        name="orchestral",
        color_palettes=(("#F8F7F2", "#C7A76C", "#8DA9C4"), ("#5B6C8D", "#E8DAB2", "#FFFFFF")),
        effect_density=0.5,
        motion_style="cinematic_phrases",
        layer_usage={"base": 0.9, "motion": 0.58, "accent": 0.42, "texture": 0.7, "max_layers": 3.0},
        intensity_curve="long_arc",
        transition_speed=0.42,
        spatial_bias={"depth_timing": 0.72, "symmetry": 0.58, "strobe_gate": 0.08},
        performer_bias={"environment": 0.9, "singer": 0.5, "drummer": 0.16},
    ),
    "ambient": StyleProfile(
        name="ambient",
        color_palettes=(("#8EC5FC", "#B8F7D4", "#FFFFFF"), ("#2EC4B6", "#A3CEF1", "#E0FBFC")),
        effect_density=0.3,
        motion_style="slow_breathing",
        layer_usage={"base": 0.86, "motion": 0.34, "accent": 0.18, "texture": 0.86, "max_layers": 2.0},
        intensity_curve="soft_bloom",
        transition_speed=0.2,
        spatial_bias={"depth_timing": 0.62, "symmetry": 0.48, "strobe_gate": 0.02},
        performer_bias={"environment": 0.95, "singer": 0.45, "drummer": 0.08},
    ),
    "experimental": StyleProfile(
        name="experimental",
        color_palettes=(("#F15BB5", "#00BBF9", "#FEE440"), ("#9B5DE5", "#00F5D4", "#111111")),
        effect_density=0.74,
        motion_style="asymmetric_fragments",
        layer_usage={"base": 0.58, "motion": 0.8, "accent": 0.76, "texture": 0.8, "max_layers": 4.0},
        intensity_curve="broken_step",
        transition_speed=0.82,
        spatial_bias={"depth_timing": 0.9, "symmetry": 0.2, "strobe_gate": 0.42},
        performer_bias={"environment": 0.82, "drummer": 0.58, "guitarist": 0.55},
    ),
}


def normalize_style_name(value: str | None) -> str:
    key = (value or "").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "dance": "edm",
        "electronic": "edm",
        "electronica": "edm",
        "cinematic": "orchestral",
        "score": "orchestral",
        "classical": "orchestral",
        "atmospheric": "ambient",
        "alt": "experimental",
    }
    return aliases.get(key, key)


def get_style_profile(name: str | None) -> StyleProfile:
    key = normalize_style_name(name)
    if key not in STYLE_PROFILES:
        return STYLE_PROFILES["pop"]
    return STYLE_PROFILES[key]


def _tokens(value: Any) -> set[str]:
    if isinstance(value, Mapping):
        return {str(key).lower() for key, enabled in value.items() if enabled}
    if isinstance(value, str):
        return {part.strip().lower() for part in value.replace(",", " ").split() if part.strip()}
    try:
        return {str(item).lower() for item in value or []}
    except Exception:
        return set()


def _feature_float(features: Mapping[str, Any], key: str, default: float = 0.0) -> float:
    try:
        return float(features.get(key, default))
    except Exception:
        return default


def infer_style(audio_features: Mapping[str, Any]) -> StyleDecision:
    features = dict(audio_features or {})
    tempo = _feature_float(features, "tempo_bpm", _feature_float(features, "tempo", 0.0))
    instrumentation = _tokens(features.get("instrumentation", features.get("instruments", ())))
    rhythm = _tokens(features.get("rhythm_patterns", features.get("rhythm", ())))
    scores = {name: 0.12 for name in STYLE_NAMES}

    if tempo >= 118:
        scores["edm"] += 0.18
        scores["pop"] += 0.08
    if 90 <= tempo <= 170:
        scores["rock"] += 0.08
    if 82 <= tempo <= 138:
        scores["pop"] += 0.12
    if tempo and tempo < 86:
        scores["ambient"] += 0.18
        scores["orchestral"] += 0.08

    if instrumentation & {"synth", "synthesizer", "electronic", "drum_machine", "sampler"}:
        scores["edm"] += 0.34
    if rhythm & {"four_on_floor", "sidechain", "drop", "club"}:
        scores["edm"] += 0.32
    if instrumentation & {"guitar", "electric_guitar", "bass_guitar"}:
        scores["rock"] += 0.28
    if rhythm & {"backbeat", "driving", "shuffle"}:
        scores["rock"] += 0.2
    if instrumentation & {"vocal", "vocals", "lead_vocal"}:
        scores["pop"] += 0.18
    if rhythm & {"hook", "steady", "syncopated_pop"}:
        scores["pop"] += 0.16
    if instrumentation & {"strings", "orchestra", "brass", "woodwinds", "choir"}:
        scores["orchestral"] += 0.36
    if rhythm & {"rubato", "crescendo", "waltz"}:
        scores["orchestral"] += 0.18
    if instrumentation & {"pad", "pads", "field_recording", "drone"}:
        scores["ambient"] += 0.34
    if rhythm & {"sparse", "free_time", "slow_pulse"}:
        scores["ambient"] += 0.22
    if instrumentation & {"noise", "glitch", "modular", "found_sound"}:
        scores["experimental"] += 0.34
    if rhythm & {"odd_meter", "polyrhythm", "glitch", "irregular"}:
        scores["experimental"] += 0.3

    scores["ambient"] += max(0.0, 0.16 - _feature_float(features, "onset_density", 0.1))
    scores["experimental"] += _feature_float(features, "syncopation", 0.0) * 0.18
    scores["edm"] += _feature_float(features, "percussive_ratio", 0.0) * 0.12

    ranked = sorted(scores.items(), key=lambda item: (item[1], item[0]), reverse=True)
    detected, top_score = ranked[0]
    runner_up = ranked[1][1] if len(ranked) > 1 else 0.0
    confidence = clamp01(0.52 + min(0.38, top_score - runner_up))
    profile = STYLE_PROFILES[detected]
    return StyleDecision(
        profile=profile,
        detected_style=detected,
        confidence=confidence,
        manual_override=None,
        blends={detected: 1.0},
        debug={
            "tempo_bpm": tempo,
            "instrumentation": sorted(instrumentation),
            "rhythm_patterns": sorted(rhythm),
            "scores": {key: round(value, 4) for key, value in scores.items()},
        },
    )


def blend_style_profiles(blends: Mapping[str, float]) -> StyleProfile:
    weighted = {
        normalize_style_name(name): max(0.0, float(weight))
        for name, weight in (blends or {}).items()
        if normalize_style_name(name) in STYLE_PROFILES and float(weight) > 0.0
    }
    if not weighted:
        return STYLE_PROFILES["pop"]
    total = sum(weighted.values()) or 1.0
    normalized = {key: value / total for key, value in weighted.items()}
    primary = max(normalized.items(), key=lambda item: item[1])[0]

    def mix_number(attr: str) -> float:
        return sum(getattr(STYLE_PROFILES[key], attr) * weight for key, weight in normalized.items())

    def mix_dict(attr: str) -> dict[str, float]:
        keys = set().union(*(getattr(STYLE_PROFILES[key], attr).keys() for key in normalized))
        return {
            key: sum(STYLE_PROFILES[name].__dict__[attr].get(key, 0.0) * weight for name, weight in normalized.items())
            for key in keys
        }

    palettes: list[tuple[str, ...]] = []
    for key in normalized:
        palettes.extend(STYLE_PROFILES[key].color_palettes[:1])
    return replace(
        STYLE_PROFILES[primary],
        name="+".join(normalized.keys()),
        color_palettes=tuple(palettes[:3]),
        effect_density=clamp01(mix_number("effect_density")),
        layer_usage=mix_dict("layer_usage"),
        transition_speed=clamp01(mix_number("transition_speed")),
        spatial_bias=mix_dict("spatial_bias"),
        performer_bias=mix_dict("performer_bias"),
    )


def resolve_style(
    context: SequenceContext,
    *,
    manual_style: str | None = None,
    blends: Mapping[str, float] | None = None,
) -> StyleDecision:
    detected = infer_style(context.audio_features)
    applied_blends: dict[str, float]
    override = normalize_style_name(manual_style) if manual_style else None
    if blends:
        profile = blend_style_profiles(blends)
        applied_blends = {normalize_style_name(key): float(value) for key, value in blends.items()}
    elif override in STYLE_PROFILES:
        profile = STYLE_PROFILES[override]
        applied_blends = {override: 1.0}
    else:
        profile = detected.profile
        applied_blends = {detected.detected_style: 1.0}

    decision = StyleDecision(
        profile=profile,
        detected_style=detected.detected_style,
        confidence=detected.confidence,
        manual_override=override if override in STYLE_PROFILES else None,
        blends=applied_blends,
        debug={
            **detected.debug,
            "active_parameters": profile.to_dict(),
            "overrides_applied": bool(blends or override in STYLE_PROFILES),
        },
    )
    context.update_style(profile.to_dict())
    context.add_debug("style_engine", "style_resolved", decision.to_dict())
    return decision
