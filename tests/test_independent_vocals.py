import math
import struct
import tempfile
import unittest
import wave
from pathlib import Path
from core.independent_vocals import analyze_independent_vocals, _read_mono_pcm, _stream_vocal_features


def make_wav(path, hz, duration=0.6, amplitude=0.4):
    rate = 16000
    with wave.open(str(path), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(rate)
        f.writeframes(b"".join(struct.pack("<h", int(amplitude * 32767 * math.sin(
            2 * math.pi * hz * i / rate))) for i in range(int(rate * duration))))


class IndependentVocalTests(unittest.TestCase):
    def test_distinct_stems_route_separately(self):
        with tempfile.TemporaryDirectory() as d:
            a, b, output = Path(d) / "lead.wav", Path(d) / "harmony.wav", Path(d) / "events.json"
            make_wav(a, 220)
            make_wav(b, 330)
            result = analyze_independent_vocals(a, b, output_json=output)
            self.assertEqual([t["performer"] for t in result["tracks"]],
                             ["lead_singer", "harmony_singer"])
            self.assertTrue(all(t["windows"] for t in result["tracks"]))
            self.assertTrue(output.exists())

    def test_duplicate_stem_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            a = Path(d) / "lead.wav"
            make_wav(a, 220)
            with self.assertRaisesRegex(ValueError, "Duplicate"):
                analyze_independent_vocals(a, a)

    def test_gain_scaled_copy_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            a, b = Path(d) / "lead.wav", Path(d) / "scaled.wav"
            make_wav(a, 220, amplitude=0.4)
            make_wav(b, 220, amplitude=0.2)
            with self.assertRaisesRegex(ValueError, "near-identical"):
                analyze_independent_vocals(a, b)

    def test_mismatched_duration_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            a, b = Path(d) / "lead.wav", Path(d) / "harmony.wav"
            make_wav(a, 220, duration=0.6)
            make_wav(b, 330, duration=0.3)
            with self.assertRaisesRegex(ValueError, "duration"):
                analyze_independent_vocals(a, b)

    def test_silent_lead_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            a, b = Path(d) / "silent.wav", Path(d) / "harmony.wav"
            make_wav(a, 220, amplitude=0.0)
            make_wav(b, 330)
            with self.assertRaisesRegex(ValueError, "Lead stem is silent"):
                analyze_independent_vocals(a, b)

    def test_silent_harmony_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            a, b = Path(d) / "lead.wav", Path(d) / "silent.wav"
            make_wav(a, 220)
            make_wav(b, 330, amplitude=0.0)
            with self.assertRaisesRegex(ValueError, "silent"):
                analyze_independent_vocals(a, b)


if __name__ == "__main__":
    unittest.main()


def test_compact_pcm_buffer_preserves_activity_and_sample_values():
    import array
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "lead.wav"
        make_wav(path, 220, duration=0.5)
        rate, samples = _read_mono_pcm(path)
        assert rate == 16000
        assert isinstance(samples, array.array)
        assert samples.typecode == "h"
        assert len(samples) == 8000
        assert max(samples) > 10000


def test_streaming_vocal_features_use_bounded_fingerprint():
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "long.wav"
        make_wav(path, 220, duration=4.0)
        rate, frames, energies, fingerprint = _stream_vocal_features(path, fingerprint_budget=1000)
        assert rate == 16000
        assert frames == 64000
        assert 190 <= len(energies) <= 210
        assert len(fingerprint) <= 1000
        assert max(energies) > 0.1


def test_streamed_activity_preserves_separate_singer_windows():
    with tempfile.TemporaryDirectory() as d:
        lead, backing = Path(d) / "lead.wav", Path(d) / "backing.wav"
        make_wav(lead, 220, duration=4.0)
        make_wav(backing, 330, duration=4.0)
        result = analyze_independent_vocals(lead, backing)
        assert all(track["windows"] for track in result["tracks"])
        assert result["independence"] == "duplicate_rejection_only_not_voice_identity_proof"
