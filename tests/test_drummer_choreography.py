from __future__ import annotations

import unittest

from audio.drum_classification import DrumEvent
from mapping.drum_mapper import apply_drummer_choreography


class DrummerChoreographyTests(unittest.TestCase):
    def test_accented_kick_gets_foot_stomp(self) -> None:
        event = DrumEvent(
            timestamp=1.0,
            velocity=0.95,
            confidence=0.9,
            frequency_band_info={},
            cluster_id=1,
            drum_type="kick",
        )
        result = apply_drummer_choreography([event])
        self.assertEqual(result[0]["motion_profile"], "foot_stomp")
        self.assertTrue(result[0]["accent"])

    def test_dense_tom_phrase_becomes_traveling_fill(self) -> None:
        events = [
            DrumEvent(
                timestamp=ts / 1000,
                velocity=0.7,
                confidence=0.8,
                frequency_band_info={},
                cluster_id=i,
                drum_type=kind,
            )
            for i, (ts, kind) in enumerate(
                [(1000, "tom_left"), (1100, "snare"), (1200, "tom_right"), (1300, "floor_tom")]
            )
        ]
        result = apply_drummer_choreography(events)
        tom_profiles = [
            item["motion_profile"]
            for item in result
            if item["drum_type"] in {"tom_left", "tom_right", "floor_tom"}
        ]
        self.assertEqual(tom_profiles, ["traveling_tom_fill"] * 3)
        self.assertTrue(all(item["fill"] for item in result if item["drum_type"] != "tom"))

    def test_same_input_is_deterministic_and_does_not_change_timing(self) -> None:
        events = [
            DrumEvent(0.0, 0.8, 0.8, {}, 1, "kick"),
            DrumEvent(0.25, 0.5, 0.8, {}, 2, "hihat"),
            DrumEvent(0.5, 0.9, 0.9, {}, 3, "crash"),
        ]
        first = apply_drummer_choreography(events)
        second = apply_drummer_choreography(list(reversed(events)))
        self.assertEqual(first, second)
        self.assertEqual([item["timestamp_ms"] for item in first], [0, 250, 500])
        self.assertEqual(first[2]["motion_profile"], "both_arm_crash")


if __name__ == "__main__":
    unittest.main()
