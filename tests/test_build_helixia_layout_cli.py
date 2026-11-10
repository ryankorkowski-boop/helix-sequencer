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
            tmp_path = Path(tmp)
            parsed = xmp.parse_layout(tmp_path / "xlights_rgbeffects.xml")
            notes = (tmp_path / "HELIXIA_LAYOUT_NOTES.txt").read_text(encoding="utf-8")
            band_assets = tmp_path / "band_assets"
            svg_files = sorted(band_assets.glob("*.svg"))
            manifest_exists = (band_assets / "helixville4_band_assets_manifest.json").exists()

        self.assertEqual(code, 0)
        self.assertIn("band_specs=True", out.getvalue())
        self.assertIn("Helixville4 spec-driven snowman band models are enabled.", notes)
        self.assertIn("Band background SVG assets were written to band_assets/.", notes)
        self.assertIn("HX_SNOWMAN_SINGER", parsed.models)
        self.assertIn("HX_SNOWMAN_SINGER/HX_SNOWMAN_SINGER_MOUTH_PHONEME", parsed.models)
        self.assertIn("HX_SNOWMAN_BAND", parsed.groups)
        self.assertEqual(len(svg_files), 5)
        self.assertTrue(manifest_exists)
        self.assertTrue(any("HX_SNOWMAN_DRUMMER" in path.name for path in svg_files))


if __name__ == "__main__":
    unittest.main()
