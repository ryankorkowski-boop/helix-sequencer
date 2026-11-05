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
