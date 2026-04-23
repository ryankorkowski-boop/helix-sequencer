from __future__ import annotations

import math
import unittest
from types import SimpleNamespace

import numpy as np

from core import helixualizer


class HelixualizerTests(unittest.TestCase):
    def _audio(self) -> SimpleNamespace:
        sr = 22050
        dur_s = 2.0
        sample_count = int(sr * dur_s)
        t = np.linspace(0.0, dur_s, sample_count, endpoint=False)
        y = (
            0.42 * np.sin(2.0 * math.pi * 130.81 * t)
            + 0.28 * np.sin(2.0 * math.pi * 261.63 * t)
            + 0.18 * np.sin(2.0 * math.pi * 523.25 * t)
        )
        times = np.linspace(0.0, dur_s, 64, endpoint=False)
        return SimpleNamespace(
            sr=sr,
            y=y.astype(float),
            dur_s=dur_s,
            times_s=times.astype(float),
            rms01=np.linspace(0.12, 0.84, 64, dtype=float),
            bass01=np.linspace(0.72, 0.26, 64, dtype=float),
            vocal01=np.linspace(0.10, 0.76, 64, dtype=float),
            pitch_hz=np.linspace(130.81, 523.25, 64, dtype=float),
        )

    def _multiband(self) -> SimpleNamespace:
        return SimpleNamespace(
            spectral_centroid01=np.linspace(0.18, 0.88, 64, dtype=float),
        )

    def test_build_helixualizer_plan_returns_perceptual_and_projection_data(self) -> None:
        payload = helixualizer.build_helixualizer_plan(
            audio_path=None,
            audio=self._audio(),
            multiband=self._multiband(),
            note_events=[],
            beat_ms=[0, 500, 1000, 1500],
            onset_ms=[120, 240, 520, 760, 980, 1200, 1540],
        )

        self.assertTrue(payload["enabled"])
        self.assertEqual(payload["title"], "Helixualizer")
        self.assertEqual(len(payload["perceptual_bands"]["banks"]), 3)
        self.assertEqual(len(payload["piano_roll"]["keys"]), 61)
        self.assertIn("candy_cane_bar_curve", payload["xlights_projection"])
        self.assertIn("arrival_curve", payload["transport"])

    def test_suggest_player_piano_neighbors_uses_transport_energy(self) -> None:
        payload = {
            "frame_times_s": [0.0, 0.5, 1.0, 1.5],
            "transport": {"arrival_curve": [0.1, 0.75, 0.9, 0.3]},
            "xlights_projection": {
                "candy_cane_bar_curve": [0.1, 0.8, 0.86, 0.2],
                "piano_lane_groups": {
                    "low": [0.2, 0.6, 0.7, 0.2],
                    "mid": [0.1, 0.5, 0.6, 0.2],
                    "high": [0.1, 0.2, 0.55, 0.1],
                },
            },
        }
        offsets = helixualizer.suggest_player_piano_neighbors(
            payload,
            start_ms=480,
            end_ms=980,
            cue="build",
            mix=1.0,
        )
        self.assertEqual(offsets, [-2, -1, 1, 2])


if __name__ == "__main__":
    unittest.main()
