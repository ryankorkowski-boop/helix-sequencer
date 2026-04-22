from __future__ import annotations

import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from tools import build_helixville_layout


class BuildHelixvilleLayoutTests(unittest.TestCase):
    def _write_layout(self, root: Path) -> Path:
        xml = """<?xml version="1.0" encoding="utf-8"?>
<xrgb>
  <models>
    <model name="Tree 1" DisplayAs="Tree 360" WorldPosX="100.0" WorldPosY="50.0" WorldPosZ="0.0" />
    <model name="Matrix 1" DisplayAs="Horiz Matrix" WorldPosX="-90.0" WorldPosY="25.0" WorldPosZ="0.0" />
  </models>
  <previewWidth value="1366"/>
  <previewHeight value="768"/>
</xrgb>
"""
        path = root / "xlights_rgbeffects.xml"
        path.write_text(xml, encoding="utf-8")
        return path

    def _write_networks(self, root: Path) -> Path:
        xml = """<?xml version="1.0" encoding="utf-8"?>
<Networks>
  <controllers>
    <controller UnitId="1" NumChannels="16" CntlrType="AC Controller"/>
    <controller UnitId="2" NumChannels="170" CntlrType="Pixel Controller"/>
  </controllers>
</Networks>
"""
        path = root / "xlights_networks.xml"
        path.write_text(xml, encoding="utf-8")
        return path

    def test_build_helixville_3d_show_folder_writes_depth_layout_and_assets(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            layout = self._write_layout(root)
            networks = self._write_networks(root)
            keybindings = root / "xlights_keybindings.xml"
            keybindings.write_text("<keys />", encoding="utf-8")
            out_folder = root / "helixville_3d_start"

            out_layout = build_helixville_layout.build_helixville_3d_show_folder(
                source_layout_xml=layout,
                source_networks_xml=networks,
                source_keybindings_xml=keybindings,
                output_show_folder=out_folder,
            )

            self.assertTrue(out_layout.exists())
            self.assertTrue((out_folder / "xlights_networks.xml").exists())
            self.assertTrue((out_folder / "xlights_keybindings.xml").exists())
            self.assertTrue((out_folder / "START_HERE.txt").exists())
            self.assertTrue((out_folder / "controllers_info.txt").exists())

            root_node = ET.parse(out_layout).getroot()
            models = root_node.findall(".//models/model")
            self.assertEqual(len(models), 2)
            for model in models:
                self.assertNotEqual(model.attrib.get("WorldPosZ"), "0.0")
            self.assertEqual(root_node.find(".//previewWidth").attrib.get("value"), "1920")
            self.assertEqual(root_node.find(".//previewHeight").attrib.get("value"), "1080")


if __name__ == "__main__":
    unittest.main()
