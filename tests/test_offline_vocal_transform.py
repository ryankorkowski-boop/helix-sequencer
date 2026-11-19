import numpy as np
import pytest

from tools.offline_vocal_candidates import stft, istft


@pytest.mark.parametrize('n_fft', [5120, 6144])
def test_candidate_transform_preserves_stereo_sample_clock(n_fft):
    rng = np.random.default_rng(188)
    wave = rng.normal(0, .03, (2, 1024 * 255)).astype('f4')
    restored = istft(stft(wave, n_fft), n_fft)
    assert restored.shape == wave.shape
    assert np.max(np.abs(restored - wave)) < 1e-6
