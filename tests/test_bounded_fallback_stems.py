"""Full-song memory repair must preserve the previous HPSS samples and clocks."""
from pathlib import Path

import librosa
import numpy as np
import pytest
import soundfile as sf

from core.audio_intelligence import _local_stem_separation


@pytest.mark.parametrize('sr,channels', [(22050, 1), (48000, 2)])
def test_full_song_windows_match_original_with_silence_and_boundary_strikes(tmp_path, sr, channels):
    t = np.arange(int(sr * 31.137)) / sr
    y = (.17 * np.sin(2 * np.pi * 110 * t) + .11 * np.sin(2 * np.pi * 660 * t)).astype('float32')
    rng = np.random.default_rng(199)
    for event in (0, 7.98, 8.00, 8.06, 15.99, 16.04, 24.01, 31.10):
        start = round(event * sr)
        length = min(round(.12 * sr), len(y) - start)
        y[start:start+length] += (.28 * rng.normal(size=length) * np.exp(-np.arange(length)/(sr*.02))).astype('float32')
    y[(t > 10) & (t < 13)] = 0
    source = tmp_path/'music.wav'
    sf.write(source, y if channels == 1 else np.stack((y, .7*y), axis=1), sr, subtype='FLOAT')
    original, rate = librosa.load(source, sr=None, mono=True)
    # Original production algorithm before the bounded-memory change.
    harmonic, drums = librosa.effects.hpss(original)
    spectrum = librosa.stft(harmonic, n_fft=2048, hop_length=512)
    frequencies = librosa.fft_frequencies(sr=rate, n_fft=2048)[:, None]
    bass = librosa.istft(spectrum*(frequencies <= 220), hop_length=512, length=len(original))
    vocals = librosa.istft(spectrum*((frequencies > 220) & (frequencies <= 4200)), hop_length=512, length=len(original))
    expected = dict(vocals=vocals, bass=bass, drums=drums,
                    other=original-(.62*vocals+.68*drums+.70*bass))
    actual = _local_stem_separation(source, tmp_path/'stems', None)
    for role, values in expected.items():
        baseline = tmp_path/(role+'-original.wav')
        sf.write(baseline, np.clip(values, -1, 1), sr, subtype='PCM_16')
        before, before_sr = sf.read(baseline)
        after, after_sr = sf.read(actual[role])
        assert after_sr == before_sr == sr
        assert after.shape == before.shape == original.shape
        np.testing.assert_allclose(after, before, rtol=0, atol=2/32768)
        assert np.sqrt(np.mean((after-before)**2)) < 1/32768
        assert not np.any(after[int(sr*11):int(sr*12)])
        assert np.any(after[-int(sr*.03):])  # Preserve the real, non-hop-aligned tail.


def test_short_recordings_keep_original_single_window_and_full_tail(tmp_path, monkeypatch):
    from core import audio_intelligence as ai
    sr = 22050
    y = np.sin(np.arange(sr*2+17)*.1).astype('float32')*.15
    source = tmp_path/'short.wav'
    sf.write(source, y, sr, subtype='FLOAT')
    original = ai._fallback_stem_samples
    lengths = []
    def record(values, rate):
        lengths.append(len(values))
        return original(values, rate)
    monkeypatch.setattr(ai, '_fallback_stem_samples', record)
    for p in ai._local_stem_separation(source, tmp_path/'short-stems', None).values():
        assert sf.info(p).frames == len(y)
    assert lengths == [len(y)]
