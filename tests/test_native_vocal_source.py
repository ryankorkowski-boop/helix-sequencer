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
    energy = np.full((20, 2), .4, dtype="float32")
    energy[::2, 1] = .2
    np.savez(tmp_path / "voice_roles.npz", energy=energy, shapes=np.ones((20, 2), "int8"))
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


def test_copied_mouth_clocks_rejected_even_with_distinct_track_hashes(source):
    audio, folder, _ = source
    energy = np.full((20, 2), .4, dtype="float32")
    shapes = np.ones((20, 2), dtype="int8")
    np.savez(folder / "voice_roles.npz", energy=energy, shapes=shapes)
    with pytest.raises(ValueError, match="mouth clocks are identical"):
        verify(audio, folder)


def test_gain_scaled_duplicate_mouth_clock_rejected(source):
    audio, folder, _ = source
    lead = np.linspace(.2, .8, 20, dtype="float32")
    energy = np.column_stack([lead, lead * .7]).astype("float32")
    shapes = np.ones((20, 2), dtype="int8")
    np.savez(folder / "voice_roles.npz", energy=energy, shapes=shapes)
    with pytest.raises(ValueError, match="gain-scaled copies"):
        verify(audio, folder)


def test_independent_harmony_with_distinct_phrase_timing_passes(source):
    audio, folder, _ = source
    energy = np.full((20, 2), .4, dtype="float32")
    energy[:5, 1] = 0
    shapes = np.ones((20, 2), dtype="int8")
    shapes[:5, 1] = 0
    np.savez(folder / "voice_roles.npz", energy=energy, shapes=shapes)
    result = verify(audio, folder)
    assert result["non_rest_frames"] == {"lead": 20, "harmony": 15}


def test_estimated_vocal_source_cannot_be_promoted_to_verified_singer(source):
    audio, folder, report = source
    report["input_tracks"]["backing"]["origin"] = "model_estimate"
    (folder / "voice_roles.json").write_text(json.dumps(report))
    with pytest.raises(ValueError, match="Model-estimated vocal candidates"):
        verify(audio, folder)


@pytest.mark.parametrize("energy_value,shape_value,error", [
    (0.0, 2, "Silent vocal frames"),
    (0.4, 0, "Active vocal frames"),
])
def test_silence_and_mouth_shapes_must_agree(source, energy_value, shape_value, error):
    audio, folder, _ = source
    energy = np.full((20, 2), .4, dtype="float32")
    energy[::2, 1] = .2
    shapes = np.ones((20, 2), dtype="int8")
    energy[3, 1] = energy_value
    shapes[3, 1] = shape_value
    np.savez(folder / "voice_roles.npz", energy=energy, shapes=shapes)
    with pytest.raises(ValueError, match=error):
        verify(audio, folder)
