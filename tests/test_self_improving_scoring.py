from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from core import self_improving_scoring as scoring


def _payload(score: float = 90.0) -> dict:
    return {
        "version": "v27.3",
        "placement_mode": "showcase_signature",
        "output": "song,v27.3.xsq",
        "duration_seconds": 120.0,
        "profile": {"darkness": 1.0},
        "runtime_tuning": {"chase_style": "wave", "palette_mode": "template"},
        "advanced_audio": {"tempo_bpm": 128.0, "genre_hint": "pop", "mood_hint": "energetic"},
        "placements": {"chorus_hook": 120, "verse_foundation": 80, "drop_focus": 40},
        "quality": {
            "score": score,
            "coverage_ratio": 0.42,
            "dominant_family_ratio": 0.28,
            "component_scores": {
                "density": 86.0,
                "structure": 92.0,
                "validation": 94.0,
                "coverage": 88.0,
                "family_diversity": 84.0,
                "dominance": 90.0,
            },
        },
        "audit": {
            "final": {
                "score": score,
                "musical_coherence": 91.0,
                "intensity_balance": 89.0,
                "section_coverage": 0.86,
                "clutter_ratio": 0.04,
                "section_scores": [
                    {
                        "label": "CHORUS",
                        "start_ms": 0,
                        "end_ms": 1000,
                        "energy": 0.9,
                        "score": 91.0,
                        "coverage_ratio": 0.8,
                        "density": 1.0,
                    }
                ],
            }
        },
        "watermark": {
            "version": scoring.HELIX_WATERMARK_POLICY_VERSION,
            "signature": "abc123",
        },
    }


class SelfImprovingScoringTests(unittest.TestCase):
    def test_metrics_are_normalized_and_composite_is_weighted(self) -> None:
        result = scoring.score_sequence(_payload())

        self.assertGreater(result.total_score, 0.0)
        self.assertLessEqual(result.total_score, 1.0)
        self.assertEqual(set(result.metrics), set(scoring.DEFAULT_METRIC_WEIGHTS))
        self.assertTrue(all(0.0 <= value <= 1.0 for value in result.metrics.values()))
        self.assertAlmostEqual(sum(result.weights.values()), 1.0, places=6)

    def test_variation_plan_caps_generation_cost(self) -> None:
        plan = scoring.plan_variations(99, labels=["a", "b", "c"], max_variations=4)

        self.assertEqual(plan.requested_count, 99)
        self.assertEqual(plan.capped_count, 4)
        self.assertEqual(plan.max_variations, 4)

    def test_ranking_and_ab_comparison(self) -> None:
        first = _payload(94.0)
        second = _payload(76.0)
        second["quality"]["component_scores"]["coverage"] = 45.0
        ranking = scoring.rank_sequence_payloads([{"label": "a", "payload": first}, {"label": "b", "payload": second}])
        comparison = scoring.compare_sequences(first, second)

        self.assertEqual(ranking[0]["label"], "a")
        self.assertEqual(comparison["winner"], "first")
        self.assertGreater(comparison["score_delta"], 0.0)

    def test_learning_memory_refuses_non_helix_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            memory_path = Path(tmp) / "memory.json"
            payload = _payload()
            payload["watermark"] = {}
            result = scoring.record_learning_decision(
                memory_path=memory_path,
                payload=payload,
                decision="signature",
            )

            self.assertFalse(result["stored"])
            self.assertEqual(result["skipped_reason"], "non_helix_generated_source")
            self.assertFalse(memory_path.exists())

    def test_learning_memory_stores_decisions_and_style_memory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            memory_path = Path(tmp) / "memory.json"
            result = scoring.record_learning_decision(
                memory_path=memory_path,
                payload=_payload(),
                decision="signature",
                rejected=[{"label": "alt", "total_score": 0.5}],
            )
            memory = scoring.load_learning_memory(memory_path)

            self.assertTrue(result["stored"])
            self.assertEqual(memory["summary"]["decision_count"], 1)
            self.assertTrue(memory["style_memory"]["successful_patterns"])
            self.assertTrue(memory["source_policy"]["helix_generated_only"])


if __name__ == "__main__":
    unittest.main()
