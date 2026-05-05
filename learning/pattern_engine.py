from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field, replace
from typing import Any, Mapping

from learning.feature_extractor import ExtractedSequenceFeatures, clamp01


@dataclass(frozen=True)
class PatternRule:
    rule_id: str
    condition: dict[str, Any]
    action: dict[str, Any]
    score_impact: float
    confidence: float
    support: int = 1
    style: str = "unknown"
    tags: tuple[str, ...] = ()
    usage_count: int = 0
    last_seen: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["tags"] = list(self.tags)
        return data

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "PatternRule":
        return cls(
            rule_id=str(payload.get("rule_id", "")),
            condition=dict(payload.get("condition", {}) or {}),
            action=dict(payload.get("action", {}) or {}),
            score_impact=float(payload.get("score_impact", 0.0) or 0.0),
            confidence=clamp01(float(payload.get("confidence", 0.0) or 0.0)),
            support=max(1, int(payload.get("support", 1) or 1)),
            style=str(payload.get("style", "unknown") or "unknown"),
            tags=tuple(str(tag) for tag in (payload.get("tags", ()) or ())),
            usage_count=max(0, int(payload.get("usage_count", 0) or 0)),
            last_seen=str(payload.get("last_seen", "") or ""),
        )


def stable_rule_id(condition: Mapping[str, Any], action: Mapping[str, Any], style: str = "unknown") -> str:
    raw = f"{style}|{sorted(condition.items())}|{sorted(action.items())}".encode("utf-8", errors="ignore")
    return hashlib.sha1(raw).hexdigest()[:16]


def _impact_from_score(score: float) -> float:
    return max(-0.35, min(0.35, (float(score) - 0.72) * 0.75))


def _top_keys(values: Mapping[str, int], limit: int = 3) -> list[str]:
    return [
        key
        for key, count in sorted(values.items(), key=lambda item: (-int(item[1]), item[0]))[:limit]
        if int(count) > 0
    ]


def _rule(condition: dict[str, Any], action: dict[str, Any], *, score: float, style: str, tags: tuple[str, ...]) -> PatternRule:
    return PatternRule(
        rule_id=stable_rule_id(condition, action, style),
        condition=condition,
        action=action,
        score_impact=round(_impact_from_score(score), 4),
        confidence=round(0.48 + (max(0.0, score - 0.6) * 0.62), 4),
        style=style,
        tags=tags,
    )


def encode_patterns(features: ExtractedSequenceFeatures) -> list[PatternRule]:
    score = float(features.score_summary.get("total_score", 0.0) or 0.0)
    musical = features.musical
    visual = features.visual
    style = musical.style_hint or musical.genre_hint or "unknown"
    rules: list[PatternRule] = []
    top_effects = _top_keys(visual.effect_types_used, 4)
    top_layers = _top_keys(visual.layer_combinations, 3)
    top_spatial = _top_keys(visual.spatial_motion_patterns, 3)

    energy_buckets = [item["energy_bucket"] for item in visual.density_over_time]
    density_buckets = [item["density_bucket"] for item in visual.density_over_time]
    high_energy_ratio = energy_buckets.count("high") / max(1, len(energy_buckets))
    low_energy_ratio = energy_buckets.count("low") / max(1, len(energy_buckets))
    dense_ratio = density_buckets.count("dense") / max(1, len(density_buckets))

    if musical.tempo_bucket in {"fast_tempo", "very_fast_tempo"} and high_energy_ratio >= 0.34:
        rules.append(
            _rule(
                {"tempo": musical.tempo_bucket, "energy": "high"},
                {
                    "effect_behavior": "short_bursts_and_rapid_motion",
                    "preferred_effects": top_effects[:3] or ["strobe_burst", "motion_sweep"],
                    "layer_strategy": top_layers[:2] or ["accent+additive"],
                },
                score=score,
                style=style,
                tags=("tempo", "energy", "motion"),
            )
        )
    if "chorus" in musical.section_types:
        rules.append(
            _rule(
                {"section": "chorus", "energy": "medium_or_high"},
                {
                    "effect_behavior": "increase_brightness_and_spatial_coverage",
                    "spatial_patterns": top_spatial or ["coverage:matrix", "coverage:tree"],
                    "density": "wider_than_verse",
                },
                score=score,
                style=style,
                tags=("section", "coverage"),
            )
        )
    if low_energy_ratio >= 0.34:
        rules.append(
            _rule(
                {"energy": "low", "density": "sparse"},
                {
                    "effect_behavior": "slow_gradients_minimal_accents",
                    "layer_strategy": ["base+normal", "texture+screen"],
                    "avoid": "dense_accent_stack",
                },
                score=score,
                style=style,
                tags=("restraint", "energy"),
            )
        )
    if dense_ratio >= 0.34 and visual.repetition_frequency <= 0.42:
        rules.append(
            _rule(
                {"density": "dense", "repetition": "controlled"},
                {
                    "effect_behavior": "layered_motion_with_diverse_families",
                    "preferred_effects": top_effects,
                    "layer_strategy": top_layers,
                },
                score=score,
                style=style,
                tags=("layering", "diversity"),
            )
        )
    for section in visual.density_over_time[:12]:
        rules.append(
            _rule(
                {
                    "section": section["section"],
                    "energy": section["energy_bucket"],
                    "density": section["density_bucket"],
                    "tempo": musical.tempo_bucket,
                },
                {
                    "effect_behavior": "section_adaptive_density",
                    "coverage": section["coverage_bucket"],
                    "preferred_effects": top_effects[:2],
                },
                score=score,
                style=style,
                tags=("section", "density"),
            )
        )
    return _dedupe_rules(rules)


def _dedupe_rules(rules: list[PatternRule]) -> list[PatternRule]:
    out: dict[str, PatternRule] = {}
    for rule in rules:
        existing = out.get(rule.rule_id)
        if existing is None:
            out[rule.rule_id] = rule
            continue
        support = existing.support + rule.support
        impact = existing.score_impact + ((rule.score_impact - existing.score_impact) / support)
        confidence = clamp01(max(existing.confidence, rule.confidence) + 0.02)
        out[rule.rule_id] = replace(existing, score_impact=round(impact, 4), confidence=round(confidence, 4), support=support)
    return list(out.values())


def rule_matches_context(rule: PatternRule, context: Mapping[str, Any]) -> bool:
    condition = rule.condition
    for key, expected in condition.items():
        actual = context.get(key)
        if actual is None:
            continue
        if isinstance(expected, str) and expected.endswith("_or_high"):
            allowed = {expected.removesuffix("_or_high"), "high"}
            if str(actual).lower() not in allowed:
                return False
            continue
        if str(actual).lower() != str(expected).lower():
            return False
    return True


def action_matches(rule: PatternRule, action: Mapping[str, Any]) -> bool:
    action_text = " ".join(str(value).lower() for value in action.values())
    rule_text = " ".join(str(value).lower() for value in rule.action.values())
    return any(token in action_text for token in rule_text.replace("[", " ").replace("]", " ").replace(",", " ").split() if len(token) > 3)


def learned_pattern_bias(
    *,
    base_score: float,
    context: Mapping[str, Any],
    candidate_action: Mapping[str, Any],
    pattern_rules: list[PatternRule | Mapping[str, Any]],
    diversity_penalty: float = 0.0,
    randomness: float = 0.0,
) -> dict[str, Any]:
    matched: list[PatternRule] = []
    for item in pattern_rules:
        rule = item if isinstance(item, PatternRule) else PatternRule.from_dict(item)
        if rule_matches_context(rule, context) and action_matches(rule, candidate_action):
            matched.append(rule)
    bias = sum(rule.score_impact * rule.confidence for rule in matched)
    bias = max(-0.4, min(0.4, bias - clamp01(diversity_penalty) * 0.16 + float(randomness)))
    decision_score = float(base_score) + bias
    return {
        "decision_score": round(decision_score, 4),
        "base_score": round(float(base_score), 4),
        "learned_bias": round(bias, 4),
        "matched_rules": [rule.rule_id for rule in matched[:8]],
        "matched_rule_count": len(matched),
    }
