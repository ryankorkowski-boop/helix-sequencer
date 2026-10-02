from __future__ import annotations

import unittest

from animation.drummer_motion import assign_hand, build_drummer_motion
from audio.drum_classification import DrumEvent, empty_drum_streams
from effects.drum_effects import build_drum_effect_cues
from mapping.drum_mapper import map_events_to_drummer_components, resolve_drum_streams, schedule_drum_events


def _event(ms: int, drum_type: str, velocity: float = 0.8, confidence: float = 0.7) -> DrumEvent:
    return DrumEvent(ms / 1000.0, velocity, confidence, {"test": 1.0}, 1, drum_type, "test")


class DrumMappingTests(unittest.TestCase):
    def test_bus_fallback_does_not_cycle_guess(self) -> None:
        streams = empty_drum_streams()
        streams["drum_bus_events"] = [_event(100, "drum_bus"), _event(300, "drum_bus"), _event(500, "drum_bus")]
        resolved = resolve_drum_streams(streams)
        self.assertEqual(resolved["fallback_mode"], "drum_bus_inference")
        self.assertTrue(all(event.drum_type == "drum_bus" for event in resolved["events"]))

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
        self.assertLessEqual(len([event for event in scheduled if event.timestamp_ms <= 170]), 6)
        self.assertIn("cymbal", types)
        self.assertIn("tom", types)

    def test_arm_assignment_and_motion_windows(self) -> None:
        self.assertEqual(assign_hand(_event(100, "kick")), "foot")
        self.assertEqual(assign_hand(_event(100, "snare")), "left")
        self.assertEqual(assign_hand(_event(100, "cymbal")), "right")
        motions = build_drummer_motion([_event(100, "snare"), _event(250, "tom")])
        self.assertEqual(motions[0]["hand"], "left")
        self.assertEqual(motions[1]["hand"], "both")
        self.assertLess(motions[0]["start_ms"], motions[0]["strike_ms"])
        self.assertEqual(motions[0]["strike_ms"], 100)
        self.assertEqual(motions[0]["musical_strike_ms"], 100)
        self.assertTrue(motions[0]["musical_event_locked"])
        clamped = build_drummer_motion([_event(100, "snare")], config=__import__("animation.drummer_motion", fromlist=["DrummerMotionConfig"]).DrummerMotionConfig(anticipation_ms=10, humanize_min_ms=30, humanize_max_ms=30, seed=414))
        self.assertLessEqual(clamped[0]["start_ms"], clamped[0]["strike_ms"])

    def test_unresolved_bus_never_maps_to_kick_component(self) -> None:
        mapped = map_events_to_drummer_components([_event(100, "drum_bus")])
        self.assertEqual(mapped, [])

    def test_effect_cues_expose_spatial_and_piano_hooks(self) -> None:
        cues = build_drum_effect_cues([_event(100, "kick")])
        self.assertEqual(cues[0]["submodel"], "kick")
        self.assertTrue(cues[0]["spatial_impulse"]["enabled"])
        self.assertTrue(cues[0]["player_piano_hook"]["enabled"])


if __name__ == "__main__":
    unittest.main()
