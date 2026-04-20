from __future__ import annotations

import math
import unittest
from types import SimpleNamespace

import numpy as np

from core import chronoflow


class ChronoflowTests(unittest.TestCase):
    def _audio(self) -> SimpleNamespace:
        sr = 22050
        dur_s = 2.0
        sample_count = int(sr * dur_s)
        t = np.linspace(0.0, dur_s, sample_count, endpoint=False)
        y = 0.45 * np.sin(2.0 * math.pi * 220.0 * t) + 0.22 * np.sin(2.0 * math.pi * 440.0 * t)
        times = np.linspace(0.0, dur_s, 64, endpoint=False)
        return SimpleNamespace(
            sr=sr,
            y=y.astype(float),
            dur_s=dur_s,
            times_s=times.astype(float),
            rms01=np.linspace(0.15, 0.85, 64, dtype=float),
            bass01=np.linspace(0.65, 0.25, 64, dtype=float),
            vocal01=np.linspace(0.10, 0.75, 64, dtype=float),
            pitch_hz=np.linspace(220.0, 660.0, 64, dtype=float),
        )

    def _multiband(self) -> SimpleNamespace:
        times = np.linspace(0.0, 2.0, 64, endpoint=False)
        return SimpleNamespace(
            tempo_bpm=128.0,
            genre_hint="edm",
            mood_hint="uplifting",
            frame_times_s=times.astype(float),
            spectral_centroid01=np.linspace(0.2, 0.9, 64, dtype=float),
            spectral_bandwidth01=np.linspace(0.25, 0.82, 64, dtype=float),
            spectral_contrast01=np.linspace(0.18, 0.73, 64, dtype=float),
            spectral_flatness01=np.linspace(0.42, 0.20, 64, dtype=float),
            spectral_flux01=np.linspace(0.22, 0.88, 64, dtype=float),
            mfcc_motion01=np.linspace(0.20, 0.68, 64, dtype=float),
            chroma_stability01=np.linspace(0.70, 0.44, 64, dtype=float),
            tonnetz_motion01=np.linspace(0.12, 0.40, 64, dtype=float),
            descriptor_summary={
                "centroid_mean": 0.56,
                "contrast_mean": 0.48,
                "flatness_mean": 0.30,
                "mfcc_motion_mean": 0.38,
                "chroma_stability_mean": 0.58,
                "tonnetz_motion_mean": 0.26,
            },
            sub_bass_marks=[120, 520, 920, 1320],
            bass_marks=[180, 580, 980, 1380],
            mid_marks=[260, 660, 1060, 1460],
            high_marks=[320, 720, 1120, 1520],
            spectral_flux_marks=[300, 700, 1100, 1500],
        )

    def test_build_chronoflow_plan_returns_visualizer_and_embedding(self) -> None:
        audio = self._audio()
        multiband = self._multiband()
        parts = [
            SimpleNamespace(label="VERSE", start_ms=0, end_ms=900),
            SimpleNamespace(label="CHORUS", start_ms=900, end_ms=2000),
        ]
        note_events = [
            SimpleNamespace(start_ms=180, end_ms=320, notes=[(60, 0.9)], part="VERSE", section="VERSE"),
            SimpleNamespace(start_ms=980, end_ms=1160, notes=[(67, 0.8)], part="CHORUS", section="CHORUS"),
        ]
        lyric_events = [
            SimpleNamespace(start_ms=940, end_ms=1080, text="hello"),
        ]

        payload = chronoflow.build_chronoflow_plan(
            audio_path=None,
            parsed_layout=None,
            audio=audio,
            multiband=multiband,
            parts=parts,
            note_events=note_events,
            lyric_events=lyric_events,
            beat_ms=[0, 500, 1000, 1500],
            onset_ms=[120, 240, 500, 760, 980, 1200, 1540],
            kicks=[120, 980],
            snares=[500, 1500],
            hats=[240, 760, 1200, 1540],
            bass_peaks=[180, 1080],
            vocal_peaks=[980],
            build_lifts=[820],
            releases=[1320],
        )

        self.assertTrue(payload["enabled"])
        self.assertIn("audio_intelligence", payload)
        self.assertIn("spatial_embedding", payload)
        self.assertIn("helixualizer", payload)
        self.assertIn("visualizer", payload)
        self.assertTrue(payload["helixualizer"]["perceptual_bands"]["banks"])
        self.assertIn("xlights_projection", payload["spatial_embedding"])
        self.assertGreater(payload["debug"]["event_count"], 0)
        self.assertGreater(payload["debug"]["trajectory_count"], 0)
        self.assertTrue(payload["visualizer"]["lyric_hits"])

    def test_build_timing_track_uses_lyric_labels(self) -> None:
        payload = {
            "visualizer": {
                "events": [
                    {
                        "time_ms": 1000,
                        "kind": "vocal",
                        "band": "mid",
                        "metadata": {"lifetime_ms": 180, "lyric_text": "shine"},
                    }
                ]
            }
        }
        track = chronoflow.build_timing_track(payload)
        self.assertEqual(track[0][0], "vocal:shine")
        self.assertEqual(track[0][1], 1000)
        self.assertEqual(track[0][2], 1180)


if __name__ == "__main__":
    unittest.main()
