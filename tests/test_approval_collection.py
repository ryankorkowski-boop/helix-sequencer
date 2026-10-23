import xml.etree.ElementTree as ET
from types import SimpleNamespace
from models.approval_layouts import build_layout, NAMES
from tools.canonical_band_cues import export_instruments
from tools.build_snowman_ensemble import NativeSequence


def test_twelve_layouts_have_unique_models_and_exact_ac_budgets():
    assert len(NAMES)==len(set(NAMES))==12
    for number in range(1,13):
        garden=build_layout(number)
        assert len({m.name for m in garden.models})==len(garden.models)
        assert all(m.points.size and m.channels>0 for m in garden.models)
        if number<=3:
            assert sum(m.channels for m in garden.models)=={1:16,2:64,3:256}[number]
            assert all(m.kind=='ac' for m in garden.models)
        if number==9:
            hero=next(m for m in garden.models if m.name=='HX_CENTER_KEYBOARD_HELIX')
            assert all(hero.submodels[f'KEY_MIDI_{p:03d}'] for p in range(21,109))
        if number in (7,8,12):
            assert len([m for m in garden.models if m.details.get('review_role')])==6


def test_native_musician_adapter_preserves_source_clock_and_reports_omissions():
    garden=build_layout(7)
    sequence=NativeSequence(garden,1,'','test')
    plan={'cues':{'bassist':[dict(start_ms=103,end_ms=207,string_index=2)],
        'guitarist':[dict(start_ms=301,end_ms=419,kind='strum')],
        'keyboardist':[dict(start_ms=503,end_ms=617,pitch_midi=60),
                       dict(start_ms=701,end_ms=817,pitch_midi=110)]}}
    report=export_instruments(sequence.root,garden,plan)
    assert report['models']['HX_SNOW_PIANO']['unmapped_pitch_events']==1
    element=sequence.root.find("ElementEffects/Element[@name='HX_SNOW_PIANO/NOTE_MIDI_60']")
    effect=element.find('EffectLayer/Effect')
    assert (effect.get('startTime'),effect.get('endTime'))==('503','617')
    for role in ('BASS','GUITAR','PIANO'):
        names=[e.get('name') for e in sequence.root.findall('DisplayElements/Element')]
        assert len(names)==len(set(names))
        assert 'HX_SNOW_'+role in names
    piano=next(m for m in garden.models if m.name.endswith('PIANO'))
    assert piano.submodels['INSTRUMENT_IDLE_NOTE_MIDI_60']
    assert set(piano.submodels['ARM_LEFT_IDLE']).isdisjoint(piano.submodels['ARM_LEFT_ACTIVE'])
