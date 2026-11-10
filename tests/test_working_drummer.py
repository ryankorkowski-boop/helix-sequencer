from __future__ import annotations

import unittest

from audio.drum_classification import DrumEvent
from models.working_band_member import WORKING_MEMBER_SCHEMA
from models.working_drummer import build_reactive_drummer_member, build_working_drummer


def _event(ms: int, drum_type: str, velocity: float = 0.8, confidence: float = 0.72) -> DrumEvent:
    return DrumEvent(ms / 1000.0, velocity, confidence, {"test": 1.0}, 1, drum_type, "test")


class WorkingDrummerTests(unittest.TestCase):
    def test_working_drummer_has_required_kit_geometry_and_animation(self) -> None:
        payload = build_working_drummer()

        self.assertEqual(payload["schema"], WORKING_MEMBER_SCHEMA)
        self.assertEqual(payload["role"], "drummer")
        self.assertEqual(payload["status"], "working_member_slice")
        self.assertTrue(payload["validation"]["has_required_submodels"])
        self.assertTrue(payload["validation"]["has_animation_frames"])
        self.assertTrue(payload["validation"]["mouth_inside_head"])
        self.assertEqual(payload["missing_required_submodels"], [])

        node_counts = payload["submodel_node_counts"]
        for submodel_name in payload["required_submodels"]:
            self.assertIn(submodel_name, node_counts)
            self.assertGreater(node_counts[submodel_name], 0)

        cue_targets = {cue["submodel"] for cue in payload["default_cues"]}
        self.assertIn("kick", cue_targets)
        self.assertIn("snare", cue_targets)
        self.assertIn("hi_hat", cue_targets)
        self.assertIn("cymbal", cue_targets)

    def test_reactive_drummer_uses_typed_drum_streams(self) -> None:
        payload = build_reactive_drummer_member(
            drum_event_streams={
                "kick_events": [_event(500, "kick", 0.9, 0.86)],
                "snare_events": [_event(1000, "snare", 0.7, 0.78)],
                "hihat_events": [_event(750, "hihat", 0.45, 0.62)],
                "cymbal_events": [_event(1500, "cymbal", 0.8, 0.74)],
                "tom_events": [],
                "drum_bus_events": [],
            }
        )

        self.assertEqual(payload["status"], "reactive_working_member_slice")
        self.assertTrue(payload["validation"]["has_reactive_cues"])
        self.assertTrue(payload["validation"]["has_motion_events"])
        self.assertTrue(payload["validation"]["has_effect_cues"])
        self.assertTrue(payload["validation"]["reactive_cues_target_existing_submodels"])
        self.assertTrue(payload["reactive_debug"]["uses_typed_detection"])

        targets = {cue["submodel"] for cue in payload["reactive_cues"]}
        self.assertIn("kick", targets)
        self.assertIn("snare", targets)
        self.assertIn("hi_hat", targets)
        self.assertIn("cymbal", targets)
        self.assertTrue(any(cue["visual_effect"].get("spatial_impulse", {}).get("enabled") for cue in payload["reactive_cues"]))
        self.assertTrue(any(cue["visual_effect"].get("player_piano_hook", {}).get("enabled") for cue in payload["reactive_cues"]))

    def test_reactive_drummer_uses_legacy_marks_when_typed_streams_missing(self) -> None:
        payload = build_reactive_drummer_member(
            kicks=[500],
            snares=[1000],
            hats=[250, 750],
            cymbals=[1500],
        )

        self.assertTrue(payload["validation"]["has_reactive_cues"])
        self.assertTrue(payload["reactive_debug"]["uses_legacy_marks"])
        self.assertEqual(payload["reactive_debug"]["fallback_mode"], "legacy_marks")

        targets = {cue["submodel"] for cue in payload["reactive_cues"]}
        self.assertIn("kick", targets)
        self.assertIn("snare", targets)
        self.assertIn("hi_hat", targets)
        self.assertIn("cymbal", targets)
        self.assertTrue(any("left_stick" in cue["motion_submodels"] or "right_stick" in cue["motion_submodels"] for cue in payload["reactive_cues"]))

    def test_reactive_drummer_distributes_drum_bus_when_only_bus_available(self) -> None:
        payload = build_reactive_drummer_member(
            drum_event_streams={
                "kick_events": [],
                "snare_events": [],
                "hihat_events": [],
                "cymbal_events": [],
                "tom_events": [],
                "drum_bus_events": [_event(100, "drum_bus"), _event(300, "drum_bus"), _event(500, "drum_bus")],
            }
        )

        self.assertTrue(payload["validation"]["has_reactive_cues"])
        self.assertTrue(payload["reactive_debug"]["uses_drum_bus_distribution"])
        self.assertEqual(payload["reactive_debug"]["fallback_mode"], "drum_bus_distribution")
        drum_types = {cue["kind"] for cue in payload["reactive_cues"]}
        self.assertIn("kick", drum_types)
        self.assertIn("snare", drum_types)


if __name__ == "__main__":
    unittest.main()
