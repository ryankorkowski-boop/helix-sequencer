from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from core import model_parser as xmp
from core.helixville4_band_stem_map import validate_stem_map_against_submodels
from models.helixville4_vocal_phonemes import PHONEME_NAMES
from tools.build_helpers.helixia import build_helixia_layout


class HelixiaXlightsBandSpecsTests(unittest.TestCase):
    def test_opt_in_band_model_specs_generate_real_band_models_and_submodels(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            payload = build_helixia_layout(
                Path(tmp),
                village_rows=3,
                village_cols=4,
                use_helixville4_band_model_specs=True,
            )
            parsed = xmp.parse_layout(Path(tmp) / "xlights_rgbeffects.xml")
            notes = (Path(tmp) / "HELIXIA_LAYOUT_NOTES.txt").read_text(encoding="utf-8")

        self.assertTrue(payload["use_helixville4_band_model_specs"])
        self.assertTrue(payload["xlights_layout"]["band_model_specs_enabled"])
        self.assertIn("Helixville4 spec-driven snowman band models are enabled.", notes)

        for model in (
            "HX_SNOWMAN_SINGER",
            "HX_SNOWMAN_SINGER_FEMALE",
            "HX_SNOWMAN_GUITARIST",
            "HX_SNOWMAN_BASSIST",
            "HX_SNOWMAN_DRUMMER",
        ):
            self.assertIn(model, parsed.models)

        for phoneme in PHONEME_NAMES:
            self.assertIn(f"HX_SNOWMAN_SINGER/HX_SNOWMAN_SINGER_MOUTH_{phoneme}", parsed.models)
            self.assertIn(f"HX_SNOWMAN_SINGER_FEMALE/HX_SNOWMAN_SINGER_FEMALE_MOUTH_{phoneme}", parsed.models)

        required_submodels = (
            "HX_SNOWMAN_GUITARIST/HX_SNOWMAN_GUITARIST_PICK_ZONE",
            "HX_SNOWMAN_GUITARIST/HX_SNOWMAN_GUITARIST_STRING_HIGH_E",
            "HX_SNOWMAN_BASSIST/HX_SNOWMAN_BASSIST_PLUCK_ZONE",
            "HX_SNOWMAN_BASSIST/HX_SNOWMAN_BASSIST_STRING_E",
            "HX_SNOWMAN_DRUMMER/HX_SNOWMAN_DRUMMER_KICK",
            "HX_SNOWMAN_DRUMMER/HX_SNOWMAN_DRUMMER_SNARE",
            "HX_SNOWMAN_DRUMMER/HX_SNOWMAN_DRUMMER_HI_HAT",
            "HX_SNOWMAN_DRUMMER/HX_SNOWMAN_DRUMMER_CYMBAL_LEFT",
            "HX_SNOWMAN_DRUMMER/HX_SNOWMAN_DRUMMER_CYMBAL_RIGHT",
        )
        for submodel in required_submodels:
            self.assertIn(submodel, parsed.models)

        self.assertIn("HX_SNOWMAN_BAND", parsed.groups)
        self.assertIn("HX_SNOWMAN_VOCALS", parsed.groups)
        self.assertIn("HX_SNOWMAN_INSTRUMENTS", parsed.groups)

    def test_opt_in_band_model_specs_are_stem_map_compatible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            build_helixia_layout(
                Path(tmp),
                village_rows=3,
                village_cols=4,
                use_helixville4_band_model_specs=True,
            )
            parsed = xmp.parse_layout(Path(tmp) / "xlights_rgbeffects.xml")

        model_submodels: dict[str, set[str]] = {}
        for name in parsed.models:
            if "/" not in name:
                continue
            model, submodel = name.split("/", 1)
            model_submodels.setdefault(model, set()).add(submodel)
        validation = validate_stem_map_against_submodels(model_submodels)
        self.assertTrue(validation["valid"], validation["errors"])

    def test_default_helixia_layout_keeps_existing_placeholder_band_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            payload = build_helixia_layout(Path(tmp), village_rows=3, village_cols=4)

            self.assertFalse(payload["use_helixville4_band_model_specs"])
            self.assertFalse(payload["xlights_layout"]["band_model_specs_enabled"])
            parsed = xmp.parse_layout(Path(tmp) / "xlights_rgbeffects.xml")
            self.assertIn("HX_SNOWMAN_SINGER_BODY", parsed.models)
            self.assertNotIn("HX_SNOWMAN_SINGER", parsed.models)


if __name__ == "__main__":
    unittest.main()
