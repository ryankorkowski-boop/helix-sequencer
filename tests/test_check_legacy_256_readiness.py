from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.check_legacy_256_readiness import check_readiness, main


def _manifest(tmp_path: Path) -> dict[str, object]:
    return {
        "schema": "helix.legacy_256_manifest.v1",
        "fixture_id": "legacy_256",
        "channel_count": 256,
        "paths": {
            "local_source_lms_dir": str(tmp_path / "local" / "source_lms"),
            "local_audio_dir": str(tmp_path / "local" / "audio"),
            "converted_template_xsq": str(tmp_path / "converted" / "template.xsq"),
            "converted_layout_file": str(tmp_path / "converted" / "xlights_rgbeffects.xml"),
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


class CheckLegacy256ReadinessTests(unittest.TestCase):
    def test_readiness_reports_missing_required_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            manifest = tmp_path / "manifest.json"
            manifest.write_text(json.dumps(_manifest(tmp_path)), encoding="utf-8")
            report = check_readiness(manifest_path=manifest)

        self.assertTrue(report.ready_for_dry_run)
        self.assertFalse(report.ready_for_real_run)
        self.assertIn("local_audio", report.missing_required)
        self.assertIn("converted_template_xsq", report.missing_required)
        self.assertIn("converted_layout_file", report.missing_required)
        self.assertTrue(report.next_commands)

    def test_readiness_passes_when_required_files_exist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            payload = _manifest(tmp_path)
            manifest = tmp_path / "manifest.json"
            manifest.write_text(json.dumps(payload), encoding="utf-8")
            audio = Path(payload["paths"]["local_audio_dir"]) / "song.mp3"  # type: ignore[index]
            template = Path(payload["paths"]["converted_template_xsq"])  # type: ignore[index]
            layout = Path(payload["paths"]["converted_layout_file"])  # type: ignore[index]
            audio.parent.mkdir(parents=True)
            template.parent.mkdir(parents=True)
            audio.write_bytes(b"fake")
            template.write_text("<xsequence />", encoding="utf-8")
            layout.write_text("<xrgb />", encoding="utf-8")

            report = check_readiness(manifest_path=manifest)

        self.assertTrue(report.ready_for_dry_run)
        self.assertTrue(report.ready_for_real_run)
        self.assertEqual(report.missing_required, [])
        self.assertTrue(any("run_legacy_256_evaluation" in command and "--dry-run" not in command for command in report.next_commands))

    def test_main_writes_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            manifest = tmp_path / "manifest.json"
            output = tmp_path / "readiness.json"
            manifest.write_text(json.dumps(_manifest(tmp_path)), encoding="utf-8")

            code = main(["--manifest", str(manifest), "--output", str(output)])
            payload = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(payload["schema"], "helix.legacy_256_readiness.v1")
        self.assertTrue(payload["ready_for_dry_run"])
        self.assertFalse(payload["ready_for_real_run"])


if __name__ == "__main__":
    unittest.main()
