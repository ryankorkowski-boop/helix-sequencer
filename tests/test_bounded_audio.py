"""Long-song memory boundaries retain original HPSS, frames and vocal events."""
from dataclasses import asdict

import librosa
import numpy as np
import pytest
import soundfile as sf

from core import bounded_audio as bounded
from core import audio_intelligence as ai


def source(sr, seconds=31.137):
    t = np.arange(round(sr * seconds)) / sr
    y = (.15*np.sin(2*np.pi*220*t) + .11*np.sin(2*np.pi*330*t)
         + .07*np.sin(2*np.pi*554.37*t)).astype('float32')
    rng = np.random.default_rng(20261029)
    for second in (0, 7.98, 8.04, 15.99, 16.04, 23.99, 24.03, seconds-.03):
        start = round(second*sr)
        count = min(round(.1*sr), len(y)-start)
        if count <= 0:
            continue
        y[start:start+count] += (.2*rng.normal(size=count)*np.exp(-np.arange(count)/(sr*.02))).astype('float32')
    y[(t > 10) & (t < 13)] = 0
    return y


@pytest.mark.parametrize('sr', [22050, 48000])
def test_long_hpss_preserves_samples_stems_rests_and_tail(sr, monkeypatch):
    y = source(sr)
    expected = librosa.effects.hpss(y)
    original = librosa.effects.hpss
    lengths = []
    def measured(values):
        lengths.append(len(values))
        return original(values)
    monkeypatch.setattr(librosa.effects, 'hpss', measured)
    actual = bounded.hpss(y, sr)
    assert len(lengths) > 1
    assert max(lengths) <= sr*8 + 128*512
    for after, before in zip(actual, expected):
        assert after.shape == y.shape and after.dtype == y.dtype
        np.testing.assert_allclose(after, before, atol=3e-7, rtol=0)
        assert not np.any(after[sr*11:sr*12])
        assert np.any(after[-round(sr*.02):])


def test_block_stft_retains_exact_centered_frame_grid_and_non_aligned_tail():
    y = source(22050, seconds=3.137)
    expected = np.abs(librosa.stft(y, n_fft=2048, hop_length=512))
    chunks = list(bounded.magnitude_blocks(y, block_frames=17))
    assert [start for start, _ in chunks] == list(range(0, expected.shape[1], 17))
    assert all(values.shape[1] <= 17 for _, values in chunks)
    np.testing.assert_array_equal(np.concatenate([v for _, v in chunks], axis=1), expected)


def unbounded_background_features(harm, sr, hop):
    # Retained full-file librosa reference, including global automatic tuning.
    magnitude = np.abs(librosa.stft(harm, n_fft=2048, hop_length=hop))
    _, pitch_mag = librosa.piptrack(S=magnitude, sr=sr, hop_length=hop, fmin=110, fmax=2200)
    thresholds = np.quantile(pitch_mag, .92, axis=0)
    counts = np.sum(pitch_mag > np.maximum(thresholds, 1e-8), axis=0)
    chroma = librosa.feature.chroma_stft(S=magnitude, sr=sr, hop_length=hop)
    probability = chroma / (np.sum(chroma, axis=0) + 1e-9)
    entropy = -np.sum(probability*np.log2(probability+1e-9), axis=0)/np.log2(12)
    return np.clip((counts-1.)/3., 0, 1), entropy


def test_bounded_classifier_preserves_global_tuning_confidences_and_event_clocks(tmp_path, monkeypatch):
    sr = 22050
    y = source(sr)
    path = tmp_path/'vocal.wav'
    sf.write(path, y, sr, subtype='FLOAT')
    harmonic, _ = librosa.effects.hpss(y)
    expected_pitch, expected_entropy = unbounded_background_features(harmonic, sr, 512)
    actual_pitch, actual_entropy = ai._bounded_background_features(harmonic, sr)
    np.testing.assert_array_equal(actual_pitch, expected_pitch)
    np.testing.assert_allclose(actual_entropy, expected_entropy, atol=1e-7, rtol=0)
    actual = [asdict(e) for e in ai._classify_background_vocals(path)]
    monkeypatch.setattr(bounded, 'hpss', lambda samples, rate: librosa.effects.hpss(samples))
    monkeypatch.setattr(ai, '_bounded_background_features', unbounded_background_features)
    expected = [asdict(e) for e in ai._classify_background_vocals(path)]
    assert actual == expected
    assert actual
