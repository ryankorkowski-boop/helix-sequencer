import hashlib
import json
import numpy as np
import pytest
import soundfile as sf
from tools.verify_native_vocal_source import verify


@pytest.fixture
def source(tmp_path):
    audio = tmp_path / "source.wav"
    sf.write(audio, np.zeros(16000, "float32"), 16000)
    report = {"source_sha256": hashlib.sha256(audio.read_bytes()).hexdigest(),
              "mixed_bus_only": False, "voice_identity_resolved": True, "independent_tracks": 2,
              "input_tracks": {"solo": {"evidence": "individual", "sha256": "a" * 64},
                               "backing": {"evidence": "individual", "sha256": "b" * 64}},
              "model_lanes": [{"name": "solo", "role": "lead", "model_lane": 0},
                              {"name": "backing", "role": "background", "model_lane": 1}]}
    (tmp_path / "voice_roles.json").write_text(json.dumps(report))
    np.savez(tmp_path / "voice_roles.npz", energy=np.full((20, 2), .4), shapes=np.ones((20, 2), "int8"))
    return audio, tmp_path, report


def test_qualified_source_does_not_replace_native_acceptance(source):
    audio, folder, _ = source
    report = verify(audio, folder)
    assert report["non_rest_frames"] == {"lead": 20, "harmony": 20}
    assert "separate" in report["limit"]


@pytest.mark.parametrize("field,value", [("source_sha256", "wrong"), ("mixed_bus_only", True), ("independent_tracks", 1)])
def test_mixed_or_wrong_source_rejected_before_native_build(source, field, value):
    audio, folder, report = source
    report[field] = value
    (folder / "voice_roles.json").write_text(json.dumps(report))
    with pytest.raises(ValueError): verify(audio, folder)


def test_empty_backing_is_a_negative_source_even_with_two_models(source):
    audio, folder, _ = source
    shapes = np.ones((20, 2), "int8"); shapes[:, 1] = 0
    np.savez(folder / "voice_roles.npz", energy=np.full((20, 2), .5), shapes=shapes)
    with pytest.raises(ValueError, match="empty lead/backing"): verify(audio, folder)


def test_duplicate_sources_cannot_pass_two_vocalist_gate(source):
    audio, folder, report = source
    report["input_tracks"]["backing"]["duplicate_of"] = "solo"
    (folder / "voice_roles.json").write_text(json.dumps(report))
    with pytest.raises(ValueError, match="ownership"): verify(audio, folder)
