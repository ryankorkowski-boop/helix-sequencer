from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.build_helixville4_band_model_specs import (
    build_helixville4_band_model_specs,
    classify_submodel,
    write_helixville4_band_model_specs,
)


class BuildHelixville4BandModelSpecsTests(unittest.TestCase):
    def test_classify_submodel_identifies_performer_parts(self) -> None:
        self.assertEqual(classify_submodel("HX_SNOWMAN_SINGER_MOUTH_PHONEME"), "phoneme")
        self.assertEqual(classify_submodel("HX_SNOWMAN_GUITARIST_GUITAR_BODY"), "instrument")
        self.assertEqual(classify_submodel("HX_SNOWMAN_BASSIST_PLUCK_ZONE"), "instrument_articulation")
        self.assertEqual(classify_submodel("HX_SNOWMAN_DRUMMER_SNARE"), "drum")
        self.assertEqual(classify_submodel("HX_SNOWMAN_DRUMMER_LEFT_ARM"), "body_motion")

    def test_model_specs_cover_all_band_models_and_groups(self) -> None:
        specs = build_helixville4_band_model_specs()
        model_names = {model["model_name"] for model in specs["models"]}

        self.assertEqual(specs["schema"], "helixville4.band_model_specs.v1")
        self.assertEqual(specs["model_count"], 5)
        self.assertEqual(
            model_names,
            {
                "HX_SNOWMAN_SINGER",
                "HX_SNOWMAN_SINGER_FEMALE",
                "HX_SNOWMAN_GUITARIST",
                "HX_SNOWMAN_BASSIST",
                "HX_SNOWMAN_DRUMMER",
            },
        )
        self.assertEqual(set(specs["groups"]["HX_SNOWMAN_BAND"]), model_names)
        self.assertEqual(set(specs["groups"]["HX_SNOWMAN_VOCALS"]), {"HX_SNOWMAN_SINGER", "HX_SNOWMAN_SINGER_FEMALE"})
        self.assertEqual(set(specs["groups"]["HX_SNOWMAN_INSTRUMENTS"]), {"HX_SNOWMAN_GUITARIST", "HX_SNOWMAN_BASSIST", "HX_SNOWMAN_DRUMMER"})

    def test_specs_include_bounds_and_submodel_kinds(self) -> None:
        specs = build_helixville4_band_model_specs()
        by_model = {model["model_name"]: model for model in specs["models"]}
        singer_submodels = {sub["name"]: sub for sub in by_model["HX_SNOWMAN_SINGER"]["submodels"]}
        drummer_submodels = {sub["name"]: sub for sub in by_model["HX_SNOWMAN_DRUMMER"]["submodels"]}

        self.assertEqual(singer_submodels["HX_SNOWMAN_SINGER_MOUTH_PHONEME"]["kind"], "phoneme")
        self.assertGreater(singer_submodels["HX_SNOWMAN_SINGER_MOUTH_PHONEME"]["bounds_px"]["max_x"], 0)
        self.assertEqual(drummer_submodels["HX_SNOWMAN_DRUMMER_KICK"]["kind"], "drum")
        self.assertGreaterEqual(by_model["HX_SNOWMAN_DRUMMER"]["submodel_count"], 16)

    def test_write_model_specs_creates_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = write_helixville4_band_model_specs(Path(tmp) / "specs.json")
            payload = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(payload["model_count"], 5)
        self.assertTrue(all(model["display_as"] == "Custom" for model in payload["models"]))
        self.assertTrue(all(model["background_svg"].endswith(".svg") for model in payload["models"]))


if __name__ == "__main__":
    unittest.main()
