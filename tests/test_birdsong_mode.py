from __future__ import annotations

import math
import tempfile
import unittest
import wave
from pathlib import Path
from unittest.mock import patch

import numpy as np

from core import birdsong_mode


def _write_wav(path: Path, samples: np.ndarray, sample_rate: int) -> None:
    clipped = np.clip(samples, -1.0, 1.0)
    pcm = (clipped * 32767.0).astype(np.int16)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(int(sample_rate))
        handle.writeframes(pcm.tobytes())


class BirdsongModeTests(unittest.TestCase):
    def _build_audio_file(self, folder: Path) -> Path:
        sr = 22050
        dur_s = 2.4
        t = np.linspace(0.0, dur_s, int(sr * dur_s), endpoint=False, dtype=float)
        sig = (
            0.36 * np.sin(2.0 * math.pi * 110.0 * t)
            + 0.24 * np.sin(2.0 * math.pi * 220.0 * t)
            + 0.15 * np.sin(2.0 * math.pi * 440.0 * t)
        )
        pulse = (np.sin(2.0 * math.pi * 2.0 * t) > 0.72).astype(float) * 0.25
        y = (sig + pulse).astype(float)
        audio_path = folder / "synthetic.wav"
        _write_wav(audio_path, y, sr)
        return audio_path

    def test_extract_features_includes_required_bands(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            audio_path = self._build_audio_file(Path(tmpdir))
            payload = birdsong_mode.extract_frame_features(audio_path)
            names = set(payload["feature_names"])
            self.assertIn("spectral_centroid", names)
            self.assertIn("spectral_bandwidth", names)
            self.assertIn("spectral_contrast", names)
            self.assertIn("onset_strength", names)
            self.assertIn("pitch_midi", names)
            self.assertGreater(payload["frame_count"], 0)
            self.assertTrue(payload["onset_ms"])

    def test_reduction_falls_back_without_sklearn(self) -> None:
        matrix = np.random.rand(64, 12)

        def _fake_optional(name: str):
            if name.startswith("sklearn"):
                return None
            return birdsong_mode.optional_import(name)

        with patch("core.birdsong_mode.optional_import", side_effect=_fake_optional):
            reduced = birdsong_mode.reduce_dimensions(matrix)
        self.assertEqual(reduced["method"], "svd_pca")
        self.assertEqual(np.asarray(reduced["coords_2d"]).shape[1], 2)
        self.assertEqual(np.asarray(reduced["coords_3d"]).shape[1], 3)

    def test_run_birdsong_mode_exports_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            audio_path = self._build_audio_file(root)
            out_dir = root / "out"
            result = birdsong_mode.run_birdsong_mode(
                audio_path=audio_path,
                output_dir=out_dir,
                preview=False,
                export_ply=False,
                use_umap=False,
                use_basic_pitch=False,
            )
            self.assertTrue(result.json_path.exists())
            self.assertTrue(result.csv_path.exists())
            self.assertTrue(result.mapping_json_path.exists())
            self.assertGreater(result.frame_count, 0)

            mapping_payload = result.mapping_json_path.read_text(encoding="utf-8")
            self.assertIn("megatree", mapping_payload)
            self.assertIn("matrix", mapping_payload)


if __name__ == "__main__":
    unittest.main()
