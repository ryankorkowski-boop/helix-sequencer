from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools import generate_aaatest_pack


def _sample_report() -> dict:
    return {
        "duration_seconds": 2,
        "effects_total": 2,
        "quality": {"score": 91.0},
        "youtube_show_summary": {
            "sections": [
                {
                    "label": "chorus",
                    "focal_target": "mega_tree",
                    "active_props": ["mega_tree", "arches"],
                    "layers": ["base", "motion"],
                    "colors": ["red", "green"],
                    "motion": "left_to_right",
                    "brightness": 0.8,
                    "density": 0.7,
                    "has_rest": True,
                }
            ]
        },
    }


class GenerateAAATestPackTests(unittest.TestCase):
    def test_copy_report_and_grade_output_write_deterministic_summaries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            source_xsq = folder / "source.xsq"
            source_xsq.write_text("<Sequence />\n", encoding="utf-8")
            source_report = folder / "source.report.json"
            source_report.write_text(json.dumps(_sample_report()), encoding="utf-8")
            target_xsq = folder / "01_sample.xsq"
            target_xsq.write_text("<Sequence />\n", encoding="utf-8")

            copied = generate_aaatest_pack._copy_report(source_xsq, target_xsq)
            grade = generate_aaatest_pack._grade_output("sample", target_xsq, copied, 70.0)
            summary = json.loads(grade.summary_path.read_text(encoding="utf-8"))

        self.assertTrue(copied.name.endswith(".report.json"))
        self.assertTrue(grade.passed)
        self.assertGreaterEqual(grade.final_score, 70.0)
        self.assertIn("youtube_show_grade", summary)

    def test_write_grading_report_records_pass_fail_indicator(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            result = generate_aaatest_pack.GradingResult(
                label="sample",
                xsq_path=folder / "sample.xsq",
                report_path=folder / "sample.report.json",
                summary_path=folder / "sample.youtube_show_summary.json",
                final_score=82.0,
                grade="B-",
                passed=True,
                problems=1,
            )
            report_path = generate_aaatest_pack._write_grading_report(folder, [result], 70.0)
            payload = json.loads(report_path.read_text(encoding="utf-8"))
            text = (folder / "aaatest_grading_summary.txt").read_text(encoding="utf-8")

        self.assertTrue(payload["passed"])
        self.assertEqual(payload["outputs"][0]["label"], "sample")
        self.assertIn("pass=True", text)


if __name__ == "__main__":
    unittest.main()
