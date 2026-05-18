from __future__ import annotations

import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from tools.build_helixville4_full_band_layout import build_full_band_layout


class Helixville4FullBandLayoutTests(unittest.TestCase):
    def test_layout_includes_xlights_safe_split_targets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            payload = build_full_band_layout(Path(tmp))
            layout_path = Path(payload["approved_full_band_export"]["layout_path"])  # type: ignore[index]
            root = ET.parse(layout_path).getroot()

        drummer = root.find(".//model[@name='HX_SNOWMAN_DRUMMER']")
        split_target = root.find(".//model[@name='HX_SNOWMAN_DRUMMER_INSTRUMENT']")

        self.assertIsNone(drummer)
        self.assertIsNotNone(split_target)
        self.assertEqual(split_target.attrib.get("HelixVisibleBandUpgrade"), "split_models_v1")  # type: ignore[union-attr]
        self.assertGreater(int(split_target.attrib.get("CustomWidth", "0")), 12)  # type: ignore[union-attr]
        self.assertIn("HX_SNOWMAN_DRUMMER_INSTRUMENT", payload["visible_band_upgrade"]["upgraded"])  # type: ignore[index]
        self.assertEqual(payload["visible_band_upgrade"]["missing"], [])  # type: ignore[index]

    def test_source_layout_nonband_models_are_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.xml"
            source.write_text(
                "<xrgb><models>"
                "<model name='HX_NONBAND_KEEP_ME' DisplayAs='Single Line' />"
                "<model name='HX_SNOWMAN_BASSIST_BODY' DisplayAs='Custom' CustomWidth='12' CustomHeight='12' />"
                "<model name='HX_BAD_MATRIX' DisplayAs='Matrix' />"
                "<model name='HX_BAD_CANE' DisplayAs='CandyCane' />"
                "</models><modelGroups /></xrgb>",
                encoding="utf-8",
            )
            out_dir = Path(tmp) / "out"
            payload = build_full_band_layout(out_dir, source_layout=source)
            layout_path = Path(payload["approved_full_band_export"]["layout_path"])  # type: ignore[index]
            root = ET.parse(layout_path).getroot()

        self.assertIsNotNone(root.find(".//model[@name='HX_NONBAND_KEEP_ME']"))
        bassist_body = root.find(".//model[@name='HX_SNOWMAN_BASSIST_BODY']")
        self.assertIsNotNone(bassist_body)
        assert bassist_body is not None
        self.assertEqual(bassist_body.attrib.get("HelixVisibleBandUpgrade"), "split_models_v1")
        self.assertEqual(root.find(".//model[@name='HX_BAD_MATRIX']").attrib.get("DisplayAs"), "Horiz Matrix")  # type: ignore[union-attr]
        self.assertEqual(root.find(".//model[@name='HX_BAD_CANE']").attrib.get("DisplayAs"), "Candy Canes")  # type: ignore[union-attr]
        self.assertIsNone(root.find(".//model[@name='HX_SNOWMAN_BASSIST']"))
        band_group = root.find(".//modelGroup[@name='HX_SNOWMAN_BAND']")
        self.assertIsNotNone(band_group)
        assert band_group is not None
        self.assertIn("HX_SNOWMAN_BASSIST_INSTRUMENT", band_group.attrib.get("models", ""))
        self.assertEqual(payload["preservation_policy"], "copy_source_layout_then_patch_band_models_only")
        self.assertEqual(payload["xlights_layout"]["display_type_fixes"]["Matrix"], 1)  # type: ignore[index]


if __name__ == "__main__":
    unittest.main()
