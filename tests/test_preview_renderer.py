from __future__ import annotations

import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from tools.preview_renderer import parse_models


class PreviewRendererTests(unittest.TestCase):
    def _write_layout(self, root: ET.Element) -> Path:
        tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(tempdir.cleanup)
        layout_path = Path(tempdir.name) / "xlights_rgbeffects.xml"
        ET.ElementTree(root).write(layout_path, encoding="utf-8", xml_declaration=True)
        return layout_path

    def test_parse_models_uses_polyline_pointdata_for_arch_segment(self) -> None:
        layout_path = Path(__file__).resolve().parents[1] / "xlights_rgbeffects.xml"
        layout = parse_models(layout_path)
        self.assertIn("Arch 2 Sec 5", layout.leaf_models)
        model = layout.leaf_models["Arch 2 Sec 5"]
        self.assertGreaterEqual(len(model.points), 3)
        self.assertNotEqual((model.x1, model.y1), (model.x2, model.y2))

    def test_parse_models_projects_3d_points_into_front_view(self) -> None:
        root = ET.Element("xrgb")
        models = ET.SubElement(root, "models")
        ET.SubElement(
            models,
            "model",
            {
                "name": "Depth Ribbon",
                "DisplayAs": "Custom",
                "WorldPosX": "10",
                "WorldPosY": "20",
                "WorldPosZ": "30",
                "PointData": "0,0,0,20,15,40,40,0,80",
                "StringType": "RGB Nodes",
            },
        )
        layout = parse_models(self._write_layout(root))
        model = layout.leaf_models["Depth Ribbon"]
        self.assertEqual(model.points[0], (10.0, 20.0))
        self.assertEqual(model.points[-1], (50.0, 20.0))
        self.assertGreaterEqual(len(model.points), 3)


if __name__ == "__main__":
    unittest.main()
