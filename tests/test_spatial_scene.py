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

    def test_depth_sweep_delays_by_z_and_decays(self) -> None:
        scene = _scene_with(
            ("Front", 0.0, 0.0, 0.0),
            ("Mid", 10.0, 0.0, 50.0),
            ("Back", 20.0, 0.0, 100.0),
            capability=spatial_scene.LAYOUT_CAPABILITY_3D,
        )

        hits = spatial_scene.depth_sweep(scene, ["Back", "Front", "Mid"], travel_ms=200, hop_decay=0.5)

        self.assertEqual([hit.name for hit in hits], ["Front", "Mid", "Back"])
        self.assertEqual([hit.delay_ms for hit in hits], [0, 100, 200])
        self.assertEqual([hit.weight for hit in hits], [1.0, 0.5, 0.25])
        self.assertLess(hits[0].delay_ms, hits[-1].delay_ms)

    def test_depth_sweep_reverse_starts_at_the_back(self) -> None:
        scene = _scene_with(
            ("Front", 0.0, 0.0, 0.0),
            ("Back", 0.0, 0.0, 80.0),
            capability=spatial_scene.LAYOUT_CAPABILITY_3D,
        )

        hits = spatial_scene.depth_sweep(scene, ["Front", "Back"], travel_ms=100, reverse=True)

        self.assertEqual(hits[0].name, "Back")
        self.assertEqual(hits[0].delay_ms, 0)
        self.assertEqual(hits[1].name, "Front")
        self.assertEqual(hits[1].delay_ms, 100)

    def test_depth_sweep_same_layer_shares_a_delay(self) -> None:
        scene = _scene_with(
            ("Front A", 0.0, 0.0, 0.0),
            ("Front B", 30.0, 0.0, 1.0),
            ("Back", 10.0, 0.0, 100.0),
            capability=spatial_scene.LAYOUT_CAPABILITY_3D,
        )

        hits = spatial_scene.depth_sweep(scene, ["Front A", "Front B", "Back"], travel_ms=100)

        by_name = {hit.name: hit for hit in hits}
        self.assertEqual(by_name["Front A"].delay_ms, by_name["Front B"].delay_ms)
        self.assertEqual(by_name["Front A"].weight, by_name["Front B"].weight)
        self.assertGreater(by_name["Back"].delay_ms, by_name["Front A"].delay_ms)
        self.assertLess(by_name["Back"].weight, 1.0)

    def test_flat_layout_depth_sweep_does_not_onset_together(self) -> None:
        scene = _scene_with(
            ("Low", 0.0, 0.0, 0.0),
            ("High", 0.0, 40.0, 0.0),
            capability=spatial_scene.LAYOUT_CAPABILITY_2D,
        )

        hits = spatial_scene.depth_sweep(scene, ["High", "Low"], travel_ms=100)

        self.assertEqual([hit.delay_ms for hit in hits], [0, 100])
        self.assertNotEqual(hits[0].delay_ms, hits[1].delay_ms)

    def test_depth_sweep_keeps_a_noisy_row_together(self) -> None:
        scene = _scene_with(
            ("Front A", 0.0, 0.0, 0.0),
            ("Front B", 12.0, 0.0, 2.0),
            ("Front C", 24.0, 0.0, 3.5),
            ("Back A", 8.0, 0.0, 100.0),
            ("Back B", 18.0, 0.0, 102.0),
            capability=spatial_scene.LAYOUT_CAPABILITY_3D,
        )

        hits = spatial_scene.depth_sweep(scene, [node for node in ("Front A", "Front B", "Front C", "Back A", "Back B")])
        by_name = {hit.name: hit for hit in hits}

        self.assertEqual(by_name["Front A"].delay_ms, by_name["Front B"].delay_ms)
        self.assertEqual(by_name["Front B"].delay_ms, by_name["Front C"].delay_ms)
        self.assertEqual(by_name["Back A"].delay_ms, by_name["Back B"].delay_ms)
        self.assertGreater(by_name["Back A"].delay_ms, by_name["Front A"].delay_ms)
        self.assertLess(by_name["Back A"].weight, by_name["Front A"].weight)

    def test_even_depth_ramp_does_not_share_one_onset(self) -> None:
        scene = _scene_with(
            ("Z0", 0.0, 0.0, 0.0),
            ("Z1", 0.0, 0.0, 25.0),
            ("Z2", 0.0, 0.0, 50.0),
            ("Z3", 0.0, 0.0, 75.0),
            ("Z4", 0.0, 0.0, 100.0),
            capability=spatial_scene.LAYOUT_CAPABILITY_3D,
        )

        hits = spatial_scene.depth_sweep(scene, ["Z4", "Z2", "Z0", "Z3", "Z1"], travel_ms=200)

        self.assertEqual([hit.delay_ms for hit in hits], [0, 50, 100, 150, 200])
        self.assertEqual(len({hit.delay_ms for hit in hits}), 5)


def _scene_with(*points: tuple[str, float, float, float], capability: str) -> spatial_scene.SpatialScene:
    nodes = {}
    for name, x, y, z in points:
        nodes[name] = spatial_scene.SceneNode(
            name=name,
            kind="model",
            center_xyz=(x, y, z),
            extents_xyz=(1.0, 1.0, 1.0),
            projected_xy=(x, y),
            bounds_xyz=(x, y, z, x + 1.0, y + 1.0, z + 1.0),
            projected_bounds_xy=(x, y, x + 1.0, y + 1.0),
            projected_outline_xy=((x, y),),
            tags=(),
            groups=(),
        )
    report = spatial_scene.LayoutCapabilityReport(
        capability=capability,
        model_count=len(nodes),
        horizontal_span=100.0,
        vertical_span=40.0,
        depth_span=100.0 if capability != spatial_scene.LAYOUT_CAPABILITY_2D else 0.0,
        depth_ratio=0.4 if capability != spatial_scene.LAYOUT_CAPABILITY_2D else 0.0,
        depth_layer_count=3 if capability != spatial_scene.LAYOUT_CAPABILITY_2D else 1,
        layered_model_ratio=0.5,
        volumetric_model_ratio=0.0,
    )
    return spatial_scene.SpatialScene(
        path=None,
        capability=capability,
        capability_report=report,
        nodes=nodes,
        group_nodes={},
        groups={},
        aliases={name.lower(): name for name in nodes},
    )


if __name__ == "__main__":
    unittest.main()
