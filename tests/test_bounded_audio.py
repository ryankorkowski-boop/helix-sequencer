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


@pytest.mark.parametrize('tail', [1, 61, 509])
def test_bounded_chroma_preserves_reference_across_long_partial_blocks(tail, monkeypatch):
    sr = 22050
    # More than two complete chroma blocks, including narrow/unaligned tails.
    frames = 4096 + tail
    harmonic = source(sr, seconds=((frames-1)*512+137)/sr)
    expected_pitch, expected_entropy = unbounded_background_features(harmonic, sr, 512)
    original = librosa.feature.chroma_stft
    widths = []

    def measured(*args, **kwargs):
        widths.append(kwargs['S'].shape[1])
        return original(*args, **kwargs)

    monkeypatch.setattr(librosa.feature, 'chroma_stft', measured)
    actual_pitch, actual_entropy = ai._bounded_background_features(harmonic, sr)
    assert len(widths) >= 3
    assert max(widths)*1025*4 < 16*1024**2
    np.testing.assert_array_equal(actual_pitch, expected_pitch)
    np.testing.assert_allclose(actual_entropy, expected_entropy, atol=1e-7, rtol=0)


def test_frame_reductions_preserve_pitch_descriptors_and_flux_at_block_boundaries():
    # Include zeros/rests and a final partial block in the actual frequency grid.
    power = np.asfortranarray(np.abs(np.random.default_rng(153).normal(size=(1025, 1301))).astype('float32'))
    power[:, 508:517] = 0
    magnitude = np.sqrt(np.maximum(0, np.asarray(power, dtype=float)))
    expected = (librosa.feature.spectral_centroid(S=magnitude, sr=48000)[0],
                librosa.feature.spectral_bandwidth(S=magnitude, sr=48000)[0],
                librosa.feature.spectral_contrast(S=magnitude, sr=48000),
                librosa.feature.spectral_flatness(S=magnitude)[0])
    for actual, reference in zip(bounded.spectral_descriptors(power, sr=48000, power=True), expected):
        np.testing.assert_array_equal(actual, reference)
    difference = np.diff(np.asarray(power, dtype=float), axis=1)
    flux = np.pad(np.sum(np.clip(difference, 0, None), axis=0), (1, 0))
    np.testing.assert_array_equal(bounded.positive_flux(power), flux)
    pitches, weights = librosa.piptrack(S=np.sqrt(power), sr=48000, hop_length=512, fmin=65, fmax=2200)
    selected = pitches[np.argmax(weights, axis=0), np.arange(power.shape[1])]
    selected = np.where(selected > 0, selected, np.nan)
    np.testing.assert_array_equal(bounded.dominant_pitch(power, sr=48000, hop=512, fmin=65, fmax=2200), selected)
    for actual, expected in zip(bounded.pitch_matrices(np.sqrt(power), sr=48000,
                               hop_length=512, fmin=65, fmax=2200), (pitches, weights)):
        np.testing.assert_array_equal(actual, expected)


def test_drum_descriptors_do_not_require_the_unused_chroma_contrast_bands():
    magnitude = np.ones((1025, 17), dtype='float32')
    actual = bounded.spectral_descriptors(magnitude, sr=8000, include_contrast=False)
    np.testing.assert_array_equal(actual[0], librosa.feature.spectral_centroid(S=magnitude, sr=8000)[0])
    assert actual[2].shape == (0, 17)


def test_float64_mel_workspace_preserves_original_global_grid_and_tail():
    y = np.asarray(source(48000, seconds=3.137), dtype=float)
    settings = dict(sr=48000, n_fft=4096, hop_length=512, n_mels=32, fmin=20, fmax=12000)
    expected = librosa.feature.melspectrogram(y=y, power=2., **settings)
    np.testing.assert_array_equal(bounded.mel_spectrogram(y, **settings), expected)


@pytest.mark.parametrize('dtype', ['float32', 'float64'])
def test_long_chroma_uses_original_whole_song_tuning_and_bins(dtype):
    y = np.asarray(source(22050), dtype=dtype)
    expected_tuning = librosa.estimate_tuning(y=y, sr=22050, bins_per_octave=36)
    tuning = bounded.estimate_tuning(y, sr=22050, bins_per_octave=36)
    assert tuning == expected_tuning
    expected = librosa.feature.chroma_cqt(y=y, sr=22050, hop_length=512)
    actual = librosa.feature.chroma_cqt(y=y, sr=22050, hop_length=512, tuning=tuning)
    np.testing.assert_array_equal(actual, expected)
