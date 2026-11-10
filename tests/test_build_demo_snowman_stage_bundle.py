from __future__ import annotations

import json
import tempfile
from pathlib import Path
import unittest

from tools.build_demo_snowman_stage_bundle import build_demo_snowman_stage_bundle_payload, write_demo_snowman_stage_bundle


class DemoSnowmanStageBundleTests(unittest.TestCase):
    def test_bundle_payload_keeps_stage_pack_manifest_preview_and_double_helix_consistent(self) -> None:
        payload = build_demo_snowman_stage_bundle_payload()

        self.assertEqual(payload["schema"], "helix.demo_snowman_stage_bundle.v1")
        self.assertTrue(payload["validation"]["stage_pack_valid"])
        self.assertTrue(payload["validation"]["manifest_valid"])
        self.assertTrue(payload["validation"]["preview_has_floor_piano_link"])
        self.assertTrue(payload["validation"]["artifact_sources_are_consistent"])
        self.assertTrue(payload["validation"]["double_helix_reactive"])
        self.assertTrue(payload["validation"]["double_helix_targets_valid"])
        self.assertTrue(payload["validation"]["double_helix_has_audio_in_and_lights_out"])
        self.assertTrue(payload["validation"]["double_helix_xlights_plan_valid"])
        self.assertTrue(payload["validation"]["double_helix_preview_has_identity"])
        self.assertEqual(payload["manifest"]["pack_id"], payload["stage_pack"]["pack_id"])
        self.assertEqual(payload["summary"]["manifest_rows"], payload["manifest"]["row_count"])
        self.assertTrue(payload["summary"]["drummer_feeds_floor_piano"])
        self.assertIn("floor_piano", payload["summary"]["stage_props"])
        self.assertIn("drummer → floor piano: ACTIVE", payload["preview_svg"])
        self.assertEqual(payload["reactive_double_helix"]["status"], "reactive_centerpiece_slice")
        self.assertGreater(payload["summary"]["double_helix_cues"], payload["manifest"]["row_count"])
        self.assertIn("HELIXIA_DNA_TOP_INPUT", payload["summary"]["double_helix_targets"])
        self.assertIn("HELIXIA_DNA_BOTTOM_OUTPUT", payload["summary"]["double_helix_targets"])
        self.assertIn("HELIXIA_DNA_STRAND_A", payload["double_helix_preview_svg"])
        self.assertEqual(payload["double_helix_xlights_plan"]["model_id"], "HELIXIA_GIANT_DOUBLE_HELIX")

    def test_write_bundle_outputs_all_review_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = write_demo_snowman_stage_bundle(Path(tmp))

            for key in (
                "stage_pack",
                "manifest",
                "preview_svg",
                "reactive_double_helix",
                "double_helix_preview_svg",
                "double_helix_xlights_plan",
                "summary",
            ):
                self.assertTrue(Path(result[key]).exists(), key)
            self.assertTrue(result["validation"]["stage_pack_valid"])
            self.assertTrue(result["validation"]["manifest_valid"])
            self.assertTrue(result["validation"]["preview_has_floor_piano_link"])
            self.assertTrue(result["validation"]["double_helix_reactive"])
            self.assertTrue(result["validation"]["double_helix_xlights_plan_valid"])

            summary = json.loads(Path(result["summary"]).read_text(encoding="utf-8"))
            self.assertEqual(summary["schema"], "helix.demo_snowman_stage_bundle.v1")
            self.assertTrue(summary["validation"]["artifact_sources_are_consistent"])
            self.assertTrue(summary["validation"]["double_helix_reactive"])
            self.assertIn("stage_pack", summary["artifacts"])
            self.assertIn("manifest", summary["artifacts"])
            self.assertIn("preview_svg", summary["artifacts"])
            self.assertIn("reactive_double_helix", summary["artifacts"])
            self.assertIn("double_helix_preview_svg", summary["artifacts"])
            self.assertIn("double_helix_xlights_plan", summary["artifacts"])

            double_helix = json.loads(Path(result["reactive_double_helix"]).read_text(encoding="utf-8"))
            self.assertEqual(double_helix["model_id"], "HELIXIA_GIANT_DOUBLE_HELIX")
            self.assertTrue(double_helix["validation"]["has_audio_in_and_lights_out"])


if __name__ == "__main__":
    unittest.main()
