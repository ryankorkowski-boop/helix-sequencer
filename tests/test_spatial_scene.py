from __future__ import annotations

import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from core import spatial_scene


class SpatialSceneTests(unittest.TestCase):
    def _write_layout(
        self,
        models: list[dict[str, str]],
        groups: list[dict[str, str]] | None = None,
    ) -> Path:
        tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(tempdir.cleanup)
        root = ET.Element("xrgb")
        models_root = ET.SubElement(root, "models")
        for attrs in models:
            ET.SubElement(models_root, "model", attrs)
        if groups:
            groups_root = ET.SubElement(root, "modelGroups")
            for attrs in groups:
                ET.SubElement(groups_root, "modelGroup", attrs)
        layout_path = Path(tempdir.name) / "xlights_rgbeffects.xml"
        ET.ElementTree(root).write(layout_path, encoding="utf-8", xml_declaration=True)
        return layout_path

    def test_build_scene_normalizes_model_and_group_data_for_flat_layout(self) -> None:
        layout_path = self._write_layout(
            models=[
                {
                    "name": "Front Arch",
                    "DisplayAs": "Arches",
                    "WorldPosX": "0",
                    "WorldPosY": "10",
                    "WorldPosZ": "0",
                    "X2": "40",
                    "Y2": "0",
                    "Z2": "0",
                    "StringType": "RGB Nodes",
                },
                {
                    "name": "Front Tree",
                    "DisplayAs": "Tree Flat",
                    "WorldPosX": "80",
                    "WorldPosY": "30",
                    "WorldPosZ": "0",
                    "X2": "0",
                    "Y2": "60",
                    "Z2": "0",
                    "NumStrings": "8",
                    "NodesPerString": "12",
                    "StringType": "RGB Nodes",
                },
            ],
            groups=[
                {
                    "name": "Front Row",
                    "models": "Front Arch,Front Tree",
                    "centrex": "50",
                    "centrey": "30",
                }
            ],
        )

        scene = spatial_scene.load_scene(layout_path)

        self.assertEqual(scene.capability, spatial_scene.LAYOUT_CAPABILITY_2D)
        arch = scene.node_for("Front Arch")
        self.assertIsNotNone(arch)
        assert arch is not None
        self.assertAlmostEqual(arch.center_xyz[0], 20.0, delta=0.01)
        self.assertAlmostEqual(arch.center_xyz[1], 10.0, delta=0.01)
        self.assertEqual(arch.projected_xy, (20.0, 10.0))
        self.assertIn("arch", arch.tags)
        self.assertIn("rgb", arch.tags)
        self.assertEqual(arch.groups, ("Front Row",))

        group = scene.node_for("Front Row")
        self.assertIsNotNone(group)
        assert group is not None
        self.assertIn("Front Arch", scene.groups["Front Row"])
        self.assertGreater(group.projected_bounds_xy[2], group.projected_bounds_xy[0])

    def test_detector_distinguishes_layered_and_volumetric_layouts(self) -> None:
        layered_layout = self._write_layout(
            models=[
                {
                    "name": "Layer A",
                    "DisplayAs": "Single Line",
                    "WorldPosX": "0",
                    "WorldPosY": "0",
                    "WorldPosZ": "0",
                    "X2": "30",
                    "Y2": "0",
                    "Z2": "0",
                },
                {
                    "name": "Layer B",
                    "DisplayAs": "Single Line",
                    "WorldPosX": "60",
                    "WorldPosY": "10",
                    "WorldPosZ": "60",
                    "X2": "30",
                    "Y2": "0",
                    "Z2": "0",
                },
                {
                    "name": "Layer C",
                    "DisplayAs": "Single Line",
                    "WorldPosX": "120",
                    "WorldPosY": "20",
                    "WorldPosZ": "120",
                    "X2": "30",
                    "Y2": "0",
                    "Z2": "0",
                },
            ]
        )
        volumetric_layout = self._write_layout(
            models=[
                {
                    "name": "Volume A",
                    "DisplayAs": "Custom",
                    "WorldPosX": "0",
                    "WorldPosY": "0",
                    "WorldPosZ": "0",
                    "PointData": "0,0,0,30,0,50,30,20,100",
                    "StringType": "RGB Nodes",
                },
                {
                    "name": "Volume B",
                    "DisplayAs": "Custom",
                    "WorldPosX": "90",
                    "WorldPosY": "0",
                    "WorldPosZ": "0",
                    "PointData": "0,0,0,20,20,40,40,0,80",
                    "StringType": "RGB Nodes",
                },
                {
                    "name": "Guide",
                    "DisplayAs": "Single Line",
                    "WorldPosX": "180",
                    "WorldPosY": "10",
                    "WorldPosZ": "0",
                    "X2": "30",
                    "Y2": "0",
                    "Z2": "0",
                },
            ]
        )

        layered_scene = spatial_scene.load_scene(layered_layout)
        volumetric_scene = spatial_scene.load_scene(volumetric_layout)

        self.assertEqual(layered_scene.capability, spatial_scene.LAYOUT_CAPABILITY_25D)
        self.assertEqual(volumetric_scene.capability, spatial_scene.LAYOUT_CAPABILITY_3D)
        self.assertGreater(volumetric_scene.capability_report.volumetric_model_ratio, 0.20)

    def test_projection_keeps_front_view_and_radial_field_uses_xyz_when_depth_exists(self) -> None:
        layout_path = self._write_layout(
            models=[
                {
                    "name": "Near",
                    "DisplayAs": "Single Line",
                    "WorldPosX": "0",
                    "WorldPosY": "0",
                    "WorldPosZ": "0",
                    "X2": "10",
                    "Y2": "0",
                    "Z2": "0",
                },
                {
                    "name": "Deep",
                    "DisplayAs": "Single Line",
                    "WorldPosX": "0",
                    "WorldPosY": "0",
                    "WorldPosZ": "80",
                    "X2": "10",
                    "Y2": "0",
                    "Z2": "0",
                },
                {
                    "name": "Side",
                    "DisplayAs": "Single Line",
                    "WorldPosX": "80",
                    "WorldPosY": "0",
                    "WorldPosZ": "0",
                    "X2": "10",
                    "Y2": "0",
                    "Z2": "0",
                },
            ]
        )

        scene = spatial_scene.load_scene(layout_path)
        coords = scene.projected_coordinate_map(["Near", "Deep", "Side"])
        scores = spatial_scene.radial_field(scene, "Near", radius=60.0)

        self.assertEqual(coords["Near"], coords["Deep"])
        self.assertAlmostEqual(scores["Near"], 1.0, delta=0.001)
        self.assertEqual(scores["Deep"], 0.0)
        self.assertLess(scores["Side"], 0.01)

    def test_effect_router_maps_depth_effects_to_intentional_flat_equivalents(self) -> None:
        depth_flat = spatial_scene.route_spatial_effect("depth sweep", spatial_scene.LAYOUT_CAPABILITY_2D)
        orbit_3d = spatial_scene.route_spatial_effect("orbit/rotation", spatial_scene.LAYOUT_CAPABILITY_3D)
        wave_25d = spatial_scene.route_spatial_effect("wave propagation", spatial_scene.LAYOUT_CAPABILITY_25D)

        self.assertEqual(depth_flat.primitive, "directional_wave")
        self.assertEqual(depth_flat.axis, "y")
        self.assertEqual(depth_flat.distance_mode, "projected_xy")
        self.assertEqual(depth_flat.fallback_family, "height_mapping")
        self.assertEqual(depth_flat.flat_equivalent, "front_view_height_mapping")

        self.assertEqual(orbit_3d.primitive, "path_travel")
        self.assertEqual(orbit_3d.path_strategy, "orbit_xz")
        self.assertEqual(orbit_3d.distance_mode, "xyz")

        self.assertEqual(wave_25d.primitive, "directional_wave")
        self.assertEqual(wave_25d.distance_mode, "xyz")


if __name__ == "__main__":
    unittest.main()
