from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from core import self_improving_scoring as scoring
from learning import feature_extractor, pattern_engine
from learning.memory import add_context_outcome, append_debug, assert_helix_generated, load_memory, save_memory


def score_variations(variations: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    ranked: list[dict[str, Any]] = []
    for idx, payload in enumerate(variations):
        assert_helix_generated(payload)
        label = str(payload.get("label", payload.get("version", f"variation_{idx + 1}")) or f"variation_{idx + 1}")
        sequence_score = scoring.score_sequence(dict(payload))
        features = feature_extractor.extract_features_from_payload(payload)
        rules = pattern_engine.encode_patterns(features)
        ranked.append(
            {
                "label": label,
                "total_score": round(sequence_score.total_score, 4),
                "metrics": {key: round(value, 4) for key, value in sequence_score.metrics.items()},
                "context": {
                    "tempo_bucket": features.musical.tempo_bucket,
                    "style_hint": features.musical.style_hint,
                    "genre_hint": features.musical.genre_hint,
                },
                "abstract_actions": [rule.action for rule in rules[:8]],
                "rule_ids": [rule.rule_id for rule in rules[:12]],
            }
        )
    ranked.sort(key=lambda item: (-float(item["total_score"]), str(item["label"])))
    return ranked


def compare_and_store_variations(
    *,
    memory_path: Path,
    segment_context: Mapping[str, Any],
    variations: list[Mapping[str, Any]],
) -> dict[str, Any]:
    ranked = score_variations(variations)
    memory = load_memory(memory_path)
    winner = ranked[0] if ranked else {}
    failures = ranked[1:]
    add_context_outcome(
        memory,
        context={"segment": dict(segment_context), "variation_count": len(ranked)},
        outcome={
            "winner": winner.get("label", ""),
            "winner_score": winner.get("total_score", 0.0),
            "failed_variations": [
                {"label": item["label"], "score": item["total_score"], "rule_ids": item["rule_ids"][:5]}
                for item in failures[:8]
            ],
        },
    )
    if winner:
        for rule_id in winner.get("rule_ids", []):
            memory.decision_preferences[rule_id] = round(float(memory.decision_preferences.get(rule_id, 0.0)) + 0.035, 4)
        for item in failures:
            for rule_id in item.get("rule_ids", []):
                memory.decision_preferences[rule_id] = round(float(memory.decision_preferences.get(rule_id, 0.0)) - 0.018, 4)
    append_debug(
        memory,
        "variation_test",
        {
            "segment_context": dict(segment_context),
            "ranking": ranked,
            "winner": winner.get("label", ""),
        },
    )
    save_memory(memory_path, memory)
    return {
        "winner": winner,
        "ranking": ranked,
        "stored": True,
        "debug": {
            "what_worked_better": winner.get("abstract_actions", []),
            "what_failed": [
                {"label": item["label"], "score": item["total_score"], "abstract_actions": item["abstract_actions"][:3]}
                for item in failures[:4]
            ],
        },
    }
