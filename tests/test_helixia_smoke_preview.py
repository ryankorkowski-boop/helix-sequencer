from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools import helixia_smoke_preview as smoke


class HelixiaSmokePreviewTests(unittest.TestCase):
    def test_build_sequence_command_uses_helixia_defaults(self) -> None:
        args = smoke.build_parser().parse_args([])
        args.audio = args.audio.resolve()
        args.layout = args.layout.resolve()
        args.template = args.template.resolve()
        args.output_dir = args.output_dir.resolve()

        command = smoke.build_sequence_command(args)

        self.assertIn("core.sequence_builder", command)
        self.assertIn("--audio-reactive-profile", command)
        self.assertIn("showcase", command)
        self.assertIn(str(smoke.DEFAULT_AUDIO), command)
        self.assertIn(str(smoke.DEFAULT_LAYOUT), command)
        self.assertIn("--max-layers-per-prop", command)

    def test_load_report_summary_extracts_quality_and_layout_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report_path = Path(tmp) / "sample.report.json"
            report_path.write_text(
                json.dumps(
                    {
                        "effects_total": 123,
                        "parsed_layout": {
                            "root_model_count": 10,
                            "model_count": 40,
                            "group_count": 3,
                        },
                        "validation": {"issues": [{"message": "sample"}]},
                        "quality": {
                            "score": 97.5,
                            "grade": "A+",
                            "top_show_benchmark": {
                                "score": 91.0,
                                "grade": "A-",
                                "aggregate_changes_per_second": 72.5,
                                "flash_like_changes_per_second": 1.2,
                            },
                        },
                    }
                ),
                encoding="utf-8",
            )

            summary = smoke.load_report_summary(report_path)

        self.assertEqual(summary["quality_score"], 97.5)
        self.assertEqual(summary["top_show_grade"], "A-")
        self.assertEqual(summary["effects_total"], 123)
        self.assertEqual(summary["models_including_submodels"], 40)
        self.assertEqual(summary["validation_issues"], 1)


if __name__ == "__main__":
    unittest.main()
