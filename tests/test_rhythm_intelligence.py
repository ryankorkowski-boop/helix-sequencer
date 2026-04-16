from __future__ import annotations

import unittest
from types import SimpleNamespace

from core import rhythm_intelligence


class RhythmIntelligenceTests(unittest.TestCase):
    def test_detects_three_two_polyrhythm_overlay(self) -> None:
        beat_ms = [0, 500, 1000, 1500, 2000, 2500, 3000]
        duplets = [beat_ms[idx] + 250 for idx in range(len(beat_ms) - 1)]
        triplets: list[int] = []
        for idx in range(len(beat_ms) - 1):
            start = beat_ms[idx]
            end = beat_ms[idx + 1]
            span = end - start
            triplets.append(int(round(start + (span / 3.0))))
            triplets.append(int(round(start + (span * 2.0 / 3.0))))
        onsets = sorted(set(duplets + triplets))
        payload = rhythm_intelligence.build_rhythm_intelligence(
            beat_ms=beat_ms,
            onset_ms=onsets,
            note_onset_ms=onsets,
            parts=[],
            audio=SimpleNamespace(times_s=[0.0, 0.5, 1.0], rms01=[0.1, 0.2, 0.3]),
        )
        ratios = {item["ratio"]: item for item in payload["polyrhythm_overlays"]}
        self.assertIn("3:2", ratios)
        self.assertGreater(float(ratios["3:2"]["confidence"]), 0.5)

    def test_microtiming_profile_tracks_consistent_late_pocket(self) -> None:
        beat_ms = [idx * 500 for idx in range(0, 13)]
        note_onsets = [beat_ms[idx] + 125 + 18 for idx in range(len(beat_ms) - 1)]
        parts = [
            SimpleNamespace(label="VERSE", start_ms=0, end_ms=3000),
            SimpleNamespace(label="CHORUS", start_ms=3000, end_ms=6000),
        ]
        payload = rhythm_intelligence.build_rhythm_intelligence(
            beat_ms=beat_ms,
            onset_ms=note_onsets,
            note_onset_ms=note_onsets,
            parts=parts,
            audio=SimpleNamespace(times_s=[0.0, 0.5, 1.0], rms01=[0.2, 0.25, 0.3]),
        )
        micro = payload["microtiming"]
        self.assertGreater(int(micro["sample_count"]), 0)
        self.assertGreater(float(micro["mean_offset_ms"]), 8.0)
        self.assertGreater(len(payload["phrase_boundaries"]), 0)
        self.assertGreaterEqual(len(micro["by_part"]), 2)

    def test_energy_prediction_reports_future_lift(self) -> None:
        times_s = [idx * 0.1 for idx in range(0, 31)]
        rms01 = [0.08 + (idx * 0.01) if idx < 12 else 0.20 + ((idx - 12) * 0.025) if idx < 20 else 0.45 - ((idx - 20) * 0.02) for idx in range(0, 31)]
        profile = rhythm_intelligence.build_energy_prediction(
            audio=SimpleNamespace(times_s=times_s, rms01=rms01),
            horizon_ms=1200,
            step_ms=200,
        )
        self.assertGreater(int(profile["point_count"]), 0)
        self.assertGreater(float(profile["max_predicted_lift"]), 0.1)


if __name__ == "__main__":
    unittest.main()

