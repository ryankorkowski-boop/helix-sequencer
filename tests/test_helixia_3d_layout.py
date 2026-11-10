from __future__ import annotations

import json
import tempfile
from pathlib import Path
import unittest

from models.layout_grounding import GROUNDING_SCHEMA, align_model_to_ground, validate_ground_alignment
from tools.build_helpers.helixia_3d import HELIXIA_3D_SCHEMA, build_helixia_3d_layout


class LayoutGroundingTests(unittest.TestCase):
    def test_align_model_to_ground_shifts_point_cloud_to_z_zero(self) -> None:
        model = {
            "model_id": "floating_test",
            "points": [
                {"x": 0, "y": 0, "z": 12},
                {"x": 1, "y": 0, "z": 22},
            ],
            "height_ft": 10,
            "intentionally_elevated": False,
        }
        grounded = align_model_to_ground(model)

        self.assertEqual(grounded["grounding_schema"], GROUNDING_SCHEMA)
        self.assertTrue(grounded["grounded"])
        self.assertEqual(grounded["min_z_ft"], 0.0)
        self.assertEqual(grounded["max_z_ft"], 10.0)
        self.assertEqual(grounded["points"][0]["z"], 0.0)
        self.assertEqual(grounded["points"][1]["z"], 10.0)

    def test_validate_ground_alignment_flags_no_grounded_floaters(self) -> None:
        models = [
            {"model_id": "ok", "min_z_ft": 0.0, "intentionally_elevated": False},
            {"model_id": "elevated", "min_z_ft": 8.0, "intentionally_elevated": True},
        ]
        report = validate_ground_alignment(models)

        self.assertTrue(report["all_grounded_models_on_ground"])
        self.assertTrue(report["no_grounded_models_below_ground"])
        self.assertEqual(report["floating_grounded_models"], [])


class Helixia3DLayoutTests(unittest.TestCase):
    def test_helixia_3d_layout_writes_grounded_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            payload = build_helixia_3d_layout(Path(tmp), village_rows=3, village_cols=4)
            manifest_path = Path(tmp) / "helixia_3d_manifest.json"

            self.assertEqual(payload["schema"], HELIXIA_3D_SCHEMA)
            self.assertTrue(manifest_path.exists())
            self.assertTrue(payload["validation"]["all_grounded_models_on_ground"])
            self.assertTrue(payload["validation"]["no_grounded_models_below_ground"])
            self.assertTrue(payload["validation"]["projection_is_derived_from_3d"])
            self.assertGreater(len(payload["models"]), 0)
            saved = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(saved["schema"], HELIXIA_3D_SCHEMA)

    def test_all_grounded_models_have_anchor_z_and_min_z_on_ground(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            payload = build_helixia_3d_layout(Path(tmp), village_rows=3, village_cols=4)

            for model in payload["models"]:
                if model.get("intentionally_elevated"):
                    continue
                self.assertEqual(model["anchor_z_ft"], 0.0, model["model_id"])
                self.assertEqual(model["min_z_ft"], 0.0, model["model_id"])
                self.assertGreaterEqual(model["max_z_ft"], 0.0, model["model_id"])
                self.assertTrue(model["grounded"], model["model_id"])

    def test_double_helix_is_present_grounded_and_vertically_spans(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            payload = build_helixia_3d_layout(Path(tmp), village_rows=3, village_cols=4)
            models = {model["model_id"]: model for model in payload["models"]}
            helix = models["HELIXIA_GIANT_DOUBLE_HELIX"]

            self.assertTrue(payload["validation"]["has_double_helix"])
            self.assertTrue(payload["validation"]["double_helix_grounded"])
            self.assertEqual(helix["anchor_z_ft"], 0.0)
            self.assertEqual(helix["min_z_ft"], 0.0)
            self.assertGreater(helix["max_z_ft"], 80.0)
            self.assertGreater(helix["height_ft"], 80.0)
            self.assertEqual(helix["base_contact_mode"], "lowest_point")
            self.assertIn("HELIXIA_DNA_FULL", helix["submodels"])

    def test_stage_and_floor_related_models_are_grounded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            payload = build_helixia_3d_layout(Path(tmp), village_rows=3, village_cols=4)
            stage_models = [model for model in payload["models"] if model.get("stage_zone")]

            self.assertTrue(payload["validation"]["has_stage_models"])
            self.assertTrue(stage_models)
            self.assertTrue(any(model["lot_id"] == "snowman_band_stage" for model in stage_models))
            self.assertTrue(any(model["model_id"] == "HELIXIA_GIANT_DOUBLE_HELIX" for model in stage_models))
            for model in stage_models:
                self.assertEqual(model["min_z_ft"], 0.0, model["model_id"])
                self.assertTrue(model["grounded"], model["model_id"])

    def test_2d_projection_is_derived_from_3d_and_keeps_lots_distinguishable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            payload = build_helixia_3d_layout(Path(tmp), village_rows=3, village_cols=4)
            projection = payload["projection_2d"]
            footprints = projection["footprints"]
            lot_ids = {item["lot_id"] for item in footprints}

            self.assertTrue(projection["readability"]["projection_is_derived_from_3d"])
            self.assertTrue(projection["readability"]["houses_preserve_grid"])
            self.assertTrue(projection["readability"]["special_lots_preserve_world_positions"])
            self.assertTrue(projection["readability"]["double_helix_uses_central_landmark_footprint"])
            self.assertIn("house_1_1", lot_ids)
            self.assertIn("snowman_band_stage", lot_ids)
            self.assertIn("giant_double_helix", lot_ids)
            self.assertLess(projection["bounds_ft"]["min_x_ft"], projection["bounds_ft"]["max_x_ft"])
            self.assertLess(projection["bounds_ft"]["min_y_ft"], projection["bounds_ft"]["max_y_ft"])


if __name__ == "__main__":
    unittest.main()
