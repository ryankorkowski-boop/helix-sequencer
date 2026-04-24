from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from export.snowman_band_json_export import export_band_pack, model_export_payload
from models.snowman_geometry import build_snowman_template
from models.submodel_generation import validate_model, xlights_mapping_hints


class GeometryValidationTests(unittest.TestCase):
    def test_generated_models_validate_without_critical_issues(self) -> None:
        for role in ("singer", "guitarist", "bassist", "drummer"):
            issues = validate_model(build_snowman_template(role, 64))
            self.assertFalse([issue for issue in issues if "outside head" in issue or "empty" in issue], issues)

    def test_export_payload_contains_xlights_hints(self) -> None:
        model = build_snowman_template("guitarist", 64)
        payload = model_export_payload(model)
        self.assertEqual(payload["export_metadata"]["xlights_target"], "custom_model_with_submodels")
        hints = xlights_mapping_hints(model)
        self.assertEqual(hints["face_definition_hint"]["style"], "Matrix or Node Ranges")
        self.assertIn("mouth_A", hints["submodels"])

    def test_export_band_pack_writes_json_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = export_band_pack(Path(tmp), 32)
            self.assertTrue(Path(result["combined_path"]).exists())
            self.assertTrue(Path(result["mouth_library_path"]).exists())
            self.assertEqual(set(result["models"]), {"singer", "guitarist", "bassist", "drummer"})


if __name__ == "__main__":
    unittest.main()
