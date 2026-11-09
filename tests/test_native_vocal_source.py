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
    energy = np.full((20, 2), .4); energy[:5, 1] = 0; energy[-5:, 0] = 0
    shapes = np.where(energy > 0, 1, 0).astype('int8')
    np.savez(tmp_path / "voice_roles.npz", energy=energy, shapes=shapes)
    return audio, tmp_path, report


def test_qualified_source_does_not_replace_native_acceptance(source):
    audio, folder, _ = source
    report = verify(audio, folder)
    assert report["non_rest_frames"] == {"lead": 15, "harmony": 15}
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


@pytest.mark.parametrize('gain', [1., .25])
def test_different_file_hashes_do_not_qualify_gain_copied_clocks(source, gain):
    audio, folder, _ = source
    energy = np.column_stack([np.linspace(.1, .8, 20), gain*np.linspace(.1, .8, 20)])
    np.savez(folder/'voice_roles.npz', energy=energy, shapes=np.ones((20, 2), 'i1'))
    with pytest.raises(ValueError, match='mouth clocks'):
        verify(audio, folder)


@pytest.mark.parametrize('origin_scope', ['report', 'track'])
def test_model_estimate_cannot_be_promoted_by_role_labels(source, origin_scope):
    audio, folder, report = source
    target = report if origin_scope == 'report' else report['input_tracks']['backing']
    target['origin'] = 'model_estimate'
    (folder/'voice_roles.json').write_text(json.dumps(report))
    with pytest.raises(ValueError, match='Model-estimated'):
        verify(audio, folder)


def test_silent_frame_cannot_retain_an_open_mouth(source):
    audio, folder, _ = source
    with np.load(folder/'voice_roles.npz') as data:
        energy, shapes = data['energy'], data['shapes']
    shapes[0, 1] = 2
    np.savez(folder/'voice_roles.npz', energy=energy, shapes=shapes)
    with pytest.raises(ValueError, match='silence/REST'):
        verify(audio, folder)
