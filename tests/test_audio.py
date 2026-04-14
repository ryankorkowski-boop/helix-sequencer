from __future__ import annotations

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


if __name__ == "__main__":
    unittest.main()
