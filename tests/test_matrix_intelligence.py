from __future__ import annotations

import random
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

from core import effect_engine, matrix_intelligence
from core.audio_intelligence import LyricEvent


class _DummyModel:
    def __init__(
        self,
        *,
        name: str,
        model_type: str,
        strings: int,
        nodes_per_string: int,
        total_pixels: int,
        is_submodel: bool = False,
        center_xy: tuple[float, float] = (0.0, 0.0),
    ) -> None:
        self.name = name
        self.type = model_type
        self.strings = strings
        self.nodes_per_string = nodes_per_string
        self.total_pixels = total_pixels
        self.is_submodel = is_submodel
        self.orientation = "horizontal"
        self._center_xy = center_xy

    def center(self) -> tuple[float, float, float]:
        return (self._center_xy[0], self._center_xy[1], 0.0)


class MatrixIntelligenceTests(unittest.TestCase):
    def _build_common_inputs(self) -> dict:
        parsed_layout = SimpleNamespace(
            models={
                "Matrix Main": _DummyModel(
                    name="Matrix Main",
                    model_type="matrix",
                    strings=64,
                    nodes_per_string=32,
                    total_pixels=2048,
                    center_xy=(100.0, 100.0),
                ),
                "Arch 1": _DummyModel(
                    name="Arch 1",
                    model_type="arch",
                    strings=8,
                    nodes_per_string=50,
                    total_pixels=400,
                    center_xy=(-50.0, 20.0),
                ),
            }
        )
        parts = [
            SimpleNamespace(label="VERSE", start_ms=0, end_ms=20000, energy=0.42),
            SimpleNamespace(label="CHORUS", start_ms=20000, end_ms=40000, energy=0.78),
        ]
        multiband = SimpleNamespace(
            tempo_bpm=128.0,
            genre_hint="edm",
            mood_hint="uplifting",
            descriptor_summary={
                "centroid_mean": 0.58,
                "contrast_mean": 0.44,
                "flatness_mean": 0.32,
                "flux_density": 62.0,
                "chroma_stability_mean": 0.56,
                "tonnetz_motion_mean": 0.30,
            },
            section_profiles={
                "VERSE": {
                    "loudness": 0.38,
                    "complexity": 0.44,
                    "scene_mode": "tight_minimal",
                    "dominant_band": "mid",
                    "flux_motion": 0.34,
                },
                "CHORUS": {
                    "loudness": 0.82,
                    "complexity": 0.72,
                    "scene_mode": "wide_bright",
                    "dominant_band": "bass",
                    "flux_motion": 0.66,
                },
            },
        )
        audio = SimpleNamespace(rms01=np.asarray([0.2, 0.35, 0.58, 0.74, 0.68], dtype=float))
        return {
            "parsed_layout": parsed_layout,
            "parts": parts,
            "multiband": multiband,
            "audio": audio,
            "beat_ms": [0, 500, 1000, 1500, 2000, 2500, 3000],
            "kicks": [500, 1000, 2000, 3000],
            "snares": [750, 1750, 2750],
            "hats": [250, 375, 625, 875, 1125, 1375],
            "bass_peaks": [600, 1100, 1600, 2100],
            "vocal_peaks": [900, 1900, 2900],
        }

    def test_discover_matrix_targets_finds_only_root_matrix_models(self) -> None:
        parsed_layout = SimpleNamespace(
            models={
                "M1": _DummyModel(name="M1", model_type="matrix", strings=32, nodes_per_string=16, total_pixels=512),
                "M1/Top": _DummyModel(
                    name="M1/Top",
                    model_type="matrix",
                    strings=32,
                    nodes_per_string=5,
                    total_pixels=160,
                    is_submodel=True,
                ),
                "Tree": _DummyModel(name="Tree", model_type="tree", strings=16, nodes_per_string=50, total_pixels=800),
            }
        )
        targets = matrix_intelligence.discover_matrix_targets(parsed_layout)
        self.assertEqual(len(targets), 1)
        self.assertEqual(targets[0]["name"], "M1")

    def test_build_matrix_plan_returns_expected_keys(self) -> None:
        kwargs = self._build_common_inputs()
        plan = matrix_intelligence.build_matrix_intelligence_plan(**kwargs, video_path=None)
        self.assertTrue(plan["enabled"])
        self.assertTrue(plan["matrix_available"])
        self.assertEqual(plan["matrix_count"], 1)
        self.assertIn("matrix_params", plan)
        self.assertIn("matrix_shader_config", plan)
        self.assertIn("frequency_layer_config", plan)
        self.assertIn("stem_layer_weights", plan)
        self.assertIn("responsible_use", plan)
        self.assertEqual(plan["matrix_params"]["width"], 64)
        self.assertEqual(plan["matrix_params"]["height"], 32)
        self.assertFalse(plan["video_data"]["video_available"])

    def test_build_matrix_plan_handles_missing_matrix_models(self) -> None:
        kwargs = self._build_common_inputs()
        kwargs["parsed_layout"] = SimpleNamespace(models={"Arch": _DummyModel(name="Arch", model_type="arch", strings=8, nodes_per_string=30, total_pixels=240)})
        plan = matrix_intelligence.build_matrix_intelligence_plan(**kwargs, video_path=None)
        self.assertTrue(plan["enabled"])
        self.assertFalse(plan["matrix_available"])
        self.assertEqual(plan["matrix_count"], 0)
        self.assertIn("copyright_warning", plan["responsible_use"])

    def test_recommend_sequence_effect_uses_text_for_active_lyrics(self) -> None:
        kwargs = self._build_common_inputs()
        plan = matrix_intelligence.build_matrix_intelligence_plan(**kwargs, video_path=None)
        effect_name = matrix_intelligence.recommend_sequence_effect(
            plan,
            cue="vocal",
            part_label="CHORUS",
            target_ms=22000,
            index=0,
            fallback="Pictures",
            lyric_active=True,
        )
        self.assertEqual(effect_name, "Text")

    def test_matrix_lyric_lookup_preserves_inclusive_and_nested_windows(self) -> None:
        lyrics = [
            LyricEvent(1500, 1600, "nested"),
            LyricEvent(4000, 3900, "reversed"),
            LyricEvent(1000, 3000, "outer"),
            LyricEvent(-50, 10, "opening"),
        ]
        expected = {
            0: True, 130: True, 131: False, 879: False, 880: True, 2900: True,
            3120: True, 3121: False, 3879: False, 3880: True, 4121: True, 4122: False,
        }
        with patch.object(
            matrix_intelligence, "recommend_sequence_effect",
            wraps=matrix_intelligence.recommend_sequence_effect,
        ) as recommend:
            effect_engine.place_pixel_reactive_score(
                style=effect_engine.VARIANTS[effect_engine.ACTIVE_STYLE_VERSION],
                pools=[effect_engine.SequentialPool("Matrix", "matrix", ["Matrix"])],
                parts=[effect_engine.SongPart("CHORUS", 0, 4500, 0.8)],
                note_events=[],
                lyric_events=lyrics,
                kicks=[],
                snares=[],
                hats=[],
                bass_peaks=[],
                vocal_peaks=list(expected),
                build_lifts=[],
                bar_ms=[],
                pool_state={},
                rng=random.Random(10),
                add_model=lambda *args, **kwargs: None,
                in_blackout=lambda time_ms: False,
                pixel_track=[],
            )
        actual = {
            call.kwargs["target_ms"]: call.kwargs["lyric_active"]
            for call in recommend.call_args_list
            if call.kwargs["cue"] == "vocal" and call.kwargs["target_ms"] in expected
        }
        self.assertEqual(actual, expected)

    def test_recommend_sequence_effect_uses_section_scene_for_bass_hits(self) -> None:
        kwargs = self._build_common_inputs()
        plan = matrix_intelligence.build_matrix_intelligence_plan(**kwargs, video_path=None)
        effect_name = matrix_intelligence.recommend_sequence_effect(
            plan,
            cue="bass",
            part_label="CHORUS",
            target_ms=24000,
            index=0,
            fallback="Pictures",
            lyric_active=False,
        )
        self.assertIn(effect_name, {"Fire", "Bars"})


if __name__ == "__main__":
    unittest.main()
