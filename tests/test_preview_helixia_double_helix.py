from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

from models.helixia_double_helix import build_giant_double_helix
from tools.preview_helixia_double_helix import build_double_helix_preview_svg, write_double_helix_preview


class HelixiaDoubleHelixPreviewTests(unittest.TestCase):
    def test_preview_svg_contains_strands_rungs_and_narrative_zones(self) -> None:
        payload = build_giant_double_helix()
        svg = build_double_helix_preview_svg(payload)

        self.assertIn("Helixia Giant Lighted Double Helix", svg)
        self.assertIn("HELIXIA_DNA_STRAND_A", svg)
        self.assertIn("HELIXIA_DNA_STRAND_B", svg)
        self.assertIn("HELIXIA_DNA_RUNGS", svg)
        self.assertIn("HELIXIA_DNA_TOP_INPUT", svg)
        self.assertIn("HELIXIA_DNA_BOTTOM_OUTPUT", svg)
        self.assertIn("AUDIO INPUT / UNTWINED TOP ZONE", svg)
        self.assertIn("LIGHTS OUT / FINISHED OUTPUT ZONE", svg)
        self.assertIn("Audio in. Lights out.", svg)

    def test_write_preview_outputs_svg_file_and_counts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "double_helix_preview.svg"
            result = write_double_helix_preview(output_path)

            self.assertEqual(result["path"], str(output_path))
            self.assertEqual(result["model_id"], "HELIXIA_GIANT_DOUBLE_HELIX")
            self.assertGreater(result["strand_nodes"], 200)
            self.assertGreater(result["rungs"], 20)
            self.assertGreater(result["top_input_nodes"], 0)
            self.assertGreater(result["bottom_output_nodes"], 0)
            self.assertTrue(output_path.exists())
            text = output_path.read_text(encoding="utf-8")
            self.assertTrue(text.startswith("<svg"))
            self.assertIn("HELIXIA_DNA_STRAND_A", text)
            self.assertIn("HELIXIA_DNA_STRAND_B", text)


if __name__ == "__main__":
    unittest.main()
