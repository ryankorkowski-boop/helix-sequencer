from __future__ import annotations

import unittest

from models.working_band_member import WORKING_MEMBER_SCHEMA, build_working_bassist


class WorkingBandMemberTests(unittest.TestCase):
    def test_working_bassist_has_required_geometry_and_animation(self) -> None:
        payload = build_working_bassist()

        self.assertEqual(payload["schema"], WORKING_MEMBER_SCHEMA)
        self.assertEqual(payload["role"], "bassist")
        self.assertEqual(payload["status"], "working_member_slice")
        self.assertTrue(payload["validation"]["has_required_submodels"])
        self.assertTrue(payload["validation"]["has_animation_frames"])
        self.assertTrue(payload["validation"]["mouth_inside_head"])
        self.assertEqual(payload["missing_required_submodels"], [])

        node_counts = payload["submodel_node_counts"]
        for submodel_name in payload["required_submodels"]:
            self.assertIn(submodel_name, node_counts)
            self.assertGreater(node_counts[submodel_name], 0)

        cue_targets = {cue["submodel"] for cue in payload["default_cues"]}
        self.assertIn("pluck_zone", cue_targets)
        self.assertIn("neck_zone", cue_targets)
        self.assertIn("bass_body", cue_targets)

    def test_working_bassist_export_contract_names_smoke_test_targets(self) -> None:
        payload = build_working_bassist()
        contract = payload["xlights_export_contract"]

        self.assertEqual(contract["target_model_type"], "custom_model_with_submodels")
        self.assertEqual(contract["node_order"], "row_major_top_left_1_based")
        self.assertIn("pluck_zone", contract["must_export_submodels"])
        self.assertIn("band_body_core", contract["must_export_submodels"])
        self.assertIn("neck_zone", contract["first_sequence_smoke_test"])


if __name__ == "__main__":
    unittest.main()
