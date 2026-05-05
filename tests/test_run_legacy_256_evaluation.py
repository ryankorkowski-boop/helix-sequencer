from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from tools.run_legacy_256_evaluation import build_parser, main, run_evaluation


def _manifest() -> dict[str, object]:
    return {
        "schema": "helix.legacy_256_manifest.v1",
        "fixture_id": "legacy_256",
        "channel_count": 256,
        "paths": {
            "local_source_lms_dir": "local_fixtures/legacy_256/source_lms",
            "local_audio_dir": "local_fixtures/legacy_256/audio",
            "converted_template_xsq": "fixtures/legacy_256/converted/template.xsq",
            "converted_layout_file": "fixtures/legacy_256/converted/xlights_rgbeffects.xml",
        },
        "permission_status": {
            "source_lms_local_only_by_default": True,
            "source_lms_commit_allowed": False,
        },
        "quality_goal": {"min_quality_score": 93.0, "max_rejected_effects": 18000},
        "placement_rules": {
            "avoid_pixel_only_effects": True,
            "prefer_ac_safe_effects": True,
            "prefer_low_rejected_effect_count": True,
            "limit_full_layout_flashes": True,
        },
    }


def _report(score: float = 93.0) -> dict[str, object]:
    return {
        "quality": {"score": score, "component_scores": {"coverage": 84, "structure": 85, "family_diversity": 80}},
        "audit": {"final": {"score": 88, "musical_coherence": 92, "section_coverage": 0.9, "clutter_ratio": 0.03, "overlap_ratio": 0.02}},
        "validation": {"rejected_effects_count": 1000},
        "shortlist": {"score": 82},
    }


class RunLegacy256EvaluationTests(unittest.TestCase):
    def test_dry_run_builds_profile_steps_without_requiring_assets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            manifest = tmp_path / "manifest.json"
            manifest.write_text(json.dumps(_manifest()), encoding="utf-8")
            parser = build_parser()
            args = parser.parse_args([
                "--manifest",
                str(manifest),
                "--output-root",
                str(tmp_path / "runs"),
                "--dry-run",
            ])
            report = run_evaluation(args)

        self.assertTrue(report.dry_run)
        self.assertEqual(report.errors, [])
        self.assertEqual(report.profiles, ["legacy_256_clean", "legacy_256_showcase", "legacy_256_pro"])
        self.assertTrue(any(step["name"] == "run_legacy_256_clean" for step in report.steps))
        self.assertTrue(any(step["name"] == "compare_reports" and step["skipped"] for step in report.steps))

    def test_skip_runs_compares_existing_reports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            manifest = tmp_path / "manifest.json"
            output_root = tmp_path / "runs"
            output = tmp_path / "evaluation.json"
            manifest.write_text(json.dumps(_manifest()), encoding="utf-8")
            report_dir = output_root / "legacy_256_showcase"
            report_dir.mkdir(parents=True)
            (report_dir / "showcase.report.json").write_text(json.dumps(_report()), encoding="utf-8")

            code = main([
                "--manifest",
                str(manifest),
                "--output-root",
                str(output_root),
                "--output",
                str(output),
                "--skip-runs",
            ])
            payload = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(payload["schema"], "helix.legacy_256_evaluation.v1")
        self.assertEqual(payload["comparison"]["winner"], "showcase")
        self.assertEqual(payload["errors"], [])

    def test_real_run_records_subprocess_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            manifest = tmp_path / "manifest.json"
            template = tmp_path / "template.xsq"
            audio = tmp_path / "song.mp3"
            layout = tmp_path / "layout.xml"
            manifest.write_text(json.dumps(_manifest()), encoding="utf-8")
            template.write_text("<xsequence />", encoding="utf-8")
            audio.write_bytes(b"fake")
            layout.write_text("<xrgb />", encoding="utf-8")
            parser = build_parser()
            args = parser.parse_args([
                "--manifest",
                str(manifest),
                "--template",
                str(template),
                "--audio",
                str(audio),
                "--layout-file",
                str(layout),
                "--output-root",
                str(tmp_path / "runs"),
                "--profiles",
                "legacy_256_clean",
            ])
            completed = Mock(returncode=7)
            with patch("tools.run_legacy_256_evaluation.subprocess.run", return_value=completed):
                report = run_evaluation(args)

        self.assertTrue(any("Profile run failed" in error for error in report.errors))
        self.assertEqual(report.steps[0]["returncode"], 7)


if __name__ == "__main__":
    unittest.main()
