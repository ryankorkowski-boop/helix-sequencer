from __future__ import annotations

import unittest

from core import feature_state


class FeatureStateTests(unittest.TestCase):
    def test_feature_state_applies_ema_and_bounded_history(self) -> None:
        state = feature_state.FeatureState(history_size=2, ema_alpha=0.5)

        state.update(0, energy=0.0, onset=0.0, centroid=100.0, low=0.0, mid=0.0, high=0.0, beat_phase=0.0, time_s=0.0)
        state.update(1, energy=1.0, onset=1.0, centroid=200.0, low=0.2, mid=0.3, high=0.5, beat_phase=0.5, time_s=0.1)
        last = state.update(2, energy=0.0, onset=0.0, centroid=300.0, low=0.0, mid=0.0, high=0.0, beat_phase=0.0, time_s=0.2)

        self.assertAlmostEqual(last.energy_smooth, 0.25, places=6)
        self.assertEqual(len(state.history), 2)
        self.assertEqual(state.history[0].frame_index, 1)
        self.assertEqual(state.history[1].frame_index, 2)

    def test_build_feature_state_sequence_derives_onset_bands_and_phase(self) -> None:
        features = {
            "energy": [0.0, 0.4, 0.8, 0.2],
            "centroid": [500.0, 1500.0, 6000.0, 3000.0],
            "tempo": 120.0,
        }
        frames = feature_state.build_feature_state_sequence(features, fps=4.0, history_size=16, ema_alpha=0.2)

        self.assertEqual(len(frames), 4)
        self.assertGreater(frames[2].onset, frames[3].onset)

        for frame in frames:
            self.assertAlmostEqual(frame.low + frame.mid + frame.high, frame.energy, places=6)

        self.assertAlmostEqual(frames[0].beat_phase, 0.0, places=6)
        self.assertAlmostEqual(frames[1].beat_phase, 0.5, places=6)
        self.assertAlmostEqual(frames[2].beat_phase, 0.0, places=6)
        self.assertAlmostEqual(frames[3].beat_phase, 0.5, places=6)

    def test_build_feature_state_sequence_handles_sparse_inputs(self) -> None:
        frames = feature_state.build_feature_state_sequence(
            {"energy": [0.3, 0.2], "tempo": 0.0},
            fps=10.0,
        )
        self.assertEqual(len(frames), 2)
        self.assertEqual(frames[0].centroid, 0.0)
        self.assertEqual(frames[0].beat_phase, 0.0)


if __name__ == "__main__":
    unittest.main()
