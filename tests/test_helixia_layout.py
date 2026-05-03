from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.build_helpers.helixia import (
    MEGATREE_CONFIGS,
    NATIVE_XLIGHTS_MODEL_TYPES,
    build_helixia_layout,
)


class HelixiaLayoutTests(unittest.TestCase):
    def test_build_helixia_layout_writes_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            payload = build_helixia_layout(Path(tmp), village_rows=3, village_cols=4)

            self.assertEqual(payload["layout_name"], "Helixia (Helixville4)")
            self.assertEqual(len(payload["village_grid"]["houses"]), 12)
            self.assertTrue((Path(tmp) / "helixia_manifest.json").exists())
            self.assertTrue((Path(tmp) / "HELIXIA_LAYOUT_NOTES.txt").exists())

    def test_required_special_lots_exist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            payload = build_helixia_layout(Path(tmp), village_rows=3, village_cols=4)
            lot_ids = {lot["lot_id"] for lot in payload["special_lots"]}
            required = {
                "ac_all_white",
                "ac_rwg",
                "arches_lot",
                "tunnels_lot",
                "snowman_band_stage",
                "dj_radio_booth",
                "coro_boscoyo_props",
                "radio_tower",
                "wreath_projection",
                "blow_mold_animals",
                "experimental_3d_playground",
            }

            self.assertTrue(required.issubset(lot_ids))

    def test_fibonacci_tree_lot_constraints(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            payload = build_helixia_layout(Path(tmp), village_rows=3, village_cols=4)
            trees = payload["fibonacci_tree_lot"]["trees"]

            self.assertGreaterEqual(len(trees), 8)
            self.assertEqual(trees[0]["tree_id"], "fib_tree_center")
            self.assertEqual(trees[0]["height_ft"], max(tree["height_ft"] for tree in trees))
            self.assertEqual(
                set(payload["fibonacci_tree_lot"]["megatree_configurations"]),
                set(MEGATREE_CONFIGS),
            )

    def test_native_model_coverage_complete(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            payload = build_helixia_layout(Path(tmp), village_rows=3, village_cols=4)
            coverage = payload["native_model_coverage"]

            for model_type in NATIVE_XLIGHTS_MODEL_TYPES:
                self.assertIn(model_type, coverage)
                self.assertGreater(len(coverage[model_type]), 0, f"missing coverage for {model_type}")

    def test_house_styles_have_personality_and_cost(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            payload = build_helixia_layout(Path(tmp), village_rows=3, village_cols=4)
            houses = payload["village_grid"]["houses"]

            self.assertTrue(all(house.get("style_id") for house in houses))
            self.assertTrue(all(house.get("aesthetics") for house in houses))
            self.assertTrue(all(int(house.get("estimated_cost_usd", 0)) > 0 for house in houses))
            self.assertTrue(all(len(house.get("preferences", [])) >= 2 for house in houses))


if __name__ == "__main__":
    unittest.main()
