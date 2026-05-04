from __future__ import annotations

from collections.abc import Mapping
from statistics import mean
from typing import Any


RECOGNIZED_SECTIONS = {
    "intro",
    "verse",
    "prechorus",
    "pre_chorus",
    "chorus",
    "bridge",
    "breakdown",
    "finale",
    "final",
    "outro",
    "drop",
}

COHERENT_MOTIONS = {
    "left_to_right",
    "right_to_left",
    "center_outward",
    "outside_inward",
    "bottom_up",
    "top_down",
    "call_response",
    "call_and_response",
    "wave_handoff",
    "radial",
    "sweep",
    "travel",
}

CHAOTIC_MOTION_TOKENS = {"random", "chaos", "jitter", "noise", "scatter"}
RAINBOW_TOKENS = {"rainbow", "multicolor", "multi", "random", "chaos"}


def clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, float(value)))


def _norm(value: Any) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, str):
        if "," in value:
            return [item.strip() for item in value.split(",") if item.strip()]
        return [value] if value.strip() else []
    if isinstance(value, Mapping):
        return list(value)
    try:
        return list(value)
    except TypeError:
        return [value]


def _number(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _score_to_report_value(score: float) -> float:
    value = _number(score)
    if value <= 1.0:
        return value * 100.0
    return value


def _extract_sections(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    raw = payload.get("sections")
    if raw is None:
        raw = ((payload.get("show_direction") or {}) or {}).get("sections")
    if raw is None:
        raw = ((payload.get("youtube_show_summary") or {}) or {}).get("sections")

    sections: list[dict[str, Any]] = []
    for item in _as_list(raw):
        if isinstance(item, Mapping):
            sections.append(dict(item))

    if sections:
        return sections

    audit_sections = (((payload.get("audit") or {}) or {}).get("final") or {}).get("section_scores", [])
    for item in _as_list(audit_sections):
        if not isinstance(item, Mapping):
            continue
        sections.append(
            {
                "label": item.get("label", ""),
                "density": _number(item.get("density"), 0.0),
                "coverage": _number(item.get("coverage_ratio"), 0.0),
            }
        )
    return sections


def _active_props(section: Mapping[str, Any]) -> list[str]:
    for key in ("active_props", "props", "prop_groups", "targets"):
        values = [_norm(item) for item in _as_list(section.get(key))]
        if values:
            return values
    return []


def _layers(section: Mapping[str, Any]) -> list[str]:
    values = [_norm(item) for item in _as_list(section.get("layers"))]
    if values:
        return values
    count = int(_number(section.get("layer_count"), 0.0))
    return [f"layer_{idx}" for idx in range(count)]


def _colors(section: Mapping[str, Any]) -> list[str]:
    for key in ("colors", "palette", "dominant_colors"):
        values = [_norm(item) for item in _as_list(section.get(key))]
        if values:
            return values
    return []


def _section_intensity(section: Mapping[str, Any]) -> float:
    brightness = _number(section.get("brightness"), 0.0)
    density = _number(section.get("density"), 0.0)
    coverage = _number(section.get("coverage"), _number(section.get("coverage_ratio"), 0.0))
    active_factor = min(1.0, len(_active_props(section)) / 8.0)
    values = [value for value in (brightness, density, coverage, active_factor) if value > 0.0]
    return mean(values) if values else 0.0


def letter_grade(score: float) -> str:
    if score >= 97:
        return "A+"
    if score >= 93:
        return "A"
    if score >= 90:
        return "A-"
    if score >= 87:
        return "B+"
    if score >= 83:
        return "B"
    if score >= 80:
        return "B-"
    if score >= 77:
        return "C+"
    if score >= 73:
        return "C"
    if score >= 70:
        return "C-"
    if score >= 67:
        return "D+"
    if score >= 63:
        return "D"
    if score >= 60:
        return "D-"
    return "F"


def focal_clarity_score(payload: Mapping[str, Any]) -> float:
    sections = _extract_sections(payload)
    if not sections:
        quality = (payload.get("quality") or {}) or {}
        dominance = ((quality.get("component_scores") or {}) or {}).get("dominance", 55.0)
        return clamp(_score_to_report_value(dominance))

    scores: list[float] = []
    for section in sections:
        focal = _norm(section.get("focal_target") or section.get("focus") or section.get("primary_target"))
        props = _active_props(section)
        active_count = len(set(props))
        score = 82.0 if focal else 48.0
        if focal and (not props or focal in props):
            score += 8.0
        if active_count <= 3:
            score += 10.0
        elif active_count <= 5:
            score += 2.0
        else:
            score -= min(38.0, (active_count - 5) * 7.0)
        scores.append(clamp(score))
    return round(mean(scores), 1)


def phrase_structure_score(payload: Mapping[str, Any]) -> float:
    sections = _extract_sections(payload)
    if not sections:
        audit = (((payload.get("audit") or {}) or {}).get("final") or {})
        return clamp(_score_to_report_value(audit.get("musical_coherence", 52.0)))

    labels = [_norm(section.get("label") or section.get("section")) for section in sections]
    recognized = [label for label in labels if any(token in label for token in RECOGNIZED_SECTIONS)]
    unique_families = {next((token for token in RECOGNIZED_SECTIONS if token in label), label) for label in recognized}
    score = 35.0
    score += min(45.0, (len(unique_families) / 6.0) * 45.0)
    score += min(12.0, len(sections) * 2.0)
    if any("chorus" in label for label in labels) and any(label in {"finale", "final", "outro"} for label in labels):
        score += 8.0
    return round(clamp(score), 1)


def darkness_usage_score(payload: Mapping[str, Any]) -> float:
    sections = _extract_sections(payload)
    if not sections:
        runtime = (payload.get("runtime_tuning") or {}) or {}
        profile = (payload.get("profile") or {}) or {}
        darkness = _number(runtime.get("darkness", profile.get("darkness", 0.45)), 0.45)
        return round(clamp(35.0 + darkness * 45.0), 1)

    intensities = [_section_intensity(section) for section in sections]
    rest_count = 0
    for section, intensity in zip(sections, intensities):
        rest_flag = bool(section.get("has_rest") or section.get("blackout") or section.get("rest"))
        if rest_flag or intensity <= 0.22:
            rest_count += 1
    rest_ratio = rest_count / max(1, len(sections))
    contrast = (max(intensities) - min(intensities)) if intensities else 0.0
    score = 28.0 + rest_ratio * 44.0 + min(28.0, contrast * 35.0)
    return round(clamp(score), 1)


def layer_control_score(payload: Mapping[str, Any]) -> float:
    sections = _extract_sections(payload)
    if not sections:
        rejected = _number(((payload.get("validation") or {}) or {}).get("rejected_effects_count"), 0.0)
        total = max(1.0, _number(payload.get("effects_total"), 1.0))
        return round(clamp(88.0 - min(55.0, (rejected / total) * 220.0)), 1)

    scores: list[float] = []
    for section in sections:
        count = len(_layers(section))
        if count == 0:
            scores.append(62.0)
        elif count <= 3:
            scores.append(100.0)
        elif count == 4:
            scores.append(76.0)
        elif count == 5:
            scores.append(56.0)
        else:
            scores.append(max(12.0, 56.0 - (count - 5) * 10.0))
    return round(mean(scores), 1)


def prop_role_consistency_score(payload: Mapping[str, Any]) -> float:
    sections = _extract_sections(payload)
    if not sections:
        used = (payload.get("used_targets") or {}) or {}
        family_count = _number(used.get("family_count"), 0.0)
        return round(clamp(48.0 + min(42.0, family_count * 5.0)), 1)

    role_map: dict[str, set[str]] = {}
    active_counts: list[int] = []
    for section in sections:
        props = _active_props(section)
        active_counts.append(len(set(props)))
        roles = section.get("prop_roles") or section.get("roles") or {}
        if isinstance(roles, Mapping):
            for prop, role in roles.items():
                role_map.setdefault(_norm(prop), set()).add(_norm(role))

    if role_map:
        stable = sum(1 for roles in role_map.values() if len(roles) <= 2)
        role_score = 45.0 + (stable / max(1, len(role_map))) * 55.0
    else:
        role_score = 68.0
    average_active = mean(active_counts) if active_counts else 0.0
    if average_active > 7:
        role_score -= min(30.0, (average_active - 7.0) * 5.0)
    return round(clamp(role_score), 1)


def color_discipline_score(payload: Mapping[str, Any]) -> float:
    sections = _extract_sections(payload)
    if not sections:
        quality = (payload.get("quality") or {}) or {}
        diversity = ((quality.get("component_scores") or {}) or {}).get("family_diversity", 58.0)
        return clamp(_score_to_report_value(diversity))

    scores: list[float] = []
    for section in sections:
        colors = list(dict.fromkeys(_colors(section)))
        count = len(colors)
        label = _norm(section.get("label") or section.get("section"))
        if count == 0:
            score = 58.0
        elif 2 <= count <= 4:
            score = 100.0
        elif count == 1:
            score = 78.0
        elif count <= 6:
            score = 74.0
        else:
            score = max(18.0, 72.0 - (count - 6) * 7.0)
        rainbowish = any(color in RAINBOW_TOKENS for color in colors)
        finale_ok = any(token in label for token in ("finale", "final", "playful", "party"))
        if rainbowish and not finale_ok:
            score -= 32.0
        scores.append(clamp(score))
    return round(mean(scores), 1)


def motion_coherence_score(payload: Mapping[str, Any]) -> float:
    sections = _extract_sections(payload)
    if not sections:
        placements = (payload.get("placements") or {}) or {}
        motion_tokens = sum(int(value or 0) for key, value in placements.items() if any(token in key for token in ("sweep", "wave", "chase", "motion", "flow")))
        total = max(1, sum(int(value or 0) for value in placements.values()))
        return round(clamp(48.0 + min(42.0, (motion_tokens / total) * 110.0)), 1)

    scores: list[float] = []
    motions = [_norm(section.get("motion") or section.get("motion_pattern")) for section in sections]
    for motion in motions:
        if not motion:
            scores.append(56.0)
        elif motion in COHERENT_MOTIONS or any(token in motion for token in COHERENT_MOTIONS):
            scores.append(94.0)
        elif any(token in motion for token in CHAOTIC_MOTION_TOKENS):
            scores.append(24.0)
        else:
            scores.append(66.0)
    unique_motions = {motion for motion in motions if motion}
    if len(unique_motions) > max(4, len(sections) // 2 + 2):
        return round(clamp(mean(scores) - 12.0), 1)
    return round(mean(scores), 1)


def escalation_score(payload: Mapping[str, Any]) -> float:
    sections = _extract_sections(payload)
    if len(sections) < 2:
        return 55.0

    labeled = [(_norm(section.get("label") or section.get("section")), _section_intensity(section)) for section in sections]
    score = 48.0
    choruses = [value for label, value in labeled if "chorus" in label]
    verses = [value for label, value in labeled if "verse" in label]
    finales = [value for label, value in labeled if any(token in label for token in ("finale", "final", "outro"))]
    if len(verses) >= 2 and verses[-1] >= verses[0]:
        score += 14.0
    if len(choruses) >= 2 and choruses[-1] >= choruses[0]:
        score += 18.0
    if finales and finales[-1] >= max(value for _, value in labeled[:-1] or labeled):
        score += 20.0
    if max(value for _, value in labeled) - min(value for _, value in labeled) >= 0.25:
        score += 10.0
    return round(clamp(score), 1)


def clutter_penalty_score(payload: Mapping[str, Any]) -> float:
    sections = _extract_sections(payload)
    penalties: list[float] = []
    for section in sections:
        layer_overage = max(0, len(_layers(section)) - 3)
        prop_overage = max(0, len(set(_active_props(section))) - 5)
        color_overage = max(0, len(set(_colors(section))) - 4)
        penalties.append(clamp(layer_overage * 16.0 + prop_overage * 8.0 + color_overage * 7.0))

    audit = (((payload.get("audit") or {}) or {}).get("final") or {})
    audit_penalty = clamp(_number(audit.get("clutter_ratio"), 0.0) * 100.0)
    if penalties:
        return round(clamp(mean(penalties) * 0.72 + audit_penalty * 0.28), 1)
    return round(audit_penalty, 1)


def score_youtube_show(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    source: Mapping[str, Any] = payload or {}
    component_scores = {
        "focal_clarity": focal_clarity_score(source),
        "phrase_structure": phrase_structure_score(source),
        "darkness_usage": darkness_usage_score(source),
        "layer_control": layer_control_score(source),
        "prop_role_consistency": prop_role_consistency_score(source),
        "color_discipline": color_discipline_score(source),
        "motion_coherence": motion_coherence_score(source),
        "escalation": escalation_score(source),
    }
    clutter_penalty = clutter_penalty_score(source)
    weighted = (
        component_scores["focal_clarity"] * 0.18
        + component_scores["phrase_structure"] * 0.15
        + component_scores["darkness_usage"] * 0.13
        + component_scores["layer_control"] * 0.12
        + component_scores["prop_role_consistency"] * 0.10
        + component_scores["color_discipline"] * 0.10
        + component_scores["motion_coherence"] * 0.09
        + component_scores["escalation"] * 0.08
    ) / 0.95
    final_score = clamp(weighted - (clutter_penalty * 0.16))
    result = {
        **{key: round(value, 1) for key, value in component_scores.items()},
        "clutter_penalty": round(clutter_penalty, 1),
        "final_score": round(final_score, 1),
        "grade": letter_grade(final_score),
        "source": "generalized_show_direction_principles",
        "non_copying_policy": "general principles only; no vendor, creator, tutorial, or YouTube timing pattern copying",
    }
    return result


def score(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    return score_youtube_show(payload)
