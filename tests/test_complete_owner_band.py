"""Owner seven-member review mode; historical defaults remain separately tested."""
import numpy as np
from models.final_band_scene import FinalBandScene
from models.approval_layouts import build_layout
from tools.build_snowman_ensemble import NativeSequence
from tools.canonical_band_cues import export_instruments
from tools.phoneme_vocal_export import static_materials
from tools.source_spatial_direction import schedule


def test_seven_solid_members_and_literal_88_keys_preserve_guitar_geometry():
    old=FinalBandScene()
    new=FinalBandScene(include_xylophonist=True,full_keyboard=True)
    assert set(new.visible_roles)=={'drummer','bass','guitar','piano','xylophone','lead','harmony'}
    keys=[o for o in new.instances if o['kind']!='hidden' and o['name'].startswith('piano_key_')]
    assert {int(o['name'].rsplit('_',1)[1]) for o in keys}==set(range(21,109))
    assert len({o['slot'] for o in keys})==88
    assert not any(o['kind']=='wire_sphere' for o in new.instances)
    assert any(o['kind']!='hidden' and o.get('performer_role')=='xylophone' for o in new.instances)
    for a,b in zip(old.strings['guitar'],new.strings['guitar']):
        np.testing.assert_array_equal(a['a'],b['a']);np.testing.assert_array_equal(a['b'],b['b'])


def test_native_seven_members_keep_notes_clocks_and_alternating_mallets():
    g=build_layout(7,include_xylophonist=True,full_keyboard=True)
    assert len([m for m in g.models if m.details.get('review_role')])==7
    piano=next(m for m in g.models if m.details.get('review_role')=='piano')
    assert all(piano.submodels.get('NOTE_MIDI_'+str(p)) for p in range(21,109))
    seq=NativeSequence(g,2,'','test')
    notes=[dict(start_ms=a,end_ms=a+70,pitch_midi=p,velocity=.8)
           for a,p in [(103,21),(303,60),(503,60),(703,108)]]
    report=export_instruments(seq.root,g,{'cues':{'keyboardist':notes}})
    assert report['models'][piano.name]['mapped_events']==4
    assert report['models'][piano.name]['unmapped_pitch_events']==0
    xy=next(m for m in g.models if m.details.get('review_role')=='xylophone')
    assert report['models'][xy.name]['source_lane']=='keyboardist'
    for side,start in [('LEFT',303),('RIGHT',503)]:
        element=seq.root.find(f"ElementEffects/Element[@name='{xy.name}/ARM_{side}_NOTE_60']")
        assert element is not None
        assert element.find('EffectLayer/Effect').get('startTime')==str(start)
    for role in ('lead','harmony'):
        singer=next(m for m in g.models if m.details.get('review_role')==role)
        static_materials(type('G',(),{'models':[singer]})())
        idle=set().union(*(set(v) for k,v in singer.submodels.items() if k.startswith('ARM_') and k.endswith('_IDLE')))
        visible=set().union(*(set(v) for k,v in singer.submodels.items() if k.startswith('STATIC_RGB_')))
        assert idle<=visible
        mouths=set().union(*(set(v) for k,v in singer.submodels.items() if k.startswith('MOUTH_')))
        assert not mouths&visible


def test_sections_and_drum_components_change_composition_without_inventing_events():
    from tools.source_spatial_direction import section_strategy
    assert section_strategy('PRE_CHORUS','keyboardist')['name']=='ascending'
    g=build_layout(10)
    m=next(m for m in g.models if m.name=='MOIRE_LINE_LATTICE_0')
    role=m.details['musical_role']
    source=[dict(start_ms=103,end_ms=303,pitch_midi=60,velocity=.8,section='verse'),
            dict(start_ms=1003,end_ms=1203,pitch_midi=60,velocity=.8,section='chorus'),
            dict(start_ms=2003,end_ms=2203,pitch_midi=108,velocity=.8,section='breakdown')]
    events=schedule(m,{'cues':{role:source}},{},3000)
    assert {e['strategy'] for e in events}=={'note_trace','wide_response','sparse'}
    assert {e['source_start_ms'] for e in events}=={103,1003,2003}
    assert len([e for e in events if e['source_start_ms']==2003])==1
    assert all(e['start_ms']==e['source_start_ms']+e['propagation_delay_ms'] for e in events)
    drum=next(m for m in build_layout(6).models if m.details.get('percussion_component')=='kick')
    hits=[dict(start_ms=100,end_ms=200,kind='kick'),dict(start_ms=400,end_ms=500,kind='snare')]
    assert {e['source_kind'] for e in schedule(drum,{'cues':{'drummer':hits}},{},1000)}=={'kick'}
    assert schedule(drum,{'cues':{'drummer':[]}},{},1000)==[]
