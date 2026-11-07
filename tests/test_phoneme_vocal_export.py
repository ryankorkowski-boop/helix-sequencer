import json
from types import SimpleNamespace
import xml.etree.ElementTree as ET
import pytest
from tools.phoneme_vocal_export import export, FIXTURE
from tools.phoneme_source import FIXTURE as AUDIO, EXPECTED_SHA256


def source_layout(tmp_path):
    root = ET.Element('xrgb')
    models = ET.SubElement(root, 'models')
    for role in ('LEAD', 'HARMONY'):
        model = ET.SubElement(models, 'model', name='HX_SNOW_'+role)
        ET.SubElement(model, 'faceInfo', Name='Helix independent phonemes', Type='NodeRange',
            **{'Mouth-AI':'1', 'Mouth-E':'2', 'Mouth-O':'3', 'Mouth-rest':'4'})
    path = tmp_path / 'layout.xml'
    ET.ElementTree(root).write(path)
    return path


def sequence():
    root = ET.Element('xsequence')
    ET.SubElement(ET.SubElement(root, 'head'), 'sequenceDuration').text = '34.88'
    ET.SubElement(root, 'DisplayElements')
    effects = ET.SubElement(root, 'ElementEffects')
    for name in ('HX_SNOW_LEAD', 'HX_SNOW_HARMONY/MOUTH_AI'):
        element = ET.SubElement(effects, 'Element', name=name)
        ET.SubElement(ET.SubElement(element, 'EffectLayer'), 'Effect', name='Wave')
    return root


def test_real_source_cache_exports_bounded_distinct_estimates_and_keeps_acceptance_open(tmp_path):
    root = sequence()
    report = export(root, source_layout(tmp_path), SimpleNamespace(models=[]))
    assert report['removed_decorative_mouth_effects'] == 2
    assert report['independent_backing_verified'] is False
    assert report['exact_phoneme_boundaries_verified'] is False
    identities = []
    for role in ('LEAD', 'HARMONY'):
        name = 'HX_SNOW_'+role
        effects = list(root.find(f'./ElementEffects/Element[@name="{name}"]').iter('Effect'))
        assert len(effects) > 10
        assert all(effect.get('name') == 'Faces' for effect in effects)
        assert all(0 <= int(effect.get('startTime')) < int(effect.get('endTime')) <= 34880 for effect in effects)
        assert any('Phoneme=rest,' in effect.get('settings', '') for effect in effects)
        assert report['models'][name]['non_rest_effect_count'] > 0
        identities.append(report['models'][name]['source_track_sha256'])
    assert identities[0] != identities[1]


def test_changed_vocal_cache_receipt_is_rejected_before_export(tmp_path):
    fixture = tmp_path / 'cache'
    fixture.mkdir()
    data = json.loads((FIXTURE/'diagnostic.json').read_text())
    data['clock_sha256'] = 'bad'
    (fixture/'diagnostic.json').write_text(json.dumps(data))
    (fixture/'acoustic_vocal_clocks.npz').write_bytes((FIXTURE/'acoustic_vocal_clocks.npz').read_bytes())
    with pytest.raises(ValueError, match='receipt'):
        export(sequence(), source_layout(tmp_path), SimpleNamespace(models=[]), fixture=fixture)


def test_real_audio_stemless_mode_exports_native_faces_with_honest_mixed_source_identity(tmp_path):
    root = sequence()
    report = export(root, source_layout(tmp_path), SimpleNamespace(models=[]), stemless_audio=AUDIO)
    assert report['stemless_estimate']['frame_ms'] == 10
    assert report['stemless_estimate']['audio_sha256'] == EXPECTED_SHA256
    assert report['stemless_estimate']['independent_voice_identity_proven'] is False
    assert report['independent_backing_verified'] is False
    active = []
    for role in ('LEAD', 'HARMONY'):
        row = root.find(f'./ElementEffects/Element[@name="HX_SNOW_{role}"]')
        effects = list(row.iter('Effect'))
        assert all(e.get('name') == 'Faces' for e in effects)
        assert all(e.get('sourceMethod') == 'stemless_mixed_audio_estimate' for e in effects)
        assert all(e.get('sourceTrackSHA256') == EXPECTED_SHA256 for e in effects)
        assert int(effects[0].get('startTime')) == 0
        assert int(effects[-1].get('endTime')) == 34880
        assert all(a.get('endTime') == b.get('startTime') for a, b in zip(effects, effects[1:]))
        active.append([(int(e.get('startTime')), int(e.get('endTime'))) for e in effects
                       if 'Phoneme=rest,' not in e.get('settings', '')])
    assert active[0]
    assert all(any(a <= lo and hi <= b for a, b in active[0]) for lo, hi in active[1])
    from tools.vocal_diagnostic import export as timeline
    import csv
    diagnostic = tmp_path/'timeline'
    timeline_report = timeline(AUDIO, FIXTURE, diagnostic, stemless_duet=True)
    assert timeline_report['stemless_estimate']['mode'] == 'stemless_mixed_audio_estimate'
    with (diagnostic/'Vocal_Timeline.csv').open() as stream:
        rows = list(csv.DictReader(stream))
    for index, role in enumerate(('lead', 'backing')):
        for frame, row in enumerate(rows):
            expected = any(lo <= frame*10 < hi for lo, hi in active[index])
            assert bool(int(row[role+'_active'])) == expected
            assert row[role+'_speech_vad_probability'] == ''


def test_stemless_audio_mismatch_does_not_modify_sequence(tmp_path):
    wrong = tmp_path/'wrong.wav'; wrong.write_bytes(b'wrong source')
    root = sequence(); before = ET.tostring(root)
    with pytest.raises(ValueError, match='Stemless estimate audio'):
        export(root, source_layout(tmp_path), SimpleNamespace(models=[]), stemless_audio=wrong)
    assert ET.tostring(root) == before
