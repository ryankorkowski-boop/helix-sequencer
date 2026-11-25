import librosa
import numpy as np
import pytest

from core.effect_engine import _mfcc_from_power_spectrum


@pytest.mark.parametrize("sr", [22050, 44100])
def test_mfcc_reuse_matches_waveform_analysis(sr, monkeypatch):
    hop = 512
    t = np.arange(sr * 2, dtype=np.float32) / sr
    y = (0.3 * np.sin(2 * np.pi * 220 * t)
         + 0.1 * np.sin(2 * np.pi * 1600 * t)).astype(np.float32)
    y[:sr // 4] = 0
    expected = librosa.feature.mfcc(y=y, sr=sr, hop_length=hop, n_mfcc=20)
    power = np.abs(librosa.stft(y, n_fft=2048, hop_length=hop)) ** 2

    def unexpected_stft(*args, **kwargs):
        pytest.fail("MFCC must reuse the supplied power spectrum")

    monkeypatch.setattr(librosa, "stft", unexpected_stft)
    actual = _mfcc_from_power_spectrum(power, sr=sr, hop=hop)
    np.testing.assert_allclose(actual, expected, rtol=1e-6, atol=1e-6)
