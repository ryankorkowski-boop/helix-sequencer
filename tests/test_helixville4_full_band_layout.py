from __future__ import annotations

import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from tools.build_helixville4_full_band_layout import build_full_band_layout


class Helixville4FullBandLayoutTests(unittest.TestCase):
    def test_layout_includes_full_models_and_upgraded_visible_targets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            payload = build_full_band_layout(Path(tmp))
            layout_path = Path(payload["approved_full_band_export"]["layout_path"])  # type: ignore[index]
            root = ET.parse(layout_path).getroot()

        drummer = root.find(".//model[@name='HX_SNOWMAN_DRUMMER']")
        split_target = root.find(".//model[@name='HX_SNOWMAN_DRUMMER_INSTRUMENT']")

        self.assertIsNotNone(drummer)
        self.assertIsNotNone(split_target)
        self.assertEqual(split_target.attrib.get("HelixVisibleBandUpgrade"), "split_models_v1")  # type: ignore[union-attr]
        self.assertGreater(int(split_target.attrib.get("CustomWidth", "0")), 12)  # type: ignore[union-attr]
        self.assertIn("HX_SNOWMAN_DRUMMER_INSTRUMENT", payload["visible_band_upgrade"]["upgraded"])  # type: ignore[index]
        self.assertEqual(payload["visible_band_upgrade"]["missing"], [])  # type: ignore[index]


if __name__ == "__main__":
    unittest.main()
