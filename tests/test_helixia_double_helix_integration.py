from __future__ import annotations

import json
import tempfile
from pathlib import Path
import unittest

from models.helixia_double_helix import DOUBLE_HELIX_SCHEMA
from tools.build_helpers.helixia_double_helix_integration import (
    DOUBLE_HELIX_GROUP,
    DOUBLE_HELIX_LOT_ID,
    build_helixia_layout_with_double_helix,
)


class HelixiaDoubleHelixIntegrationTests(unittest.TestCase):
    def test_helixia_layout_with_double_helix_writes_manifest_lot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            payload = build_helixia_layout_with_double_helix(Path(tmp), village_rows=3, village_cols=4)
            manifest_path = Path(tmp) / "helixia_manifest.json"
            notes_path = Path(tmp) / "HELIXIA_LAYOUT_NOTES.txt"

            self.assertTrue(manifest_path.exists())
            self.assertTrue(notes_path.exists())
            self.assertTrue((Path(tmp) / "xlights_rgbeffects.xml").exists())
            self.assertEqual(payload["giant_double_helix"]["schema"], DOUBLE_HELIX_SCHEMA)
            self.assertTrue(payload["requirements_satisfied"]["giant_double_helix_centerpiece_present"])
            self.assertTrue(payload["requirements_satisfied"]["giant_double_helix_geometry_backed"])
            self.assertIn("Giant Lighted Double Helix", notes_path.read_text(encoding="utf-8"))

            saved = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertIn("giant_double_helix", saved)
            self.assertEqual(saved["giant_double_helix"]["model_id"], "HELIXIA_GIANT_DOUBLE_HELIX")

    def test_double_helix_special_lot_is_geometry_backed_and_placeholder_safe(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            payload = build_helixia_layout_with_double_helix(Path(tmp), village_rows=3, village_cols=4)
            lots = {lot["lot_id"]: lot for lot in payload["special_lots"]}
            lot = lots[DOUBLE_HELIX_LOT_ID]

            self.assertEqual(lot["display_name"], "Giant Lighted Double Helix")
            self.assertTrue(lot["geometry_only"])
            self.assertTrue(lot["xlights_placeholder_safe"])
            self.assertIn("HELIXIA_GIANT_DOUBLE_HELIX", lot["contains"])
            self.assertIn("HELIXIA_DNA_STRAND_A", lot["contains"])
            self.assertIn("HELIXIA_DNA_STRAND_B", lot["contains"])
            self.assertIn("HELIXIA_DNA_RUNGS", lot["contains"])
            self.assertIn("HELIXIA_DNA_TOP_INPUT", lot["contains"])
            self.assertIn("HELIXIA_DNA_BOTTOM_OUTPUT", lot["contains"])
            self.assertGreater(lot["height_ft"], 80)
            self.assertGreater(lot["radius_ft"], 10)
            self.assertIn("HELIXIA_DNA_FULL", lot["submodels"])

    def test_layout_intelligence_tracks_double_helix_centerpiece(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            payload = build_helixia_layout_with_double_helix(Path(tmp), village_rows=3, village_cols=4)
            intelligence = payload["layout_intelligence"]
            special = {lot["lot_id"]: lot for lot in intelligence["special_lots"]}

            self.assertIn(DOUBLE_HELIX_LOT_ID, special)
            self.assertTrue(special[DOUBLE_HELIX_LOT_ID]["stage_zone"])
            self.assertTrue(special[DOUBLE_HELIX_LOT_ID]["geometry_only"])
            self.assertIn("giant_double_helix", intelligence["performer_models"])
            self.assertIn("HELIXIA_GIANT_DOUBLE_HELIX", intelligence["performer_models"]["giant_double_helix"])
            self.assertIn(DOUBLE_HELIX_GROUP, intelligence["required_groups"])
            self.assertTrue(intelligence["two_dimensional_readability"]["double_helix_uses_central_vertical_landmark"])


if __name__ == "__main__":
    unittest.main()
