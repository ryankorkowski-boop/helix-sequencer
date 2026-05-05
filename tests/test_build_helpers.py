from __future__ import annotations

import unittest
from pathlib import Path

from core import effect_engine
from core import model_parser as xmp
from tools.build_helpers import (
    DEFAULT_MAX_REJECTED_EFFECTS,
    DEFAULT_MIN_AUDIT_SCORE,
    DEFAULT_MIN_QUALITY_SCORE,
    DEFAULT_VENDOR_MAX_REJECTED_EFFECTS,
    DEFAULT_VENDOR_MIN_AUDIT_SCORE,
    DEFAULT_VENDOR_MIN_QUALITY_SCORE,
    build_neighbor_graph,
    build_runtime_candidates,
    choose_best_candidate,
    collect_coverage_targets,
    evaluate_quality_gates,
    expand_neighbor_targets,
)


def _model(name: str, *, model_type: str, x: float, y: float = 0.0) -> xmp.Model:
    return xmp.Model(
        name=name,
        display_as=model_type,
        type=model_type,
        strings=8,
        nodes_per_string=25,
        total_pixels=200,
        start_channel=None,
        coordinates=(x, y, 0.0),
        end_coordinates=(x + 5.0, y + 15.0, 0.0),
        orientation="horizontal",
        wiring=None,
        string_type="RGB Nodes",
        color_family="rgb",
    )


class BuildHelperTests(unittest.TestCase):
    def _layout(self) -> xmp.ParsedLayout:
        models = {
            "Mega 1": _model("Mega 1", model_type="tree", x=0.0),
            "Mega 2": _model("Mega 2", model_type="tree", x=20.0),
            "Garage Tree": _model("Garage Tree", model_type="tree", x=35.0),
            "Matrix 1": _model("Matrix 1", model_type="matrix", x=50.0),
        }
        return xmp.ParsedLayout(path=Path("layout.xml"), models=models, groups={}, aliases={})

    def test_collect_coverage_targets_prefers_unused_families(self) -> None:
        plan = collect_coverage_targets(
            parsed_layout=self._layout(),
            available_layer_names=["Mega 1", "Mega 2", "Garage Tree", "Matrix 1"],
            used_root_models={"Mega 1"},
            model_category_map={},
            limit=3,
        )
        self.assertIn("Matrix 1", plan.uncovered_models)
        self.assertNotIn("Mega 1", plan.recommended_targets)
        self.assertGreaterEqual(len(plan.family_counts), 2)

    def test_neighbor_graph_expands_adjacent_models(self) -> None:
        graph = build_neighbor_graph(self._layout(), available_names=["Mega 1", "Mega 2", "Garage Tree"])
        self.assertEqual(graph.routes["mega"], ["Mega 1", "Mega 2"])
        self.assertEqual(graph.seed_targets("mega", limit=1), ["Mega 1"])
        self.assertEqual(expand_neighbor_targets(graph, ["Mega 1"], depth=1, limit=2), ["Mega 2"])

    def test_runtime_candidates_and_shortlist_scoring(self) -> None:
        candidates = build_runtime_candidates(
            effect_engine.VARIANTS[effect_engine.ACTIVE_STYLE_VERSION],
            effect_engine.RuntimeTuning(),
            5,
        )
        self.assertEqual(
            [candidate.label for candidate in candidates],
            ["signature", "hook_focus", "wide_stage", "stem_story", "cinematic_arc"],
        )
        best = choose_best_candidate(
            [
                {
                    "label": "signature",
                    "quality": {
                        "score": 90.0,
                        "component_scores": {"structure": 88.0, "coverage": 84.0, "detail": 80.0, "family_diversity": 82.0, "dominance": 85.0},
                    },
                    "audit": {
                        "initial": {"score": 82.0},
                        "final": {"score": 88.0, "musical_coherence": 89.0, "section_coverage": 0.84, "overlap_ratio": 0.03, "clutter_ratio": 0.09},
                    },
                    "validation": {"rejected_effects_count": 16000},
                    "polish": {"score": 90.0, "hook_enhancements": 4, "breathing_fades": 2, "palette_swaps": 3},
                },
                {
                    "label": "wide_stage",
                    "quality": {
                        "score": 87.0,
                        "component_scores": {"structure": 82.0, "coverage": 80.0, "detail": 74.0, "family_diversity": 78.0, "dominance": 80.0},
                    },
                    "audit": {"score": 84.0, "musical_coherence": 84.0, "section_coverage": 0.77, "overlap_ratio": 0.05, "clutter_ratio": 0.12},
                    "validation": {"rejected_effects_count": 21000},
                    "polish": {"score": 84.0, "hook_enhancements": 1, "breathing_fades": 0, "palette_swaps": 0},
                },
                {
                    "label": "cinematic_arc",
                    "quality": {
                        "score": 89.0,
                        "component_scores": {"structure": 93.0, "coverage": 90.0, "detail": 85.0, "family_diversity": 88.0, "dominance": 90.0},
                    },
                    "audit": {
                        "initial": {"score": 86.0},
                        "final": {"score": 91.0, "musical_coherence": 95.0, "section_coverage": 0.92, "overlap_ratio": 0.01, "clutter_ratio": 0.05},
                    },
                    "validation": {"rejected_effects_count": 12000},
                    "polish": {"score": 92.0, "hook_enhancements": 3, "breathing_fades": 3, "palette_swaps": 4},
                },
            ]
        )
        self.assertIsNotNone(best)
        self.assertEqual(best["label"], "cinematic_arc")
        self.assertGreater(best["shortlist_score"], 70.0)
        self.assertTrue(best["quality_gate_passed"])

    def test_evaluate_quality_gates_reads_nested_audit_and_validation(self) -> None:
        verdict = evaluate_quality_gates(
            {
                "audit": {"initial": {"score": 70.0}, "final": {"score": 92.0}},
                "validation": {"rejected_effects_count": 15000},
            }
        )
        self.assertTrue(verdict["passed"])
        self.assertEqual(verdict["reasons"], [])

    def test_evaluate_quality_gates_blocks_low_audit_or_high_rejections(self) -> None:
        low_audit = evaluate_quality_gates(
            {
                "audit": {"final": {"score": DEFAULT_MIN_AUDIT_SCORE - 1.0}},
                "validation": {"rejected_effects_count": 12000},
            }
        )
        self.assertFalse(low_audit["passed"])
        self.assertIn("audit_below_threshold", low_audit["reasons"][0])

        high_rejections = evaluate_quality_gates(
            {
                "audit": {"final": {"score": DEFAULT_MIN_AUDIT_SCORE + 5.0}},
                "validation": {"rejected_effects_count": DEFAULT_MAX_REJECTED_EFFECTS + 1},
                "quality": {"score": DEFAULT_MIN_QUALITY_SCORE + 2.0},
            }
        )
        self.assertFalse(high_rejections["passed"])
        self.assertIn("rejected_effects_above_threshold", high_rejections["reasons"][0])

    def test_evaluate_quality_gates_can_enforce_quality_threshold(self) -> None:
        verdict = evaluate_quality_gates(
            {
                "quality": {"score": DEFAULT_VENDOR_MIN_QUALITY_SCORE - 0.5},
                "audit": {"final": {"score": DEFAULT_VENDOR_MIN_AUDIT_SCORE + 1.0}},
                "validation": {"rejected_effects_count": DEFAULT_VENDOR_MAX_REJECTED_EFFECTS - 10},
            },
            min_quality_score=DEFAULT_VENDOR_MIN_QUALITY_SCORE,
            min_audit_score=DEFAULT_VENDOR_MIN_AUDIT_SCORE,
            max_rejected_effects=DEFAULT_VENDOR_MAX_REJECTED_EFFECTS,
        )
        self.assertFalse(verdict["passed"])
        self.assertIn("quality_below_threshold", verdict["reasons"][0])

    def test_choose_best_candidate_respects_vendor_thresholds(self) -> None:
        best = choose_best_candidate(
            [
                {
                    "label": "high_quality_but_fails_vendor",
                    "quality": {"score": 98.0, "component_scores": {}},
                    "audit": {"final": {"score": 86.0}},
                    "validation": {"rejected_effects_count": 9000},
                    "polish": {"score": 95.0},
                },
                {
                    "label": "passes_vendor",
                    "quality": {"score": 96.5, "component_scores": {}},
                    "audit": {"final": {"score": 92.0}},
                    "validation": {"rejected_effects_count": 7000},
                    "polish": {"score": 93.0},
                },
            ],
            min_quality_score=DEFAULT_VENDOR_MIN_QUALITY_SCORE,
            min_audit_score=DEFAULT_VENDOR_MIN_AUDIT_SCORE,
            max_rejected_effects=DEFAULT_VENDOR_MAX_REJECTED_EFFECTS,
        )
        self.assertIsNotNone(best)
        self.assertEqual(best["label"], "passes_vendor")
        self.assertTrue(best["quality_gate_passed"])


if __name__ == "__main__":
    unittest.main()
