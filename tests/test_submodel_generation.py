from __future__ import annotations

import unittest

from models.snowman_geometry import build_band_templates, build_snowman_template


class SubmodelGenerationTests(unittest.TestCase):
    def test_all_band_members_have_required_submodels(self) -> None:
        required = {"head", "mouth_A", "mouth_E", "mouth_I", "mouth_O", "mouth_U", "mouth_MBP", "left_arm", "right_arm", "body_top", "body_bottom", "mouth_all", "band_body_core"}
        for model in build_band_templates(64).values():
            self.assertTrue(required.issubset(model.submodels), model.id)
            self.assertTrue(all(submodel.included_coordinates for submodel in model.submodels.values()))

    def test_role_specific_submodels_exist(self) -> None:
        self.assertIn("mic_stand", build_snowman_template("singer").submodels)
        self.assertIn("strum_zone", build_snowman_template("guitarist").submodels)
        self.assertIn("pluck_zone", build_snowman_template("bassist").submodels)
        self.assertIn("drumkit_all", build_snowman_template("drummer").submodels)


if __name__ == "__main__":
    unittest.main()
