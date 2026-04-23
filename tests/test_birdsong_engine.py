from __future__ import annotations

import random
import unittest
from types import SimpleNamespace

from core import birdsong_engine
from core import effect_engine


class BirdsongEngineTests(unittest.TestCase):
    def test_estimate_birdsong_confidence_tracks_high_frequency_activity(self) -> None:
        audio = SimpleNamespace(
            dur_s=12.0,
            centroid=[3200.0, 4100.0, 3500.0, 2800.0, 3600.0, 3900.0],
            pitch_hz=[620.0, 790.0, 660.0, 820.0, 670.0, 880.0],
        )
        note_events = [
            SimpleNamespace(start_ms=100, end_ms=220, notes=[(72, 0.8)], part="VERSE"),
            SimpleNamespace(start_ms=480, end_ms=620, notes=[(79, 0.7)], part="CHORUS"),
        ]
        confidence = birdsong_engine.estimate_birdsong_confidence(
            audio=audio,
            hats=[110, 250, 400, 610, 820],
            vocal_peaks=[500, 960],
            note_events=note_events,
        )
        self.assertGreater(confidence, 0.45)

    def test_place_birdsong_engine_places_calls_and_timing_events(self) -> None:
        audio = SimpleNamespace(
            dur_s=18.0,
            centroid=[3300.0] * 32,
            pitch_hz=[650.0, 780.0, 620.0, 840.0] * 8,
        )
        note_events = [
            SimpleNamespace(start_ms=200, end_ms=330, notes=[(74, 0.9), (79, 0.8)], part="VERSE"),
            SimpleNamespace(start_ms=540, end_ms=740, notes=[(67, 0.8), (71, 0.7)], part="CHORUS"),
            SimpleNamespace(start_ms=980, end_ms=1180, notes=[(63, 0.7), (67, 0.6)], part="BRIDGE"),
        ]
        pools = [
            SimpleNamespace(name="stars_1", category="stars", models=["s1", "s2", "s3"]),
            SimpleNamespace(name="line_1", category="line", models=["l1", "l2", "l3"]),
            SimpleNamespace(name="mega_1", category="mega", models=["m1", "m2", "m3", "m4"]),
        ]

        placements: list[tuple[str, int, int, str, str, str]] = []

        def add_model(model: str, st: int, en: int, label: str, eff: str = "On", stem: str = "other", **_: object) -> None:
            placements.append((model, st, en, label, eff, stem))

        result = birdsong_engine.place_birdsong_engine(
            audio=audio,
            note_events=note_events,
            hats=[190, 350, 520, 700, 870, 1120],
            vocal_peaks=[560, 1220],
            pools=pools,
            add_model=add_model,
            in_blackout=lambda _value: False,
            rng=random.Random(13),
            enabled=True,
            auto_enable=False,
            intensity=1.2,
            min_confidence=0.5,
            profile="wild",
        )

        self.assertTrue(result.enabled)
        self.assertGreater(result.calls, 0)
        self.assertGreater(len(result.timing_spans), 0)
        self.assertGreater(len(placements), 0)
        self.assertTrue(any(label == "birdsong_call" for _, _, _, label, _, _ in placements))

    def test_parse_args_accepts_birdsong_flags(self) -> None:
        args = effect_engine.parse_args(
            effect_engine.VARIANTS["v27.3"],
            [
                "--birdsong",
                "--birdsong-auto",
                "--birdsong-intensity",
                "1.35",
                "--birdsong-min-confidence",
                "0.5",
                "--birdsong-profile",
                "canopy",
            ],
        )
        self.assertTrue(args.birdsong_enabled)
        self.assertTrue(args.birdsong_auto)
        self.assertAlmostEqual(args.birdsong_intensity, 1.35)
        self.assertAlmostEqual(args.birdsong_min_confidence, 0.5)
        self.assertEqual(args.birdsong_profile, "canopy")


if __name__ == "__main__":
    unittest.main()
