from __future__ import annotations

import random
import unittest
from types import SimpleNamespace

import numpy as np

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

    def test_birdsong_v2_dynamic_mix_scales_density_deterministically(self) -> None:
        low_mix = effect_engine.birdsong_v2_dynamic_mix(base_mix=0.35, energy=0.1, intensity=0.5)
        high_mix = effect_engine.birdsong_v2_dynamic_mix(base_mix=0.35, energy=0.9, intensity=1.5)

        self.assertLess(low_mix, high_mix)
        self.assertEqual(
            effect_engine.birdsong_v2_event_limit(base_mix=0.35, energy=0.1, intensity=0.5),
            int(2 + low_mix * 6),
        )
        self.assertGreater(
            effect_engine.birdsong_v2_event_limit(base_mix=0.35, energy=0.9, intensity=1.5),
            effect_engine.birdsong_v2_event_limit(base_mix=0.35, energy=0.1, intensity=0.5),
        )

    def test_birdsong_v2_enable_guardrails_are_deterministic(self) -> None:
        self.assertFalse(
            effect_engine.birdsong_v2_should_enable(
                enabled=False,
                auto=False,
                confidence=1.0,
                min_confidence=0.45,
            )
        )
        self.assertFalse(
            effect_engine.birdsong_v2_should_enable(
                enabled=False,
                auto=True,
                confidence=0.44,
                min_confidence=0.45,
            )
        )
        self.assertTrue(
            effect_engine.birdsong_v2_should_enable(
                enabled=False,
                auto=True,
                confidence=0.45,
                min_confidence=0.45,
            )
        )
        self.assertTrue(
            effect_engine.birdsong_v2_should_enable(
                enabled=True,
                auto=False,
                confidence=0.0,
                min_confidence=1.0,
            )
        )

    def test_place_birdsong_v2_overlay_is_flag_gated(self) -> None:
        audio = SimpleNamespace(
            dur_s=2.0,
            times_s=np.asarray([0.0, 1.0, 2.0]),
            rms01=np.asarray([0.1, 0.9, 0.2]),
            bass01=np.asarray([0.1, 0.8, 0.1]),
            vocal01=np.asarray([0.1, 0.4, 0.1]),
        )
        multiband = effect_engine.MultiBandAnalysis(
            sub_bass_marks=[],
            bass_marks=[],
            mid_marks=[],
            high_marks=[],
            spectral_flux_marks=[],
            loud_marks=[1000],
            quiet_windows=[],
            dominance_marks={},
            frame_times_s=np.asarray([0.0, 1.0, 2.0]),
            spectral_centroid01=np.asarray([0.1, 0.7, 0.2]),
            spectral_flux01=np.asarray([0.1, 0.9, 0.1]),
        )
        placements: list[tuple[str, int, int, str, str]] = []

        def add_model(model: str, st: int, en: int, label: str, eff: str = "On", **_: object) -> None:
            placements.append((model, st, en, label, eff))

        disabled = effect_engine.place_birdsong_v2_overlay(
            audio=audio,
            multiband=multiband,
            model_names=["left_line", "kick_drum_ground", "roof_star"],
            event_times_ms=[1000],
            onset_ms=[1000],
            beat_ms=[0, 1000, 2000],
            add_model=add_model,
            in_blackout=lambda _value: False,
            enabled=False,
        )
        self.assertFalse(disabled.enabled)
        self.assertEqual(disabled.reason, "disabled")
        self.assertEqual(placements, [])

    def test_place_birdsong_v2_overlay_places_deterministic_events_when_enabled(self) -> None:
        audio = SimpleNamespace(
            dur_s=2.0,
            times_s=np.asarray([0.0, 1.0, 2.0]),
            rms01=np.asarray([0.1, 0.9, 0.2]),
            bass01=np.asarray([0.1, 0.8, 0.1]),
            vocal01=np.asarray([0.1, 0.4, 0.1]),
        )
        multiband = effect_engine.MultiBandAnalysis(
            sub_bass_marks=[],
            bass_marks=[],
            mid_marks=[],
            high_marks=[],
            spectral_flux_marks=[],
            loud_marks=[1000],
            quiet_windows=[],
            dominance_marks={},
            frame_times_s=np.asarray([0.0, 1.0, 2.0]),
            spectral_centroid01=np.asarray([0.1, 0.7, 0.2]),
            spectral_flux01=np.asarray([0.1, 0.9, 0.1]),
        )

        def run_once() -> list[tuple[str, int, int, str, str]]:
            placements: list[tuple[str, int, int, str, str]] = []

            def add_model(model: str, st: int, en: int, label: str, eff: str = "On", **_: object) -> None:
                placements.append((model, st, en, label, eff))

            result = effect_engine.place_birdsong_v2_overlay(
                audio=audio,
                multiband=multiband,
                model_names=["left_line", "kick_drum_ground", "roof_star"],
                event_times_ms=[1000],
                onset_ms=[1000],
                beat_ms=[0, 1000, 2000],
                hats=[1000],
                add_model=add_model,
                in_blackout=lambda _value: False,
                enabled=True,
            )
            self.assertTrue(result.enabled)
            self.assertGreater(result.placements, 0)
            self.assertEqual(result.trigger_waves, 1)
            self.assertEqual(result.director_sections, ("drop",))
            self.assertEqual(result.choreographed_events, result.placements)
            return placements

        first = run_once()
        second = run_once()

        self.assertEqual(first, second)
        self.assertTrue(all(label == "birdsong_v2" for _, _, _, label, _ in first))

    def test_place_birdsong_v2_overlay_quantizes_events_when_tempo_is_available(self) -> None:
        audio = SimpleNamespace(
            dur_s=2.0,
            times_s=np.asarray([0.0, 1.12, 2.0]),
            rms01=np.asarray([0.1, 0.9, 0.2]),
            bass01=np.asarray([0.1, 0.8, 0.1]),
            vocal01=np.asarray([0.1, 0.4, 0.1]),
        )
        multiband = effect_engine.MultiBandAnalysis(
            sub_bass_marks=[],
            bass_marks=[],
            mid_marks=[],
            high_marks=[],
            spectral_flux_marks=[],
            loud_marks=[1120],
            quiet_windows=[],
            dominance_marks={},
            frame_times_s=np.asarray([0.0, 1.12, 2.0]),
            spectral_centroid01=np.asarray([0.1, 0.7, 0.2]),
            spectral_flux01=np.asarray([0.1, 0.9, 0.1]),
            tempo_bpm=120.0,
        )
        placements: list[tuple[str, int, int, str, str]] = []

        def add_model(model: str, st: int, en: int, label: str, eff: str = "On", **_: object) -> None:
            placements.append((model, st, en, label, eff))

        result = effect_engine.place_birdsong_v2_overlay(
            audio=audio,
            multiband=multiband,
            model_names=["left_line", "kick_drum_ground", "roof_star"],
            event_times_ms=[1120],
            onset_ms=[1120],
            beat_ms=[0, 500, 1000, 1500, 2000],
            hats=[],
            add_model=add_model,
            in_blackout=lambda _value: False,
            enabled=True,
        )

        self.assertTrue(result.enabled)
        self.assertTrue(placements)
        self.assertTrue(all(st % 125 == 0 for _, st, _, _, _ in placements))
        self.assertTrue(all(en % 125 == 0 for _, _, en, _, _ in placements))

    def test_place_birdsong_v2_overlay_passes_color_when_supported(self) -> None:
        audio = SimpleNamespace(
            dur_s=2.0,
            times_s=np.asarray([0.0, 1.0, 2.0]),
            rms01=np.asarray([0.1, 0.9, 0.2]),
            bass01=np.asarray([0.1, 0.8, 0.1]),
            vocal01=np.asarray([0.1, 0.4, 0.1]),
        )
        multiband = effect_engine.MultiBandAnalysis(
            sub_bass_marks=[],
            bass_marks=[],
            mid_marks=[],
            high_marks=[],
            spectral_flux_marks=[],
            loud_marks=[1000],
            quiet_windows=[],
            dominance_marks={},
            frame_times_s=np.asarray([0.0, 1.0, 2.0]),
            spectral_centroid01=np.asarray([0.1, 0.7, 0.2]),
            spectral_flux01=np.asarray([0.1, 0.9, 0.1]),
        )
        placements: list[tuple[str, tuple[int, int, int] | None]] = []

        def add_model(model: str, st: int, en: int, label: str, eff: str = "On", color: tuple[int, int, int] | None = None, **_: object) -> None:
            placements.append((model, color))

        result = effect_engine.place_birdsong_v2_overlay(
            audio=audio,
            multiband=multiband,
            model_names=["left_line", "kick_drum_ground", "roof_star"],
            event_times_ms=[1000],
            onset_ms=[1000],
            beat_ms=[0, 1000, 2000],
            hats=[],
            add_model=add_model,
            in_blackout=lambda _value: False,
            enabled=True,
        )

        self.assertEqual(result.colorized_events, result.placements)
        self.assertTrue(all(color is not None for _, color in placements))

    def test_place_birdsong_v2_overlay_does_not_require_color_support(self) -> None:
        audio = SimpleNamespace(
            dur_s=2.0,
            times_s=np.asarray([0.0, 1.0, 2.0]),
            rms01=np.asarray([0.1, 0.9, 0.2]),
            bass01=np.asarray([0.1, 0.8, 0.1]),
            vocal01=np.asarray([0.1, 0.4, 0.1]),
        )
        multiband = effect_engine.MultiBandAnalysis(
            sub_bass_marks=[],
            bass_marks=[],
            mid_marks=[],
            high_marks=[],
            spectral_flux_marks=[],
            loud_marks=[1000],
            quiet_windows=[],
            dominance_marks={},
            frame_times_s=np.asarray([0.0, 1.0, 2.0]),
            spectral_centroid01=np.asarray([0.1, 0.7, 0.2]),
            spectral_flux01=np.asarray([0.1, 0.9, 0.1]),
        )
        placements: list[str] = []

        def add_model(model: str, st: int, en: int, label: str, eff: str = "On", stem: str = "other") -> None:
            placements.append(model)

        result = effect_engine.place_birdsong_v2_overlay(
            audio=audio,
            multiband=multiband,
            model_names=["left_line", "kick_drum_ground", "roof_star"],
            event_times_ms=[1000],
            onset_ms=[1000],
            beat_ms=[0, 1000, 2000],
            hats=[],
            add_model=add_model,
            in_blackout=lambda _value: False,
            enabled=True,
        )

        self.assertGreater(result.placements, 0)
        self.assertEqual(result.colorized_events, 0)
        self.assertTrue(placements)


if __name__ == "__main__":
    unittest.main()
