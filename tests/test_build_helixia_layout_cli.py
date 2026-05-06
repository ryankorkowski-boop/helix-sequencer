from __future__ import annotations

import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from core import model_parser as xmp
from tools.build_helixia_layout import main


class BuildHelixiaLayoutCliTests(unittest.TestCase):
    def test_cli_default_builds_placeholder_band_layout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = StringIO()
            with redirect_stdout(out):
                code = main(["--output-dir", tmp])
            parsed = xmp.parse_layout(Path(tmp) / "xlights_rgbeffects.xml")

        self.assertEqual(code, 0)
        self.assertIn("band_specs=False", out.getvalue())
        self.assertIn("HX_SNOWMAN_SINGER_BODY", parsed.models)
        self.assertNotIn("HX_SNOWMAN_SINGER", parsed.models)

    def test_cli_can_enable_spec_driven_band_layout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = StringIO()
            with redirect_stdout(out):
                code = main(["--output-dir", tmp, "--use-helixville4-band-model-specs"])
            parsed = xmp.parse_layout(Path(tmp) / "xlights_rgbeffects.xml")
            notes = (Path(tmp) / "HELIXIA_LAYOUT_NOTES.txt").read_text(encoding="utf-8")

        self.assertEqual(code, 0)
        self.assertIn("band_specs=True", out.getvalue())
        self.assertIn("Helixville4 spec-driven snowman band models are enabled.", notes)
        self.assertIn("HX_SNOWMAN_SINGER", parsed.models)
        self.assertIn("HX_SNOWMAN_SINGER/HX_SNOWMAN_SINGER_MOUTH_PHONEME", parsed.models)
        self.assertIn("HX_SNOWMAN_BAND", parsed.groups)


if __name__ == "__main__":
    unittest.main()
