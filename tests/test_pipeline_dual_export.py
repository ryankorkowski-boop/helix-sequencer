"""Exercise real AC XSQ/LMS files through normal sequencing and rollback."""
import json
from pathlib import Path
from types import SimpleNamespace
import xml.etree.ElementTree as ET

import pytest
from core import dual_export, sequence_builder


def fixtures(root):
    layout = root / 'layout.xml'
    layout.write_text('<xrgb><models><model name="Red" StringType="Single Color Red" '
                      'StartChannel="1"/></models><modelGroups/></xrgb>')
    mapping = root / 'map.csv'
    mapping.write_text('model,color,controller_unit,controller_circuit,xlights_start_channel\n'
                       'Red,red,1,5,1\n')
    source = root / 'song.xsq'
    source.write_text('<xsequence><head><sequenceDuration>2</sequenceDuration>'
        '<mediaFile>song.wav</mediaFile></head><nextid>2</nextid><ColorPalettes>'
        '<ColorPalette>C_BUTTON_Palette1=#FFFFFF,C_CHECKBOX_Palette1=1</ColorPalette>'
        '</ColorPalettes><EffectDB><Effect>E_TEXTCTRL_Eff_On_Start=100,'
        'E_TEXTCTRL_Eff_On_End=100</Effect></EffectDB><DisplayElements>'
        '<Element type="model" name="Red"/></DisplayElements><ElementEffects>'
        '<Element type="model" name="Red"><EffectLayer><Effect name="On" '
        'ref="0" palette="0" startTime="100" endTime="400"/></EffectLayer></Element>'
        '</ElementEffects></xsequence>')
    return layout, mapping, source


def test_actual_xsq_and_lms_share_note_intervals_and_media(tmp_path):
    layout, mapping, source = fixtures(tmp_path)
    dual_export.validate_mapping(layout, mapping)
    before = source.read_bytes()
    outputs = dual_export.export_lms_siblings([source], mapping)
    assert source.read_bytes() == before
    assert set(outputs) == {source.with_suffix('.lms'), source.with_suffix('.lms_validation.json')}
    lms = ET.parse(source.with_suffix('.lms')).getroot()
    channel = lms.find('./channels/channel')
    assert (channel.get('unit'), channel.get('circuit')) == ('1', '5')
    effect = channel.find('effect')
    assert (effect.get('startCentisecond'), effect.get('endCentisecond')) == ('10', '40')
    assert lms.get('musicFilename') == 'song.wav'
    report = json.loads(source.with_suffix('.lms_validation.json').read_text())
    assert report['output'] == str(source.with_suffix('.lms'))
    assert report['verified_lor_import'] is False


@pytest.mark.parametrize('field,value', [('color', 'green'), ('xlights_start_channel', '2')])
def test_mismatched_map_rejected_before_sequencing(tmp_path, field, value):
    layout, mapping, _ = fixtures(tmp_path)
    import csv, io
    rows = list(csv.DictReader(io.StringIO(mapping.read_text())))
    rows[0][field] = value
    with mapping.open('w') as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0]);writer.writeheader();writer.writerows(rows)
    with pytest.raises(ValueError, match='differs from layout'):
        dual_export.validate_mapping(layout, mapping)


def test_later_invalid_sequence_leaves_no_partial_lms_or_sidecars(tmp_path):
    _, mapping, source = fixtures(tmp_path)
    second = tmp_path / 'invalid.xsq'
    second.write_text('<xsequence/>')
    with pytest.raises(ValueError):
        dual_export.export_lms_siblings([source, second], mapping)
    assert not list(tmp_path.glob('*.lms'))
    assert not list(tmp_path.glob('*.lms_validation.json'))


def test_existing_sidecar_and_lms_are_never_overwritten(tmp_path):
    _, mapping, source = fixtures(tmp_path)
    sidecar = source.with_suffix('.lms_validation.json')
    sidecar.write_text('keep original evidence')
    with pytest.raises(FileExistsError):
        dual_export.export_lms_siblings([source], mapping)
    assert sidecar.read_text() == 'keep original evidence'
    assert not source.with_suffix('.lms').exists()


def test_normal_run_writes_both_formats_and_success_manifest(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    layout, mapping, template = fixtures(tmp_path)
    audio = tmp_path / 'song.wav';audio.write_bytes(b'unit input, no audio analysis in fake engine')
    output = tmp_path / 'output';output.mkdir()
    def engine(version, args):
        assert dual_export.DUAL_MAP_FLAG not in args
        (output / 'generated.xsq').write_bytes(template.read_bytes())
    monkeypatch.setattr(sequence_builder, '_effect_engine', lambda: SimpleNamespace(main_for=engine))
    sequence_builder.run_profile('master', ['--audio', str(audio), '--template', str(template),
        '--layout-file', str(layout), '--output-dir', str(output), dual_export.DUAL_MAP_FLAG, str(mapping)])
    assert (output / 'generated.xsq').is_file()
    lms = ET.parse(output / 'generated.lms').getroot()
    assert lms.find('./channels/channel').get('circuit') == '5'
    manifests = list((output / 'beta').rglob('run_manifest.json'))
    assert len(manifests) == 1
    manifest = json.loads(manifests[0].read_text())
    assert manifest['status'] == 'success'
    assert any(item['kind'] == 'lor_sequence' for item in manifest['artifacts'])


def test_racing_external_target_is_preserved_and_own_outputs_rolled_back(tmp_path, monkeypatch):
    _, mapping, source = fixtures(tmp_path)
    original = dual_export.export_legacy_lms
    sidecar = source.with_suffix('.lms_validation.json')
    def concurrent_writer(*args):
        result = original(*args)
        sidecar.write_text('another process owns this file')
        return result
    monkeypatch.setattr(dual_export, 'export_legacy_lms', concurrent_writer)
    with pytest.raises(FileExistsError):
        dual_export.export_lms_siblings([source], mapping)
    assert not source.with_suffix('.lms').exists()
    assert sidecar.read_text() == 'another process owns this file'


def test_controller_map_change_after_preflight_is_rejected(tmp_path):
    layout, mapping, source = fixtures(tmp_path)
    digest = dual_export.validate_mapping(layout, mapping)
    mapping.write_text(mapping.read_text().replace('Red,red,1,5,1','Red,red,2,5,1'))
    with pytest.raises(ValueError, match='changed since preflight'):
        dual_export.export_lms_siblings([source], mapping, expected_mapping_sha256=digest)
    assert not source.with_suffix('.lms').exists()


def test_each_conversion_uses_frozen_mapping_even_if_original_changes(tmp_path, monkeypatch):
    _, mapping, source = fixtures(tmp_path)
    second = tmp_path / 'second.xsq';second.write_bytes(source.read_bytes())
    original = dual_export.export_legacy_lms
    def change_after_first(*args):
        result = original(*args)
        mapping.write_text(mapping.read_text().replace('Red,red,1,5,1','Red,red,2,5,1'))
        return result
    monkeypatch.setattr(dual_export, 'export_legacy_lms', change_after_first)
    dual_export.export_lms_siblings([source, second], mapping)
    for path in (source, second):
        assert ET.parse(path.with_suffix('.lms')).find('./channels/channel').get('unit') == '1'
