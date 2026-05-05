from __future__ import annotations

import math
from pathlib import Path
import tempfile
import unittest
import wave

from helix_sequencer import AudioPipeline


class HelixSequencerAudioPipelineTests(unittest.TestCase):
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

    def test_pipeline_imports_and_uses_available_audio_backend(self) -> None:
        sr = 22050
        values = []
        for idx in range(sr * 2):
            t = idx / sr
            pulse = 0.8 if idx % 4096 < 180 else 0.2
            values.append(pulse * math.sin((2.0 * math.pi * 330.0 * t)))
        path = self._write_wave(values, sample_rate=sr)

        result = AudioPipeline().process(path)

        self.assertIn(result["timing"]["backend"], {"madmom", "librosa"})
        self.assertIn(result["features"]["backend"], {"essentia", "librosa"})
        self.assertTrue(result["features"]["energy"])
        self.assertTrue(result["feature_state"])
        self.assertIn("timeline", result)


if __name__ == "__main__":
    unittest.main()
