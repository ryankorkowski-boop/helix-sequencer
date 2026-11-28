"""Fast, deterministic contract tests for the isolated Infinity engineering layout."""
from __future__ import annotations

import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from tools.export_infinity_xlights_layout import EXPECTED_PIXELS, export_layout


class InfinityLayoutTests(unittest.TestCase):
    def test_spatial_model_export_and_channels(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            dst = Path(folder)
            manifest = export_layout(dst, include_band=False)
            self.assertEqual(manifest["pixels_spatial"], 38928)
            self.assertEqual(manifest["rgb_channels_spatial"], 116784)
            self.assertGreater(manifest["spatial_model_count"], 300)
            self.assertEqual(sum(manifest["family_pixel_counts"].values()), EXPECTED_PIXELS)
            root = ET.parse(dst / "xlights_rgbeffects.xml").getroot()
            all_models = root.findall("./models/model")
            ornaments = next(g for g in root.findall("./modelGroups/modelGroup") if g.get("name") == "HX_INFINITY_NATIVE_ORNAMENTS")
            ornament_names = set(ornaments.get("models").split(","))
            self.assertEqual(len(ornament_names), manifest["native_ornament_count"])
            self.assertEqual(len(all_models), manifest["total_xml_model_count"])
            models = [m for m in all_models if m.get("name") not in ornament_names]
            self.assertTrue({"Star", "Wreath", "Tree 360"}.issubset({m.get("DisplayAs") for m in all_models}))
            self.assertEqual(len(models), manifest["spatial_model_count"])
            actual = sorted((int(m.get("StartChannel")), int(m.get("parm2")), m.get("name")) for m in models)
            cursor = 1
            for start, count, name in actual:
                self.assertEqual(start, cursor, name)
                cursor += count * 3
            self.assertEqual(cursor, 107665)
            self.assertTrue(all(len(m.get("PointData").split(",")) == int(m.get("NumPoints")) * 3 for m in models))
            groups = {g.get("name"): g.get("models", "") for g in root.findall("./modelGroups/modelGroup")}
            self.assertEqual(len(groups["HX_INFINITY_DOUBLE_HELIX"].split(",")), 4)
            self.assertIn("HX_INFINITY_PIXEL_VOLUME", groups)
            for route in ("WEST_TO_EAST", "GROUND_TO_SKY", "FRONT_TO_BACK", "CENTER_OUT", "CLOCKWISE_ORBIT"):
                self.assertEqual(set(groups["HX_INFINITY_SPATIAL_"+route].split(",")), {m.get("name") for m in models})
            self.assertTrue(any(m.get("DisplayAs") == "Arches" for m in models))
            self.assertTrue(any(m.get("DisplayAs") == "Single Line" for m in models))
            self.assertEqual(sum(1 for m in models if m.get("name", "").startswith("HX_INFINITY_PixelVolume_")), 256)
            self.assertEqual(json.loads((dst / "infinity_manifest.json").read_text())["owner_approval"], False)

    def test_imports_original_six_role_canonical_band(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            dst = Path(folder)
            manifest = export_layout(dst, include_band=True)
            root = ET.parse(dst / "xlights_rgbeffects.xml").getroot()
            band = next(x for x in root.findall("./modelGroups/modelGroup") if x.get("name") == "HX_SNOWMAN_BAND")
            self.assertEqual(set(band.get("models").split(",")), set(manifest["band_info"]["model_names"]))
            self.assertEqual(len(band.get("models").split(",")), 6)
            self.assertIn("PIANO", band.get("models").upper())
            self.assertEqual(manifest["band_info"]["performer_count"], 6)
            self.assertEqual(set(manifest["band_info"]["roles"]), {"drummer", "bass", "guitar", "piano", "lead", "harmony"})
            self.assertIn("UNAPPROVED", manifest["band_verification"])


if __name__ == "__main__":
    unittest.main()
