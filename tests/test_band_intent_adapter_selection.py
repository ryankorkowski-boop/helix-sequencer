from __future__ import annotations

import unittest

from core.band_intent_adapter import BandIntentAdapter


class BandIntentAdapterSelectionTests(unittest.TestCase):
    def test_explicit_empty_selection_remains_empty(self) -> None:
        adapter = BandIntentAdapter(performers=())
        self.assertEqual(adapter.performers, ())

    def test_default_selection_is_unchanged(self) -> None:
        adapter = BandIntentAdapter()
        self.assertEqual(adapter.performers, BandIntentAdapter.DEFAULT_PERFORMERS)

    def test_unknown_performer_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unknown band performer"):
            BandIntentAdapter(performers=("drummer", "xylophonist"))

    def test_duplicate_performer_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "must be unique"):
            BandIntentAdapter(performers=("drummer", "drummer"))

    def test_explicit_subset_is_preserved(self) -> None:
        self.assertEqual(BandIntentAdapter(performers=("singer",)).performers, ("singer",))


if __name__ == "__main__":
    unittest.main()
