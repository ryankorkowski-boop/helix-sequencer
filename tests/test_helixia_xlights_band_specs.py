from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from core import model_parser as xmp
from tools.build_helpers.helixia import build_helixia_layout


class HelixiaXlightsBandSpecsTests(unittest.TestCase):
    def test_opt_in_band_model_specs_generate_real_band_models_and_submodels(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            payload = build_helixia_layout(Path(tmp), village_rows=3, village_cols=4)
            payload["use_helixville4_band_model_specs"] = True
            from tools.build_helpers.helixia_xlights import build_helixia_xlights_layout

            build_helixia_xlights_layout(payload, Path(tmp) / "band_specs")
            parsed = xmp.parse_layout(Path(tmp) / "band_specs" / "xlights_rgbeffects.xml")

        for model in (
            "HX_SNOWMAN_SINGER",
            "HX_SNOWMAN_SINGER_FEMALE",
            "HX_SNOWMAN_GUITARIST",
            "HX_SNOWMAN_BASSIST",
            "HX_SNOWMAN_DRUMMER",
        ):
            self.assertIn(model, parsed.models)

        for submodel in (
            "HX_SNOWMAN_SINGER/HX_SNOWMAN_SINGER_MOUTH_PHONEME",
            "HX_SNOWMAN_SINGER_FEMALE/HX_SNOWMAN_SINGER_FEMALE_CALL_RESPONSE",
            "HX_SNOWMAN_GUITARIST/HX_SNOWMAN_GUITARIST_STRUM_ZONE",
            "HX_SNOWMAN_BASSIST/HX_SNOWMAN_BASSIST_PLUCK_ZONE",
            "HX_SNOWMAN_DRUMMER/HX_SNOWMAN_DRUMMER_SNARE",
            "HX_SNOWMAN_DRUMMER/HX_SNOWMAN_DRUMMER_CYMBALS",
        ):
            self.assertIn(submodel, parsed.models)

        self.assertIn("HX_SNOWMAN_BAND", parsed.groups)
        self.assertIn("HX_SNOWMAN_VOCALS", parsed.groups)
        self.assertIn("HX_SNOWMAN_INSTRUMENTS", parsed.groups)

    def test_default_helixia_layout_keeps_existing_placeholder_band_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            payload = build_helixia_layout(Path(tmp), village_rows=3, village_cols=4)

            self.assertFalse(payload["xlights_layout"]["band_model_specs_enabled"])
            parsed = xmp.parse_layout(Path(tmp) / "xlights_rgbeffects.xml")
            self.assertIn("HX_SNOWMAN_SINGER_BODY", parsed.models)
            self.assertNotIn("HX_SNOWMAN_SINGER", parsed.models)


if __name__ == "__main__":
    unittest.main()
