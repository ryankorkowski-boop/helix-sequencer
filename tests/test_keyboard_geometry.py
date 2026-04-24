from __future__ import annotations

import unittest

from render.keyboard_geometry import generate_keyboard_geometry, is_black_key


class KeyboardGeometryTests(unittest.TestCase):
    def test_white_black_key_geometry_for_octave(self) -> None:
        geometry = generate_keyboard_geometry(60, 71)
        self.assertEqual(len(geometry.keys), 12)
        whites = [key for key in geometry.keys if not key.is_black]
        blacks = [key for key in geometry.keys if key.is_black]
        self.assertEqual(len(whites), 7)
        self.assertEqual(len(blacks), 5)
        self.assertFalse(is_black_key(60))
        self.assertTrue(is_black_key(61))
        self.assertLess(geometry.key_for_pitch(61).height, geometry.key_for_pitch(60).height)  # type: ignore[union-attr]

    def test_omit_sharps_filters_black_keys(self) -> None:
        geometry = generate_keyboard_geometry(60, 71, show_sharps_flats=False)
        self.assertEqual([key.pitch for key in geometry.keys], [60, 62, 64, 65, 67, 69, 71])
        self.assertIsNone(geometry.key_for_pitch(61))

    def test_vertical_orientation_swaps_axes(self) -> None:
        horizontal = generate_keyboard_geometry(60, 64, orientation="horizontal")
        vertical = generate_keyboard_geometry(60, 64, orientation="vertical")
        self.assertEqual(vertical.key_for_pitch(60).width, horizontal.key_for_pitch(60).height)  # type: ignore[union-attr]


if __name__ == "__main__":
    unittest.main()
