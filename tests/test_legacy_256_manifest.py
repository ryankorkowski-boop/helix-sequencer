from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.legacy_256_manifest import (
    load_legacy_256_manifest,
    validate_legacy_256_manifest,
    validate_legacy_256_manifest_file,
)


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
            "converted_assets_commit_allowed": False,
        },
        "quality_goal": {
            "preset": "showcase",
            "min_quality_score": 93.0,
            "min_audit_score": 86.0,
            "max_rejected_effects": 18000,
        },
        "placement_rules": {
            "avoid_pixel_only_effects": True,
            "prefer_ac_safe_effects": True,
            "prefer_low_rejected_effect_count": True,
            "limit_full_layout_flashes": True,
        },
        "profile_direction": ["legacy_256_clean", "legacy_256_showcase", "legacy_256_pro"],
        "channel_families": [],
    }


class Legacy256ManifestTests(unittest.TestCase):
    def test_valid_manifest_passes(self) -> None:
        report = validate_legacy_256_manifest(_manifest())

        self.assertTrue(report.passed)
        self.assertEqual(report.errors, [])
        self.assertEqual(report.metrics["channel_count"], 256)
        self.assertEqual(report.metrics["profile_direction_count"], 3)

    def test_wrong_schema_and_channel_count_fail(self) -> None:
        payload = _manifest()
        payload["schema"] = "bad.schema"
        payload["channel_count"] = 128

        report = validate_legacy_256_manifest(payload)

        self.assertFalse(report.passed)
        self.assertTrue(any("Unexpected schema" in error for error in report.errors))
        self.assertIn("channel_count must be 256", report.errors)

    def test_permission_commit_allowed_warns(self) -> None:
        payload = _manifest()
        payload["permission_status"] = {
            "source_lms_local_only_by_default": False,
            "source_lms_commit_allowed": True,
        }

        report = validate_legacy_256_manifest(payload)

        self.assertTrue(report.passed)
        self.assertGreaterEqual(len(report.warnings), 2)

    def test_file_loader_and_validator(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "layout_256_manifest.json"
            path.write_text(json.dumps(_manifest()), encoding="utf-8")
            payload = load_legacy_256_manifest(path)
            report = validate_legacy_256_manifest_file(path)

        self.assertEqual(payload["fixture_id"], "legacy_256")
        self.assertTrue(report.passed)


if __name__ == "__main__":
    unittest.main()
