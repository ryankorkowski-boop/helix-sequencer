from __future__ import annotations

import unittest

from models.mouth_templates import default_mouth_box, generate_mouth_library


class MouthTemplateTests(unittest.TestCase):
    def test_mouth_library_generates_all_shapes_with_coordinates(self) -> None:
        library = generate_mouth_library(64)
        self.assertEqual(set(library), {"mouth_A", "mouth_E", "mouth_I", "mouth_O", "mouth_U", "mouth_MBP"})
        self.assertTrue(all(shape.coordinates for shape in library.values()))
        self.assertIn("AH", library["mouth_A"].phoneme_aliases)
        self.assertIn("closed", library["mouth_MBP"].style_tags)

    def test_mouth_box_downscales_for_smaller_canvases(self) -> None:
        self.assertGreater(default_mouth_box(64)[0], default_mouth_box(32)[0])
        small = generate_mouth_library(32)
        self.assertTrue(all(shape.coordinates for shape in small.values()))


if __name__ == "__main__":
    unittest.main()
