import librosa
import numpy as np
import pytest

from core.audio_intelligence import _shared_spectral_features


@pytest.mark.parametrize("sr", [22050, 44100])
def test_shared_spectral_features_match_independent_calls(sr, monkeypatch):
    hop = 512
    t = np.arange(sr * 2, dtype=np.float32) / sr
    y = (0.35 * np.sin(2 * np.pi * 220 * t)
         + 0.12 * np.sin(2 * np.pi * 1700 * t)).astype(np.float32)
    y[:sr // 4] = 0
    y[sr:sr + 24] += 0.5
    expected = (
        librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=hop)[0],
        librosa.feature.spectral_bandwidth(y=y, sr=sr, hop_length=hop)[0],
        librosa.feature.spectral_contrast(y=y, sr=sr, hop_length=hop),
        librosa.feature.spectral_rolloff(y=y, sr=sr, hop_length=hop)[0],
    )
    original = librosa.stft
    calls = []

    def counted(*args, **kwargs):
        calls.append(1)
        return original(*args, **kwargs)

    monkeypatch.setattr(librosa, "stft", counted)
    actual = _shared_spectral_features(y, sr, hop)
    assert len(calls) == 1
    for observed, reference in zip(actual, expected):
        np.testing.assert_allclose(observed, reference, rtol=1e-6, atol=1e-7)
