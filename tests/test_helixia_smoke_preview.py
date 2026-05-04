from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

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

    def test_peak_sample_seconds_picks_separated_busy_frames(self) -> None:
        scores = [0, 10, 9, 1, 0, 8, 0, 7, 0, 6]

        seconds = smoke.peak_sample_seconds(scores, fps=1, samples=3, min_gap_seconds=2.0)

        self.assertEqual(seconds, [1.0, 5.0, 7.0])

    def test_even_sample_seconds_spreads_across_duration(self) -> None:
        self.assertEqual(smoke.even_sample_seconds(12.0, 3), [3.0, 6.0, 9.0])

    def test_frame_visual_metrics_rewards_spread_bright_pixels(self) -> None:
        frame = np.zeros((20, 20, 3), dtype=np.uint8)
        frame[2:4, 2:4] = [255, 255, 255]
        frame[15:17, 15:17] = [255, 255, 255]

        metrics = smoke.frame_visual_metrics(frame)

        self.assertGreater(metrics["bright_pixel_ratio"], 0.0)
        self.assertGreater(metrics["spread_ratio"], metrics["bright_pixel_ratio"])


if __name__ == "__main__":
    unittest.main()
