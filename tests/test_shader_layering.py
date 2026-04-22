from __future__ import annotations

import unittest

from core import shader_layering


class ShaderLayeringTests(unittest.TestCase):
    def test_recommend_layer_stack_returns_three_profiles(self) -> None:
        layers = shader_layering.recommend_layer_stack(energy=0.7, onset=0.5, spread=0.4, contrast=0.6)
        self.assertEqual(len(layers), 3)
        self.assertEqual(layers[0].role, "base")
        self.assertEqual(layers[1].role, "mid")
        self.assertEqual(layers[2].role, "accent")

    def test_compatibility_score_within_unit_range(self) -> None:
        layers = shader_layering.recommend_layer_stack(energy=0.8, onset=0.8, spread=0.8, contrast=0.8)
        score = shader_layering.compatibility_score(layers)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)

    def test_coordinate_uniforms_shape_matches_trajectory(self) -> None:
        trajectory = [
            {"x": 0.0, "y": 0.0, "z": 0.0},
            {"x": 1.0, "y": 0.5, "z": 0.1},
            {"x": 2.0, "y": 1.0, "z": 0.4},
        ]
        uniforms = shader_layering.coordinate_uniforms(trajectory, focus_depth=0.25)
        self.assertEqual(sorted(uniforms.keys()), ["u_focus_x", "u_focus_y", "u_path_speed", "u_slice_z"])
        self.assertEqual(len(uniforms["u_focus_x"]), 3)
        self.assertEqual(len(uniforms["u_focus_y"]), 3)
        self.assertEqual(len(uniforms["u_slice_z"]), 3)
        self.assertEqual(len(uniforms["u_path_speed"]), 3)


if __name__ == "__main__":
    unittest.main()
