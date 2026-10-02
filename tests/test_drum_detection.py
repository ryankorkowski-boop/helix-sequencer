from __future__ import annotations

import math
import unittest

import numpy as np

from audio.drum_classification import classify_drum_hit, score_drum_hit_families
from audio.drum_detection import DrumDetectionConfig, _compress_events, _detector_votes, _select_supported_families, detect_drum_event_streams


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
        snare, snare_conf = classify_drum_hit(
            {
                "low_ratio": 0.10,
                "mid_low_ratio": 0.18,
                "mid_ratio": 0.42,
                "high_ratio": 0.24,
                "centroid_hz": 1900,
                "spectral_spread01": 0.52,
                "transient_sharpness": 0.55,
                "decay_profile": 0.22,
            }
        )
        tom, tom_conf = classify_drum_hit(
            {
                "low_ratio": 0.18,
                "mid_low_ratio": 0.46,
                "mid_ratio": 0.22,
                "high_ratio": 0.10,
                "centroid_hz": 850,
                "spectral_spread01": 0.35,
                "transient_sharpness": 0.34,
                "decay_profile": 0.40,
            }
        )
        cymbal, cymbal_conf = classify_drum_hit(
            {
                "low_ratio": 0.02,
                "mid_low_ratio": 0.06,
                "mid_ratio": 0.16,
                "high_ratio": 0.62,
                "centroid_hz": 6200,
                "spectral_spread01": 0.72,
                "transient_sharpness": 0.22,
                "decay_profile": 0.72,
            }
        )
        self.assertEqual(kick, "kick")
        self.assertEqual(hat, "hihat")
        self.assertEqual(snare, "snare")
        self.assertEqual(tom, "tom")
        self.assertEqual(cymbal, "cymbal")
        self.assertGreater(kick_conf, 0.4)
        self.assertGreater(hat_conf, 0.4)
        self.assertGreater(snare_conf, 0.4)
        self.assertGreater(tom_conf, 0.4)
        self.assertGreater(cymbal_conf, 0.4)

    def test_tonal_kick_and_tom_survive_hpss_harmonic_contamination(self) -> None:
        kick_scores = score_drum_hit_families(
            {
                "low_ratio": 0.64,
                "mid_low_ratio": 0.19,
                "mid_ratio": 0.04,
                "high_ratio": 0.01,
                "centroid_hz": 250.0,
                "low_centroid_hz": 131.0,
                "low_flux_peak_hz": 64.6,
                "low_flux_strength": 0.68,
                "mid_low_flux_strength": 0.56,
                "high_flux_strength": 0.32,
                "spectral_spread01": 0.05,
                "spectral_flatness": 0.0,
                "percussive_ratio": 0.14,
                "transient_sharpness": 0.22,
                "decay_profile": 0.01,
            }
        )
        tom_scores = score_drum_hit_families(
            {
                "low_ratio": 0.81,
                "mid_low_ratio": 0.24,
                "mid_ratio": 0.03,
                "high_ratio": 0.01,
                "centroid_hz": 265.0,
                "low_centroid_hz": 147.0,
                "low_flux_peak_hz": 129.2,
                "low_flux_strength": 0.45,
                "mid_low_flux_strength": 0.65,
                "high_flux_strength": 0.32,
                "spectral_spread01": 0.04,
                "spectral_flatness": 0.0,
                "percussive_ratio": 0.39,
                "transient_sharpness": 0.17,
                "decay_profile": 0.01,
            }
        )

        self.assertGreater(kick_scores["kick"], 0.5)
        self.assertGreater(kick_scores["kick"], kick_scores["tom"])
        self.assertGreater(tom_scores["tom"], 0.45)
        self.assertGreater(tom_scores["tom"], tom_scores["kick"])

    def test_weak_low_band_ring_is_not_promoted_to_tom(self) -> None:
        scores = score_drum_hit_families(
            {
                "low_ratio": 0.33,
                "mid_low_ratio": 0.26,
                "mid_ratio": 0.04,
                "high_ratio": 0.01,
                "centroid_hz": 720.0,
                "low_centroid_hz": 175.0,
                "low_flux_peak_hz": 86.1,
                "low_flux_strength": 0.10,
                "mid_low_flux_strength": 0.15,
                "high_flux_strength": 0.03,
                "spectral_spread01": 0.05,
                "spectral_flatness": 0.0,
                "percussive_ratio": 0.10,
                "transient_sharpness": 0.02,
                "decay_profile": 1.0,
            }
        )

        self.assertLess(scores["tom"], 0.34)

    def test_medium_decay_broadband_hit_prefers_snare_over_cymbal(self) -> None:
        scores = score_drum_hit_families(
            {
                "low_ratio": 0.03,
                "mid_low_ratio": 0.03,
                "mid_ratio": 0.08,
                "high_ratio": 0.52,
                "centroid_hz": 10700.0,
                "low_centroid_hz": 245.0,
                "low_flux_peak_hz": 193.8,
                "low_flux_strength": 0.12,
                "mid_low_flux_strength": 0.18,
                "high_flux_strength": 0.82,
                "spectral_spread01": 0.30,
                "spectral_flatness": 0.55,
                "percussive_ratio": 1.0,
                "transient_sharpness": 0.02,
                "decay_profile": 0.62,
            }
        )

        self.assertGreater(scores["snare"], 0.34)
        self.assertGreater(scores["snare"], scores["cymbal"])

    def test_parallel_family_evidence_preserves_kick_plus_cymbal(self) -> None:
        features = {
            "low_ratio": 0.38,
            "mid_low_ratio": 0.10,
            "mid_ratio": 0.10,
            "high_ratio": 0.42,
            "centroid_hz": 4500.0,
            "low_centroid_hz": 200.0,
            "spectral_spread01": 0.70,
            "transient_sharpness": 0.70,
            "decay_profile": 0.75,
            "percussive_ratio": 0.75,
            "spectral_flatness": 0.10,
        }
        scores = score_drum_hit_families(features)
        selected = _select_supported_families(
            scores,
            DrumDetectionConfig(
                multi_hit_confidence_min=0.46,
                multi_hit_score_window=0.14,
                max_hits_per_onset=2,
            ),
        )

        self.assertEqual({name for name, _ in selected}, {"kick", "cymbal"})
        self.assertGreater(scores["kick"], 0.5)
        self.assertGreater(scores["cymbal"], 0.5)
        self.assertLess(scores["hihat"], scores["cymbal"])

    def test_compression_deduplicates_same_family_across_interleaved_hits(self) -> None:
        from audio.drum_classification import DrumEvent

        events = [
            DrumEvent(0.100, 0.60, 0.70, {}, 1, "kick"),
            DrumEvent(0.110, 0.50, 0.70, {}, 1, "hihat"),
            DrumEvent(0.121, 0.90, 0.80, {}, 1, "kick"),
        ]

        compressed = _compress_events(events, min_gap_ms=30)
        kicks = [event for event in compressed if event.drum_type == "kick"]
        hats = [event for event in compressed if event.drum_type == "hihat"]

        self.assertEqual(len(kicks), 1)
        self.assertEqual(len(hats), 1)
        self.assertAlmostEqual(kicks[0].timestamp, 0.121)

    def test_detector_votes_match_nearby_onset_and_flux_candidates(self) -> None:
        onset, flux, agreement = _detector_votes(
            101,
            {100},
            {102},
            tolerance_frames=1,
        )
        self.assertEqual(onset, 1.0)
        self.assertEqual(flux, 1.0)
        self.assertEqual(agreement, 2.0)

        onset, flux, agreement = _detector_votes(
            110,
            {100},
            {109},
            tolerance_frames=1,
        )
        self.assertEqual(onset, 0.0)
        self.assertEqual(flux, 1.0)
        self.assertEqual(agreement, 1.0)

    def test_synthetic_percussive_signal_produces_events(self) -> None:
        sr = 22050
        y = np.zeros(sr, dtype=np.float32)
        for start, freq in ((0.20, 90), (0.50, 1800), (0.75, 6500)):
            idx = int(start * sr)
            length = int(0.08 * sr)
            t = np.arange(length) / sr
            burst = np.sin(2 * math.pi * freq * t) * np.exp(-t * 35)
            y[idx : idx + length] += burst.astype(np.float32)
        streams = detect_drum_event_streams(
            y,
            sr,
            DrumDetectionConfig(onset_delta=0.025, min_gap_ms=12),
            source_label="demucs:drums",
        )
        total = sum(len(events) for events in streams.values())
        self.assertGreaterEqual(total, 2)
        self.assertTrue(any(streams[key] for key in ("kick_events", "snare_events", "hihat_events", "drum_bus_events")))
        flattened = [event for events in streams.values() for event in events]
        self.assertTrue(flattened)
        self.assertTrue(all(event.source == "demucs:drums" for event in flattened))
        self.assertTrue(all("score_kick" in event.frequency_band_info for event in flattened))
        self.assertTrue(all("detector_agreement" in event.frequency_band_info for event in flattened))
        self.assertTrue(any(event.frequency_band_info["detector_spectral_flux"] > 0 for event in flattened))


if __name__ == "__main__":
    unittest.main()
