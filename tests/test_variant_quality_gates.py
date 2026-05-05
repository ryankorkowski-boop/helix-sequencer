from __future__ import annotations

import unittest

from tools.build_helpers.variants import (
    DEFAULT_VENDOR_MAX_REJECTED_EFFECTS,
    DEFAULT_VENDOR_MIN_AUDIT_SCORE,
    DEFAULT_VENDOR_MIN_QUALITY_SCORE,
    choose_best_candidate,
    evaluate_quality_gates,
)


def _entry(
    *,
    quality: float = 92.0,
    audit: float = 86.0,
    rejected: int = 1000,
    self_score: float = 0.82,
    structure: float = 84.0,
    coverage: float = 82.0,
    detail: float = 78.0,
    family_diversity: float = 80.0,
    dominance: float = 82.0,
    musical_coherence: float = 88.0,
    section_coverage: float = 0.85,
    overlap_ratio: float = 0.02,
    clutter_ratio: float = 0.06,
    label: str = "candidate",
) -> dict[str, object]:
    return {
        "label": label,
        "output_path": f"{label}.xsq",
        "report_path": f"{label}.report.json",
        "notes_path": f"{label}.sequence_notes.txt",
        "quality": {
            "score": quality,
            "component_scores": {
                "structure": structure,
                "coverage": coverage,
                "detail": detail,
                "family_diversity": family_diversity,
                "dominance": dominance,
            },
        },
        "audit": {
            "final": {
                "score": audit,
                "musical_coherence": musical_coherence,
                "section_coverage": section_coverage,
                "overlap_ratio": overlap_ratio,
                "clutter_ratio": clutter_ratio,
            }
        },
        "self_improving_scoring": {"total_score": self_score},
        "polish": {"score": 84.0, "hook_enhancements": 4, "breathing_fades": 3, "palette_swaps": 3},
        "validation": {"rejected_effects_count": rejected},
    }


class VariantQualityGateTests(unittest.TestCase):
    def test_evaluate_quality_gates_passes_balanced_candidate(self) -> None:
        result = evaluate_quality_gates(_entry(), min_quality_score=90.0, min_audit_score=80.0, max_rejected_effects=12000)

        self.assertTrue(result["passed"])
        self.assertEqual(result["reasons"], [])
        self.assertEqual(result["quality_score"], 92.0)
        self.assertEqual(result["audit_score"], 86.0)

    def test_evaluate_quality_gates_rejects_low_quality_audit_and_rejections(self) -> None:
        result = evaluate_quality_gates(
            _entry(quality=75.0, audit=70.0, rejected=50000),
            min_quality_score=90.0,
            min_audit_score=80.0,
            max_rejected_effects=12000,
        )

        self.assertFalse(result["passed"])
        self.assertIn("quality_below_threshold<90.0", result["reasons"])
        self.assertIn("audit_below_threshold<80.0", result["reasons"])
        self.assertIn("rejected_effects_above_threshold>12000", result["reasons"])

    def test_vendor_defaults_are_stricter_than_general_defaults(self) -> None:
        result = evaluate_quality_gates(
            _entry(quality=95.0, audit=89.0, rejected=13000),
            min_quality_score=DEFAULT_VENDOR_MIN_QUALITY_SCORE,
            min_audit_score=DEFAULT_VENDOR_MIN_AUDIT_SCORE,
            max_rejected_effects=DEFAULT_VENDOR_MAX_REJECTED_EFFECTS,
        )

        self.assertFalse(result["passed"])
        self.assertIn("quality_below_threshold<96.0", result["reasons"])
        self.assertIn("audit_below_threshold<90.0", result["reasons"])
        self.assertIn("rejected_effects_above_threshold>12000", result["reasons"])

    def test_choose_best_candidate_prefers_gate_pass_over_raw_score(self) -> None:
        flashy_fail = _entry(
            quality=99.0,
            audit=92.0,
            rejected=50000,
            label="flashy_fail",
            overlap_ratio=0.01,
            clutter_ratio=0.02,
        )
        cleaner_pass = _entry(
            quality=91.0,
            audit=84.0,
            rejected=1000,
            label="cleaner_pass",
            overlap_ratio=0.02,
            clutter_ratio=0.06,
        )

        best = choose_best_candidate(
            [flashy_fail, cleaner_pass],
            min_quality_score=90.0,
            min_audit_score=80.0,
            max_rejected_effects=12000,
        )

        self.assertIsNotNone(best)
        self.assertEqual(best["label"], "cleaner_pass")
        self.assertTrue(best["quality_gate_passed"])

    def test_choose_best_candidate_rewards_musical_coherence_and_coverage(self) -> None:
        technically_dense = _entry(
            quality=92.0,
            audit=84.0,
            label="dense",
            musical_coherence=80.0,
            section_coverage=0.62,
            overlap_ratio=0.08,
            clutter_ratio=0.16,
        )
        musical = _entry(
            quality=92.0,
            audit=84.0,
            label="musical",
            musical_coherence=92.0,
            section_coverage=0.92,
            overlap_ratio=0.02,
            clutter_ratio=0.05,
        )

        best = choose_best_candidate(
            [technically_dense, musical],
            min_quality_score=90.0,
            min_audit_score=80.0,
            max_rejected_effects=12000,
        )

        self.assertIsNotNone(best)
        self.assertEqual(best["label"], "musical")
        self.assertGreater(float(best["shortlist_score"]), 0.0)


if __name__ == "__main__":
    unittest.main()
