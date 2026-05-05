from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any, Mapping

from core import self_improving_scoring as scoring
from learning.pattern_engine import PatternRule


LEARNING_MEMORY_SCHEMA_VERSION = 1
MAX_RULES = 400
MAX_HISTORY = 250
CONFIDENCE_DECAY = 0.985


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass
class LearningMemory:
    schema_version: int = LEARNING_MEMORY_SCHEMA_VERSION
    source_policy: dict[str, Any] = field(
        default_factory=lambda: {
            "helix_generated_only": True,
            "accepted_watermark_version": scoring.HELIX_WATERMARK_POLICY_VERSION,
            "stores_full_sequences": False,
            "stores_vendor_timing_or_layouts": False,
        }
    )
    pattern_rules: dict[str, dict[str, Any]] = field(default_factory=dict)
    scoring_history: list[dict[str, Any]] = field(default_factory=list)
    context_outcome_mappings: list[dict[str, Any]] = field(default_factory=list)
    success_metrics: dict[str, Any] = field(default_factory=lambda: {"sequence_count": 0, "average_score": 0.0, "best_score": 0.0})
    style_tendencies: dict[str, dict[str, Any]] = field(default_factory=dict)
    decision_preferences: dict[str, float] = field(default_factory=dict)
    debug_log: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "LearningMemory":
        if int(payload.get("schema_version", 0) or 0) != LEARNING_MEMORY_SCHEMA_VERSION:
            return cls()
        return cls(
            schema_version=LEARNING_MEMORY_SCHEMA_VERSION,
            source_policy=dict(payload.get("source_policy", {}) or cls().source_policy),
            pattern_rules=dict(payload.get("pattern_rules", {}) or {}),
            scoring_history=list(payload.get("scoring_history", []) or [])[-MAX_HISTORY:],
            context_outcome_mappings=list(payload.get("context_outcome_mappings", []) or [])[-MAX_HISTORY:],
            success_metrics=dict(payload.get("success_metrics", {}) or {}),
            style_tendencies=dict(payload.get("style_tendencies", {}) or {}),
            decision_preferences={str(key): float(value) for key, value in (payload.get("decision_preferences", {}) or {}).items()},
            debug_log=list(payload.get("debug_log", []) or [])[-MAX_HISTORY:],
        )


def load_memory(path: Path) -> LearningMemory:
    if not path.exists():
        return LearningMemory()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return LearningMemory()
    return LearningMemory.from_dict(payload if isinstance(payload, dict) else {})


def save_memory(path: Path, memory: LearningMemory) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(memory.to_dict(), indent=2, sort_keys=True), encoding="utf-8")


def assert_helix_generated(payload: Mapping[str, Any]) -> None:
    if not scoring.is_helix_generated_payload(dict(payload)):
        raise ValueError("principle learning accepts Helix-generated payloads only")


def _merge_rule(existing: PatternRule | None, incoming: PatternRule, *, actual_score: float, expected_score: float | None = None) -> PatternRule:
    if existing is None:
        return incoming
    support = existing.support + 1
    score_delta = float(actual_score) - float(expected_score if expected_score is not None else actual_score)
    impact_observation = incoming.score_impact + (score_delta * 0.35)
    score_impact = existing.score_impact + ((impact_observation - existing.score_impact) / support)
    confidence_direction = 0.035 if score_delta >= -0.015 else -0.055
    confidence = max(0.02, min(0.98, (existing.confidence * CONFIDENCE_DECAY) + confidence_direction + (0.01 if actual_score >= 0.78 else 0.0)))
    return PatternRule(
        rule_id=existing.rule_id,
        condition=existing.condition,
        action=existing.action,
        score_impact=round(score_impact, 4),
        confidence=round(confidence, 4),
        support=support,
        style=existing.style,
        tags=existing.tags,
        usage_count=existing.usage_count,
        last_seen=utc_now(),
    )


def add_or_update_patterns(
    memory: LearningMemory,
    rules: list[PatternRule],
    *,
    actual_score: float,
    expected_score: float | None = None,
) -> list[dict[str, Any]]:
    updates: list[dict[str, Any]] = []
    for rule in rules:
        existing_payload = memory.pattern_rules.get(rule.rule_id)
        existing = PatternRule.from_dict(existing_payload) if existing_payload else None
        merged = _merge_rule(existing, rule, actual_score=actual_score, expected_score=expected_score)
        memory.pattern_rules[merged.rule_id] = merged.to_dict()
        updates.append({"rule_id": merged.rule_id, "confidence": merged.confidence, "score_impact": merged.score_impact, "support": merged.support})
    return updates


def record_score(
    memory: LearningMemory,
    *,
    score: float,
    metrics: Mapping[str, float],
    context_summary: Mapping[str, Any],
    expected_score: float | None = None,
) -> dict[str, Any]:
    entry = {
        "timestamp": utc_now(),
        "total_score": round(float(score), 4),
        "expected_score": round(float(expected_score), 4) if expected_score is not None else None,
        "delta": round(float(score) - float(expected_score), 4) if expected_score is not None else 0.0,
        "metrics": {str(key): round(float(value), 4) for key, value in metrics.items()},
        "context": dict(context_summary),
    }
    memory.scoring_history.append(entry)
    memory.scoring_history = memory.scoring_history[-MAX_HISTORY:]
    scores = [float(item.get("total_score", 0.0) or 0.0) for item in memory.scoring_history]
    memory.success_metrics = {
        "sequence_count": len(scores),
        "average_score": round(mean(scores), 4) if scores else 0.0,
        "best_score": round(max(scores), 4) if scores else 0.0,
        "last_delta": entry["delta"],
    }
    return entry


def add_context_outcome(memory: LearningMemory, *, context: Mapping[str, Any], outcome: Mapping[str, Any]) -> None:
    memory.context_outcome_mappings.append(
        {
            "timestamp": utc_now(),
            "context": dict(context),
            "outcome": dict(outcome),
        }
    )
    memory.context_outcome_mappings = memory.context_outcome_mappings[-MAX_HISTORY:]


def prune_weak_patterns(memory: LearningMemory, *, min_confidence: float = 0.12, min_support: int = 1, max_rules: int = MAX_RULES) -> dict[str, Any]:
    before = len(memory.pattern_rules)
    survivors = [
        PatternRule.from_dict(payload)
        for payload in memory.pattern_rules.values()
        if float(payload.get("confidence", 0.0) or 0.0) >= min_confidence and int(payload.get("support", 0) or 0) >= min_support
    ]
    survivors.sort(key=lambda rule: (rule.confidence * max(1, rule.support), abs(rule.score_impact)), reverse=True)
    memory.pattern_rules = {rule.rule_id: rule.to_dict() for rule in survivors[:max_rules]}
    return {"before": before, "after": len(memory.pattern_rules), "removed": before - len(memory.pattern_rules)}


def mark_rules_used(memory: LearningMemory, rule_ids: list[str]) -> None:
    for rule_id in rule_ids:
        payload = memory.pattern_rules.get(rule_id)
        if not payload:
            continue
        rule = PatternRule.from_dict(payload)
        memory.pattern_rules[rule_id] = PatternRule(
            **{
                **rule.to_dict(),
                "usage_count": rule.usage_count + 1,
                "confidence": round(max(0.02, rule.confidence * (0.995 if rule.usage_count > 6 else 1.0)), 4),
                "last_seen": utc_now(),
            }
        ).to_dict()


def append_debug(memory: LearningMemory, event: str, payload: Mapping[str, Any]) -> None:
    memory.debug_log.append({"timestamp": utc_now(), "event": str(event), "payload": dict(payload)})
    memory.debug_log = memory.debug_log[-MAX_HISTORY:]
