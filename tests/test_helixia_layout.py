from __future__ import annotations

import tempfile
import unittest
import json
from pathlib import Path
import xml.etree.ElementTree as ET

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
            report_path = Path(tmp) / "helixia_layout_intelligence.json"

            self.assertEqual(payload["layout_name"], "Helixia (Helixville4)")
            self.assertEqual(len(payload["village_grid"]["houses"]), 12)
            self.assertTrue((Path(tmp) / "helixia_manifest.json").exists())
            self.assertTrue(report_path.exists())
            self.assertTrue((Path(tmp) / "HELIXIA_LAYOUT_NOTES.txt").exists())
            self.assertTrue((Path(tmp) / "xlights_rgbeffects.xml").exists())
            self.assertGreater(payload["xlights_layout"]["model_count"], 0)
            self.assertEqual(json.loads(report_path.read_text(encoding="utf-8")), payload["layout_intelligence"])

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

    def test_layout_intelligence_metadata_proves_required_roles(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            payload = build_helixia_layout(Path(tmp), village_rows=3, village_cols=4)
            intelligence = payload["layout_intelligence"]
            model_metadata = intelligence["model_type_metadata"]
            performer_metadata = intelligence["performer_metadata"]

            self.assertEqual(intelligence["schema"], "helixia.layout_intelligence.v1")
            self.assertEqual(intelligence["report_filename"], "helixia_layout_intelligence.json")
            self.assertTrue(intelligence["coverage_complete"])
            self.assertEqual(len(intelligence["house_lots"]), 12)
            self.assertIn("HELIXIA_STAGE", intelligence["required_groups"])
            self.assertIn("HX_LOT_SNOWMAN_BAND_STAGE", intelligence["required_groups"])
            self.assertIn("HX_LOT_DJ_RADIO_BOOTH", intelligence["required_groups"])
            self.assertEqual(model_metadata["line"]["visual_role"], "structure")
            self.assertEqual(model_metadata["line"]["prop_family"], "roofline_or_outline")
            self.assertEqual(model_metadata["matrix"]["visual_role"], "detail_surface")
            self.assertEqual(model_metadata["tree"]["visual_role"], "hero")
            for model_type in ("line", "matrix", "tree", "custom", "dmx"):
                self.assertIn("ac_pixel_classification", model_metadata[model_type])
                self.assertIn("power_notes", model_metadata[model_type])
                self.assertIn("safe_max_density", model_metadata[model_type])
                self.assertIn("default_color_behavior", model_metadata[model_type])
            self.assertEqual(performer_metadata["snowman_band"]["performer_role"], "stage_band")
            self.assertEqual(performer_metadata["cactus"]["performer_role"], "comic_dj_host")
            self.assertEqual(performer_metadata["tubeman"]["performer_role"], "kinetic_hype_character")
            self.assertIn("lead_singer", performer_metadata["snowman_band"]["members"])
            self.assertIn("dj_cactus", performer_metadata["cactus"]["members"])
            self.assertIn("inflatable_tube_man", performer_metadata["tubeman"]["members"])
            lot_by_id = {lot["lot_id"]: lot for lot in intelligence["special_lots"]}
            self.assertTrue(lot_by_id["ac_all_white"]["legacy_control_zone"])
            self.assertEqual(lot_by_id["ac_all_white"]["model_type_metadata"]["line"]["visual_role"], "structure")
            self.assertEqual(lot_by_id["dj_radio_booth"]["model_type_metadata"]["custom"]["visual_role"], "performer_or_special")

    def test_build_helixia_layout_writes_parseable_xlights_xml(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            payload = build_helixia_layout(Path(tmp), village_rows=3, village_cols=4)
            parsed = xmp.parse_layout(Path(tmp) / "xlights_rgbeffects.xml")

            # Canonical artifact counts
            self.assertEqual(len(parsed.root_models()), 105)
            self.assertEqual(len(parsed.groups), 49)
            self.assertEqual(payload["xlights_layout"]["model_count"], 105)

            self.assertIn("HELIXIA_ALL", parsed.groups)
            self.assertIn("HELIXIA_STAGE", parsed.groups)
            self.assertIn("HELIXIA_HOUSES", parsed.groups)
            self.assertGreaterEqual(len(parsed.submodel_names()), 300)

    def test_helixia_xlights_xml_covers_required_model_families(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            build_helixia_layout(Path(tmp), village_rows=3, village_cols=4)
            parsed = xmp.parse_layout(Path(tmp) / "xlights_rgbeffects.xml")
            types = {model.type for model in parsed.models.values()}

            for model_type in ("line", "matrix", "tree", "arch", "cane", "star", "spinner", "custom"):
                self.assertIn(model_type, types)
            self.assertIn("HX_FAMILY_MATRIX", parsed.groups)
            self.assertIn("HX_FAMILY_CUSTOM", parsed.groups)

    def test_helixia_xlights_xml_uses_xlights_model_type_tokens(self) -> None:
        valid_display_as = {
            "Arches",
            "Candy Canes",
            "Circle",
            "Custom",
            "DmxGeneral",
            "Horiz Matrix",
            "Icicles",
            "Single Line",
            "Sphere",
            "Spinner",
            "Star",
            "Tree 360",
            "Window Frame",
        }
        with tempfile.TemporaryDirectory() as tmp:
            build_helixia_layout(Path(tmp), village_rows=3, village_cols=4)
            root = ET.parse(Path(tmp) / "xlights_rgbeffects.xml").getroot()
            models = root.find("models")
            self.assertIsNotNone(models)
            display_values = {model.attrib.get("DisplayAs", "") for model in list(models)}

            self.assertTrue(display_values.issubset(valid_display_as))
            self.assertNotIn("Candy Cane", display_values)
            self.assertNotIn("Matrix", display_values)
            self.assertNotIn("DMX General", display_values)

    def test_helixia_xlights_xml_attaches_models_to_default_preview(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            build_helixia_layout(Path(tmp), village_rows=3, village_cols=4)
            root = ET.parse(Path(tmp) / "xlights_rgbeffects.xml").getroot()
            models = root.find("models")
            groups = root.find("modelGroups")
            view_objects = root.find("view_objects")
            self.assertIsNotNone(models)
            self.assertIsNotNone(groups)
            self.assertIsNotNone(view_objects)

            for model in list(models):
                self.assertEqual(model.attrib.get("LayoutGroup"), "Default")
                self.assertEqual(model.attrib.get("versionNumber"), "7")
                self.assertEqual(model.attrib.get("Antialias"), "1")
                self.assertIsNotNone(model.find("ControllerConnection"))

            for group in list(groups):
                self.assertEqual(group.attrib.get("LayoutGroup"), "Default")

            self.assertIsNotNone(view_objects.find("view_object[@name='Gridlines']"))
            self.assertIsNotNone(root.find("layoutGroups"))

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

    def test_committed_helixia_artifacts_are_parser_valid(self) -> None:
        committed_xml = ROOT / "helixville4" / "xlights_rgbeffects.xml"
        committed_manifest = ROOT / "helixville4" / "helixia_manifest.json"
        parsed = xmp.parse_layout(committed_xml)

        # Canonical artifact validation
        self.assertEqual(len(parsed.root_models()), 105)
        self.assertEqual(len(parsed.groups), 49)
        self.assertGreaterEqual(len(parsed.submodel_names()), 300)
        self.assertTrue(committed_manifest.exists())


if __name__ == "__main__":
    unittest.main()
