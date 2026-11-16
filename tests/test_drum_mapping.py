from __future__ import annotations

import unittest

from animation.drummer_motion import build_drummer_motion
from audio.drum_classification import DrumEvent, empty_drum_streams
from effects.drum_effects import build_drum_effect_cues
from mapping.drum_mapper import resolve_drum_streams, schedule_drum_events


def _event(ms: int, drum_type: str, velocity: float = 0.8, confidence: float = 0.7) -> DrumEvent:
    return DrumEvent(ms / 1000.0, velocity, confidence, {"test": 1.0}, 1, drum_type, "test")


class DrumMappingTests(unittest.TestCase):
    def test_bus_fallback_distributes_across_kit(self) -> None:
        streams = empty_drum_streams()
        streams["drum_bus_events"] = [_event(100, "drum_bus"), _event(300, "drum_bus"), _event(500, "drum_bus")]
        resolved = resolve_drum_streams(streams)
        types = [event.drum_type for event in resolved["events"]]
        self.assertEqual(resolved["fallback_mode"], "drum_bus_distribution")
        self.assertIn("kick", types)
        self.assertIn("snare", types)

    def test_scheduler_prioritizes_dense_hits_and_reduces_repeats(self) -> None:
        events = [
            _event(100, "hihat"),
            _event(105, "kick"),
            _event(110, "snare"),
            _event(115, "cymbal"),
            _event(120, "tom"),
            _event(150, "hihat"),
        ]
        scheduled = schedule_drum_events(events)
        types = [event.drum_type for event in scheduled]
        self.assertIn("kick", types)
        self.assertIn("snare", types)
        self.assertLessEqual(len([event for event in scheduled if event.timestamp_ms <= 170]), 4)

    def test_arm_assignment_and_motion_windows(self) -> None:
        # Current motion contract assigns contacting hands per timed event,
        # rather than exporting the removed assign_hand helper.
        events = [
            _event(100, "snare"),
            _event(200, "snare"),
            _event(250, "cymbal"),
            _event(320, "cymbal"),
            _event(450, "tom"),
            _event(600, "kick"),
        ]
        motions = build_drummer_motion(events)
        self.assertEqual([motion["hand"] for motion in motions[:4]], ["L", "R", "L", "R"])
        self.assertEqual(motions[4]["hand"], None)
        self.assertEqual(motions[5]["hand"], None)
        self.assertNotEqual(motions[2]["component"], motions[3]["component"])
        self.assertEqual(motions[0]["component"], motions[1]["component"])
        self.assertTrue(all(motion["submodels"] == [motion["component"]] for motion in motions))
        self.assertLess(motions[0]["start_ms"], motions[0]["strike_ms"])
        self.assertGreater(motions[0]["rebound_end_ms"], motions[0]["strike_ms"])
        self.assertEqual(motions, build_drummer_motion(events))

    def test_effect_cues_expose_spatial_and_piano_hooks(self) -> None:
        cues = build_drum_effect_cues([_event(100, "kick")])
        self.assertEqual(cues[0]["submodel"], "kick")
        self.assertTrue(cues[0]["spatial_impulse"]["enabled"])
        self.assertTrue(cues[0]["player_piano_hook"]["enabled"])


if __name__ == "__main__":
    unittest.main()
