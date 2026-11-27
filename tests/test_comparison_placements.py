import xml.etree.ElementTree as ET
from types import SimpleNamespace

from tools.build_snowman_ensemble import NativeSequence
from tools.comparison_placements import import_placements, uses_prime
from xlights.xml_io import materialize_native_effect_tables


def test_yard_keeps_prime_layers_and_clocks_separate_from_performer_rows():
    roof = SimpleNamespace(name='roof', kind='pixel', details={}, submodels={})
    window = SimpleNamespace(name='window', kind='pixel', details={}, submodels={'LEFT': [1]})
    drummer = SimpleNamespace(name='drummer', kind='pixel', details={'review_role': 'drummer'},
                              submodels={'KICK': [1]})
    garden = SimpleNamespace(models=[roof, window, drummer])
    sequence = NativeSequence(garden, 3, 'music.wav', 'yard')
    sequence.effect(drummer, 'KICK', 150, 300, '#FFFFFF', 80)
    native = ET.fromstring("""
        <xsequence><EffectDB><Effect>E_SLIDER_Wave_NumberWaves=2</Effect></EffectDB>
        <ColorPalettes><ColorPalette>C_BUTTON_Palette1=#00AAFF,C_CHECKBOX_Palette1=1</ColorPalette></ColorPalettes>
        <ElementEffects>
          <Element type="model" name="roof"><EffectLayer>
            <Effect name="Wave" startTime="200" endTime="1400" ref="0" palette="0"/>
          </EffectLayer></Element>
          <Element type="model" name="window"><SubModelEffectLayer name="LEFT" layer="0">
            <Effect name="Bars" startTime="825" endTime="2300" ref="0" palette="0"/>
          </SubModelEffectLayer></Element>
          <Element type="model" name="drummer"><EffectLayer>
            <Effect name="On" startTime="0" endTime="3000" ref="0" palette="0"/>
          </EffectLayer></Element>
          <Element type="model" name="HX_WHOLE_SHOW"><EffectLayer>
            <Effect name="On" startTime="0" endTime="3000" ref="0" palette="0"/>
          </EffectLayer></Element>
        </ElementEffects></xsequence>""")
    targets = {m.name: m for m in garden.models if uses_prime(m)}
    assert import_placements(sequence, native, targets) == {'roof': 1, 'window': 1}
    materialize_native_effect_tables(sequence.root)
    rows = sequence.elements
    assert rows['roof'].find('./EffectLayer/Effect').get('name') == 'Wave'
    event = rows['window'].find('./SubModelEffectLayer[@name="LEFT"]/Effect')
    assert (event.get('name'), event.get('startTime'), event.get('endTime')) == ('Bars', '825', '2300')
    assert sequence.root.findall('ColorPalettes/ColorPalette')[int(event.get('palette'))].text.startswith('C_BUTTON_Palette1=#00AAFF')
    assert sequence.root.findall('EffectDB/Effect')[int(event.get('ref'))].text == 'E_SLIDER_Wave_NumberWaves=2'
    assert len(list(rows['drummer'].iter('Effect'))) == 1
    assert set(rows) == {'roof', 'window', 'drummer'}


def test_preserves_literal_source_owners():
    for name, details in [
        ('singer', {'generic_singer': 'estimated_backing'}),
        ('helix', {'keyboard_pitch_rungs': True}),
        ('lattice', {'spatial_showcase_native_xyz': True}),
        ('arch', {'percussion_component': 'snare'}),
        ('North Candy Cane 12', {'original_start_channel': 12}),
    ]:
        assert not uses_prime(SimpleNamespace(name=name, kind='pixel', details=details))


def test_comparison_build_keeps_independent_prime_events_when_note_clocks_coincide(tmp_path, monkeypatch):
    import json
    import wave
    from core import effect_engine
    from models.full_song_layouts import NAMES, build as layout
    from tools.build_current_comparison import build
    from tools.phoneme_source import digest

    source = tmp_path / 'source'
    (source / 'media').mkdir(parents=True)
    (source / 'sequence').mkdir()
    audio = source / 'media' / 'clip.wav'
    with wave.open(str(audio), 'wb') as wav:
        wav.setparams((1, 2, 8000, 0, 'NONE', 'not compressed'))
        wav.writeframes(bytes(3 * 8000 * 2))
    sha = digest(audio)
    (source / 'run_manifest.json').write_text(json.dumps({'audio_name': audio.name, 'audio_sha256': sha}))
    hit = dict(kind='note', start_ms=500, end_ms=800, pitch_midi=64, velocity=0.8)
    cues = dict(keyboardist=[hit], guitarist=[hit], bassist=[], drummer=[])
    (source / 'sequence' / 'clip.snowman_band.json').write_text(json.dumps({'cues': cues}))

    def run_variant(variant, template, source_audio, output, profile, **kwargs):
        tree = ET.parse(template)
        for layer in tree.findall('.//EffectLayer'):
            layer.clear()
        for target, family, start in [('HOME_ROOF', 'Wave', 150), ('HOME_WINDOW_1', 'Bars', 950)]:
            layer = tree.find(f"ElementEffects/Element[@name='{target}']/EffectLayer")
            ET.SubElement(layer, 'Effect', name=family, startTime=str(start), endTime='2000')
        tree.write(output)

    monkeypatch.setattr(effect_engine, 'run_variant', run_variant)
    output = tmp_path / 'result'
    build(source, None, output, numbers=[4], names=NAMES, layout_builder=layout,
          instrumental=True, expected_sha256=sha)
    xsq = ET.parse(output / '04' / 'Performance.xsq')
    for model, expected in [('HOME_ROOF', [('Wave', '150')]), ('HOME_WINDOW_1', [('Bars', '950')]),
                            ('HOME_DOOR', [])]:
        row = xsq.find(f"ElementEffects/Element[@name='{model}']")
        assert [(e.get('name'), e.get('startTime')) for e in row.iter('Effect')] == expected
