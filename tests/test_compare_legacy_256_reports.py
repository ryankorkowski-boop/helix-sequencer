from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.compare_legacy_256_reports import compare_reports, main, summarize_report


def _report(
    *,
    quality: float,
    audit: float,
    rejected: int,
    musical: float,
    section: float,
    clutter: float,
    overlap: float,
    coverage: float = 84.0,
    structure: float = 86.0,
    family: float = 80.0,
    shortlist: float = 82.0,
) -> dict[str, object]:
    return {
        "quality": {
            "score": quality,
            "component_scores": {
                "coverage": coverage,
                "structure": structure,
                "family_diversity": family,
            },
        },
        "audit": {
            "final": {
                "score": audit,
                "musical_coherence": musical,
                "section_coverage": section,
                "clutter_ratio": clutter,
                "overlap_ratio": overlap,
            }
        },
        "validation": {"rejected_effects_count": rejected},
        "shortlist": {"score": shortlist},
    }


class CompareLegacy256ReportsTests(unittest.TestCase):
    def test_summarize_report_extracts_key_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "showcase.report.json"
            path.write_text(json.dumps(_report(quality=94, audit=88, rejected=1500, musical=91, section=0.9, clutter=0.04, overlap=0.02)), encoding="utf-8")
            summary = summarize_report(path)

        self.assertEqual(summary.label, "showcase")
        self.assertEqual(summary.quality_score, 94.0)
        self.assertEqual(summary.audit_score, 88.0)
        self.assertEqual(summary.rejected_effects, 1500)
        self.assertGreater(summary.comparison_score, 0.0)

    def test_compare_reports_prefers_clean_musical_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            messy = tmp_path / "messy.report.json"
            clean = tmp_path / "clean.report.json"
            messy.write_text(json.dumps(_report(quality=96, audit=88, rejected=24000, musical=82, section=0.65, clutter=0.2, overlap=0.12)), encoding="utf-8")
            clean.write_text(json.dumps(_report(quality=93, audit=88, rejected=1200, musical=93, section=0.92, clutter=0.04, overlap=0.02)), encoding="utf-8")

            comparison = compare_reports([messy, clean])

        self.assertEqual(comparison.winner, "clean")
        self.assertEqual(comparison.summaries[0]["label"], "clean")
        self.assertGreater(comparison.summaries[0]["comparison_score"], comparison.summaries[1]["comparison_score"])
        self.assertTrue(comparison.summaries[1]["warnings"])

    def test_main_writes_comparison_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            report = tmp_path / "clean.report.json"
            output = tmp_path / "comparison.json"
            report.write_text(json.dumps(_report(quality=93, audit=88, rejected=1200, musical=93, section=0.92, clutter=0.04, overlap=0.02)), encoding="utf-8")

            code = main([str(report), "--output", str(output)])
            payload = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(payload["schema"], "helix.legacy_256_comparison.v1")
        self.assertEqual(payload["winner"], "clean")


if __name__ == "__main__":
    unittest.main()
