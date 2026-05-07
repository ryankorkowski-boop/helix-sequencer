from __future__ import annotations

import json
import tempfile
from pathlib import Path
import unittest

from tools.build_helpers.helixia_3d import build_helixia_3d_layout
from tools.preview_helixia_3d_layout import build_helixia_3d_preview_svg, write_helixia_3d_preview


class Helixia3DPreviewTests(unittest.TestCase):
    def test_preview_svg_marks_ground_plane_and_double_helix(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            layout = build_helixia_3d_layout(Path(tmp), village_rows=3, village_cols=4)
            svg = build_helixia_3d_preview_svg(layout)

            self.assertIn("Helixia 3D Grounded Layout Preview", svg)
            self.assertIn("3D is source of truth", svg)
            self.assertIn("GROUND PLANE Z=0", svg)
            self.assertIn("DOUBLE HELIX GROUNDED", svg)
            self.assertIn("Validation: PASS", svg)
            self.assertIn("double helix", svg)
            self.assertIn("houses", svg)
            self.assertIn("stage", svg)

    def test_write_preview_outputs_manifest_svg_and_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = write_helixia_3d_preview(Path(tmp))

            self.assertTrue(Path(result["layout_manifest"]).exists())
            self.assertTrue(Path(result["preview_svg"]).exists())
            self.assertTrue(Path(result["summary"]).exists())
            self.assertTrue(result["validation"]["all_grounded_models_on_ground"])
            self.assertTrue(result["validation"]["double_helix_grounded"])

            preview = Path(result["preview_svg"]).read_text(encoding="utf-8")
            self.assertTrue(preview.startswith("<svg"))
            self.assertIn("GROUND PLANE Z=0", preview)
            self.assertIn("DOUBLE HELIX GROUNDED", preview)

            summary = json.loads(Path(result["summary"]).read_text(encoding="utf-8"))
            self.assertEqual(summary["schema"], "helixia.layout3d_preview.summary.v1")
            self.assertGreater(summary["model_count"], 0)
            self.assertTrue(summary["grounding"]["all_grounded_models_on_ground"])
            self.assertEqual(summary["grounding"]["floating_grounded_models"], [])
            self.assertEqual(summary["grounding"]["negative_grounded_models"], [])


if __name__ == "__main__":
    unittest.main()
