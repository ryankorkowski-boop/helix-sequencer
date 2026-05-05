from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from statistics import mean
from typing import Any


LEARNING_MEMORY_SCHEMA_VERSION = 1
HELIX_WATERMARK_POLICY_VERSION = "dream-sequence-weaver-signature-v1"
DEFAULT_MAX_VARIATIONS = 8
DEFAULT_WEIGHT_ADJUSTMENT_RATE = 0.035


DEFAULT_METRIC_WEIGHTS: dict[str, float] = {
    "beat_alignment": 0.20,
    "visual_coherence": 0.18,
    "repetition_penalty": 0.12,
    "spatial_coverage": 0.16,
    "energy_balance": 0.18,
    "emotional_consistency": 0.16,
}


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _score01(value: Any) -> float:
    try:
        return clamp01(float(value) / 100.0)
    except Exception:
        return 0.0


def _ratio(value: Any) -> float:
    try:
        return clamp01(float(value))
    except Exception:
        return 0.0


def _normalized_weights(weights: dict[str, float] | None = None) -> dict[str, float]:
    source = dict(DEFAULT_METRIC_WEIGHTS)
    if weights:
        for key in source:
            if key in weights:
                source[key] = max(0.0, float(weights[key]))
    total = sum(source.values()) or 1.0
    return {key: value / total for key, value in source.items()}


def _payload_quality(payload: dict[str, Any]) -> dict[str, Any]:
    return (payload.get("quality") or {}) or {}


def _component_scores(payload: dict[str, Any]) -> dict[str, Any]:
    return (_payload_quality(payload).get("component_scores") or {}) or {}


def _final_audit(payload: dict[str, Any]) -> dict[str, Any]:
    return ((payload.get("audit") or {}).get("final") or {}) or {}


def _placements(payload: dict[str, Any]) -> dict[str, int]:
    placements = (payload.get("placements") or {}) or {}
    return {str(key): int(value or 0) for key, value in placements.items()}


def _style_key(payload: dict[str, Any]) -> str:
    return "|".join(
        item
        for item in (
            str(payload.get("version", "") or ""),
            str(payload.get("placement_mode", "") or ""),
            str(((payload.get("runtime_tuning") or {}) or {}).get("chase_style", "") or ""),
            str(((payload.get("runtime_tuning") or {}) or {}).get("palette_mode", "") or ""),
        )
        if item
    ) or "unknown"


def _top_placement_patterns(payload: dict[str, Any], limit: int = 6) -> list[str]:
    ordered = sorted(_placements(payload).items(), key=lambda item: (-item[1], item[0]))
    return [key for key, count in ordered[:limit] if count > 0]


def is_helix_generated_payload(payload: dict[str, Any]) -> bool:
    watermark = (payload.get("watermark") or {}) or {}
    if watermark.get("version") == HELIX_WATERMARK_POLICY_VERSION and watermark.get("signature"):
        return True
    responsible_use = (payload.get("responsible_use") or {}) or {}
    return bool(responsible_use.get("helix_generated_only", False))


def beat_alignment_score(payload: dict[str, Any]) -> float:
    audit = _final_audit(payload)
    components = _component_scores(payload)
    musical = _score01(audit.get("musical_coherence", 0.0))
    validation = _score01(components.get("validation", 0.0))
    return clamp01((musical * 0.70) + (validation * 0.30))


def visual_coherence_score(payload: dict[str, Any]) -> float:
    components = _component_scores(payload)
    audit = _final_audit(payload)
    structure = _score01(components.get("structure", 0.0))
    dominance = _score01(components.get("dominance", 0.0))
    clutter = 1.0 - _ratio(audit.get("clutter_ratio", 0.0))
    return clamp01((structure * 0.42) + (dominance * 0.30) + (clutter * 0.28))


def repetition_penalty_score(payload: dict[str, Any]) -> float:
    quality = _payload_quality(payload)
    components = _component_scores(payload)
    dominant = _ratio(quality.get("dominant_family_ratio", 0.0))
    diversity = _score01(components.get("family_diversity", 0.0))
    return clamp01(((1.0 - dominant) * 0.58) + (diversity * 0.42))


def spatial_coverage_score(payload: dict[str, Any]) -> float:
    quality = _payload_quality(payload)
    components = _component_scores(payload)
    coverage_ratio = _ratio(quality.get("coverage_ratio", 0.0))
    coverage_component = _score01(components.get("coverage", 0.0))
    audit_coverage = _ratio(_final_audit(payload).get("section_coverage", 0.0))
    return clamp01((coverage_ratio * 0.30) + (coverage_component * 0.45) + (audit_coverage * 0.25))


def energy_balance_score(payload: dict[str, Any]) -> float:
    audit = _final_audit(payload)
    components = _component_scores(payload)
    intensity = _score01(audit.get("intensity_balance", 0.0))
    density = _score01(components.get("density", 0.0))
    return clamp01((intensity * 0.72) + (density * 0.28))


def emotional_consistency_score(payload: dict[str, Any]) -> float:
    advanced_audio = (payload.get("advanced_audio") or {}) or {}
    runtime = (payload.get("runtime_tuning") or {}) or {}
    profile = (payload.get("profile") or {}) or {}
    mood = str(advanced_audio.get("mood_hint", "neutral") or "neutral").lower()
    darkness = _ratio(profile.get("darkness", 1.0)) / 1.95
    palette_mode = str(runtime.get("palette_mode", "template") or "template").lower()
    structure = _score01(_component_scores(payload).get("structure", 0.0))
    musical = _score01(_final_audit(payload).get("musical_coherence", 0.0))
    mood_fit = 0.76
    if any(token in mood for token in ("bright", "happy", "uplift", "dance", "energetic")):
        mood_fit = 1.0 - min(0.45, darkness * 0.45)
    elif any(token in mood for token in ("dark", "sad", "tense", "minor", "ambient")):
        mood_fit = 0.68 + min(0.30, darkness * 0.30)
    elif palette_mode in {"template", "workspace_match"}:
        mood_fit = 0.84
    return clamp01((mood_fit * 0.34) + (structure * 0.30) + (musical * 0.36))


def evaluate_metrics(payload: dict[str, Any]) -> dict[str, float]:
    return {
        "beat_alignment": beat_alignment_score(payload),
        "visual_coherence": visual_coherence_score(payload),
        "repetition_penalty": repetition_penalty_score(payload),
        "spatial_coverage": spatial_coverage_score(payload),
        "energy_balance": energy_balance_score(payload),
        "emotional_consistency": emotional_consistency_score(payload),
    }


def composite_score(metrics: dict[str, float], weights: dict[str, float] | None = None) -> float:
    normalized = _normalized_weights(weights)
    return clamp01(sum(clamp01(metrics.get(key, 0.0)) * weight for key, weight in normalized.items()))


@dataclass(frozen=True)
class SequenceScore:
    total_score: float
    metrics: dict[str, float]
    weights: dict[str, float]

    def as_dict(self) -> dict[str, Any]:
        return {
            "total_score": round(self.total_score, 4),
            "metrics": {key: round(value, 4) for key, value in self.metrics.items()},
            "weights": {key: round(value, 4) for key, value in self.weights.items()},
        }


def score_sequence(payload: dict[str, Any], weights: dict[str, float] | None = None) -> SequenceScore:
    normalized = _normalized_weights(weights)
    metrics = evaluate_metrics(payload)
    return SequenceScore(total_score=composite_score(metrics, normalized), metrics=metrics, weights=normalized)


@dataclass(frozen=True)
class VariationPlan:
    requested_count: int
    capped_count: int
    max_variations: int = DEFAULT_MAX_VARIATIONS
    labels: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "requested_count": self.requested_count,
            "capped_count": self.capped_count,
            "max_variations": self.max_variations,
            "labels": self.labels,
        }


def plan_variations(requested_count: int, labels: list[str] | None = None, max_variations: int = DEFAULT_MAX_VARIATIONS) -> VariationPlan:
    requested = max(1, int(requested_count))
    capped = min(max(1, int(max_variations)), requested)
    return VariationPlan(
        requested_count=requested,
        capped_count=capped,
        max_variations=max(1, int(max_variations)),
        labels=(labels or [])[:capped],
    )


def rank_sequence_payloads(
    entries: list[dict[str, Any]],
    weights: dict[str, float] | None = None,
) -> list[dict[str, Any]]:
    ranked: list[dict[str, Any]] = []
    for idx, entry in enumerate(entries):
        payload = entry.get("payload") if isinstance(entry.get("payload"), dict) else entry
        score = score_sequence(payload, weights)
        ranked.append(
            {
                "rank": 0,
                "label": str(entry.get("label", payload.get("output", f"candidate_{idx + 1}"))),
                "output": str(entry.get("output_path", payload.get("output", ""))),
                "style_version": str(entry.get("style_version", payload.get("version", ""))),
                "total_score": score.total_score,
                "metrics": score.metrics,
            }
        )
    ranked.sort(key=lambda item: float(item["total_score"]), reverse=True)
    for idx, item in enumerate(ranked, 1):
        item["rank"] = idx
        item["total_score"] = round(float(item["total_score"]), 4)
        item["metrics"] = {key: round(float(value), 4) for key, value in item["metrics"].items()}
    return ranked


def compare_sequences(first: dict[str, Any], second: dict[str, Any], weights: dict[str, float] | None = None) -> dict[str, Any]:
    first_score = score_sequence(first, weights)
    second_score = score_sequence(second, weights)
    metric_delta = {
        key: round(first_score.metrics.get(key, 0.0) - second_score.metrics.get(key, 0.0), 4)
        for key in DEFAULT_METRIC_WEIGHTS
    }
    return {
        "winner": "first" if first_score.total_score >= second_score.total_score else "second",
        "first_total_score": round(first_score.total_score, 4),
        "second_total_score": round(second_score.total_score, 4),
        "score_delta": round(first_score.total_score - second_score.total_score, 4),
        "metric_delta": metric_delta,
    }


def default_memory_payload() -> dict[str, Any]:
    return {
        "schema_version": LEARNING_MEMORY_SCHEMA_VERSION,
        "source_policy": {
            "helix_generated_only": True,
            "accepted_watermark_version": HELIX_WATERMARK_POLICY_VERSION,
        },
        "weights": dict(DEFAULT_METRIC_WEIGHTS),
        "decisions": [],
        "style_memory": {
            "successful_patterns": {},
            "failed_combinations": {},
        },
        "summary": {
            "decision_count": 0,
            "average_score": 0.0,
            "best_score": 0.0,
        },
    }


def load_learning_memory(path: Path) -> dict[str, Any]:
    if not path.exists():
        return default_memory_payload()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default_memory_payload()
    if int(payload.get("schema_version", 0) or 0) != LEARNING_MEMORY_SCHEMA_VERSION:
        return default_memory_payload()
    payload.setdefault("weights", dict(DEFAULT_METRIC_WEIGHTS))
    payload.setdefault("decisions", [])
    payload.setdefault("style_memory", {"successful_patterns": {}, "failed_combinations": {}})
    payload.setdefault("summary", {"decision_count": 0, "average_score": 0.0, "best_score": 0.0})
    payload.setdefault(
        "source_policy",
        {"helix_generated_only": True, "accepted_watermark_version": HELIX_WATERMARK_POLICY_VERSION},
    )
    return payload


def save_learning_memory(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _adjust_weights(
    current: dict[str, float],
    metrics: dict[str, float],
    total_score: float,
    baseline_score: float,
    rate: float = DEFAULT_WEIGHT_ADJUSTMENT_RATE,
) -> dict[str, float]:
    updated = _normalized_weights(current)
    direction = 1.0 if total_score >= baseline_score else -1.0
    metric_average = mean(metrics.values()) if metrics else 0.0
    for key in DEFAULT_METRIC_WEIGHTS:
        metric_delta = clamp01(metrics.get(key, 0.0)) - metric_average
        updated[key] = max(0.02, updated[key] + (direction * metric_delta * rate))
    return _normalized_weights(updated)


def record_learning_decision(
    *,
    memory_path: Path,
    payload: dict[str, Any],
    decision: str,
    rejected: list[dict[str, Any]] | None = None,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    memory = load_learning_memory(memory_path)
    score = score_sequence(payload, memory.get("weights", DEFAULT_METRIC_WEIGHTS))
    skipped_reason = ""
    if not is_helix_generated_payload(payload):
        skipped_reason = "non_helix_generated_source"
        return {
            "enabled": True,
            "stored": False,
            "skipped_reason": skipped_reason,
            "score": score.as_dict(),
            "memory_path": str(memory_path),
        }

    decisions = list(memory.get("decisions") or [])
    prior_scores = [float(item.get("total_score", 0.0) or 0.0) for item in decisions]
    baseline = mean(prior_scores) if prior_scores else score.total_score
    memory["weights"] = _adjust_weights(
        dict(memory.get("weights") or DEFAULT_METRIC_WEIGHTS),
        score.metrics,
        score.total_score,
        baseline,
    )

    style_key = _style_key(payload)
    patterns = _top_placement_patterns(payload)
    rejected_summaries = [
        {
            "label": str(item.get("label", "")),
            "output": str(item.get("output_path", "")),
            "total_score": float(item.get("total_score", 0.0) or 0.0),
        }
        for item in (rejected or [])[:12]
    ]
    entry = {
        "decision": decision,
        "output": str(payload.get("output", "")),
        "version": str(payload.get("version", "")),
        "style_key": style_key,
        "total_score": round(score.total_score, 4),
        "metrics": {key: round(value, 4) for key, value in score.metrics.items()},
        "context": context or {
            "tempo_bpm": ((payload.get("advanced_audio") or {}) or {}).get("tempo_bpm", 0.0),
            "genre_hint": ((payload.get("advanced_audio") or {}) or {}).get("genre_hint", "unknown"),
            "mood_hint": ((payload.get("advanced_audio") or {}) or {}).get("mood_hint", "neutral"),
            "duration_seconds": payload.get("duration_seconds", 0.0),
        },
        "patterns": patterns,
        "rejected_variations": rejected_summaries,
    }
    decisions.append(entry)
    memory["decisions"] = decisions[-250:]

    style_memory = memory.setdefault("style_memory", {"successful_patterns": {}, "failed_combinations": {}})
    successful = style_memory.setdefault("successful_patterns", {})
    failed = style_memory.setdefault("failed_combinations", {})
    target = successful if score.total_score >= baseline else failed
    for pattern in patterns:
        bucket = target.setdefault(pattern, {"count": 0, "average_score": 0.0, "styles": {}})
        count = int(bucket.get("count", 0)) + 1
        old_avg = float(bucket.get("average_score", 0.0) or 0.0)
        bucket["count"] = count
        bucket["average_score"] = round(old_avg + ((score.total_score - old_avg) / count), 4)
        styles = bucket.setdefault("styles", {})
        styles[style_key] = int(styles.get(style_key, 0)) + 1

    scores = [float(item.get("total_score", 0.0) or 0.0) for item in memory["decisions"]]
    memory["summary"] = {
        "decision_count": len(memory["decisions"]),
        "average_score": round(mean(scores), 4) if scores else 0.0,
        "best_score": round(max(scores), 4) if scores else 0.0,
    }
    save_learning_memory(memory_path, memory)
    return {
        "enabled": True,
        "stored": True,
        "skipped_reason": skipped_reason,
        "score": score.as_dict(),
        "memory_path": str(memory_path),
        "summary": memory["summary"],
        "updated_weights": {key: round(float(value), 4) for key, value in memory["weights"].items()},
    }
