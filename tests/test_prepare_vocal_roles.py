"""Exercise public preparation/NPZ export; acoustic clocks are supplied fixtures."""
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from tools import prepare_vocal_roles as preparation


def run_prepare(tmp_path, monkeypatch, roles, *, instrumental=False):
    source = tmp_path / 'source.wav'
    sf.write(source, np.zeros(16000, dtype='float32'), 16000)
    original = source.read_bytes()
    lanes = [dict(name=f'voice{i}', role=role,
                  energy=np.full(20, .2 + i * .3, dtype='float32'),
                  shapes=np.full(20, 2 + i, dtype='int8'))
             for i, role in enumerate(roles)]
    monkeypatch.setattr(preparation, 'route_voices',
                        lambda tracks, duration: (
                            lanes, np.full(20, 'solo', dtype='<U18'),
                            {'schema': 'helix.voice_roles.v1'}))
    config = tmp_path / 'config.json'
    config.write_text(json.dumps({
        'source_audio': source.name, 'duration': 1.,
        'tracks': [], 'known_instrumental': instrumental}))
    output = tmp_path / 'analysis'
    report = preparation.prepare(config, output)
    assert source.read_bytes() == original
    assert report['source_sha256'] == hashlib.sha256(original).hexdigest()
    return output, report, lanes


@pytest.mark.parametrize('role,slot', [('lead', 0), ('second', 1), ('background', 1)])
def test_lone_voice_uses_declared_performer_slot(tmp_path, monkeypatch, role, slot):
    output, report, lanes = run_prepare(tmp_path, monkeypatch, [role])
    with np.load(output / 'voice_roles.npz') as data:
        np.testing.assert_array_equal(data['energy'][:, slot], lanes[0]['energy'])
        np.testing.assert_array_equal(data['shapes'][:, slot], lanes[0]['shapes'])
        assert not np.any(data['energy'][:, 1-slot])
        assert not np.any(data['shapes'][:, 1-slot])
    assert report['model_lanes'][0]['model_lane'] == slot
    assert report['model_lanes'][0]['role'] == role


def test_unordered_lead_and_backing_keep_independent_shapes(tmp_path, monkeypatch):
    output, report, lanes = run_prepare(tmp_path, monkeypatch, ['background', 'lead'])
    with np.load(output / 'voice_roles.npz') as data:
        np.testing.assert_array_equal(data['energy'][:, 0], lanes[1]['energy'])
        np.testing.assert_array_equal(data['shapes'][:, 0], lanes[1]['shapes'])
        np.testing.assert_array_equal(data['energy'][:, 1], lanes[0]['energy'])
        np.testing.assert_array_equal(data['shapes'][:, 1], lanes[0]['shapes'])
    assert {entry['role']: entry['model_lane'] for entry in report['model_lanes']} == {
        'lead': 0, 'background': 1}


@pytest.mark.parametrize('roles', [('background', 'background'), ('second', 'background')])
def test_multiple_parts_cannot_silently_share_one_backing_mouth(tmp_path, monkeypatch, roles):
    with pytest.raises(ValueError, match='separate face models'):
        run_prepare(tmp_path, monkeypatch, roles)
    assert not (tmp_path / 'analysis' / 'voice_roles.npz').exists()


def test_known_instrumental_guard_still_silences_both_slots(tmp_path, monkeypatch):
    output, report, _ = run_prepare(
        tmp_path, monkeypatch, ['background', 'lead'], instrumental=True)
    with np.load(output / 'voice_roles.npz') as data:
        assert not np.any(data['energy'])
        assert not np.any(data['shapes'])
        assert set(data['modes']) == {'silence'}
    assert report['instrumental_source_guard'] is True
