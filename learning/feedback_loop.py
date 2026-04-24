from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from core import self_improving_scoring as scoring
from learning import feature_extractor, pattern_engine
from learning.memory import (
    add_context_outcome,
    add_or_update_patterns,
    append_debug,
    assert_helix_generated,
    load_memory,
    prune_weak_patterns,
    save_memory,
)


def _context_summary(features: feature_extractor.ExtractedSequenceFeatures) -> dict[str, Any]:
    return {
        "tempo_bucket": features.musical.tempo_bucket,
        "genre_hint": features.musical.genre_hint,
        "style_hint": features.musical.style_hint,
        "section_types": dict(features.musical.section_types),
        "dominant_elements": dict(features.musical.dominant_elements),
        "emotion_profile": dict(features.musical.emotion_profile),
    }


def update_learning_from_sequence(
    *,
    memory_path: Path,
    payload: Mapping[str, Any],
    expected_score: float | None = None,
    prune: bool = True,
) -> dict[str, Any]:
    assert_helix_generated(payload)
    memory = load_memory(memory_path)
    features = feature_extractor.extract_features_from_payload(payload)
    score = scoring.score_sequence(dict(payload))
    rules = pattern_engine.encode_patterns(features)
    context = _context_summary(features)

    from learning.memory import record_score

    recorded = record_score(
        memory,
        score=score.total_score,
        metrics=score.metrics,
        context_summary=context,
        expected_score=expected_score,
    )
    updates = add_or_update_patterns(memory, rules, actual_score=score.total_score, expected_score=expected_score)
    from learning.style_learning import update_style_tendencies

    style_update = update_style_tendencies(
        memory,
        style=features.musical.style_hint or features.musical.genre_hint,
        pattern_ids=[rule.rule_id for rule in rules],
        score=score.total_score,
    )
    add_context_outcome(
        memory,
        context=context,
        outcome={
            "score": round(score.total_score, 4),
            "expected_score": round(expected_score, 4) if expected_score is not None else None,
            "rule_count": len(rules),
        },
    )
    prune_result = prune_weak_patterns(memory) if prune else {"before": len(memory.pattern_rules), "after": len(memory.pattern_rules), "removed": 0}
    append_debug(
        memory,
        "feedback_update",
        {
            "actual_score": round(score.total_score, 4),
            "expected_score": round(expected_score, 4) if expected_score is not None else None,
            "patterns_updated": len(updates),
            "style": features.musical.style_hint or features.musical.genre_hint,
            "pruned": prune_result,
        },
    )
    save_memory(memory_path, memory)
    return {
        "stored": True,
        "memory_path": str(memory_path),
        "actual_score": round(score.total_score, 4),
        "expected_score": round(expected_score, 4) if expected_score is not None else None,
        "delta": recorded["delta"],
        "patterns_extracted": len(rules),
        "patterns_updated": updates,
        "style_learning": style_update,
        "prune": prune_result,
        "debug": {
            "features": features.to_dict(),
            "learned_patterns": [rule.to_dict() for rule in rules],
            "before_vs_after_scores": {"expected": expected_score, "actual": round(score.total_score, 4)},
        },
    }


def learned_decision_score(
    *,
    memory_path: Path,
    base_score: float,
    context: Mapping[str, Any],
    candidate_action: Mapping[str, Any],
    diversity_penalty: float = 0.0,
    randomness: float = 0.0,
) -> dict[str, Any]:
    memory = load_memory(memory_path)
    result = pattern_engine.learned_pattern_bias(
        base_score=base_score,
        context=context,
        candidate_action=candidate_action,
        pattern_rules=list(memory.pattern_rules.values()),
        diversity_penalty=diversity_penalty,
        randomness=randomness,
    )
    if result["matched_rules"]:
        from learning.memory import mark_rules_used

        mark_rules_used(memory, list(result["matched_rules"]))
        append_debug(memory, "decision_guidance", result)
        save_memory(memory_path, memory)
    return result
