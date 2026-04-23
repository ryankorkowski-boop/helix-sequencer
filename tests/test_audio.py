from __future__ import annotations

from pathlib import Path
import unittest

from core import audio_intelligence


class AudioIntelligenceTests(unittest.TestCase):
    def test_normalize_name_collapses_spacing_and_case(self) -> None:
        self.assertEqual(audio_intelligence.normalize_name("  Mega_TREE-01  "), "mega tree 01")

    def test_ordered_spatial_path_preserves_input_for_none(self) -> None:
        models = ["A", "B", "C"]
        coords = {"A": (0.0, 0.0), "B": (1.0, 0.0), "C": (2.0, 0.0)}
        ordered = audio_intelligence.ordered_spatial_path(models, coords, "none", rng=None)
        self.assertEqual(ordered, models)

    def test_nearest_mark_distance_and_confidence(self) -> None:
        marks = [100, 250, 400]
        self.assertEqual(audio_intelligence.nearest_mark_distance_ms(260, marks), 10)
        self.assertAlmostEqual(
            audio_intelligence.proximity_confidence(260, marks, window_ms=100, floor=0.1),
            0.9,
            places=6,
        )

    def test_build_stem_analysis_missing_audio_is_stable(self) -> None:
        result = audio_intelligence.build_stem_analysis(
            audio_path=Path("does-not-exist.wav"),
            use_moises=False,
            api_key=None,
            cache_dir=Path("."),
        )
        self.assertEqual(result.source, "direct")
        self.assertEqual(result.stems, {})
        self.assertEqual(result.bass_peaks_ms, [])
        self.assertEqual(result.vocal_peaks_ms, [])
        self.assertEqual(result.drum_kicks_ms, [])
        self.assertEqual(result.drum_snares_ms, [])
        self.assertEqual(result.drum_hats_ms, [])


if __name__ == "__main__":
    unittest.main()
