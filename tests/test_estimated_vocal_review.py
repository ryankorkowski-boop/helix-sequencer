"""Estimated review must never imply authenticated vocal ownership."""
import numpy as np
from models.band_sampler_logic import NATIVE_SHAPE_NAMES
from tools.verify_estimated_vocal_review import evaluate


def _write(tmp_path, energy, shapes):
    np.savez(tmp_path / "voice_roles.npz", energy=np.asarray(energy, dtype=float),
             shapes=np.asarray(shapes, dtype=int))
    return evaluate(tmp_path)


def test_distinct_estimated_clocks_are_review_only(tmp_path):
    energy = [[0.8, 0], [0.7, 0.5], [0, 0.7], [0, 0]]
    shapes = [[1, 0], [2, 1], [0, 2], [0, 0]]
    report = _write(tmp_path, energy, shapes)
    assert report["passed"] and report["state"] == "ESTIMATED_REVIEW"
    assert not report["release_verified"] and not report["identity_verified"]


def test_gain_copy_is_rejected(tmp_path):
    report = _write(tmp_path, [[0.5, 0.25], [0.7, 0.35], [0, 0]],
                    [[1, 1], [2, 2], [0, 0]])
    assert not report["passed"] and report["state"] == "REJECTED"


def test_empty_harmony_is_rejected(tmp_path):
    report = _write(tmp_path, [[0.8, 0], [0.6, 0]], [[1, 0], [2, 0]])
    assert not report["passed"]


def test_out_of_range_shape_is_rejected(tmp_path):
    import pytest
    with pytest.raises(ValueError):
        _write(tmp_path, [[0.8, 0], [0.6, 0]],
               [[len(NATIVE_SHAPE_NAMES), 0], [2, 0]])
