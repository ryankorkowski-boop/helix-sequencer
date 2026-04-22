from __future__ import annotations

import unittest
from unittest.mock import patch

from tools import open_source_intake


class OpenSourceIntakeTests(unittest.TestCase):
    def test_license_status_filters_non_allowlisted(self) -> None:
        ok, reason = open_source_intake.license_status("mit")
        self.assertTrue(ok)
        self.assertIn("permissive", reason)

        bad_ok, bad_reason = open_source_intake.license_status("gpl-3.0")
        self.assertFalse(bad_ok)
        self.assertIn("allowlist", bad_reason)

    def test_build_manifest_keeps_metadata_only(self) -> None:
        fake_items = [
            {
                "full_name": "demo/xsq-demo",
                "html_url": "https://github.com/demo/xsq-demo",
                "description": "Demo",
                "stargazers_count": 200,
                "forks_count": 30,
                "language": "Python",
                "topics": ["xlights"],
                "license": {"spdx_id": "MIT"},
                "updated_at": "2026-01-01T00:00:00Z",
            }
        ]

        with patch("tools.open_source_intake._search", return_value=fake_items):
            manifest = open_source_intake.build_manifest(min_stars=5, max_results_per_category=1, token=None)
        self.assertEqual(manifest["summary"]["total_rows"], 2)
        self.assertEqual(manifest["summary"]["legal_ok_count"], 2)
        self.assertEqual(manifest["policy"]["download_behavior"], "metadata_only_no_source_copy")


if __name__ == "__main__":
    unittest.main()
