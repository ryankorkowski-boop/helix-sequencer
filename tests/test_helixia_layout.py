from __future__ import annotations

import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from core import model_parser as xmp
from helix_layout.layout_health import build_layout_health_report
from tools.build_helpers.helixia import (
    MEGATREE_CONFIGS,
    NATIVE_XLIGHTS_MODEL_TYPES,
    build_helixia_layout,
)


ROOT = Path(__file__).resolve().parents[1]


class HelixiaLayoutTests(unittest.TestCase):
    def test_build_helixia_layout_writes_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            payload = build_helixia_layout(Path(tmp), village_rows=3, village_cols=4)

            self.assertEqual(payload["layout_name"], "Helixia (Helixville4)")
            self.assertEqual(len(payload["village_grid"]["houses"]), 12)
            self.assertTrue((Path(tmp) / "helixia_manifest.json").exists())
            self.assertTrue((Path(tmp) / "HELIXIA_LAYOUT_NOTES.txt").exists())
            self.assertTrue((Path(tmp) / "xlights_rgbeffects.xml").exists())
            self.assertGreater(payload["xlights_layout"]["model_count"], 0)

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

    def test_layout_intelligence_metadata_proves_required_roles(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            payload = build_helixia_layout(Path(tmp), village_rows=3, village_cols=4)
            intelligence = payload["layout_intelligence"]

            self.assertEqual(intelligence["schema"], "helixia.layout_intelligence.v1")
            self.assertTrue(intelligence["coverage_complete"])
            self.assertEqual(len(intelligence["house_lots"]), 12)
            self.assertEqual(intelligence["role_by_model_type"]["arch"], "travel")
            self.assertEqual(intelligence["role_by_model_type"]["tree"], "hero")
            self.assertEqual(intelligence["role_by_model_type"]["window_frame"], "structure")
            self.assertIn("HELIXIA_STAGE", intelligence["required_groups"])
            self.assertIn("HX_LOT_SNOWMAN_BAND_STAGE", intelligence["required_groups"])
            self.assertIn("HX_LOT_DJ_RADIO_BOOTH", intelligence["required_groups"])

    def test_layout_intelligence_metadata_proves_performer_models(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            payload = build_helixia_layout(Path(tmp), village_rows=3, village_cols=4)
            performers = payload["layout_intelligence"]["performer_models"]

            snowman_band = set(performers["snowman_band"])
            cactus_tubeman = set(performers["cactus_tubeman"])

            self.assertIn("HX_SNOWMAN_BASSIST_BODY", snowman_band)
            self.assertIn("HX_SNOWMAN_GUITARIST_INSTRUMENT", snowman_band)
            self.assertIn("HX_SNOWMAN_DRUMMER_INSTRUMENT", snowman_band)
            self.assertIn("HX_SNOWMAN_SINGER_BODY", snowman_band)
            self.assertIn("HX_SNOWMAN_SINGER_FEMALE_BODY", snowman_band)
            self.assertIn("HX_CACTUS_BODY", cactus_tubeman)
            self.assertIn("HX_CACTUS_FACE", cactus_tubeman)
            self.assertIn("HX_TUBEMAN_BODY", cactus_tubeman)
            self.assertIn("HX_TUBEMAN_ARMS", cactus_tubeman)
            self.assertIn("HX_DJ_BOOTH", cactus_tubeman)

    def test_layout_intelligence_marks_stage_ac_and_2d_readability(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            payload = build_helixia_layout(Path(tmp), village_rows=3, village_cols=4)
            intelligence = payload["layout_intelligence"]
            special = {lot["lot_id"]: lot for lot in intelligence["special_lots"]}

            self.assertTrue(special["snowman_band_stage"]["stage_zone"])
            self.assertTrue(special["dj_radio_booth"]["stage_zone"])
            self.assertTrue(special["ac_all_white"]["legacy_control_zone"])
            self.assertTrue(special["ac_rwg"]["legacy_control_zone"])
            self.assertTrue(intelligence["two_dimensional_readability"]["houses_use_grid"])
            self.assertTrue(intelligence["two_dimensional_readability"]["performers_use_stage_zone"])
            self.assertTrue(intelligence["two_dimensional_readability"]["hero_trees_use_separate_lot"])

    def test_build_helixia_layout_writes_parseable_xlights_xml(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            payload = build_helixia_layout(Path(tmp), village_rows=3, village_cols=4)
            parsed = xmp.parse_layout(Path(tmp) / "xlights_rgbeffects.xml")

            self.assertEqual(len(parsed.root_models()), payload["xlights_layout"]["model_count"])
            self.assertIn("HELIXIA_ALL", parsed.groups)
            self.assertIn("HELIXIA_STAGE", parsed.groups)
            self.assertIn("HELIXIA_HOUSES", parsed.groups)
            self.assertIn("HX_FLOOR_PIANO_BASE", parsed.models)
            self.assertIn("HX_REINDEER_DANCE_BODY", parsed.models)
            self.assertGreaterEqual(len(parsed.submodel_names()), 160)

    def test_helixia_xlights_xml_covers_required_model_families(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            build_helixia_layout(Path(tmp), village_rows=3, village_cols=4)
            parsed = xmp.parse_layout(Path(tmp) / "xlights_rgbeffects.xml")
            types = {model.type for model in parsed.models.values()}

            for model_type in ("line", "matrix", "tree", "arch", "cane", "star", "spinner", "custom"):
                self.assertIn(model_type, types)
            self.assertIn("HX_FAMILY_MATRIX", parsed.groups)
            self.assertIn("HX_FAMILY_CUSTOM", parsed.groups)

    def test_helixia_candy_cane_models_use_xlights_import_token(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            build_helixia_layout(Path(tmp), village_rows=3, village_cols=4)
            layout_path = Path(tmp) / "xlights_rgbeffects.xml"
            root = ET.parse(layout_path).getroot()
            candy_models = [
                model
                for model in root.findall(".//model")
                if "CANDY_CANE" in str(model.attrib.get("name", ""))
            ]

            self.assertGreater(len(candy_models), 0)
            self.assertEqual({model.attrib.get("DisplayAs") for model in candy_models}, {"CandyCane"})
            parsed = xmp.parse_layout(layout_path)
            self.assertTrue(all(parsed.models[model.attrib["name"]].type == "cane" for model in candy_models))

    def test_helixia_generated_layout_has_complex_prop_submodels(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            build_helixia_layout(Path(tmp), village_rows=3, village_cols=4)
            layout_path = Path(tmp) / "xlights_rgbeffects.xml"
            parsed = xmp.parse_layout(layout_path)
            health = build_layout_health_report(layout_path).to_dict()

            self.assertEqual(health["no_submodels_for_complex_props"], [])
            self.assertIn("HX_HOUSE_1_2_MATRIX/TOP", parsed.models)
            self.assertIn("HX_HOUSE_1_4_SPINNER/ARM_01", parsed.models)
            self.assertIn("HX_FIB_FIB_TREE_CENTER/SPIRAL", parsed.models)
            self.assertIn("HX_SNOWMAN_BAND_STAGE_CUSTOM/HEAD", parsed.models)

    def test_committed_helixia_artifacts_are_parser_valid_and_regenerate_stably(self) -> None:
        committed_xml = ROOT / "helixville4" / "xlights_rgbeffects.xml"
        committed_manifest = ROOT / "helixville4" / "helixia_manifest.json"
        parsed = xmp.parse_layout(committed_xml)

        with tempfile.TemporaryDirectory() as tmp:
            payload = build_helixia_layout(Path(tmp), village_rows=3, village_cols=4)
            generated_xml = Path(tmp) / "xlights_rgbeffects.xml"
            generated = xmp.parse_layout(generated_xml)

            self.assertEqual(committed_xml.read_bytes(), generated_xml.read_bytes())
            self.assertEqual(len(parsed.root_models()), 105)
            self.assertEqual(len(parsed.groups), 49)
            self.assertEqual(len(parsed.submodel_names()), 345)
            self.assertEqual(len(generated.root_models()), len(parsed.root_models()))
            self.assertEqual(payload["xlights_layout"]["model_count"], 105)
            self.assertTrue(committed_manifest.exists())


if __name__ == "__main__":
    unittest.main()
