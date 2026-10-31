from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import numpy as np

from core.audio_analysis_cache import audio_cache_key, cached_arrays


class AudioAnalysisCacheTests(unittest.TestCase):
    def test_content_and_parameters_change_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "audio.wav"
            path.write_bytes(b"first")
            first = audio_cache_key(path, {"sr": 22050, "hpss": True})
            self.assertEqual(first, audio_cache_key(path, {"hpss": True, "sr": 22050}))
            self.assertNotEqual(first, audio_cache_key(path, {"sr": 44100, "hpss": True}))
            path.write_bytes(b"second")
            self.assertNotEqual(first, audio_cache_key(path, {"sr": 22050, "hpss": True}))

    def test_cache_hit_skips_compute(self):
        with tempfile.TemporaryDirectory() as tmp:
            calls = []
            def compute():
                calls.append(True)
                return {"rms": np.array([0.1, 0.2], dtype=np.float32)}
            key = "a" * 64
            self.assertEqual(cached_arrays(tmp, key, compute)["rms"].tolist(),
                             cached_arrays(tmp, key, compute)["rms"].tolist())
            self.assertEqual(len(calls), 1)

    def test_corrupt_entry_recomputed(self):
        with tempfile.TemporaryDirectory() as tmp:
            key = "b" * 64
            Path(tmp, key + ".npz").write_bytes(b"invalid")
            result = cached_arrays(tmp, key, lambda: {"onsets": np.array([1, 2])})
            self.assertEqual(result["onsets"].tolist(), [1, 2])

    def test_truncated_zip_entry_recomputed(self):
        with tempfile.TemporaryDirectory() as tmp:
            key = "e" * 64
            cached_arrays(tmp, key, lambda: {"a": np.ones(8)})
            path = Path(tmp, key + ".npz")
            path.write_bytes(path.read_bytes()[:-20])
            result = cached_arrays(tmp, key, lambda: {"a": np.zeros(8)})
            np.testing.assert_array_equal(result["a"], np.zeros(8))

    def test_cache_persists_exact_array_dtype_and_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            key = "d" * 64
            expected = np.arange(12, dtype=np.float32).reshape(3, 4)
            cached_arrays(tmp, key, lambda: {"chroma": expected})
            actual = cached_arrays(tmp, key, lambda: self.fail("cache miss"))
            np.testing.assert_array_equal(actual["chroma"], expected)
            self.assertEqual(actual["chroma"].dtype, expected.dtype)
            self.assertEqual(actual["chroma"].shape, expected.shape)

    def test_rejects_unsafe_key_and_object_array(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                cached_arrays(tmp, "../escape", lambda: {})
            with self.assertRaises(TypeError):
                cached_arrays(tmp, "c" * 64, lambda: {"bad": np.array([object()])})


if __name__ == "__main__":
    unittest.main()
