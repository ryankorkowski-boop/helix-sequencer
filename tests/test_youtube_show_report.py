from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools import youtube_show_report


def sample_report() -> dict:
    return {
        "duration_seconds": 60,
        "effects_total": 1200,
        "quality": {
            "score": 91.0,
            "top_show_benchmark": {"score": 88.0},
        },
        "youtube_show_summary": {
            "sections": [
                {
                    "label": "verse",
                    "active_props": ["faces", "mega_tree", "matrix", "arches", "rooflines", "windows", "floods"],
                    "layers": ["base", "texture", "motion", "accent", "focus"],
                    "colors": ["red", "orange", "yellow", "green", "blue", "purple", "rainbow"],
                    "motion": "random",
                    "brightness": 0.9,
                    "density": 0.95,
                }
            ]
        },
        "audit": {"final": {"score": 90.0}},
    }


class YoutubeShowReportToolTests(unittest.TestCase):
    def test_build_summary_scores_report_payload(self) -> None:
        summary = youtube_show_report.build_summary(sample_report())

        self.assertIn("youtube_show_grade", summary)
        self.assertEqual(summary["quality_score"], 91.0)
        self.assertEqual(summary["top_show_score"], 88.0)
        self.assertEqual(summary["section_count"], 1)
        self.assertGreater(summary["youtube_show_grade"]["problem_count"], 0)

    def test_format_summary_prints_problems_and_recommendations(self) -> None:
        summary = youtube_show_report.build_summary(sample_report())
        text = youtube_show_report.format_summary(Path("sample.report.json"), summary)

        self.assertIn("Final score:", text)
        self.assertIn("Direction problems:", text)
        self.assertIn("Director recommendations:", text)
        self.assertIn("section_missing_focal_target", text)

    def test_format_summary_notes_aggregate_fallback_without_sections(self) -> None:
        summary = youtube_show_report.build_summary({"quality": {"score": 80.0}})
        text = youtube_show_report.format_summary(Path("sample.report.json"), summary)

        self.assertIn("aggregate report fallback", text)

    def test_main_json_prints_computed_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.report.json"
            path.write_text(json.dumps(sample_report()), encoding="utf-8")

            with patch("builtins.print") as mocked_print:
                result = youtube_show_report.main([str(path), "--json"])

        self.assertEqual(result, 0)
        printed = mocked_print.call_args.args[0]
        payload = json.loads(printed)
        self.assertIn("youtube_show_grade", payload)
        self.assertGreater(payload["youtube_show_grade"]["recommendation_count"], 0)


if __name__ == "__main__":
    unittest.main()
