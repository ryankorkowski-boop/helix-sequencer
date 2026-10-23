import xml.etree.ElementTree as ET
from types import SimpleNamespace
from models.approval_layouts import build_layout, NAMES
from tools.canonical_band_cues import export_instruments, export_drums
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
            if number==3:
                assert len([m for m in garden.models if m.details.get('generic_singer')])==2
                assert any('SPINNER' in m.name for m in garden.models)
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


def test_real_drum_classes_do_not_collapse_to_one_tom_or_hihat_sticks():
    garden=build_layout(7);sequence=NativeSequence(garden,1,'','test')
    cues=[dict(start_ms=103,end_ms=207,kind='kick',velocity=.8),
          dict(start_ms=301,end_ms=419,kind='hihat',velocity=.7),
          dict(start_ms=501,end_ms=619,kind='snare',velocity=.9),
          dict(start_ms=701,end_ms=819,kind='tom',velocity=.5)]
    report=export_drums(sequence.root,garden,{'cues':{'drummer':cues}})
    assert report['component_events']=={'KICK':1,'HI_HAT':1,'SNARE':1}
    assert len(report['unresolved_events'])==1
    effects=list(sequence.root.iter('Effect'))
    actual=[e for e in effects if e.get('sourceMethod')=='retained_production_drum_plan']
    assert any(e.get('sourceStartMs')=='103' and e.get('sourceComponent').endswith('KICK_SURFACE') for e in actual)
    assert any(e.get('sourceStartMs')=='301' and e.get('sourceComponent').endswith('HI_HAT_FOOT') for e in actual)
    assert not any('HI_HAT' in e.get('sourceComponent','') and 'STICK' in e.get('sourceComponent','') for e in actual)


def test_comparison_optional_labels_keep_all_streams_and_one_soundtrack(tmp_path, monkeypatch):
    import tools.render_approval_collection as collection
    captured=[]
    def produce(args):
        captured.extend(args)
        from pathlib import Path
        Path(args[-1]).write_bytes(b'completed comparison')
    monkeypatch.setattr(collection,'command',produce)
    monkeypatch.setattr(collection,'probe_media',lambda *args:{'streams':[]})
    target=tmp_path/'comparison.mp4'
    collection.comparison([tmp_path/'a.mp4',tmp_path/'b.mp4'],[],target,tmp_path/'source.mp3',2,1)
    graph=captured[captured.index('-filter_complex')+1]
    assert '[0:v]setpts=PTS-STARTPTS' in graph
    assert '[1:v]setpts=PTS-STARTPTS' in graph
    assert '2:a:0' in captured
    assert target.read_bytes()==b'completed comparison'
    assert not list(tmp_path.glob('.comparison-*'))


def test_failed_comparison_preserves_existing_movie_and_removes_partial(tmp_path, monkeypatch):
    import tools.render_approval_collection as collection
    import pytest
    def fail(args):
        from pathlib import Path
        Path(args[-1]).write_bytes(b'partial')
        raise RuntimeError('encoder rejected input')
    monkeypatch.setattr(collection,'command',fail)
    target=tmp_path/'comparison.mp4';target.write_bytes(b'previous verified movie')
    with pytest.raises(RuntimeError,match='encoder rejected'):
        collection.comparison([tmp_path/'a.mp4',tmp_path/'b.mp4'],[],target,tmp_path/'source.mp3',2,1)
    assert target.read_bytes()==b'previous verified movie'
    assert not list(tmp_path.glob('.comparison-*'))
