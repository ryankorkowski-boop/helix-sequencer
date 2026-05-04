from __future__ import annotations

import re
from collections import Counter, defaultdict
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

PROP_ROLE_BY_FAMILY = {
    "faces": "vocals",
    "talking_heads": "vocals",
    "matrix": "lyrics_detail",
    "mega_tree": "hero",
    "tree": "hero",
    "arches": "travel",
    "arch": "travel",
    "rooflines": "structure",
    "line": "structure",
    "windows": "structure",
    "window": "structure",
    "mini_trees": "beat_grid",
    "spinner": "motion",
    "sphere": "mood",
    "floods": "mood",
    "snowman_band": "performer",
    "character": "performer",
}

MOTION_BY_EFFECT_TOKEN = {
    "spiral": "radial",
    "sweep": "left_to_right",
    "chase": "left_to_right",
    "wave": "wave_handoff",
    "bars": "bottom_up",
    "butterfly": "center_outward",
    "pinwheel": "radial",
    "fan": "center_outward",
    "marquee": "travel",
    "morph": "travel",
    "shockwave": "center_outward",
    "ripple": "center_outward",
}


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


def _overlap_ms(start: int, end: int, window_start: int, window_end: int) -> int:
    return max(0, min(int(end), int(window_end)) - max(int(start), int(window_start)))


def _entry_palette(entry: Any) -> str:
    xml_effect = getattr(entry, "xml_effect", None)
    attrib = getattr(xml_effect, "attrib", {}) or {}
    for key, value in attrib.items():
        if "palette" in str(key).lower() and str(value).strip():
            return str(value)
    return ""


def _palette_colors(raw: str) -> list[str]:
    hexes = re.findall(r"#[0-9a-fA-F]{6}", raw or "")
    if hexes:
        return [item.lower() for item in hexes]
    tokens = re.findall(r"\b(red|green|blue|white|gold|yellow|orange|purple|pink|cyan|rainbow|multicolor)\b", raw.lower())
    return list(tokens)


def _model_family(model_name: str) -> str:
    name = _norm(model_name)
    if any(token in name for token in ("face", "mouth", "singing", "talking_head")):
        return "faces"
    if "snowman" in name or "band" in name:
        return "snowman_band"
    if any(token in name for token in ("cactus", "tubeman", "dj_", "character")):
        return "character"
    if "matrix" in name:
        return "matrix"
    if "mega" in name or "tree" in name or "_gt" in name:
        return "mega_tree"
    if "arch" in name:
        return "arches"
    if "window" in name:
        return "windows"
    if "roof" in name or "outline" in name or "line" in name:
        return "rooflines"
    if "mini" in name and "tree" in name:
        return "mini_trees"
    if "spinner" in name or "star" in name:
        return "spinner"
    if "sphere" in name or "flood" in name or "wash" in name:
        return "sphere"
    return name.split("_", 1)[0] if name else "unknown"


def _effect_motion(effect_name: str) -> str:
    name = _norm(effect_name)
    for token, motion in MOTION_BY_EFFECT_TOKEN.items():
        if token in name:
            return motion
    if name == "on":
        return ""
    if any(token in name for token in ("shimmer", "twinkle")):
        return "accent"
    return ""


def build_show_direction_summary(
    *,
    timelines: Mapping[str, Any],
    parts: list[Any],
    quiet_windows: list[tuple[int, int]] | None = None,
) -> dict[str, Any]:
    """
    Summarize generated timelines for report-only YouTube-grade direction scoring.

    The adapter intentionally uses duck typing so it can run after generation without
    importing the heavy effect engine or changing placement behavior.
    """
    quiet = [(int(start), int(end)) for start, end in (quiet_windows or []) if int(end) > int(start)]
    sections: list[dict[str, Any]] = []
    all_role_map: dict[str, str] = {}

    for part in parts:
        start_ms = int(getattr(part, "start_ms", 0) or 0)
        end_ms = int(getattr(part, "end_ms", start_ms) or start_ms)
        if end_ms <= start_ms:
            continue
        duration_ms = max(1, end_ms - start_ms)
        family_duration: Counter[str] = Counter()
        layer_duration: Counter[str] = Counter()
        color_counter: Counter[str] = Counter()
        motion_counter: Counter[str] = Counter()
        effect_count = 0

        for model_name, timeline in timelines.items():
            family = _model_family(str(model_name))
            layers = getattr(timeline, "layers", {}) or {}
            for layer_name, entries in layers.items():
                for entry in entries:
                    overlap = _overlap_ms(
                        int(getattr(entry, "start", 0) or 0),
                        int(getattr(entry, "end", 0) or 0),
                        start_ms,
                        end_ms,
                    )
                    if overlap <= 0:
                        continue
                    effect_count += 1
                    family_duration[family] += overlap
                    layer_duration[_norm(layer_name)] += overlap
                    effect_name = str(getattr(entry, "effect_name", "") or "")
                    motion = _effect_motion(effect_name)
                    if motion:
                        motion_counter[motion] += overlap
                    for color in _palette_colors(_entry_palette(entry)):
                        color_counter[color] += overlap

        active_families = [family for family, _value in family_duration.most_common()]
        focal_target = active_families[0] if active_families else ""
        role_map = {family: PROP_ROLE_BY_FAMILY.get(family, "support") for family in active_families}
        all_role_map.update(role_map)
        colors = [color for color, _value in color_counter.most_common(4)]
        if not colors and effect_count:
            colors = ["template_palette"]
        quiet_ms = sum(_overlap_ms(start_ms, end_ms, q_start, q_end) for q_start, q_end in quiet)
        density = min(1.0, effect_count / max(1.0, duration_ms / 1000.0) / 95.0)
        coverage = min(1.0, len(active_families) / 8.0)
        brightness = min(1.0, (density * 0.55) + (coverage * 0.45))
        has_rest = quiet_ms / duration_ms >= 0.08 or effect_count == 0
        sections.append(
            {
                "label": str(getattr(part, "label", "") or ""),
                "start_ms": start_ms,
                "end_ms": end_ms,
                "focal_target": focal_target,
                "active_props": active_families[:10],
                "layers": [layer for layer, _value in layer_duration.most_common()],
                "colors": colors,
                "motion": motion_counter.most_common(1)[0][0] if motion_counter else "",
                "brightness": round(brightness, 4),
                "density": round(density, 4),
                "coverage": round(coverage, 4),
                "has_rest": bool(has_rest),
                "prop_roles": role_map,
                "effect_count": int(effect_count),
            }
        )

    return {
        "schema_version": 1,
        "source": "generated_timeline_report_adapter",
        "sections": sections,
        "section_count": len(sections),
        "prop_roles": all_role_map,
        "quiet_window_count": len(quiet),
        "notes": [
            "Report-only summary for generalized show-design scoring.",
            "Does not copy or infer any external creator timing pattern.",
        ],
    }


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


def _problem(
    code: str,
    message: str,
    *,
    severity: str = "warning",
    section: str | None = None,
    metric: str | None = None,
) -> dict[str, str]:
    item = {
        "code": code,
        "severity": severity,
        "message": message,
    }
    if section:
        item["section"] = section
    if metric:
        item["metric"] = metric
    return item


def direction_problems(
    payload: Mapping[str, Any],
    component_scores: Mapping[str, float] | None = None,
    clutter_penalty: float | None = None,
) -> list[dict[str, str]]:
    components = dict(component_scores or {})
    if not components:
        components = {
            "focal_clarity": focal_clarity_score(payload),
            "phrase_structure": phrase_structure_score(payload),
            "darkness_usage": darkness_usage_score(payload),
            "layer_control": layer_control_score(payload),
            "prop_role_consistency": prop_role_consistency_score(payload),
            "color_discipline": color_discipline_score(payload),
            "motion_coherence": motion_coherence_score(payload),
            "escalation": escalation_score(payload),
        }
    clutter = clutter_penalty_score(payload) if clutter_penalty is None else float(clutter_penalty)
    sections = _extract_sections(payload)
    problems: list[dict[str, str]] = []

    thresholds = (
        ("focal_clarity", 72.0, "weak_focal_clarity", "Focal target is unclear or competing with too many prop groups."),
        ("phrase_structure", 70.0, "weak_phrase_structure", "Sections do not yet read like distinct musical phrases."),
        ("darkness_usage", 68.0, "weak_darkness_usage", "Show needs more rests, blackouts, or contrast before major payoffs."),
        ("layer_control", 76.0, "excess_layering", "Layering is too busy for routine moments."),
        ("prop_role_consistency", 70.0, "weak_prop_roles", "Prop families are not holding consistent visual jobs."),
        ("color_discipline", 72.0, "weak_color_discipline", "Palette appears too broad or insufficiently controlled."),
        ("motion_coherence", 70.0, "weak_motion_coherence", "Motion direction is unclear or too chaotic."),
        ("escalation", 70.0, "weak_escalation", "Repeated sections are not building toward a larger chorus/finale payoff."),
    )
    for metric, threshold, code, message in thresholds:
        if float(components.get(metric, 100.0)) < threshold:
            problems.append(_problem(code, message, metric=metric))

    if clutter >= 28.0:
        problems.append(
            _problem(
                "clutter_risk",
                "Too many active props, layers, or colors are competing at once.",
                severity="error" if clutter >= 45.0 else "warning",
                metric="clutter_penalty",
            )
        )

    for section in sections:
        label = str(section.get("label") or section.get("section") or "").strip()
        props = list(dict.fromkeys(_active_props(section)))
        layers = _layers(section)
        colors = list(dict.fromkeys(_colors(section)))
        motion = _norm(section.get("motion") or section.get("motion_pattern"))
        focal = _norm(section.get("focal_target") or section.get("focus") or section.get("primary_target"))
        if not focal and props:
            problems.append(
                _problem(
                    "section_missing_focal_target",
                    "Section has active props but no declared focal target.",
                    section=label,
                    metric="focal_clarity",
                )
            )
        if len(props) > 6:
            problems.append(
                _problem(
                    "section_too_many_prop_families",
                    "Section activates too many prop families for clear audience focus.",
                    section=label,
                    metric="focal_clarity",
                )
            )
        if len(layers) > 3:
            problems.append(
                _problem(
                    "section_too_many_layers",
                    "Section exceeds the preferred three-layer show direction rule.",
                    section=label,
                    metric="layer_control",
                )
            )
        if len(colors) > 4 or any(color in RAINBOW_TOKENS for color in colors):
            finale_ok = any(token in _norm(label) for token in ("finale", "final", "playful", "party"))
            if not finale_ok:
                problems.append(
                    _problem(
                        "section_palette_sprawl",
                        "Section palette is too broad for disciplined phrase identity.",
                        section=label,
                        metric="color_discipline",
                    )
                )
        if motion and any(token in motion for token in CHAOTIC_MOTION_TOKENS):
            problems.append(
                _problem(
                    "section_chaotic_motion",
                    "Section uses chaotic motion without a reportable musical reason.",
                    section=label,
                    metric="motion_coherence",
                )
            )

    return problems[:24]


RECOMMENDATION_BY_PROBLEM = {
    "weak_focal_clarity": {
        "action": "declare_primary_focus",
        "guidance": "Pick one focal family for the phrase and demote competing props to background or accent support.",
    },
    "weak_phrase_structure": {
        "action": "separate_section_identities",
        "guidance": "Give intro, verse, chorus, bridge, and finale different visual identities instead of one continuous effect texture.",
    },
    "weak_darkness_usage": {
        "action": "add_contrast_rest",
        "guidance": "Add short rests, half-house dark moments, or a blackout before the next chorus/drop payoff.",
    },
    "excess_layering": {
        "action": "cap_routine_layers",
        "guidance": "Keep routine phrases near three layers: background, motion/rhythm, and focal/accent.",
    },
    "weak_prop_roles": {
        "action": "stabilize_prop_roles",
        "guidance": "Assign each prop family a job such as structure, travel, vocals, hero, mood, or accent.",
    },
    "weak_color_discipline": {
        "action": "limit_palette",
        "guidance": "Use two to four dominant colors for the section and reserve rainbow/multicolor for playful or finale moments.",
    },
    "weak_motion_coherence": {
        "action": "choose_directional_motion",
        "guidance": "Use a clear motion grammar such as left-to-right, center-out, bottom-up, or call-and-response.",
    },
    "weak_escalation": {
        "action": "shape_payoff_arc",
        "guidance": "Make repeated sections grow through coverage, brightness, motion width, or accent intensity, not all-on clutter.",
    },
    "clutter_risk": {
        "action": "reduce_competing_activity",
        "guidance": "Reduce simultaneous active prop families, layers, or colors until the main focal idea reads clearly.",
    },
    "section_missing_focal_target": {
        "action": "set_section_focal_target",
        "guidance": "Choose the section's main audience target before adding supporting motion or accents.",
    },
    "section_too_many_prop_families": {
        "action": "reduce_section_fanout",
        "guidance": "Hold some prop families dark or low-intensity so the section has a readable center of attention.",
    },
    "section_too_many_layers": {
        "action": "merge_or_drop_layers",
        "guidance": "Merge compatible effects or drop the weakest layer unless this is a chorus/finale payoff.",
    },
    "section_palette_sprawl": {
        "action": "tighten_section_palette",
        "guidance": "Constrain the section to a controlled palette before adding color variation.",
    },
    "section_chaotic_motion": {
        "action": "replace_random_motion",
        "guidance": "Replace random direction changes with a readable sweep, handoff, or call-and-response pattern.",
    },
}


def director_recommendations(problems: list[Mapping[str, Any]]) -> list[dict[str, str]]:
    recommendations: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for problem in problems:
        code = str(problem.get("code", ""))
        mapping = RECOMMENDATION_BY_PROBLEM.get(code)
        if mapping is None:
            continue
        section = str(problem.get("section", "") or "")
        key = (code, section)
        if key in seen:
            continue
        seen.add(key)
        item = {
            "problem_code": code,
            "action": mapping["action"],
            "guidance": mapping["guidance"],
            "priority": "high" if problem.get("severity") == "error" else "normal",
        }
        if section:
            item["section"] = section
        metric = str(problem.get("metric", "") or "")
        if metric:
            item["metric"] = metric
        recommendations.append(item)
    return recommendations[:16]


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
    problems = direction_problems(source, component_scores, clutter_penalty)
    recommendations = director_recommendations(problems)
    result = {
        **{key: round(value, 1) for key, value in component_scores.items()},
        "clutter_penalty": round(clutter_penalty, 1),
        "final_score": round(final_score, 1),
        "grade": letter_grade(final_score),
        "direction_problems": problems,
        "problem_count": len(problems),
        "director_recommendations": recommendations,
        "recommendation_count": len(recommendations),
        "source": "generalized_show_direction_principles",
        "non_copying_policy": "general principles only; no vendor, creator, tutorial, or YouTube timing pattern copying",
    }
    return result


def score(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    return score_youtube_show(payload)
