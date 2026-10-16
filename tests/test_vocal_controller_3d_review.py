import numpy as np
import pytest
from core.output_capabilities import detect_output, encode_output, resolve_layout_outputs
from music.vocal_roles import VoiceTrack, route_voices


def tone(frequency, start=0, end=2, gain=.2):
    t=np.arange(32000)/16000;y=np.zeros(len(t),'f4');mask=(t>=start)&(t<end)
    y[mask]=gain*(np.sin(t[mask]*2*np.pi*frequency)+.25*np.sin(t[mask]*4*np.pi*frequency))
    return y


def test_mixed_vocal_bus_is_not_cast_as_duet():
    y=tone(180)+tone(267)
    lanes,modes,report=route_voices([VoiceTrack('mixed',y,16000)],duration=2)
    assert len(lanes)==1 and lanes[0]['role']=='lead'
    assert not report['voice_identity_resolved'] and 'duet' not in modes


def test_distinct_voice_tracks_route_duet_and_background_independently():
    tracks=[VoiceTrack('a',tone(180),16000,'individual','lead'),
            VoiceTrack('b',tone(267,.6,1.7),16000,'individual','second'),
            VoiceTrack('choir',tone(330,1.2,1.7,.06),16000,'ensemble')]
    lanes,modes,report=route_voices(tracks,duration=2)
    assert [x['role'] for x in lanes]==['lead','second','background']
    assert 'duet' in modes and 'lead_background' in modes
    assert lanes[1]['energy'][:10].max()==0 and lanes[2]['energy'][:20].max()==0
    assert report['voice_identity_resolved']


def test_gain_delayed_duplicate_does_not_create_a_singer():
    y=tone(180,.2,1.7);copy=np.r_[np.zeros(160),y[:-160]]*.6
    lanes,modes,report=route_voices([VoiceTrack('a',y,16000,'individual'),VoiceTrack('copy',copy,16000,'individual')],duration=2)
    assert len(lanes)==1 and report['input_tracks']['copy']['duplicate_of']=='a'


def test_verified_unvoiced_consonant_keeps_its_timing():
    cues=({'start':.5,'end':.65,'shape':'FV','verified':True},)
    lanes,_,_=route_voices([VoiceTrack('a',tone(180,0,.4),16000,'individual',phonemes=cues)],duration=2)
    assert (lanes[0]['shapes'][10:13]==5).all()
    assert lanes[0]['energy'][14]==0
    with pytest.raises(ValueError):
        route_voices([VoiceTrack('a',tone(180),16000,phonemes=({'start':0,'end':1,'shape':'FV'},))],duration=2)


def test_controller_type_not_lor_transport_or_sixteen_ports():
    assert detect_output({}, {'Type':'LOR','Channels':'16'}).mode=='unknown'
    assert detect_output({}, {'Model':'CTB16PCg3'}).mode=='ac16'
    assert detect_output({}, {'Model':'Pixie16','Type':'LOR'}).mode=='pixel'
    with pytest.raises(ValueError):detect_output({'StringType':'RGB Nodes'},{'Model':'CTB16PC'})
    with pytest.raises(ValueError):encode_output(np.zeros((1,17)),'ac16')
    assert encode_output(np.array([[.5,1]]),'ac16').tolist()==[[128,255]]


def test_mixed_layout_resolves_per_controller():
    import xml.etree.ElementTree as ET
    l=ET.fromstring('<xrgb><models><model name="snow" Controller="AC"/><model name="tree" Controller="PIX" StringType="RGB Nodes"/></models></xrgb>')
    n=ET.fromstring('<Networks><Controller Name="AC" Model="CTB16PC"/><Controller Name="PIX" Model="Pixie16"/></Networks>')
    modes=resolve_layout_outputs(l,n);assert modes['snow']['mode']=='ac16' and modes['tree']['mode']=='pixel'


def test_native_band_has_seven_standalone_ac_models_and_ten_separate_mouths():
    from models.native_review_band import add_band, ac_variant, allocate, VISEMES
    from models.ultimate_showcase import Garden
    g=Garden();add_band(g);assert len(g.models)==7
    a=Garden();a.models=[ac_variant(m) for m in g.models];allocate(a)
    for i,m in enumerate(a.models):
        assert m.channels<=16 and m.start==i*16+1
        assert detect_output(m.attrs).mode=='ac16'
        assert "WorldPosZ" in m.attrs
        if m.details["review_role"]!="drummer":assert np.ptp(m.points[:,2])>0
        assert max(m.details['point_circuits'])<=16
        if m.details['review_role'] in ('lead','harmony'):
            channels=[m.submodels['MOUTH_'+v][0] for v in VISEMES]
            assert len(set(channels))==10
            assert all(c in m.details['point_circuits'] for c in channels)


def test_every_hero_rung_is_complete_disjoint_and_absolutely_pitched():
    from models.review_spatial_worlds import build_world
    g=build_world(0);hero=next(m for m in g.models if m.details.get('midi_rungs'))
    all_nodes=[]
    for pitch in range(21,109):
        nodes=hero.submodels[f'KEY_MIDI_{pitch:03d}'];all_nodes+=nodes
        assert len(nodes)>3
        assert np.ptp(hero.points[np.array(nodes)-1,1])<1e-6
    assert len(set(all_nodes))==len(all_nodes)==len(hero.submodels['RUNGS'])
    assert sum(bool(m.details.get('spiral_tree')) for m in g.models)>=24
    assert any(m.details.get('moire') for m in g.models)
