from __future__ import annotations

import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from core import camera_path
from core import model_parser
from core import spatial_scene


class CameraPathTests(unittest.TestCase):
    def _scene(self) -> spatial_scene.SpatialScene:
        tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(tempdir.cleanup)
        root = ET.Element("xrgb")
        models = ET.SubElement(root, "models")
        for attrs in (
            {"name": "Lead Singer", "DisplayAs": "Single Line", "WorldPosX": "0", "WorldPosY": "20", "WorldPosZ": "0", "X2": "0", "Y2": "50", "Z2": "0"},
            {"name": "Drummer", "DisplayAs": "Single Line", "WorldPosX": "40", "WorldPosY": "15", "WorldPosZ": "20", "X2": "45", "Y2": "45", "Z2": "24"},
            {"name": "Guitarist", "DisplayAs": "Single Line", "WorldPosX": "-35", "WorldPosY": "12", "WorldPosZ": "12", "X2": "-20", "Y2": "42", "Z2": "16"},
            {"name": "Bass", "DisplayAs": "Single Line", "WorldPosX": "28", "WorldPosY": "10", "WorldPosZ": "-18", "X2": "32", "Y2": "44", "Z2": "-20"},
        ):
            ET.SubElement(models, "model", attrs)
        path = Path(tempdir.name) / "xlights_rgbeffects.xml"
        ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)
        return spatial_scene.build_scene(model_parser.parse_layout(path))

    def test_camera_targets_resolve_performer_positions(self) -> None:
        scene = self._scene()
        targets = camera_path.build_camera_targets(
            scene,
            snowman_payload={
                "layout_mapping": {
                    "lead_singer": {"targets": ["Lead Singer"]},
                    "drummer": {"targets": ["Drummer"]},
                    "guitarist": {"targets": ["Guitarist"]},
                    "bassist": {"targets": ["Bass"]},
                }
            },
            active_models=["Drummer", "Guitarist"],
        )
        self.assertIn("lead_singer", targets)
        self.assertIn("spatial_energy_cluster", targets)
        self.assertNotEqual(targets["drummer"].position[2], 0.0)

    def test_camera_path_uses_music_sections_for_modes_and_focus(self) -> None:
        scene = self._scene()
        payload = camera_path.build_camera_path(
            scene,
            band_sync_payload={
                "timeline": [
                    {"start_ms": 0, "end_ms": 1000, "energy_level": 0.25, "section_type": "intro", "density_level": "sparse", "dominant_features": ["environment"]},
                    {"start_ms": 1000, "end_ms": 2200, "energy_level": 0.86, "section_type": "chorus", "density_level": "busy", "dominant_features": ["vocals", "guitar"]},
                    {"start_ms": 2200, "end_ms": 3200, "energy_level": 0.95, "section_type": "drop", "density_level": "busy", "dominant_features": ["drums"]},
                ],
                "performer_focus": [
                    {"start_ms": 1000, "end_ms": 2200, "primary_focus": "singer"},
                    {"start_ms": 2200, "end_ms": 3200, "primary_focus": "drummer"},
                ],
            },
            snowman_payload={
                "layout_mapping": {
                    "lead_singer": {"targets": ["Lead Singer"]},
                    "drummer": {"targets": ["Drummer"]},
                }
            },
            song_length_ms=3200,
            sample_step_ms=400,
        )
        modes = {state["mode"] for state in payload["path"]}
        targets = {state["target_label"] for state in payload["path"]}
        self.assertIn("orbit", modes)
        self.assertIn("fly_through", modes)
        self.assertIn("chase", modes)
        self.assertIn("lead_singer", targets)
        self.assertIn("drummer", targets)
        self.assertEqual(payload["camera_model"]["coordinate_space"], "layout_world_xyz")

    def test_smoothing_populates_velocity_and_debug_preview_export(self) -> None:
        scene = self._scene()
        payload = camera_path.build_camera_path(
            scene,
            band_sync_payload={"timeline": [{"start_ms": 0, "end_ms": 1500, "energy_level": 0.7, "section_type": "verse", "density_level": "medium", "dominant_features": ["vocals"]}]},
            snowman_payload={"layout_mapping": {"lead_singer": {"targets": ["Lead Singer"]}}},
            song_length_ms=1500,
            sample_step_ms=300,
        )
        velocities = [tuple(state["velocity"]) for state in payload["path"][1:]]
        self.assertTrue(any(any(abs(component) > 0.001 for component in velocity) for velocity in velocities))
        self.assertTrue(payload["preview"]["states"])
        self.assertEqual(payload["export"]["attach_to_sequence_payload_key"], "camera_path")
        self.assertTrue(payload["debug"]["speed_graph"])


if __name__ == "__main__":
    unittest.main()
