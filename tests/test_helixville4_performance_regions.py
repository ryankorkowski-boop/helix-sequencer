from __future__ import annotations

import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from tools.build_helpers.helixville4_full_band import add_full_helixville4_band_models


class Helixville4PerformanceRegionTests(unittest.TestCase):
    def build_root(self) -> ET.Element:
        with tempfile.TemporaryDirectory() as tmp:
            layout = Path(tmp) / "layout.xml"
            layout.write_text("<xrgb><models/><modelGroups/></xrgb>", encoding="utf-8")
            add_full_helixville4_band_models(layout)
            return ET.parse(layout).getroot()

    def regions(self, root: ET.Element, model_name: str) -> set[str]:
        model = root.find(f".//model[@name='{model_name}']")
        return {sub.attrib.get("name", "") for sub in model.findall("subModel")}

    def test_bassist_reactive_string_regions_exist(self) -> None:
        root = self.build_root()
        regions = self.regions(root, "HX_SNOWMAN_BASSIST")
        self.assertIn("HX_SNOWMAN_BASSIST_STRING_E", regions)
        self.assertIn("HX_SNOWMAN_BASSIST_STRING_A", regions)
        self.assertIn("HX_SNOWMAN_BASSIST_STRING_D", regions)
        self.assertIn("HX_SNOWMAN_BASSIST_STRING_G", regions)
        self.assertIn("HX_SNOWMAN_BASSIST_PLUCK_ZONE", regions)
        self.assertIn("HX_SNOWMAN_BASSIST_BODY_RESONANCE", regions)

    def test_guitarist_reactive_string_regions_exist(self) -> None:
        root = self.build_root()
        regions = self.regions(root, "HX_SNOWMAN_GUITARIST")
        self.assertIn("HX_SNOWMAN_GUITARIST_PICK_ZONE", regions)
        self.assertIn("HX_SNOWMAN_GUITARIST_STRING_LOW_E", regions)
        self.assertIn("HX_SNOWMAN_GUITARIST_STRING_HIGH_E", regions)
        self.assertIn("HX_SNOWMAN_GUITARIST_PICKUPS", regions)
        self.assertIn("HX_SNOWMAN_GUITARIST_BRIDGE", regions)

    def test_singer_vocal_regions_exist(self) -> None:
        root = self.build_root()
        regions = self.regions(root, "HX_SNOWMAN_SINGER")
        self.assertIn("HX_SNOWMAN_SINGER_MOUTH", regions)
        self.assertIn("HX_SNOWMAN_SINGER_MICROPHONE", regions)
        self.assertIn("HX_SNOWMAN_SINGER_MIC_STAND", regions)
        self.assertIn("HX_SNOWMAN_SINGER_VOCAL_GLOW", regions)

    def test_female_singer_harmony_regions_exist(self) -> None:
        root = self.build_root()
        regions = self.regions(root, "HX_SNOWMAN_SINGER_FEMALE")
        self.assertIn("HX_SNOWMAN_SINGER_FEMALE_BOW", regions)
        self.assertIn("HX_SNOWMAN_SINGER_FEMALE_VOCAL_GLOW", regions)
        self.assertIn("HX_SNOWMAN_SINGER_FEMALE_STAGE_GLOW", regions)
        self.assertIn("HX_SNOWMAN_SINGER_FEMALE_SCARF_TAIL_LEFT", regions)
        self.assertIn("HX_SNOWMAN_SINGER_FEMALE_SCARF_TAIL_RIGHT", regions)

    def test_drummer_kit_regions_exist(self) -> None:
        root = self.build_root()
        regions = self.regions(root, "HX_SNOWMAN_DRUMMER")
        self.assertIn("HX_SNOWMAN_DRUMMER_KICK", regions)
        self.assertIn("HX_SNOWMAN_DRUMMER_SNARE", regions)
        self.assertIn("HX_SNOWMAN_DRUMMER_TOM_LEFT", regions)
        self.assertIn("HX_SNOWMAN_DRUMMER_TOM_RIGHT", regions)
        self.assertIn("HX_SNOWMAN_DRUMMER_CYMBAL_LEFT", regions)
        self.assertIn("HX_SNOWMAN_DRUMMER_CYMBAL_RIGHT", regions)


if __name__ == "__main__":
    unittest.main()
