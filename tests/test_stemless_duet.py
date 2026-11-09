"""Guard the optional stemless mouth estimator without pretending it proves voices."""
import numpy as np
import pytest
from tools import stemless_duet


def test_silent_original_vocals_never_create_a_singer(monkeypatch):
    monkeypatch.setattr(stemless_duet.librosa, "load", lambda *a, **k: (np.zeros(11025), 11025))
    energy = np.zeros((20, 2), dtype=np.float32)
    shapes = np.zeros((20, 2), dtype=np.int16)
    result, mouth, proof = stemless_duet.estimate_duet("unused.wav", energy, shapes, frames=20)
    assert not np.any(result)
    assert not np.any(mouth)
    assert proof["independent_voice_identity_proven"] is False


def test_reject_malformed_source_lanes():
    with pytest.raises(ValueError):
        stemless_duet.estimate_duet("unused.wav", np.ones((20, 1)), np.ones((20, 1)), frames=20)


def test_mixed_source_is_never_accepted_as_independent_stems(monkeypatch):
    monkeypatch.setattr(stemless_duet.librosa, "load", lambda *a, **k: (np.zeros(11025), 11025))
    energy = np.zeros((20, 2), dtype=np.float32)
    energy[5:10, 0] = .8
    shapes = np.zeros((20, 2), dtype=np.int16)
    shapes[5:10, 0] = 2
    result, mouth, proof = stemless_duet.estimate_duet("unused.wav", energy, shapes, frames=20)
    assert not np.any(result[:, 1])
    assert not np.any(mouth[:, 1])
    assert proof["independent_vocal_stems"] is False


@pytest.mark.parametrize('frame_ms', [10, 25, 50])
def test_dual_pitch_requires_persistence_and_never_crosses_source_rests(monkeypatch, frame_ms):
    frames = 1000 // frame_ms
    monkeypatch.setattr(stemless_duet.librosa, 'load', lambda *a, **k: (np.zeros(12000), 12000))
    monkeypatch.setattr(stemless_duet.librosa, 'stft', lambda *a, **k: np.zeros((3, frames)))
    pitches = np.tile([[220.], [277.18], [0.]], (1, frames))
    magnitudes = np.tile([[1.], [.6], [0.]], (1, frames))
    # A single isolated pitch spike must not open a mouth.
    magnitudes[1, :max(1, 200 // frame_ms)] = 0
    magnitudes[1, 0] = .6
    monkeypatch.setattr(stemless_duet.librosa, 'piptrack', lambda **k: (pitches, magnitudes))
    energy = np.full((frames, 2), .8, dtype='f4')
    shapes = np.full((frames, 2), 2, dtype='i2')
    shapes[frames//2:frames//2+2, 0] = 0
    result, mouth, proof = stemless_duet.estimate_duet('unused', energy, shapes,
        frames=frames, frame_ms=frame_ms)
    assert result.shape == mouth.shape == (frames, 2)
    assert not mouth[0, 1]
    assert np.any(mouth[:, 1])
    assert not np.any(mouth[shapes[:, 0] == 0])
    assert not np.any(result[shapes[:, 0] == 0])
    assert proof['persistence_ms'] == 150


def test_one_frame_input_and_audio_tail_stay_closed(monkeypatch):
    monkeypatch.setattr(stemless_duet.librosa, 'load', lambda *a, **k: (np.zeros(12), 12000))
    energy = np.ones((1, 2), dtype='f4')
    shapes = np.full((1, 2), 2, dtype='i2')
    result, mouth, _ = stemless_duet.estimate_duet('unused', energy, shapes, frames=1)
    assert result.shape == mouth.shape == (1, 2)
    assert mouth[0, 1] == 0


def test_fractional_hop_is_mapped_back_to_original_clock(monkeypatch):
    rate, frames = 11025, 8000
    monkeypatch.setattr(stemless_duet.librosa, 'load', lambda *a, **k: (np.zeros(rate*400), rate))
    hop = round(rate / 20)
    columns = np.rint(np.arange(frames)*.05*rate/hop).astype(int)
    pitch = np.tile([[220.], [277.18], [0.]], (1, columns[-1]+1))
    mag = np.zeros_like(pitch); mag[0] = 1
    mag[1, columns[6000]:columns[6005]+1] = .6
    monkeypatch.setattr(stemless_duet.librosa, 'stft', lambda *a, **k: np.zeros_like(pitch))
    monkeypatch.setattr(stemless_duet.librosa, 'piptrack', lambda **k: (pitch, mag))
    _, mouth, _ = stemless_duet.estimate_duet('unused', np.ones((frames, 2)),
        np.full((frames, 2), 2), frames=frames)
    assert np.flatnonzero(mouth[:, 1]).tolist() == [6001, 6002, 6003, 6004]


@pytest.mark.parametrize('value', [np.nan, -1, 1.5, 100])
def test_invalid_shapes_fail_before_audio_decode(value):
    shapes = np.ones((20, 2)); shapes[0, 0] = value
    with pytest.raises(ValueError, match='mouth shapes'):
        stemless_duet.estimate_duet('does-not-exist', np.ones((20, 2)), shapes, frames=20)


def test_stemless_second_pitch_never_borrows_lead_phonemes(monkeypatch):
    """A pitch candidate cannot manufacture harmony syllables without a backing clock."""
    frames = 20
    monkeypatch.setattr(stemless_duet.librosa, 'load',
                        lambda *a, **k: (np.zeros(12000), 12000))
    monkeypatch.setattr(stemless_duet.librosa, 'stft',
                        lambda *a, **k: np.zeros((3, frames)))
    pitch = np.tile([[220.], [277.18], [0.]], (1, frames))
    mag = np.tile([[1.], [.8], [0.]], (1, frames))
    monkeypatch.setattr(stemless_duet.librosa, 'piptrack',
                        lambda **k: (pitch, mag))
    energy = np.zeros((frames, 2), dtype='f4')
    energy[:, 0] = .9
    shapes = np.zeros((frames, 2), dtype='i2')
    shapes[:, 0] = 2
    result, mouth, proof = stemless_duet.estimate_duet(
        'unused', energy, shapes, frames=frames)
    assert np.any(result[:, 0])
    assert not np.any(result[:, 1])
    assert not np.any(mouth[:, 1])
    assert proof['independent_voice_identity_proven'] is False
