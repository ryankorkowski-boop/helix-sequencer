from __future__ import annotations

import hashlib

import pytest

from core.birdsong_native_adapter import place_source_birdsong


def _inputs(tmp_path):
    audio = tmp_path / "real-source.wav"
    audio.write_bytes(b"source-audio-identity-test")
    digest = hashlib.sha256(audio.read_bytes()).hexdigest()
    features = {"energy": [0.05, 0.9, 0.1, 0.85],
                "centroid": [500, 7000, 900, 6000], "tempo": 120}
    return audio, digest, features


def test_birdsong_source_identity_must_match(tmp_path):
    audio, digest, features = _inputs(tmp_path)
    with pytest.raises(ValueError, match="do not match"):
        place_source_birdsong(audio, features, source_audio_sha256=digest,
                              features_audio_sha256="0" * 64, fps=20,
                              models=["Pixel Tree"], add_model=lambda *a, **kw: True)


def test_birdsong_requires_native_callback_proof(tmp_path):
    audio, digest, features = _inputs(tmp_path)
    with pytest.raises(RuntimeError, match="no proof"):
        place_source_birdsong(audio, features, source_audio_sha256=digest,
                              features_audio_sha256=digest, fps=20,
                              models=["Pixel Tree"], add_model=lambda *a, **kw: None)


def test_birdsong_preexport_callback_records_rows_without_claiming_native_proof(tmp_path):
    audio, digest, features = _inputs(tmp_path)
    calls = []
    def add_model(*args, **kwargs):
        calls.append((args, kwargs))
        return True
    result = place_source_birdsong(audio, features,
        source_audio_sha256=digest, features_audio_sha256=digest,
        fps=20, models=["Pixel Tree"], add_model=add_model)
    assert result["planned_rows"] == len(calls) > 0
    assert result["callback_confirmed_rows"] == len(calls)
    assert result["native_artifact_verified"] is False


def test_birdsong_rejects_nonfinite_frame_rate(tmp_path):
    audio, digest, features = _inputs(tmp_path)
    for fps in (float("nan"), float("inf"), float("-inf")):
        with pytest.raises(ValueError, match="fps out of range"):
            place_source_birdsong(audio, features, source_audio_sha256=digest,
                                  features_audio_sha256=digest, fps=fps,
                                  models=["Pixel Tree"], add_model=lambda *a, **kw: True)
