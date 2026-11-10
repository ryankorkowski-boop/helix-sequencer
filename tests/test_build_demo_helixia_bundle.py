from __future__ import annotations

import json
import tempfile
from pathlib import Path
import unittest

from tools.build_demo_helixia_bundle import build_demo_helixia_bundle_payload, write_demo_helixia_bundle


class DemoHelixiaBundleTests(unittest.TestCase):
    def test_helixia_bundle_payload_contains_layout_3d_double_helix_and_stage_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            payload = build_demo_helixia_bundle_payload(Path(tmp))

            self.assertEqual(payload["schema"], "helixia.demo_bundle.v1")
            self.assertTrue(payload["validation"]["helixia_manifest_has_double_helix"])
            self.assertTrue(payload["validation"]["xlights_xml_generated"])
            self.assertTrue(payload["validation"]["layout_3d_valid"])
            self.assertTrue(payload["validation"]["all_grounded_models_on_ground"])
            self.assertTrue(payload["validation"]["no_grounded_models_below_ground"])
            self.assertTrue(payload["validation"]["double_helix_grounded"])
            self.assertTrue(payload["validation"]["double_helix_xlights_plan_valid"])
            self.assertTrue(payload["validation"]["double_helix_preview_has_identity"])
            self.assertTrue(payload["validation"]["layout_3d_preview_has_ground_plane"])
            self.assertTrue(payload["validation"]["snowman_stage_bundle_valid"])
            self.assertEqual(payload["summary"]["double_helix_model_id"], "HELIXIA_GIANT_DOUBLE_HELIX")
            self.assertGreater(payload["summary"]["layout_3d_model_count"], 0)
            self.assertGreater(payload["summary"]["double_helix_xlights_effects"], 0)
            self.assertIn("giant_double_helix", payload["layout"])
            self.assertIn("HELIXIA_GIANT_DOUBLE_HELIX", payload["layout_3d_preview_svg"])

    def test_write_helixia_bundle_outputs_all_review_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = write_demo_helixia_bundle(Path(tmp))

            for key in (
                "helixia_manifest",
                "layout_notes",
                "xlights_rgbeffects",
                "helixia_3d_manifest",
                "helixia_3d_preview_svg",
                "helixia_double_helix_preview_svg",
                "helixia_double_helix_xlights_plan",
                "summary",
            ):
                self.assertTrue(Path(result[key]).exists(), key)
            self.assertTrue(result["validation"]["layout_3d_valid"])
            self.assertTrue(result["validation"]["double_helix_grounded"])
            self.assertTrue(result["validation"]["snowman_stage_bundle_valid"])

            snowman = result["snowman_stage_bundle"]
            self.assertTrue(Path(snowman["stage_pack"]).exists())
            self.assertTrue(Path(snowman["reactive_double_helix"]).exists())
            self.assertTrue(Path(snowman["double_helix_xlights_plan"]).exists())

            summary = json.loads(Path(result["summary"]).read_text(encoding="utf-8"))
            self.assertEqual(summary["schema"], "helixia.demo_bundle.v1")
            self.assertTrue(summary["validation"]["layout_3d_valid"])
            self.assertIn("helixia_manifest", summary["artifacts"])
            self.assertIn("snowman_stage_bundle", summary["artifacts"])
            self.assertIn("helixia_double_helix_xlights_plan", summary["artifacts"])


if __name__ == "__main__":
    unittest.main()
