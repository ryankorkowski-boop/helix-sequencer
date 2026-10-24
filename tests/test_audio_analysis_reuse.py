"""Compare to librosa's original waveform path, including exact event timing."""
import librosa
import numpy as np
import pytest
import soundfile as sf
from xlights import xsq_writer as writer


@pytest.mark.parametrize('sr', [22050, 44100, 48000])
def test_reused_spectrum_preserves_onsets_beats_centroid_and_pitch(tmp_path, monkeypatch, sr):
    t = np.arange(sr * 3) / sr
    y = (.3 * np.sin(2 * np.pi * 220 * t) + .15 * np.sin(2 * np.pi * 440 * t))
    for start in (.2, .7, 1.1, 1.7, 2.4):
        y += .5 * np.exp(-np.maximum(0, t-start)*50) * (t >= start) * np.sin(2*np.pi*1700*t)
    path = tmp_path / 'source.wav'
    sf.write(path, y, sr, subtype='FLOAT')
    samples, rate = librosa.load(path, sr=None)
    hop = writer.HOP_MS
    env = librosa.onset.onset_strength(y=samples, sr=rate, hop_length=hop)
    onset = librosa.onset.onset_detect(onset_envelope=env, sr=rate, hop_length=hop,
        backtrack=False, units='frames', pre_max=3, post_max=3, pre_avg=3, post_avg=3, delta=.08, wait=0)
    _, beat = librosa.beat.beat_track(onset_envelope=env, sr=rate, hop_length=hop, units='frames')
    centroid = librosa.feature.spectral_centroid(y=samples, sr=rate, hop_length=hop)[0]
    power = np.abs(librosa.stft(samples, n_fft=2048, hop_length=hop))**2
    pitches, mags = librosa.piptrack(S=np.sqrt(power), sr=rate, hop_length=hop,
        fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'))
    old_pitch = np.array([float(pitches[int(np.argmax(mags[:, i])), i]) or np.nan
                          for i in range(pitches.shape[1])])
    calls = []
    original_stft = librosa.stft
    def counted(*args, **kwargs):
        calls.append(1)
        return original_stft(*args, **kwargs)
    monkeypatch.setattr(librosa, 'stft', counted)
    monkeypatch.setattr(writer, '_aubio_module', lambda: None)
    actual = writer.analyze(path)
    assert len(calls) == 1  # independent of duration and number of pitch frames
    assert actual.onset_ms == [writer.ms(v) for v in librosa.frames_to_time(onset, sr=rate, hop_length=hop)]
    assert actual.beat_ms == [writer.ms(v) for v in librosa.frames_to_time(beat, sr=rate, hop_length=hop)]
    np.testing.assert_allclose(actual.centroid, centroid, rtol=0, atol=0)
    np.testing.assert_array_equal(actual.pitch_hz, old_pitch)
