from __future__ import annotations

import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from tools.build_helpers.helixville4_finished_band import (
    DRUMMER_SUBMODEL_NAMES,
    add_finished_helixville4_band_models,
    build_drummer_submodel_runs,
)


class FinishedHelixville4DrummerTests(unittest.TestCase):
    def test_drummer_exports_many_real_submodels(self) -> None:
        runs = build_drummer_submodel_runs()
        self.assertGreaterEqual(len(runs), 16)
        self.assertEqual(len(runs), len(DRUMMER_SUBMODEL_NAMES))
        self.assertTrue(any(run.name.endswith("KICK") for run in runs))
        self.assertTrue(any(run.name.endswith("CYMBAL_LEFT") for run in runs))
        self.assertTrue(all(run.count > 4 for run in runs))

    def test_drummer_does_not_use_placeholder_dimensions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            layout_path = Path(tmp) / "layout.xml"
            layout_path.write_text("<xrgb><models/></xrgb>", encoding="utf-8")
            add_finished_helixville4_band_models(layout_path)
            root = ET.parse(layout_path).getroot()
            drummer = root.find(".//model[@name='HX_SNOWMAN_DRUMMER']")
            self.assertIsNotNone(drummer)
            self.assertNotEqual(drummer.attrib.get("CustomWidth"), "12")
            self.assertNotEqual(drummer.attrib.get("CustomHeight"), "12")
            self.assertGreaterEqual(int(drummer.attrib.get("CustomWidth", "0")), 72)
            self.assertGreaterEqual(int(drummer.attrib.get("CustomHeight", "0")), 48)

    def test_drummer_submodels_are_real_ranges(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            layout_path = Path(tmp) / "layout.xml"
            layout_path.write_text("<xrgb><models/></xrgb>", encoding="utf-8")
            add_finished_helixville4_band_models(layout_path)
            root = ET.parse(layout_path).getroot()
            drummer = root.find(".//model[@name='HX_SNOWMAN_DRUMMER']")
            self.assertIsNotNone(drummer)
            submodels = drummer.findall("subModel")
            self.assertGreaterEqual(len(submodels), 16)
            ranges = [sub.attrib.get("line0", "") for sub in submodels]
            self.assertFalse(all(value == "1-4" for value in ranges))
            self.assertTrue(any("-" in value and value != "1-4" for value in ranges))


if __name__ == "__main__":
    unittest.main()
