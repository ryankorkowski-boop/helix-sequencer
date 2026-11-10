from __future__ import annotations

import unittest

from models.helixia_double_helix import DOUBLE_HELIX_SCHEMA, DoubleHelixConfig, build_giant_double_helix


class HelixiaDoubleHelixTests(unittest.TestCase):
    def test_giant_double_helix_has_two_equal_strands_and_rungs(self) -> None:
        payload = build_giant_double_helix()

        self.assertEqual(payload["schema"], DOUBLE_HELIX_SCHEMA)
        self.assertEqual(payload["model_id"], "HELIXIA_GIANT_DOUBLE_HELIX")
        self.assertTrue(payload["validation"]["has_two_equal_strands"])
        self.assertTrue(payload["validation"]["has_rungs"])
        self.assertEqual(len(payload["strand_a"]), len(payload["strand_b"]))
        self.assertGreater(len(payload["rungs"]), 20)
        self.assertEqual(payload["strand_a"][0]["index"], 0)
        self.assertEqual(payload["strand_b"][0]["index"], 0)

    def test_giant_double_helix_has_required_submodels_and_zones(self) -> None:
        payload = build_giant_double_helix()
        submodels = payload["submodels"]

        for name in (
            "HELIXIA_DNA_STRAND_A",
            "HELIXIA_DNA_STRAND_B",
            "HELIXIA_DNA_RUNGS",
            "HELIXIA_DNA_RUNG_ODD",
            "HELIXIA_DNA_RUNG_EVEN",
            "HELIXIA_DNA_TOP_INPUT",
            "HELIXIA_DNA_BOTTOM_OUTPUT",
            "HELIXIA_DNA_CORE",
            "HELIXIA_DNA_FULL",
        ):
            self.assertIn(name, submodels)
            self.assertTrue(submodels[name], name)

        self.assertTrue(payload["validation"]["has_top_input_zone"])
        self.assertTrue(payload["validation"]["has_bottom_output_zone"])
        self.assertTrue(payload["validation"]["has_core_zone"])
        self.assertIn("HELIXIA_DNA_TOP_INPUT", payload["xlights_export_contract"]["must_export_submodels"])

    def test_giant_double_helix_geometry_is_bounded_and_scaled(self) -> None:
        config = DoubleHelixConfig(height_ft=120.0, radius_ft=30.0, turns=4.0, nodes_per_strand=96, rung_every=3)
        payload = build_giant_double_helix(config)
        bounds = payload["bounds_ft"]

        self.assertTrue(payload["validation"]["height_matches_config"])
        self.assertAlmostEqual(bounds["max_y_ft"] - bounds["min_y_ft"], 120.0, places=3)
        self.assertLessEqual(abs(bounds["min_x_ft"]), 30.01)
        self.assertLessEqual(abs(bounds["max_x_ft"]), 30.01)
        self.assertLessEqual(abs(bounds["min_z_ft"]), 30.01)
        self.assertLessEqual(abs(bounds["max_z_ft"]), 30.01)
        self.assertEqual(len(payload["strand_a"]), 96)
        self.assertEqual(len(payload["strand_b"]), 96)

    def test_rungs_connect_matching_strand_nodes(self) -> None:
        payload = build_giant_double_helix(DoubleHelixConfig(nodes_per_strand=32, rung_every=4))
        strand_a_nodes = {point["node_id"] for point in payload["strand_a"]}
        strand_b_nodes = {point["node_id"] for point in payload["strand_b"]}

        for rung in payload["rungs"]:
            self.assertIn(rung["strand_a_node"], strand_a_nodes)
            self.assertIn(rung["strand_b_node"], strand_b_nodes)
            self.assertGreater(rung["length_ft"], 0.0)


if __name__ == "__main__":
    unittest.main()
