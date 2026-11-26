"""Production sequencing must refuse a silent full-mix stem fallback."""
from __future__ import annotations

import unittest
import wave
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np

from audio.drum_stem_cohits import detect_stem_cohits
from core import audio_intelligence


def _tone(path: Path) -> None:
    rate = 22050
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(rate)
        frames = bytearray()
        for index in range(rate // 10):
            sample = int(8000 * np.sin(2 * np.pi * 220 * index / rate))
            frames.extend(int(sample).to_bytes(2, "little", signed=True))
        handle.writeframes(bytes(frames))


class NeuralStemRequirementTests(unittest.TestCase):
    def test_missing_demucs_fails_instead_of_using_the_mix(self) -> None:
        with TemporaryDirectory() as directory:
            audio = Path(directory) / "song.wav"
            _tone(audio)
            original = audio_intelligence._demucs_available
            audio_intelligence._demucs_available = lambda: False
            try:
                with self.assertRaises(audio_intelligence.NeuralStemRequired):
                    audio_intelligence._try_demucs_stem_separation(
                        audio, Path(directory) / "cache", None, required=True,
                    )
            finally:
                audio_intelligence._demucs_available = original

    def test_sha256_cache_is_reused_without_running_demucs(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            audio = root / "song.wav"
            _tone(audio)
            digest = audio_intelligence._file_sha256(audio)
            cache = root / "cache" / digest
            stems = {}
            for role in audio_intelligence.STEM_ROLES:
                path = cache / f"{role}.wav"
                path.parent.mkdir(parents=True, exist_ok=True)
                _tone(path)
                stems[role] = path
            audio_intelligence._write_demucs_manifest(cache, digest, stems)
            calls = []
            original = audio_intelligence._demucs_available
            audio_intelligence._demucs_available = lambda: calls.append("ran") or False
            try:
                found = audio_intelligence._try_demucs_stem_separation(
                    audio, root / "cache", None, source_sha256=digest, required=True,
                )
            finally:
                audio_intelligence._demucs_available = original
            self.assertEqual(calls, [])
            self.assertEqual(found["drums"], stems["drums"])
            with stems["vocals"].open("ab") as stream:
                stream.write(b"corrupt")
            self.assertIsNone(audio_intelligence._cached_demucs_stems(cache, digest))

    def test_bounded_app_path_does_not_claim_demucs(self) -> None:
        import os
        with TemporaryDirectory() as directory:
            audio = Path(directory) / "song.wav"
            _tone(audio)
            original = audio_intelligence._demucs_available
            audio_intelligence._demucs_available = lambda: False
            os.environ["HELIX_REQUIRE_NEURAL_STEMS"] = "0"
            try:
                result = audio_intelligence.build_stem_analysis(
                    audio, False, "", Path(directory) / "cache", require_neural_stems=True,
                )
            finally:
                os.environ.pop("HELIX_REQUIRE_NEURAL_STEMS", None)
                audio_intelligence._demucs_available = original
            self.assertNotEqual(result.source, "demucs")
            self.assertIn(result.source, {"local_hpss_diagnostic", "direct"})

    def test_missing_whisper_fails_on_the_required_path(self) -> None:
        real_import = __import__

        def blocked(name, *args, **kwargs):
            if name == "whisper":
                raise ImportError("whisper missing")
            return real_import(name, *args, **kwargs)

        import builtins
        original = builtins.__import__
        builtins.__import__ = blocked
        try:
            with self.assertRaises(audio_intelligence.NeuralStemRequired):
                audio_intelligence._try_whisper_lyrics(Path("vocal.wav"), required=True)
        finally:
            builtins.__import__ = original

    def test_empty_stem_adds_no_cohits(self) -> None:
        added, report = detect_stem_cohits(np.zeros(64, dtype=np.float32), 44100)
        self.assertEqual(added, [])
        self.assertEqual(report["measured"]["kick"], 0)


if __name__ == "__main__":
    unittest.main()
