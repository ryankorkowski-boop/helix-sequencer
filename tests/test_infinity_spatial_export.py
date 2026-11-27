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
            self.assertEqual(manifest["pixels_spatial"], 35888)
            self.assertEqual(manifest["rgb_channels_spatial"], 107664)
            self.assertGreater(manifest["spatial_model_count"], 300)
            self.assertEqual(sum(manifest["family_pixel_counts"].values()), EXPECTED_PIXELS)
            root = ET.parse(dst / "xlights_rgbeffects.xml").getroot()
            models = root.findall("./models/model")
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
            self.assertEqual(sum(1 for m in models if m.get("name", "").startswith("HX_INFINITY_PixelVolume_")), 256)
            self.assertEqual(json.loads((dst / "infinity_manifest.json").read_text())["owner_approval"], False)

    def test_imports_existing_band_without_claiming_sixth_member(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            dst = Path(folder)
            manifest = export_layout(dst, include_band=True)
            root = ET.parse(dst / "xlights_rgbeffects.xml").getroot()
            band = next(x for x in root.findall("./modelGroups/modelGroup") if x.get("name") == "HX_SNOWMAN_BAND")
            self.assertIn("HX_SNOWMAN_DRUMMER", band.get("models"))
            self.assertNotIn("KEYBOARD", band.get("models").upper())
            self.assertIn("UNAPPROVED", manifest["band_verification"])


if __name__ == "__main__":
    unittest.main()
