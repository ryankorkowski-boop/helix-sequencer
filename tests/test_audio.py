from __future__ import annotations

import math
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import wave

from core import audio_intelligence, stem_cache


class AudioIntelligenceTests(unittest.TestCase):
    def _write_wave(self, values: list[float], *, sample_rate: int = 22050) -> Path:
        tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(tempdir.cleanup)
        path = Path(tempdir.name) / "test.wav"
        with wave.open(str(path), "wb") as handle:
            handle.setnchannels(1)
            handle.setsampwidth(2)
            handle.setframerate(sample_rate)
            frames = bytearray()
            for value in values:
                sample = max(-32767, min(32767, int(round(value * 32767.0))))
                frames.extend(int(sample).to_bytes(2, byteorder="little", signed=True))
            handle.writeframes(bytes(frames))
        return path

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
        self.assertEqual(result.background_vocal_events, [])
        self.assertEqual(result.drum_event_streams, {})


    def test_demucs_uses_six_stem_model_and_preserves_guitar_piano(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            audio = root / "song.wav"
            audio.write_bytes(b"fake")
            out_dir = root / "stems"

            def fake_run(cmd, check, capture_output):
                self.assertIn("htdemucs_6s", cmd)
                track_dir = out_dir / "htdemucs_6s" / audio.stem
                track_dir.mkdir(parents=True, exist_ok=True)
                for name in ("vocals", "drums", "bass", "guitar", "piano", "other"):
                    (track_dir / f"{name}.wav").write_bytes(b"stem")

            with mock.patch.object(audio_intelligence.shutil, "which", return_value="/fake/demucs"), mock.patch.object(
                audio_intelligence.subprocess, "run", side_effect=fake_run
            ):
                stems = audio_intelligence._try_demucs_stem_separation(audio, out_dir, None)

        self.assertIsNotNone(stems)
        self.assertEqual(
            set(stems or {}),
            {"vocals", "drums", "bass", "guitar", "piano", "other"},
        )

    def test_build_stem_analysis_reuses_cached_demucs_stems(self) -> None:
        audio = self._write_wave([0.0] * 4096)
        with tempfile.TemporaryDirectory() as cache:
            stem_dir = Path(cache) / audio.stem
            track_dir = stem_dir / "htdemucs_6s" / audio.stem
            track_dir.mkdir(parents=True, exist_ok=True)
            stems = {}
            for name in ("vocals", "drums", "bass", "guitar", "piano", "other"):
                path = track_dir / f"{name}.wav"
                path.write_bytes(b"stem")
                stems[name] = path
            stem_cache.write_stem_cache_manifest(
                audio,
                stem_dir,
                source="demucs",
                stems=stems,
                separator="htdemucs_6s",
            )
            detector_result = {
                "kick_events": [],
                "snare_events": [],
                "tom_events": [],
                "hihat_events": [],
                "cymbal_events": [],
                "drum_bus_events": [],
            }
            with mock.patch.object(
                audio_intelligence,
                "_try_demucs_stem_separation",
                side_effect=AssertionError("valid cache should bypass Demucs"),
            ) as demucs, mock.patch.object(
                audio_intelligence, "_analyze_drum_events", return_value=([], [], [])
            ), mock.patch.object(
                audio_intelligence, "_analyze_peak_events", return_value=[]
            ), mock.patch.object(
                audio_intelligence, "_classify_background_vocals", return_value=[]
            ), mock.patch.object(
                audio_intelligence, "_summarize_stem_file", return_value={"confidence": 0.5}
            ), mock.patch.object(
                audio_intelligence.drum_intel,
                "detect_drum_event_streams_from_file",
                return_value=detector_result,
            ) as detector:
                result = audio_intelligence.build_stem_analysis(
                    audio_path=audio,
                    use_moises=False,
                    api_key=None,
                    cache_dir=Path(cache),
                )

        demucs.assert_not_called()
        self.assertEqual(result.source, "demucs")
        self.assertEqual(set(result.stems), {"vocals", "drums", "bass", "guitar", "piano", "other"})
        detector.assert_called_once()
        self.assertEqual(detector.call_args.args[0].name, "drums.wav")
        self.assertEqual(detector.call_args.kwargs["source_label"], "demucs:drums")

    def test_build_stem_analysis_routes_detector_to_isolated_drum_stem(self) -> None:
        audio = self._write_wave([0.0] * 4096)
        with tempfile.TemporaryDirectory() as cache:
            stem_root = Path(cache) / "fake_stems"
            stems = {
                name: stem_root / f"{name}.wav"
                for name in ("vocals", "drums", "bass", "guitar", "piano", "other")
            }
            detector_result = {"kick_events": [], "snare_events": [], "tom_events": [], "hihat_events": [], "cymbal_events": [], "drum_bus_events": []}
            with mock.patch.object(audio_intelligence, "_try_demucs_stem_separation", return_value=stems), mock.patch.object(
                audio_intelligence, "_analyze_drum_events", return_value=([], [], [])
            ), mock.patch.object(
                audio_intelligence, "_analyze_peak_events", return_value=[]
            ), mock.patch.object(
                audio_intelligence, "_classify_background_vocals", return_value=[]
            ), mock.patch.object(
                audio_intelligence, "_summarize_stem_file", return_value={"confidence": 0.5}
            ), mock.patch.object(
                audio_intelligence.drum_intel,
                "detect_drum_event_streams_from_file",
                return_value=detector_result,
            ) as detector:
                result = audio_intelligence.build_stem_analysis(
                    audio_path=audio,
                    use_moises=False,
                    api_key=None,
                    cache_dir=Path(cache),
                )

        self.assertEqual(result.source, "demucs")
        self.assertIn("guitar", result.stems)
        self.assertIn("piano", result.stems)
        detector.assert_called_once()
        self.assertEqual(detector.call_args.args[0], stems["drums"])
        self.assertEqual(detector.call_args.kwargs["source_label"], "demucs:drums")

    def test_background_vocal_score_grouping_classifies_harmony_and_chant(self) -> None:
        harmony = audio_intelligence._group_background_vocal_scores(
            times_ms=[0, 100, 200, 300, 700],
            scores=[0.2, 0.62, 0.66, 0.64, 0.1],
            energies=[0.1, 0.55, 0.58, 0.56, 0.1],
        )
        self.assertEqual(len(harmony), 1)
        self.assertEqual(harmony[0].role, "harmony")
        self.assertEqual(harmony[0].source_reason, "vocal_stem_harmony_classifier")

        chant = audio_intelligence._group_background_vocal_scores(
            times_ms=[0, 100, 200, 300],
            scores=[0.82, 0.84, 0.8, 0.81],
            energies=[0.78, 0.8, 0.76, 0.77],
        )
        self.assertEqual(chant[0].role, "group_chant")

    def test_load_audio_analysis_config_defaults(self) -> None:
        config = audio_intelligence.load_audio_analysis_config(Path("does-not-exist.json"))

        self.assertGreater(config.onset_sensitivity, 0.0)
        self.assertGreater(config.max_candidate_events_per_second, 0)

    def test_analyze_audio_file_missing_audio_returns_empty_result(self) -> None:
        result = audio_intelligence.analyze_audio_file(Path("does-not-exist.wav"))

        self.assertFalse(result.metadata["exists"])
        self.assertEqual(result.beat_events, [])
        self.assertIn("fallback", result.debug_summaries)

    def test_extract_note_candidates_and_prop_mapping(self) -> None:
        sr = 22050
        values = [0.35 * math.sin((2.0 * math.pi * 440.0 * idx) / sr) for idx in range(sr)]
        path = self._write_wave(values, sample_rate=sr)
        y, loaded_sr = audio_intelligence.librosa.load(str(path), sr=None, mono=True)
        events, raw = audio_intelligence._extract_note_candidates(
            audio_intelligence.np.asarray(y, dtype=audio_intelligence.np.float32),
            int(loaded_sr),
            source_stem="mix_harmonic",
            config=audio_intelligence.AudioAnalysisConfig(pitch_confidence_min=0.01),
        )

        self.assertTrue(raw)
        self.assertTrue(events)
        mapping = audio_intelligence.map_note_event_to_prop(events[0], prop_count=16)
        self.assertIn("prop_index", mapping)
        self.assertGreaterEqual(mapping["brightness"], 0.0)

    def test_analyze_audio_file_builds_sections_hits_and_spatial_frames(self) -> None:
        sr = 22050
        values: list[float] = []
        for idx in range(sr * 2):
            t = idx / sr
            burst = 0.9 if idx % 4000 < 180 else 0.2
            values.append((0.28 * math.sin((2.0 * math.pi * 220.0 * t))) + (burst * math.sin((2.0 * math.pi * 440.0 * t)) * 0.4))
        path = self._write_wave(values, sample_rate=sr)
        result = audio_intelligence.analyze_audio_file(path, enable_lyrics=False)

        self.assertEqual(result.metadata["analysis_schema"], "helix.audio_analysis.v1")
        self.assertTrue(result.onset_events)
        self.assertTrue(result.section_events)
        self.assertTrue(result.part_hits)
        self.assertTrue(result.spatial_audio_frames)
        self.assertTrue(result.feature_state_frames)
        self.assertIn("feature_state_fps", result.metadata)
        self.assertIn("beat_feature_timeline", result.to_dict())
        self.assertIn("audio_reactive_actions", result.to_dict())
        self.assertIn("audio_reactive", result.debug_summaries)
        self.assertIn("pitch_candidates", result.raw_candidates)
        with tempfile.TemporaryDirectory() as output_dir:
            exported = audio_intelligence.export_audio_analysis_result(result, Path(output_dir))
            self.assertTrue(Path(exported["feature_state_csv"]).exists())
            self.assertTrue(Path(exported["audio_reactive_csv"]).exists())

    def test_low_threshold_candidate_retention_keeps_raw_pitch_candidates(self) -> None:
        sr = 22050
        values = [0.12 * math.sin((2.0 * math.pi * 329.63 * idx) / sr) for idx in range(sr)]
        path = self._write_wave(values, sample_rate=sr)
        result = audio_intelligence.analyze_audio_file(
            path,
            config=audio_intelligence.AudioAnalysisConfig(
                onset_sensitivity=0.95,
                pitch_confidence_min=0.6,
                max_candidate_events_per_second=24,
            ),
            enable_lyrics=False,
        )

        self.assertTrue(result.raw_candidates["pitch_candidates"])
        self.assertGreaterEqual(len(result.raw_candidates["pitch_candidates"]), len(result.note_events))


if __name__ == "__main__":
    unittest.main()
