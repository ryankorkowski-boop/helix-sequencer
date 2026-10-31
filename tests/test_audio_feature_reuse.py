from dataclasses import fields

import numpy as np
import pytest

from core import audio_features as features
from xlights import xsq_writer as writer


@pytest.fixture
def source(tmp_path, monkeypatch):
    path = tmp_path / "source.wav"
    path.write_bytes(b"source identity; computation is supplied by this cache contract")
    monkeypatch.setenv("HELIX_AUDIO_CACHE_DIR", str(tmp_path / "cache"))
    return path


def audio_fixture():
    return writer.Audio(sr=22050, y=np.arange(8, dtype=np.float32), dur_s=8/22050,
                        onset_ms=[1, 2], beat_ms=[1], times_s=np.array([0., 1.]),
                        centroid=np.array([300., 5000.]), rms01=np.array([.1, .7]),
                        bass01=np.array([.2, .3]), vocal01=np.array([.4, .5]),
                        pitch_hz=np.array([np.nan, 440.]))


def assert_exact_audio(actual, expected):
    for field in fields(expected):
        a, b = getattr(actual, field.name), getattr(expected, field.name)
        if isinstance(b, np.ndarray):
            np.testing.assert_array_equal(a, b)
            assert a.dtype == b.dtype and a.shape == b.shape
        else:
            assert a == b


def test_audio_cache_preserves_nan_pitch_sentinels_and_skips_recomputation(source, monkeypatch):
    expected = audio_fixture()
    calls = []
    def compute(path):
        calls.append(path)
        return expected
    monkeypatch.setattr(features, "_compute_audio", compute)
    assert_exact_audio(features.analyze_audio(source), expected)
    assert_exact_audio(features.analyze_audio(source), expected)
    assert calls == [source]


def test_content_and_public_writer_settings_invalidate_cache(source, monkeypatch):
    calls = []
    def compute(path):
        calls.append(True)
        return audio_fixture()
    monkeypatch.setattr(features, "_compute_audio", compute)
    features.analyze_audio(source)
    source.write_bytes(b"changed recording")
    features.analyze_audio(source)
    monkeypatch.setattr(writer, "HOP_MS", 256)
    features.analyze_audio(source)
    monkeypatch.setattr(writer, "USE_FAST_PITCH", False)
    features.analyze_audio(source)
    assert len(calls) == 4


def test_incomplete_but_readable_npz_is_recomputed(source, monkeypatch):
    calls = []
    def compute(path):
        calls.append(True)
        return audio_fixture()
    monkeypatch.setattr(features, "_compute_audio", compute)
    features.analyze_audio(source)
    target = next((source.parent / "cache").glob("*.npz"))
    np.savez(target, sr=np.array(22050))
    assert_exact_audio(features.analyze_audio(source), audio_fixture())
    assert_exact_audio(features.analyze_audio(source), audio_fixture())
    assert len(calls) == 2


def test_harmonic_cache_binds_actual_in_memory_samples(source, monkeypatch):
    audio = audio_fixture()
    expected = features.HarmonicData(
        times_s=np.array([0., 1.]), cqt_mag=np.ones((60, 2), dtype=np.float32),
        base_midi=36, pitch_hz=np.zeros((1025, 2)), pitch_mag=np.ones((1025, 2)))
    calls = []
    def compute(value):
        calls.append(True)
        return expected
    monkeypatch.setattr(features, "_compute_harmonic", compute)
    first = features.analyze_harmonic(audio, audio_path=source)
    second = features.analyze_harmonic(audio, audio_path=source)
    np.testing.assert_array_equal(first.cqt_mag, second.cqt_mag)
    assert second.cqt_mag.dtype == np.float32 and len(calls) == 1
    audio.y[0] = 900
    features.analyze_harmonic(audio, audio_path=source)
    assert len(calls) == 2


def test_real_dsp_cache_roundtrip_matches_uncached_writer_entry(source, monkeypatch):
    import soundfile as sf
    wave = np.sin(2*np.pi*440*np.arange(44100)/22050).astype(np.float32) * .1
    sf.write(source, wave, 22050, subtype="FLOAT")
    monkeypatch.delenv("HELIX_AUDIO_CACHE_DIR")
    expected = writer.analyze(source)
    monkeypatch.setenv("HELIX_AUDIO_CACHE_DIR", str(source.parent / "cache"))
    assert_exact_audio(writer.analyze(source), expected)
    assert_exact_audio(writer.analyze(source), expected)
