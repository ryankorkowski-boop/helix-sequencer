from __future__ import annotations

import math
import tempfile
import unittest
import wave
from pathlib import Path

import numpy as np

from core import birdsong_mode


class BirdsongModeTests(unittest.TestCase):
    def _write_wave(self, root: Path) -> Path:
        sample_rate = 22050
        duration_s = 1.2
        samples = int(sample_rate * duration_s)
        t = np.linspace(0.0, duration_s, samples, endpoint=False)
        signal = (
            0.38 * np.sin(2.0 * math.pi * 220.0 * t)
            + 0.22 * np.sin(2.0 * math.pi * 1760.0 * t)
            + 0.15 * np.sin(2.0 * math.pi * 3200.0 * t)
        )
        pcm = np.clip(signal * 32767.0, -32768, 32767).astype(np.int16)
        path = root / "bird.wav"
        with wave.open(str(path), "wb") as writer:
            writer.setnchannels(1)
            writer.setsampwidth(2)
            writer.setframerate(sample_rate)
            writer.writeframes(pcm.tobytes())
        return path

    def test_analyze_audio_returns_band_and_flux_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            audio = self._write_wave(Path(temp_dir))
            metrics = birdsong_mode.analyze_audio(audio)
            self.assertGreater(metrics.duration_s, 1.0)
            self.assertGreaterEqual(metrics.low_ratio, 0.0)
            self.assertGreaterEqual(metrics.mid_ratio, 0.0)
            self.assertGreaterEqual(metrics.high_ratio, 0.0)
            self.assertLessEqual(metrics.high_ratio, 1.0)
            self.assertGreaterEqual(metrics.flux_density, 0.0)

    def test_default_task_presets_include_requested_named_runs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            audio = self._write_wave(Path(temp_dir))
            presets = birdsong_mode.default_task_presets(audio)
            names = {item.name for item in presets}
            targets = {item.target_xsq_name for item in presets}
            self.assertIn("birdmap", names)
            self.assertIn("legacyplusbirdinputlegacyoutput", names)
            self.assertIn("heavylogicwhatever", names)
            self.assertIn("birdmap.xsq", targets)
            self.assertIn("legacyplusbirdinputlegacyoutput.xsq", targets)


if __name__ == "__main__":
    unittest.main()
