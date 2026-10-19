import json
import xml.etree.ElementTree as ET
from core.native_pitched_props import apply_native_pitched_props
from tests.test_magic_keyboard_export import fixture


def test_automatic_gui_cli_rung_routing_uses_harmonic_cues_and_preserves_layout(tmp_path):
    sequence,layout=fixture(tmp_path)
    root=ET.parse(sequence);head=root.getroot().find('head')
    ET.SubElement(head,'sequenceDuration').text='1.0';root.write(sequence)
    plan=tmp_path/'band.json';plan.write_text(json.dumps({'cues':{'keyboardist':[
        {'start_ms':100,'end_ms':400,'pitch_midi':60,'velocity':.8,'pitch_source':'helix_harmonic_polyphony'},
        {'start_ms':100,'end_ms':400,'pitch_midi':64,'velocity':.9,'pitch_source':'helix_harmonic_polyphony'},
        {'start_ms':500,'end_ms':600,'pitch_midi':67,'pitch_source':'untrusted_energy_fallback'}]}}))
    before=layout.read_bytes();report=apply_native_pitched_props(sequence,layout,plan)
    assert report['events']==2 and layout.read_bytes()==before
    root=ET.parse(sequence)
    assert root.find("ElementEffects/Element[@name='old']/EffectLayer/Effect").get('id')=='1'
    assert {e.get('name') for e in root.findall('.//SubModelEffectLayer')}=={'KEY_MIDI_060','KEY_MIDI_064'}


def test_ordinary_layouts_do_not_require_band_inputs_or_change_output(tmp_path):
    sequence=tmp_path/'song.xsq';sequence.write_text('protected source')
    layout=tmp_path/'layout.xml';layout.write_text('<xrgb><models><model name="House"/></models></xrgb>')
    assert apply_native_pitched_props(sequence,layout,tmp_path/'missing.json') is None
    assert sequence.read_text()=='protected source'
