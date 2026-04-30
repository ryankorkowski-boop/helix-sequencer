from __future__ import annotations

import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from tools.build_helpers.helixville3 import DEFAULT_GP_LAYOUT, DEFAULT_NEIGHBOR_LAYOUT, build_helixville3_layout


def _find_model(models: list[ET.Element], target: str) -> ET.Element | None:
    lowered = target.strip().lower()
    for model in models:
        if str(model.attrib.get("name", "")).strip().lower() == lowered:
            return model
    return None


def _world_position(model: ET.Element) -> tuple[float, float, float]:
    return (
        float(model.attrib.get("WorldPosX", "0") or 0.0),
        float(model.attrib.get("WorldPosY", "0") or 0.0),
        float(model.attrib.get("WorldPosZ", "0") or 0.0),
    )


class Helixville3LayoutTests(unittest.TestCase):
    def test_build_helixville3_generates_grounded_layout_with_lyric_groups(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "helixville3"
            manifest = build_helixville3_layout(
                source_layout=DEFAULT_GP_LAYOUT,
                neighbor_layout=DEFAULT_NEIGHBOR_LAYOUT,
                output_dir=output_dir,
            )

            self.assertEqual(manifest["layout_name"], "helixville3")
            self.assertGreaterEqual(int(manifest["gp_model_count"]), 256)
            self.assertGreaterEqual(int(manifest["neighbor_imported_count"]), 90)
            self.assertGreaterEqual(int(manifest["gp_ground_aligned_count"]), 200)

            layout_path = output_dir / "xlights_rgbeffects.xml"
            self.assertTrue(layout_path.exists())
            root = ET.parse(layout_path).getroot()
            models = root.findall(".//model")
            self.assertGreater(len(models), 340)

            north_1 = _find_model(models, "North Candy Cane 1")
            self.assertIsNotNone(north_1)
            _x, _y, z = _world_position(north_1)  # type: ignore[arg-type]
            self.assertAlmostEqual(z, 0.0, delta=0.01)

            star_1 = _find_model(models, "star 1")
            self.assertIsNotNone(star_1)
            _sx, _sy, sz = _world_position(star_1)  # type: ignore[arg-type]
            self.assertAlmostEqual(sz, 200.0, delta=0.01)

            group_map = {group.attrib.get("name", ""): group for group in root.findall(".//modelGroup")}
            self.assertIn("HV3_LYRIC_MARQUEE", group_map)
            self.assertIn("HV3_SINGING_FACES", group_map)
            self.assertIn("HV3_NEIGHBOR_LEFT_COMMON", group_map)
            self.assertIn("HV3_NEIGHBOR_RIGHT_COMMON", group_map)

            lyric_members = [
                item.strip()
                for item in str(group_map["HV3_LYRIC_MARQUEE"].attrib.get("models", "")).split(",")
                if item.strip()
            ]
            face_members = [
                item.strip()
                for item in str(group_map["HV3_SINGING_FACES"].attrib.get("models", "")).split(",")
                if item.strip()
            ]
            self.assertGreaterEqual(len(lyric_members), 5)
            self.assertGreaterEqual(len(face_members), 3)


if __name__ == "__main__":
    unittest.main()
