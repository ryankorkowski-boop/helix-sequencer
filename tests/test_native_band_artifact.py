"""Transport regressions only: fixtures are never accepted native-show evidence."""
import json
import xml.etree.ElementTree as ET
from unittest.mock import patch

import pytest
from tools import verify_native_band_artifact as gate


@pytest.fixture
def artifact(tmp_path, monkeypatch):
    model_names = sorted('HX_SNOW_' + r.upper() for r in gate.ROLES)
    layout = ET.Element('xrgb')
    models = ET.SubElement(layout, 'models')
    seq = ET.Element('xsequence')
    ET.SubElement(ET.SubElement(seq, 'head'), 'sequenceDuration').text = '36'
    elements = ET.SubElement(seq, 'ElementEffects')
    for name in model_names:
        model = ET.SubElement(models, 'model', name=name)
        ET.SubElement(model, 'subModel', name='BODY')
        row = ET.SubElement(elements, 'Element', name=name, type='model')
        ET.SubElement(ET.SubElement(row, 'SubModelEffectLayer', name='BODY'), 'Effect')
    ET.ElementTree(layout).write(tmp_path / 'xlights_rgbeffects.xml')
    ET.ElementTree(seq).write(tmp_path / 'Performance.xsq')
    for name in ('audio.wav', 'preview.mp4', 'Performance.fseq'):
        (tmp_path / name).write_bytes(b'unit fixture only: ' + name.encode())
    audio_sha = gate._sha256(tmp_path / 'audio.wav')
    monkeypatch.setattr(gate, 'AUDIO_SHA256', audio_sha)
    report = {'status': 'success', 'backend': 'xlights_house_preview',
              'audio_stream_verified': True, 'duration_seconds': 36}
    for key, name in {'audio': 'audio.wav', 'mp4': 'preview.mp4',
                      'xsq': 'Performance.xsq', 'layout': 'xlights_rgbeffects.xml',
                      'native_fseq': 'Performance.fseq'}.items():
        report[key + '_sha256'] = gate._sha256(tmp_path / name)
    (tmp_path / 'run_manifest.json').write_text(json.dumps({'native_preview': report}))
    (tmp_path / 'pose_provenance.json').write_text(json.dumps({
        'audio_sha256': audio_sha, 'visible_performer_roles': list(gate.ROLES),
        'legacy_xylophone_enabled': False, 'source_score': 'ReviewBandPerformance.pose'}))
    return tmp_path


def test_transport_checks_keep_six_independent_rows(artifact):
    result = gate.verify_inputs(artifact)
    assert len(result['effects_per_model']) == 6
    assert all(result['effects_per_model'].values())


@pytest.mark.parametrize('filename', ['preview.mp4', 'audio.wav', 'Performance.xsq',
                                     'Performance.fseq', 'xlights_rgbeffects.xml'])
def test_changed_artifact_bytes_fail_before_decoding(artifact, filename):
    (artifact / filename).write_bytes(b'tampered')
    with pytest.raises(ValueError, match='digest differs'):
        gate.verify_inputs(artifact)


def test_missing_or_ambiguous_movie_rejected(artifact):
    (artifact / 'second').mkdir()
    (artifact / 'second' / 'preview.mp4').write_bytes(b'arbitrary movie')
    with pytest.raises(ValueError, match='exactly one preview.mp4'):
        gate.verify_inputs(artifact)
    (artifact / 'preview.mp4').unlink()
    (artifact / 'second' / 'preview.mp4').unlink()
    with pytest.raises(ValueError, match='exactly one preview.mp4'):
        gate.verify_inputs(artifact)


def test_diagnostic_manifest_rejected(artifact):
    path = artifact / 'run_manifest.json'
    report = json.loads(path.read_text())
    report['native_preview']['status'] = 'fallback'
    path.write_text(json.dumps(report))
    with pytest.raises(ValueError, match='No successful native'):
        gate.verify_inputs(artifact)


def test_duplicate_model_row_rejected_even_with_updated_hash(artifact):
    path = artifact / 'Performance.xsq'
    tree = ET.parse(path)
    elements = tree.find('ElementEffects')
    elements.append(ET.fromstring(ET.tostring(elements[0])))
    tree.write(path)
    manifest = artifact / 'run_manifest.json'
    report = json.loads(manifest.read_text())
    report['native_preview']['xsq_sha256'] = gate._sha256(path)
    manifest.write_text(json.dumps(report))
    with pytest.raises(ValueError, match='independent editable'):
        gate.verify_inputs(artifact)


def test_silent_fseq_fails_before_media_acceptance(artifact):
    with patch.object(gate, 'inspect_fseq', return_value={
            'nonzero_frames': 0, 'frames': 720, 'nonzero_samples': 0, 'duration_ms': 36000}):
        with pytest.raises(ValueError, match='Inactive'):
            gate.verify(artifact)
