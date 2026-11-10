from pathlib import Path
import shutil
import xml.etree.ElementTree as ET
import numpy as np
from core.gui_options import OPTIONS, resolve_layout
from core.gui_band import configure
from core.preview_geometry import custom_nodes
from tools.preview_renderer import parse_models, SequenceData, EffectRecord, build_leaf_intensity_matrix

ROOT=Path(__file__).resolve().parents[1]


def test_default_sampler_has_four_comparisons_and_exact_six_roles():
    layout=resolve_layout(ROOT,OPTIONS['default_layout'])
    models=ET.parse(layout).findall('models/model')
    assert len({m.get('HelixSamplerPanel') for m in models})==4
    assert {m.get('HelixBandRole') for m in models if m.get('HelixGuiBand')}=={'drummer','bass','guitar','piano','lead','harmony'}
    assert not any('XYLO' in m.get('name','').upper() for m in models)
    # AC banks retain their actual node-address counts, rather than bulb counts.
    from core.model_parser import parse_layout
    parsed=parse_layout(layout)
    assert sum(parsed.models[m.get('name')].total_pixels for m in models if m.get('HelixSamplerPanel')=='16 channel AC')==16
    assert sum(parsed.models[m.get('name')].total_pixels for m in models if m.get('HelixSamplerPanel')=='64 channel AC')==64


def test_authored_nodes_keep_order_holes_and_repeated_circuit_locations():
    model=ET.fromstring('<model CustomModelCompressed="1,0,0,0;2,2,4,0;1,1,2,0" ScaleX="2" ScaleY="3" WorldPosX="10"/>')
    nodes=custom_nodes(model)
    assert nodes==[(1,(6.,3.,0.)),(2,(14.,-3.,0.)),(1,(10.,0.,0.))]


def test_band_on_adds_real_members_without_moving_imported_channels(tmp_path):
    path=tmp_path/'layout.xml'
    path.write_text('<xrgb><models><model name="Roof" DisplayAs="Single Line" parm1="1" parm2="10" StringType="RGB Nodes" StartChannel="73"/></models></xrgb>')
    original=ET.parse(path).find('models/model').attrib.copy()
    result=configure(path,None,ROOT,enabled=True)
    assert len(result['added_models'])==6
    models=ET.parse(path).findall('models/model')
    assert models[0].attrib==original
    assert all(int(m.get('StartChannel'))>102 for m in models[1:])
    assert configure(path,None,ROOT,enabled=True)['added_models']==[]
    configure(path,None,ROOT,enabled=False)
    assert [m.attrib for m in ET.parse(path).findall('models/model')]==[original]


def test_faces_light_only_requested_authored_nodes_and_singer(tmp_path):
    layout=tmp_path/'layout.xml'
    layout.write_text('''<xrgb><models><model name="Lead" DisplayAs="Custom" CustomModelCompressed="1,0,0,0;2,0,4,0;3,3,2,0" parm1="5" parm2="4"><faceInfo Name="Phones" Type="NodeRange" Mouth-AI="2" Mouth-rest="3"/></model></models></xrgb>''')
    geom=parse_models(layout)
    effect=EffectRecord('Faces',0,500,'E_CHOICE_Faces_FaceDefinition=Phones,E_CHOICE_Faces_Phoneme=AI')
    seq=SequenceData(1000,{'Lead':[effect]}, {})
    names,values=build_leaf_intensity_matrix(geom,seq,10)
    alias=geom.face_targets[('Lead','Phones','ai')]
    assert geom.leaf_models[alias].points==((2.,1.5),)
    assert geom.leaf_models[alias].discrete_nodes
    assert np.all(values[names.index('Lead')]==0)
    assert np.all(values[names.index(alias),:5]==1)
    assert np.all(values[names.index(alias),5:]==0)


def test_unknown_native_effect_never_becomes_a_full_brightness_placeholder():
    from tools.preview_renderer import LayoutData,ModelGeom,unsupported_effects
    geom=LayoutData({'Prop':ModelGeom('Prop',0,0,1,1,((0,0),(1,1)),'Single Line',(255,255,255))},{},(0,0,1,1))
    sequence=SequenceData(1000,{'Prop':[EffectRecord('UnsupportedNativeFX',0,1000)]},{})
    assert unsupported_effects(sequence)==['UnsupportedNativeFX']
    _,values=build_leaf_intensity_matrix(geom,sequence,15)
    assert not np.any(values)


def test_sampler_exports_real_source_event_windows_for_ac_and_rgb(tmp_path):
    import json
    from core.gui_band import apply_performance
    layout=tmp_path/'xlights_rgbeffects.xml'
    shutil.copyfile(resolve_layout(ROOT,'layout_sampler'),layout)
    sequence=tmp_path/'song.xsq'
    sequence.write_text('<xsequence><head><sequenceDuration>1</sequenceDuration></head><ColorPalettes/><EffectDB/><DisplayElements/><ElementEffects/></xsequence>')
    event=dict(start_ms=100,end_ms=300,pitch_midi=60,velocity=.8,section='verse',kind='note')
    sequence.with_name(sequence.stem+'.snowman_band.json').write_text(json.dumps({'cues':{
        'guitarist':[event],'bassist':[event],'keyboardist':[event],'drummer':[]}}))
    apply_performance(sequence,layout)
    root=ET.parse(sequence)
    events=[(e.get('name'),x) for e in root.findall('ElementEffects/Element') for x in e.findall('.//Effect')
            if x.get('sourceMethod')=='gui_sampler_retained_band_plan']
    assert {name.split('_')[1] for name,e in events}=={'1','2','4','7'}
    assert all(e.get('name')=='On' and e.get('sourceStartMs')=='100' and e.get('sourceEndMs')=='300' for _,e in events)


def test_historical_empty_band_stubs_cannot_block_canonical_band_selection(tmp_path):
    layout=tmp_path/'layout.xml'
    layout.write_text('<xrgb><models><model name="Roof" DisplayAs="Single Line" StartChannel="7" parm2="10"/>'
                      '<model name="HX_SNOWMAN_DRUMMER_BODY" DisplayAs="Custom" CustomWidth="12" CustomHeight="12" StartChannel="99"/></models></xrgb>')
    report=configure(layout,None,ROOT,enabled=True)
    assert report['replaced_missing_geometry_models']==['HX_SNOWMAN_DRUMMER_BODY']
    models=ET.parse(layout).findall('models/model')
    assert models[0].get('StartChannel')=='7'
    assert len([m for m in models if m.get('HelixGuiBand')])==6
