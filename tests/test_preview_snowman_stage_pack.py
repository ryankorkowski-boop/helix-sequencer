from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

from export.stage_pack_manifest_export import build_demo_stage_pack_export_manifest
from tools.preview_snowman_stage_pack import build_stage_pack_preview_svg, write_demo_stage_pack_preview


class SnowmanStagePackPreviewTests(unittest.TestCase):
    def test_preview_svg_includes_performers_and_active_floor_piano_link(self) -> None:
        manifest = build_demo_stage_pack_export_manifest()
        svg = build_stage_pack_preview_svg(manifest)

        self.assertIn("Helix Snowman Stage Pack Preview", svg)
        self.assertIn("Lead Singer", svg)
        self.assertIn("Female Singer", svg)
        self.assertIn("Guitarist", svg)
        self.assertIn("Bassist", svg)
        self.assertIn("Drummer", svg)
        self.assertIn("Floor Piano", svg)
        self.assertIn("drummer → floor piano: ACTIVE", svg)
        self.assertIn("Generated from the flattened stage-pack export manifest", svg)

    def test_write_preview_outputs_svg_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "preview.svg"
            result = write_demo_stage_pack_preview(output_path)

            self.assertEqual(result["path"], str(output_path))
            self.assertTrue(result["drummer_feeds_floor_piano"])
            self.assertTrue(output_path.exists())
            text = output_path.read_text(encoding="utf-8")
            self.assertTrue(text.startswith("<svg"))
            self.assertIn("drummer → floor piano: ACTIVE", text)


if __name__ == "__main__":
    unittest.main()
