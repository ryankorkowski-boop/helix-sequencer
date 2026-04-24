from __future__ import annotations

import math
import unittest

import numpy as np

from audio.drum_classification import classify_drum_hit
from audio.drum_detection import DrumDetectionConfig, detect_drum_event_streams


class DrumDetectionTests(unittest.TestCase):
    def test_classifier_maps_frequency_profiles(self) -> None:
        kick, kick_conf = classify_drum_hit(
            {
                "low_ratio": 0.72,
                "mid_low_ratio": 0.12,
                "mid_ratio": 0.08,
                "high_ratio": 0.02,
                "centroid_hz": 120,
                "spectral_spread01": 0.2,
                "transient_sharpness": 0.7,
                "decay_profile": 0.25,
            }
        )
        hat, hat_conf = classify_drum_hit(
            {
                "low_ratio": 0.02,
                "mid_low_ratio": 0.08,
                "mid_ratio": 0.18,
                "high_ratio": 0.72,
                "centroid_hz": 7000,
                "spectral_spread01": 0.72,
                "transient_sharpness": 0.8,
                "decay_profile": 0.1,
            }
        )
        self.assertEqual(kick, "kick")
        self.assertEqual(hat, "hihat")
        self.assertGreater(kick_conf, 0.4)
        self.assertGreater(hat_conf, 0.4)

    def test_synthetic_percussive_signal_produces_events(self) -> None:
        sr = 22050
        y = np.zeros(sr, dtype=np.float32)
        for start, freq in ((0.20, 90), (0.50, 1800), (0.75, 6500)):
            idx = int(start * sr)
            length = int(0.08 * sr)
            t = np.arange(length) / sr
            burst = np.sin(2 * math.pi * freq * t) * np.exp(-t * 35)
            y[idx : idx + length] += burst.astype(np.float32)
        streams = detect_drum_event_streams(y, sr, DrumDetectionConfig(onset_delta=0.025, min_gap_ms=12))
        total = sum(len(events) for events in streams.values())
        self.assertGreaterEqual(total, 2)
        self.assertTrue(any(streams[key] for key in ("kick_events", "snare_events", "hihat_events", "drum_bus_events")))


if __name__ == "__main__":
    unittest.main()
