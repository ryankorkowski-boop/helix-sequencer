from __future__ import annotations

import json
import tempfile
from pathlib import Path
import unittest

from export.helixia_double_helix_xlights_plan import (
    DOUBLE_HELIX_XLIGHTS_PLAN_SCHEMA,
    build_double_helix_xlights_plan,
    write_double_helix_xlights_plan,
)


class HelixiaDoubleHelixXlightsPlanTests(unittest.TestCase):
    def test_xlights_plan_contains_model_submodels_and_effects(self) -> None:
        plan = build_double_helix_xlights_plan()

        self.assertEqual(plan["schema"], DOUBLE_HELIX_XLIGHTS_PLAN_SCHEMA)
        self.assertEqual(plan["model_id"], "HELIXIA_GIANT_DOUBLE_HELIX")
        self.assertEqual(plan["status"], "xlights_custom_model_plan")
        self.assertEqual(plan["model_requirements"]["DisplayAs"], "Custom")
        self.assertGreater(plan["model_requirements"]["strand_a_nodes"], 100)
        self.assertGreater(plan["model_requirements"]["strand_b_nodes"], 100)
        self.assertGreater(plan["model_requirements"]["rung_count"], 20)
        self.assertTrue(plan["validation"]["all_required_submodels_planned"])
        self.assertTrue(plan["validation"]["has_effect_placements"])
        self.assertTrue(plan["validation"]["all_effect_targets_planned"])
        self.assertTrue(plan["validation"]["has_audio_in_zone"])
        self.assertTrue(plan["validation"]["has_lights_out_zone"])
        self.assertTrue(plan["validation"]["has_drum_rung_plan"])

        submodels = {row["name"] for row in plan["submodel_requirements"]}
        self.assertIn("HELIXIA_DNA_STRAND_A", submodels)
        self.assertIn("HELIXIA_DNA_STRAND_B", submodels)
        self.assertIn("HELIXIA_DNA_RUNGS", submodels)
        self.assertIn("HELIXIA_DNA_TOP_INPUT", submodels)
        self.assertIn("HELIXIA_DNA_BOTTOM_OUTPUT", submodels)

        tracks = set(plan["timing_tracks_required"])
        self.assertIn("drums", tracks)
        self.assertIn("phoneme", tracks)
        self.assertIn("phrase", tracks)
        self.assertIn("guitar", tracks)
        self.assertIn("bass", tracks)

    def test_xlights_plan_includes_safety_warning_before_xml_mutation(self) -> None:
        plan = build_double_helix_xlights_plan()
        warnings = "\n".join(plan["warnings"])

        self.assertIn("Plan only", warnings)
        self.assertIn("do not merge", warnings)
        self.assertIn("xlights_rgbeffects.xml", warnings)

    def test_write_xlights_plan_outputs_json_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "double_helix_xlights_plan.json"
            result = write_double_helix_xlights_plan(output_path)

            self.assertEqual(result["path"], str(output_path))
            self.assertEqual(result["schema"], DOUBLE_HELIX_XLIGHTS_PLAN_SCHEMA)
            self.assertTrue(result["validation"]["all_required_submodels_planned"])
            self.assertTrue(output_path.exists())
            data = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(data["model_id"], "HELIXIA_GIANT_DOUBLE_HELIX")
            self.assertGreater(data["effect_placements"].__len__(), 0)


if __name__ == "__main__":
    unittest.main()
