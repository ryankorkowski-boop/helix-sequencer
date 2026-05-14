from __future__ import annotations

import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from tools.build_helpers.helixville4_visible_band import VISIBLE_BAND_MODELS, upgrade_visible_band_models


def _placeholder_model(name: str) -> str:
    return (
        f'<model name="{name}" DisplayAs="Custom" parm1="12" parm2="12" '
        'CustomWidth="12" CustomHeight="12" X2="24.000" Y2="18.000">'
        '<subModel name="OLD_PLACEHOLDER" line0="1-4" />'
        "</model>"
    )


class Helixville4VisibleBandTests(unittest.TestCase):
    def test_upgrade_replaces_split_placeholders_with_visible_sequence_targets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            layout_path = Path(tmp) / "xlights_rgbeffects.xml"
            layout_path.write_text(
                "<?xml version='1.0' encoding='utf-8'?><xrgb><models>"
                + "".join(_placeholder_model(spec.name) for spec in VISIBLE_BAND_MODELS)
                + "</models></xrgb>",
                encoding="utf-8",
            )

            payload = upgrade_visible_band_models(layout_path)
            root = ET.parse(layout_path).getroot()
            drummer = root.find(".//model[@name='HX_SNOWMAN_DRUMMER_INSTRUMENT']")
            singer = root.find(".//model[@name='HX_SNOWMAN_SINGER_BODY']")

        self.assertEqual(payload["missing"], [])
        self.assertEqual(len(payload["upgraded"]), len(VISIBLE_BAND_MODELS))
        self.assertIsNotNone(drummer)
        self.assertIsNotNone(singer)
        assert drummer is not None
        assert singer is not None
        self.assertEqual(drummer.attrib["HelixVisibleBandUpgrade"], "split_models_v1")
        self.assertEqual(drummer.attrib["parm1"], "90")
        self.assertEqual(drummer.attrib["parm2"], "72")
        self.assertGreater(int(singer.attrib["CustomHeight"]), 80)
        self.assertIn("HX_SNOWMAN_DRUMMER_KICK", {node.attrib["name"] for node in drummer.findall("subModel")})
        self.assertNotIn("OLD_PLACEHOLDER", {node.attrib["name"] for node in singer.findall("subModel")})
        self.assertGreater(drummer.attrib["CustomModel"].count(","), 1000)


if __name__ == "__main__":
    unittest.main()
