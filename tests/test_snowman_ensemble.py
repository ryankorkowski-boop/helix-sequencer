from pathlib import Path
import json
import xml.etree.ElementTree as ET
import numpy as np
import pytest

from models.snowman_ensemble import build_ensemble
from tools.render_drummer_v3_preview import _expand_ranges
from tools.align_snowman_lyrics import compile_mouths,pronunciation,select_words
from tools.build_snowman_ensemble import NativeSequence,source_curves

ROOT=Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('variant',['band','faces'])
def test_preserved_drummer_and_disjoint_native_channels(variant):
    g=build_ensemble(variant);drummer=g.models[0]
    original=ET.parse(ROOT/'fixtures/band_geometry/models/HX_SNOWMAN_DRUMMER_V3.xmodel').getroot()
    assert drummer.attrs['CustomModel']==original.get('CustomModel')
    assert len(drummer.points)==6912
    for sub in original.findall('subModels/subModel'):
        assert set(drummer.submodels[sub.get('name')])==_expand_ranges(sub.get('line0'))
    start=1
    for model in g.models:
        assert model.start==start;start+=model.channels
        assert all(1<=node<=len(model.points) for ids in model.submodels.values() for node in ids)
        assert len(set(map(tuple,model.points)))==len(model.points)


def test_six_members_and_real_depth():
    g=build_ensemble();roles={m.details.get('performer') for m in g.models if m.details.get('performer')}
    assert roles=={'bassist','guitarist','singer','female_singer','keyboardist'}
    for model in g.models:
        if model.details.get('performer'):
            assert np.ptp(model.points[:,2])>=20
            assert 'ARM_ACTIVE' in model.submodels
            mouths=set().union(*(set(ids) for part,ids in model.submodels.items() if part.startswith('MOUTH_')))
            fixed=set().union(*(set(ids) for part,ids in model.submodels.items() if not part.startswith('MOUTH_')))
            assert not mouths & fixed


def test_words_not_character_grid_and_no_overlapping_mouth_intervals():
    dictionary={'love':[['L','AH1','V']],'boom':[['B','UW1','M']]}
    words=[dict(word='love',start=1,end=1.3,probability=.9),dict(word='boom',start=1.2,end=1.6,probability=.8)]
    mouths=compile_mouths(words,dictionary)
    assert [m['phoneme'] for m in mouths[:3]]==['L','AH','FV']
    assert all(m['start_ms']%50==m['end_ms']%50==0 for m in mouths)
    assert all(a['end_ms']<=b['start_ms'] for a,b in zip(mouths,mouths[1:]))
    assert all(m['pronunciation_source']=='cmu_pronunciation_dictionary' for m in mouths)


def test_sung_ba_does_not_use_bachelor_of_arts_dictionary_pronunciation():
    shapes,method=pronunciation('ba',{'ba':[['B','IY1','EY1']]})
    assert shapes==['MBP','AH']
    assert method=='nonlexical_sung_syllable_rule'


def test_recognized_practice_vowels_keep_their_low_confidence():
    word=dict(word='Ah',start=1,end=2,probability=.08)
    assert select_words([word])==[]
    assert select_words([word],phoneme_exercise=True)==[word]


def test_instrument_silence_stays_idle_and_source_onset_is_not_beat_grid():
    events=[dict(start_ms=350,duration_ms=150,midi=45,intensity=.8)]
    active,notes=source_curves(events,30,4)
    assert not active[:7].any() and not active[10:].any()
    assert list(np.flatnonzero(active))==[7,8,9]
    assert notes[1][7]==92 and not notes[0].any()


def test_native_references_and_out_of_song_clipping(tmp_path):
    g=build_ensemble();seq=NativeSequence(g,1.01,'media/song.mp3','test')
    assert seq.duration==1050
    seq.effect(g.models[0],'BODY_KEEPALIVE',0,5000,'#FFFFFF')
    seq.write(tmp_path/'test.xsq')
    root=ET.parse(tmp_path/'test.xsq').getroot()
    effect=root.find('./ElementEffects/Element/SubModelEffectLayer/Effect')
    assert effect.get('endTime')=='1050'
    assert root.find('head/mediaFile').text=='media/song.mp3'
    assert root.find('ColorPalettes/ColorPalette').text.endswith('C_CHECKBOX_Palette1=1')
    with pytest.raises(ValueError):seq.effect(g.models[0],'made-up-target',0,500,'#FFFFFF')


@pytest.mark.parametrize('variant',['band','faces'])
def test_reusable_native_face_definitions_map_standard_visemes_to_real_nodes(variant):
    from models.snowman_face_contract import VISEME_TO_SHAPE,FACE_NAME
    for model in build_ensemble(variant).models:
        if 'MOUTH_AH' not in model.submodels:continue
        attrs=next(attributes for tag,attributes in model.children if tag=='faceInfo')
        assert attrs['Name']==FACE_NAME and attrs['Type']=='NodeRange'
        for native,shape in VISEME_TO_SHAPE.items():
            assert _expand_ranges(attrs['Mouth-'+native])==set(model.submodels['MOUTH_'+shape])
