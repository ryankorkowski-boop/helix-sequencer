from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

from tools.audit_demo_snowman_stage_bundle import audit_fresh_demo_bundle, audit_generated_bundle, format_audit_report
from tools.build_demo_snowman_stage_bundle import write_demo_snowman_stage_bundle


class DemoSnowmanStageBundleAuditTests(unittest.TestCase):
    def test_fresh_demo_bundle_audit_passes_and_formats_report(self) -> None:
        audit = audit_fresh_demo_bundle()
        report = format_audit_report(audit)

        self.assertEqual(audit["schema"], "helix.demo_snowman_stage_bundle.audit.v1")
        self.assertEqual(audit["status"], "pass")
        self.assertTrue(all(audit["checks"].values()))
        self.assertIn("Snowman stage bundle audit: PASS", report)
        self.assertIn("PASS stage_pack_valid", report)
        self.assertIn("PASS drummer_feeds_floor_piano", report)
        self.assertIn("performers: bassist, drummer, female_singer, guitarist, singer", report)
        self.assertIn("props: floor_piano", report)

    def test_generated_bundle_audit_reads_written_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle_dir = Path(tmp)
            write_demo_snowman_stage_bundle(bundle_dir)
            audit = audit_generated_bundle(bundle_dir)

            self.assertEqual(audit["status"], "pass")
            self.assertTrue(audit["checks"]["summary_file_exists"])
            self.assertTrue(audit["checks"]["stage_pack_valid"])
            self.assertTrue(audit["checks"]["manifest_valid"])
            self.assertTrue(audit["checks"]["drummer_feeds_floor_piano"])

    def test_generated_bundle_audit_fails_when_summary_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            audit = audit_generated_bundle(Path(tmp))

            self.assertEqual(audit["status"], "fail")
            self.assertFalse(audit["checks"]["summary_file_exists"])


if __name__ == "__main__":
    unittest.main()
