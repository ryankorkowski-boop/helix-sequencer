from __future__ import annotations

import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from tools.build_helpers.helixville4_full_band import FULL_BAND_SPECS, add_full_helixville4_band_models


class Helixville4FullBandModelTests(unittest.TestCase):
    def build_root(self) -> ET.Element:
        with tempfile.TemporaryDirectory() as tmp:
            layout = Path(tmp) / "layout.xml"
            layout.write_text("<xrgb><models/><modelGroups/></xrgb>", encoding="utf-8")
            add_full_helixville4_band_models(layout)
            return ET.parse(layout).getroot()

    def test_all_approved_band_members_are_exported(self) -> None:
        root = self.build_root()
        exported = {model.attrib.get("name") for model in root.findall(".//model")}
        expected = {spec.model_name for spec in FULL_BAND_SPECS}
        self.assertEqual(expected, expected & exported)

    def test_band_members_are_not_tiny_placeholders(self) -> None:
        root = self.build_root()
        for spec in FULL_BAND_SPECS:
            model = root.find(f".//model[@name='{spec.model_name}']")
            self.assertIsNotNone(model)
            self.assertNotEqual(model.attrib.get("CustomWidth"), "12")
            self.assertNotEqual(model.attrib.get("CustomHeight"), "12")
            self.assertGreaterEqual(int(model.attrib.get("CustomWidth", "0")), 60)
            self.assertGreaterEqual(int(model.attrib.get("CustomHeight", "0")), 60)

    def test_every_member_has_many_named_submodels(self) -> None:
        root = self.build_root()
        for spec in FULL_BAND_SPECS:
            model = root.find(f".//model[@name='{spec.model_name}']")
            submodels = model.findall("subModel")
            self.assertGreaterEqual(len(submodels), 16)
            self.assertTrue(all(sub.attrib.get("name", "").startswith(spec.model_name) for sub in submodels))


if __name__ == "__main__":
    unittest.main()
