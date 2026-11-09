"""Test adapter against strict source binding; no acoustic truth inferred."""
import json
import numpy as np
import pytest
import soundfile as sf
from tools.vocal_analysis_fixture import build, verify_fixture
from tools.phoneme_source import digest


def qualified(tmp_path):
    audio = tmp_path/'source.wav'; sf.write(audio, np.zeros(16000), 16000)
    analysis = tmp_path/'analysis'; analysis.mkdir()
    report = dict(source_sha256=digest(audio), mixed_bus_only=False,
                  voice_identity_resolved=True, independent_tracks=2,
                  input_tracks={'a':dict(evidence='individual', sha256='a'*64),
                                'b':dict(evidence='individual', sha256='b'*64)},
                  model_lanes=[dict(name='a', role='lead', model_lane=0),
                               dict(name='b', role='background', model_lane=1)])
    (analysis/'voice_roles.json').write_text(json.dumps(report))
    energy = np.zeros((20, 2), 'f4'); energy[1:8, 0] = .8; energy[10:18, 1] = .4
    shapes = np.where(energy > 0, [2, 5], 0).astype('i1')
    np.savez(analysis/'voice_roles.npz', energy=energy, shapes=shapes)
    return audio, analysis, energy, shapes


def test_qualified_inputs_retain_each_lane_at_exact_native_times(tmp_path):
    audio, analysis, energy, shapes = qualified(tmp_path)
    fixture = build(audio, analysis, tmp_path/'fixture')
    receipt = json.loads((fixture/'diagnostic.json').read_text())
    assert verify_fixture(audio, fixture, receipt)['state'] == 'VERIFIED'
    with np.load(fixture/'acoustic_vocal_clocks.npz') as data:
        for i, lane in enumerate(('estimated_lead', 'estimated_backing')):
            np.testing.assert_array_equal(data[lane+'_energy'], np.repeat(energy[:, i], 5))
            np.testing.assert_array_equal(data[lane+'_shapes'], np.repeat(shapes[:, i], 5))
    assert receipt['exact_phoneme_boundaries_verified'] is False


def test_clock_tampering_cannot_hide_behind_a_new_cache_hash(tmp_path):
    audio, analysis, _, _ = qualified(tmp_path)
    fixture = build(audio, analysis, tmp_path/'fixture')
    receipt = json.loads((fixture/'diagnostic.json').read_text())
    with np.load(fixture/'acoustic_vocal_clocks.npz') as data:
        arrays = dict(data)
    arrays['estimated_backing_shapes'][60] = 2
    np.savez(fixture/'acoustic_vocal_clocks.npz', **arrays)
    receipt['clock_sha256'] = digest(fixture/'acoustic_vocal_clocks.npz')
    with pytest.raises(ValueError, match='differs from qualified'):
        verify_fixture(audio, fixture, receipt)


def test_unqualified_source_fails_before_creating_native_fixture(tmp_path):
    audio, analysis, _, _ = qualified(tmp_path)
    report = json.loads((analysis/'voice_roles.json').read_text()); report['origin'] = 'model_estimate'
    (analysis/'voice_roles.json').write_text(json.dumps(report))
    with pytest.raises(ValueError, match='Model-estimated'):
        build(audio, analysis, tmp_path/'fixture')
    assert not (tmp_path/'fixture').exists()
