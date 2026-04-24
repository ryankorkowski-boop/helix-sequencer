from __future__ import annotations

import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from tools.build_helpers.helixville2 import DEFAULT_GP_LAYOUT, DEFAULT_NEIGHBOR_LAYOUT, build_helixville2_layout


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


class Helixville2LayoutTests(unittest.TestCase):
    def test_build_helixville2_places_core_landmarks_and_neighbors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "helixville2"
            manifest = build_helixville2_layout(
                source_layout=DEFAULT_GP_LAYOUT,
                neighbor_layout=DEFAULT_NEIGHBOR_LAYOUT,
                output_dir=output_dir,
            )

            self.assertEqual(manifest["layout_name"], "helixville2")
            self.assertGreaterEqual(int(manifest["gp_model_count"]), 256)
            self.assertGreaterEqual(int(manifest["neighbor_imported_count"]), 80)

            layout_path = output_dir / "xlights_rgbeffects.xml"
            self.assertTrue(layout_path.exists())

            root = ET.parse(layout_path).getroot()
            models = root.findall(".//model")
            self.assertGreater(len(models), 330)

            north_1 = _find_model(models, "North Candy Cane 1")
            north_2 = _find_model(models, "North Candy Cane 2")
            south_1 = _find_model(models, "South Candy Cane 1")
            self.assertIsNotNone(north_1)
            self.assertIsNotNone(north_2)
            self.assertIsNotNone(south_1)
            n1_x, n1_y, _n1_z = _world_position(north_1)  # type: ignore[arg-type]
            _n2_x, n2_y, _n2_z = _world_position(north_2)  # type: ignore[arg-type]
            s1_x, _s1_y, _s1_z = _world_position(south_1)  # type: ignore[arg-type]
            self.assertLess(n1_x, 0.0)
            self.assertGreater(s1_x, 0.0)
            self.assertAlmostEqual(n2_y - n1_y, 60.0, delta=0.01)  # 6ft * 10 world units

            star_1 = _find_model(models, "star 1")
            star_15 = _find_model(models, "star 15")
            self.assertIsNotNone(star_1)
            self.assertIsNotNone(star_15)
            _s1x, _s1y, s1z = _world_position(star_1)  # type: ignore[arg-type]
            _s15x, _s15y, s15z = _world_position(star_15)  # type: ignore[arg-type]
            self.assertAlmostEqual(s1z, 200.0, delta=0.01)
            self.assertAlmostEqual(s15z, 200.0, delta=0.01)

            sf2 = _find_model(models, "sf2")
            sf14 = _find_model(models, "sf14")
            self.assertIsNotNone(sf2)
            self.assertIsNotNone(sf14)
            _sf2x, _sf2y, sf2z = _world_position(sf2)  # type: ignore[arg-type]
            _sf14x, _sf14y, sf14z = _world_position(sf14)  # type: ignore[arg-type]
            self.assertAlmostEqual(sf2z, 160.0, delta=0.01)
            self.assertAlmostEqual(sf14z, 160.0, delta=0.01)

            group_names = {group.attrib.get("name", "") for group in root.findall(".//modelGroup")}
            self.assertIn("HV2_GP_AERIAL", group_names)
            self.assertIn("HV2_NEIGHBOR_LEFT_COMMON", group_names)
            self.assertIn("HV2_NEIGHBOR_RIGHT_COMMON", group_names)


if __name__ == "__main__":
    unittest.main()
