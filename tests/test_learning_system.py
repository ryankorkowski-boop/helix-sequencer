from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from core import self_improving_scoring as scoring
from learning import feature_extractor, feedback_loop, memory, pattern_engine, style_learning, variation_tester


def _payload(score: float = 92.0, *, label: str = "winner", style: str = "edm") -> dict:
    return {
        "label": label,
        "version": "v27.3",
        "duration_seconds": 120.0,
        "profile": {"darkness": 0.8},
        "style_profile": {"name": style, "effect_density": 0.86},
        "runtime_tuning": {"palette_mode": "template", "layering_mode": "smart_layer"},
        "advanced_audio": {"tempo_bpm": 128.0, "genre_hint": style, "mood_hint": "energetic", "percussive_ratio": 0.8},
        "placements": {"strobe_burst": 24, "motion_sweep": 18, "chorus_hook": 16, "matrix_shader": 10},
        "effect_layering": {
            "layered_effects": [
                {"model": "Matrix", "effect": "Shader", "layer_role": "base", "blend_mode": "Normal", "intensity": 0.7},
                {"model": "Matrix", "effect": "Wave", "layer_role": "motion", "blend_mode": "Screen", "intensity": 0.8},
                {"model": "Tree", "effect": "On", "layer_role": "accent", "blend_mode": "Additive", "intensity": 0.9},
            ],
            "layering_logs": [{"action": "composited"}],
        },
        "spatial_mapping": {
            "mapping_logs": [
                {"source": "point", "mapped_category": "tree", "effect": "Spirals"},
                {"source": "trajectory", "mapped_category": "matrix", "effect": "Shader"},
                {"source": "energy_field", "mapped_category": "arch", "effect": "Wave"},
            ],
            "coverage_visualization": {"coverage_by_type": {"tree": 3, "matrix": 4, "arch": 2}},
        },
        "polish": {"score": score, "palette_swaps": 2},
        "quality": {
            "score": score,
            "coverage_ratio": 0.76,
            "dominant_family_ratio": 0.28,
            "component_scores": {
                "density": score - 4,
                "structure": score,
                "validation": score,
                "coverage": score - 2,
                "family_diversity": score - 5,
                "dominance": score - 3,
            },
        },
        "audit": {
            "final": {
                "score": score,
                "musical_coherence": score,
                "intensity_balance": score - 3,
                "section_coverage": 0.82,
                "clutter_ratio": 0.05,
                "section_scores": [
                    {"label": "VERSE", "start_ms": 0, "end_ms": 1000, "energy": 0.42, "score": score - 4, "coverage_ratio": 0.58, "density": 0.45},
                    {"label": "CHORUS", "start_ms": 1000, "end_ms": 2000, "energy": 0.9, "score": score, "coverage_ratio": 0.86, "density": 0.84},
                    {"label": "DROP", "start_ms": 2000, "end_ms": 3000, "energy": 0.95, "score": score - 1, "coverage_ratio": 0.9, "density": 0.9},
                ],
            }
        },
        "watermark": {"version": scoring.HELIX_WATERMARK_POLICY_VERSION, "signature": "helix-test"},
    }


class LearningSystemTests(unittest.TestCase):
    def test_feature_extractor_rejects_non_helix_payloads(self) -> None:
        payload = _payload()
        payload["watermark"] = {}

        with self.assertRaises(ValueError):
            feature_extractor.extract_features_from_payload(payload)

    def test_feedback_loop_stores_abstract_patterns_not_sequence_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            memory_path = Path(tmp) / "learning.json"
            result = feedback_loop.update_learning_from_sequence(
                memory_path=memory_path,
                payload=_payload(),
                expected_score=0.72,
            )
            stored = json.loads(memory_path.read_text(encoding="utf-8"))

            self.assertTrue(result["stored"])
            self.assertGreater(result["patterns_extracted"], 0)
            self.assertTrue(stored["source_policy"]["stores_full_sequences"] is False)
            self.assertTrue(stored["pattern_rules"])
            stored_text = json.dumps(stored)
            self.assertNotIn("ElementEffects", stored_text)
            self.assertNotIn("xlights_rgbeffects", stored_text)
            self.assertNotIn("startTime", stored_text)

    def test_pattern_engine_produces_decision_bias_from_memory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            memory_path = Path(tmp) / "learning.json"
            feedback_loop.update_learning_from_sequence(memory_path=memory_path, payload=_payload(), expected_score=0.65)

            decision = feedback_loop.learned_decision_score(
                memory_path=memory_path,
                base_score=0.5,
                context={"tempo": "fast_tempo", "energy": "high"},
                candidate_action={"effect_behavior": "short_bursts_and_rapid_motion"},
            )

            self.assertGreater(decision["matched_rule_count"], 0)
            self.assertGreater(decision["decision_score"], decision["base_score"])

    def test_learning_memory_prunes_weak_patterns(self) -> None:
        loaded = memory.LearningMemory()
        weak = pattern_engine.PatternRule(
            rule_id="weak",
            condition={"energy": "low"},
            action={"effect_behavior": "minimal"},
            score_impact=-0.1,
            confidence=0.05,
        )
        strong = pattern_engine.PatternRule(
            rule_id="strong",
            condition={"energy": "high"},
            action={"effect_behavior": "wide_motion"},
            score_impact=0.1,
            confidence=0.7,
        )
        loaded.pattern_rules = {"weak": weak.to_dict(), "strong": strong.to_dict()}

        result = memory.prune_weak_patterns(loaded, min_confidence=0.1)

        self.assertEqual(result["removed"], 1)
        self.assertNotIn("weak", loaded.pattern_rules)
        self.assertIn("strong", loaded.pattern_rules)

    def test_variation_tester_ranks_and_stores_winner(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            memory_path = Path(tmp) / "learning.json"
            high = _payload(94.0, label="bright_drop")
            low = _payload(68.0, label="flat_drop")
            low["quality"]["dominant_family_ratio"] = 0.82
            low["audit"]["final"]["clutter_ratio"] = 0.3

            result = variation_tester.compare_and_store_variations(
                memory_path=memory_path,
                segment_context={"section": "drop", "tempo": "fast_tempo"},
                variations=[low, high],
            )
            loaded = memory.load_memory(memory_path)

            self.assertEqual(result["winner"]["label"], "bright_drop")
            self.assertTrue(loaded.context_outcome_mappings)
            self.assertTrue(loaded.decision_preferences)

    def test_style_learning_returns_refinement_biases(self) -> None:
        loaded = memory.LearningMemory()
        style_learning.update_style_tendencies(loaded, style="EDM", pattern_ids=["a", "b", "a"], score=0.91)

        refinement = style_learning.style_refinement(loaded, "edm")

        self.assertEqual(refinement["style"], "edm")
        self.assertEqual(refinement["sample_count"], 1)
        self.assertIn("a", refinement["preferred_patterns"])


if __name__ == "__main__":
    unittest.main()
