from __future__ import annotations

import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from core.sequential_layering import (
    LayerEvent,
    chord_to_members,
    melody_run,
    merge_layer_events,
    ordered_members,
    pitch_to_member,
)
from tools.build_helpers.helixville4_floor_piano import FLOOR_PIANO_KEYS, add_floor_piano_to_layout


class Helixville4FloorPianoTests(unittest.TestCase):
    def build_root(self) -> ET.Element:
        with tempfile.TemporaryDirectory() as tmp:
            layout = Path(tmp) / "layout.xml"
            layout.write_text("<xrgb><models/><modelGroups/></xrgb>", encoding="utf-8")
            add_floor_piano_to_layout(layout)
            return ET.parse(layout).getroot()

    def test_floor_piano_exists(self) -> None:
        root = self.build_root()
        model = root.find(".//model[@name='HX_FLOOR_PIANO']")
        self.assertIsNotNone(model)
        self.assertGreaterEqual(int(model.attrib.get("CustomWidth", "0")), 80)
        self.assertGreaterEqual(int(model.attrib.get("CustomHeight", "0")), 30)

    def test_floor_piano_contains_expected_note_submodels(self) -> None:
        root = self.build_root()
        model = root.find(".//model[@name='HX_FLOOR_PIANO']")
        names = {sub.attrib.get("name") for sub in model.findall("subModel")}
        expected = {f"HX_FLOOR_PIANO_{key.label}" for key in FLOOR_PIANO_KEYS}
        self.assertEqual(expected, expected & names)
        self.assertGreaterEqual(len(expected), 24)

    def test_global_layer_submodels_exist(self) -> None:
        root = self.build_root()
        model = root.find(".//model[@name='HX_FLOOR_PIANO']")
        names = {sub.attrib.get("name") for sub in model.findall("subModel")}
        self.assertIn("HX_FLOOR_PIANO_WHITE_KEYS", names)
        self.assertIn("HX_FLOOR_PIANO_BLACK_KEYS", names)
        self.assertIn("HX_FLOOR_PIANO_CHORD_BLOOM", names)
        self.assertIn("HX_FLOOR_PIANO_SUSTAIN_GLOW", names)
        self.assertIn("HX_FLOOR_PIANO_LEFT_TO_RIGHT_CHASE", names)
        self.assertIn("HX_FLOOR_PIANO_VELOCITY_LANE", names)

    def test_pitch_to_member_mapping(self) -> None:
        self.assertEqual(
            pitch_to_member("HX_FLOOR_PIANO", "C", "LOW"),
            "HX_FLOOR_PIANO_C_LOW",
        )
        self.assertEqual(
            pitch_to_member("HX_FLOOR_PIANO", "F#", "HIGH"),
            "HX_FLOOR_PIANO_FS_HIGH",
        )

    def test_chord_mapping_returns_multiple_members(self) -> None:
        members = chord_to_members("HX_FLOOR_PIANO", "C", "major")
        self.assertIn("HX_FLOOR_PIANO_C_LOW", members)
        self.assertIn("HX_FLOOR_PIANO_E_LOW", members)
        self.assertIn("HX_FLOOR_PIANO_G_LOW", members)
        self.assertIn("HX_FLOOR_PIANO_C_HIGH", members)
        self.assertGreaterEqual(len(members), 6)

    def test_melody_run_is_ordered(self) -> None:
        run = melody_run("HX_FLOOR_PIANO", 0, 5)
        self.assertEqual(run[0], "HX_FLOOR_PIANO_C_LOW")
        self.assertEqual(run[-1], "HX_FLOOR_PIANO_F_LOW")
        self.assertEqual(len(run), 6)

    def test_ordered_members_are_deterministic(self) -> None:
        members = ordered_members("HX_FLOOR_PIANO")
        self.assertEqual(members[0], "HX_FLOOR_PIANO_C_LOW")
        self.assertEqual(members[-1], "HX_FLOOR_PIANO_B_HIGH")
        self.assertEqual(len(members), 24)

    def test_layer_merge_priority(self) -> None:
        events = (
            LayerEvent(layer="accent", members=("a",), intensity=1.0, sustain_ms=40, source="drop"),
            LayerEvent(layer="base", members=("b",), intensity=0.2, sustain_ms=1200, source="ambient"),
            LayerEvent(layer="sustain", members=("c",), intensity=0.5, sustain_ms=600, source="pad"),
        )
        merged = merge_layer_events(events)
        self.assertEqual(merged[0].layer, "base")
        self.assertEqual(merged[-1].layer, "accent")


if __name__ == "__main__":
    unittest.main()
