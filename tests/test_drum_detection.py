from __future__ import annotations

import math
import unittest

import numpy as np

from audio.drum_classification import classify_drum_hit
from audio.drum_detection import DrumDetectionConfig, detect_drum_event_streams
from mapping.drum_mapper import resolve_drum_streams


class DrumDetectionTests(unittest.TestCase):
    def test_classifier_maps_frequency_profiles(self) -> None:
        profiles = {
            "kick": {"low_ratio": .72, "mid_low_ratio": .12, "mid_ratio": .08, "high_ratio": .02, "centroid_hz": 120, "spectral_spread01": .2, "transient_sharpness": .7, "decay_profile": .25},
            "hihat": {"low_ratio": .02, "mid_low_ratio": .08, "mid_ratio": .18, "high_ratio": .72, "centroid_hz": 7000, "spectral_spread01": .72, "transient_sharpness": .8, "decay_profile": .1},
            "snare": {"low_ratio": .10, "mid_low_ratio": .18, "mid_ratio": .42, "high_ratio": .24, "centroid_hz": 1900, "spectral_spread01": .52, "transient_sharpness": .55, "decay_profile": .22},
            "tom": {"low_ratio": .18, "mid_low_ratio": .46, "mid_ratio": .22, "high_ratio": .10, "centroid_hz": 850, "spectral_spread01": .35, "transient_sharpness": .34, "decay_profile": .40},
            "cymbal": {"low_ratio": .02, "mid_low_ratio": .06, "mid_ratio": .16, "high_ratio": .62, "centroid_hz": 6200, "spectral_spread01": .72, "transient_sharpness": .22, "decay_profile": .72},
        }
        for expected, features in profiles.items():
            detected, confidence = classify_drum_hit(features)
            self.assertEqual(detected, expected)
            self.assertGreater(confidence, .35)

    def test_mixed_track_profiles_do_not_collapse_to_bus(self) -> None:
        # Real recordings often have harmonic bleed after HPSS. These profiles
        # deliberately contain enough harmonic contamination to reproduce that
        # condition while retaining a clear transient identity.
        snare, _ = classify_drum_hit({"low_ratio": .08, "mid_low_ratio": .20, "mid_ratio": .36, "high_ratio": .18, "centroid_hz": 1700, "spectral_spread01": .48, "transient_sharpness": .31, "decay_profile": .25, "percussive_ratio": .38})
        tom, _ = classify_drum_hit({"low_ratio": .14, "mid_low_ratio": .38, "mid_ratio": .20, "high_ratio": .09, "centroid_hz": 780, "spectral_spread01": .34, "transient_sharpness": .20, "decay_profile": .44, "percussive_ratio": .34})
        self.assertEqual(snare, "snare")
        self.assertEqual(tom, "tom")

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

    def test_partial_typed_detection_suppresses_bus_fallback(self) -> None:
        streams = {
            "kick_events": [],
            "snare_events": [],
            "tom_events": [],
            "hihat_events": [],
            "cymbal_events": [],
            "drum_bus_events": [
                # A large bus stream must not become a fake performance once
                # even one genuine typed hit has been identified.
                *[type("E", (), {"timestamp_ms": i * 80, "timestamp": i * .08, "velocity": .5, "confidence": .2, "frequency_band_info": {}, "cluster_id": i, "drum_type": "drum_bus", "source": "test"})() for i in range(100)]
            ],
        }
        from audio.drum_classification import DrumEvent
        streams["kick_events"] = [DrumEvent(.1, .8, .8, {"low_ratio": .8}, 1, "kick")]
        resolved = resolve_drum_streams(streams)
        self.assertEqual(resolved["fallback_mode"], "typed_detection_bus_suppressed")
        self.assertEqual([event.drum_type for event in resolved["events"]], ["kick"])


if __name__ == "__main__":
    unittest.main()
