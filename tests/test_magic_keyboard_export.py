from pathlib import Path
import xml.etree.ElementTree as ET

import pytest
from music.magic_keyboard import magic_keyboard_events
from music.note_events import NoteEvent
from core.keyboard_rung_export import export_keyboard_rungs


def test_mallet_synth_and_horn_share_keys_without_drum_or_voice_leakage():
    notes = [NoteEvent(0, .2, 60, source='piano_stem_harmonic_estimate'),
             NoteEvent(.3, .5, 64, source='synth_pitched_onset', confidence=.9),
             NoteEvent(.6, .8, 67, source='horn_harmonic_onset', confidence=.8),
             NoteEvent(1, 1.2, 72, source='drum_pitched', confidence=.99),
             NoteEvent(1.3, 1.5, 70, source='unclassified_pitched', confidence=.2)]
    hits = [dict(time=.9, source_time=.89, pitch=76, velocity=.7)]
    actual = magic_keyboard_events(notes, hits, duration=2)
    assert [e.pitch for e in actual] == [60, 64, 67, 76]
    assert actual[-1].start == .89


def fixture(tmp_path):
    source = tmp_path/'source.xsq'
    source.write_text('<xsequence><head/><nextid>2</nextid><ColorPalettes/><EffectDB/><DisplayElements/><ElementEffects><Element name="old" type="model"><EffectLayer><Effect name="On" id="1" startTime="0" endTime="100"/></EffectLayer></Element></ElementEffects></xsequence>')
    root = ET.Element('xrgb'); models = ET.SubElement(root, 'models')
    model = ET.SubElement(models, 'model', name='HX_CENTER_KEYBOARD_HELIX', StringType='RGB Nodes')
    for n in range(21, 109):
        ET.SubElement(model, 'subModel', name=f'KEY_MIDI_{n:03d}', line0=str(n-20))
    layout = tmp_path/'layout.xml'; ET.ElementTree(root).write(layout)
    return source, layout


def test_native_rung_export_keeps_original_layers_and_chords(tmp_path):
    source, layout = fixture(tmp_path); before = layout.read_bytes()
    result = export_keyboard_rungs(source, layout, tmp_path/'out.xsq',
        [dict(pitch=60, start=.1, end=.5), dict(pitch=64, start=.1, end=.4)], duration=1)
    root = ET.parse(tmp_path/'out.xsq').getroot()
    assert result['active_rungs'] == 2 and layout.read_bytes() == before
    assert root.find("ElementEffects/Element[@name='old']/EffectLayer/Effect").get('id') == '1'
    layers = root.findall(".//SubModelEffectLayer")
    assert {x.get('name') for x in layers} == {'KEY_MIDI_060', 'KEY_MIDI_064'}
    assert all(x.find('Effect').get('startTime') == '100' for x in layers)


def test_rung_export_rejects_missing_submodel_and_layout_overwrite(tmp_path):
    source, layout = fixture(tmp_path)
    with pytest.raises(ValueError, match='overwrite'):
        export_keyboard_rungs(source, layout, layout, [], duration=1)
    root = ET.parse(layout); root.find('models/model').remove(root.find('models/model/subModel')); root.write(layout)
    with pytest.raises(ValueError, match='88 nonempty'):
        export_keyboard_rungs(source, layout, tmp_path/'out.xsq', [], duration=1)
