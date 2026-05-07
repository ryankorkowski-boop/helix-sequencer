from __future__ import annotations

import json
import tempfile
from pathlib import Path
import unittest

from tools.build_demo_snowman_stage_bundle import build_demo_snowman_stage_bundle_payload, write_demo_snowman_stage_bundle


class DemoSnowmanStageBundleTests(unittest.TestCase):
    def test_bundle_payload_keeps_stage_pack_manifest_and_preview_consistent(self) -> None:
        payload = build_demo_snowman_stage_bundle_payload()

        self.assertEqual(payload["schema"], "helix.demo_snowman_stage_bundle.v1")
        self.assertTrue(payload["validation"]["stage_pack_valid"])
        self.assertTrue(payload["validation"]["manifest_valid"])
        self.assertTrue(payload["validation"]["preview_has_floor_piano_link"])
        self.assertTrue(payload["validation"]["artifact_sources_are_consistent"])
        self.assertEqual(payload["manifest"]["pack_id"], payload["stage_pack"]["pack_id"])
        self.assertEqual(payload["summary"]["manifest_rows"], payload["manifest"]["row_count"])
        self.assertTrue(payload["summary"]["drummer_feeds_floor_piano"])
        self.assertIn("floor_piano", payload["summary"]["stage_props"])
        self.assertIn("drummer → floor piano: ACTIVE", payload["preview_svg"])

    def test_write_bundle_outputs_all_review_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = write_demo_snowman_stage_bundle(Path(tmp))

            for key in ("stage_pack", "manifest", "preview_svg", "summary"):
                self.assertTrue(Path(result[key]).exists(), key)
            self.assertTrue(result["validation"]["stage_pack_valid"])
            self.assertTrue(result["validation"]["manifest_valid"])
            self.assertTrue(result["validation"]["preview_has_floor_piano_link"])

            summary = json.loads(Path(result["summary"]).read_text(encoding="utf-8"))
            self.assertEqual(summary["schema"], "helix.demo_snowman_stage_bundle.v1")
            self.assertTrue(summary["validation"]["artifact_sources_are_consistent"])
            self.assertIn("stage_pack", summary["artifacts"])
            self.assertIn("manifest", summary["artifacts"])
            self.assertIn("preview_svg", summary["artifacts"])


if __name__ == "__main__":
    unittest.main()
