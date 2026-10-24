from types import SimpleNamespace
import numpy as np
from models.approval_layouts import build_layout
from tools.source_spatial_direction import role_for,schedule,export_model
from tools.build_snowman_ensemble import NativeSequence


def test_roles_do_not_depend_on_model_insertion_order():
    g=build_layout(6)
    roles={m.name:role_for(m) for m in g.models}
    g.models.reverse()
    assert {m.name:role_for(m) for m in g.models}==roles
    assert roles['HOME_EAVE']=='bassist'
    assert roles['HOME_ROOF']=='guitarist'
    assert roles['HOME_WINDOW_-1']=='harmony'


def test_real_pitch_selects_position_and_authored_depth_preserves_source_clock():
    g=build_layout(11);m=next(m for m in g.models if m.name=='PERSPECTIVE_BOX_3')
    plan=dict(cues={'bassist':[dict(start_ms=100,end_ms=400,pitch_midi=30,velocity=.7),
                              dict(start_ms=900,end_ms=1100,pitch_midi=90,velocity=.5)]})
    events=schedule(m,plan,{},2000)
    assert {e['source_start_ms'] for e in events}=={100,900}
    assert all(e['start_ms']==e['source_start_ms']+e['propagation_delay_ms'] for e in events)
    assert events[0]['part']!=events[2]['part']
    assert not schedule(m,dict(cues={'bassist':[]}),{},2000)


def test_matrix_uses_supported_native_bars_and_reports_source_roles():
    g=build_layout(10);m=next(m for m in g.models if m.name=='MOIRE_LINE_LATTICE_0')
    sequence=NativeSequence(g,2,'','spatial test')
    plan=dict(cues={'keyboardist':[dict(start_ms=100,end_ms=700,pitch_midi=60,velocity=.8)]})
    report=export_model(sequence,m,plan,{},g.palette)
    assert report['role']=='keyboardist'
    effects=sequence.root.findall('./ElementEffects//Effect')
    assert any(e.get('name')=='Bars' and e.get('sourceStartMs')=='100' for e in effects)
    assert all(e.get('sourceMethod') for e in effects)


def test_optical_layers_and_depth_corridor_have_distinct_roles_and_geometry():
    g=build_layout(10)
    layers=[m for m in g.models if m.name.startswith('MOIRE_LINE_LATTICE_')]
    assert len(layers)==3
    assert len({m.details['line_spacing_ft'] for m in layers})==3
    assert len({role_for(m) for m in layers})==3
    corridor=[m for m in build_layout(11).models if m.name.startswith('PERSPECTIVE_BOX_')]
    assert len(corridor)==8
    assert len({m.details['propagation_delay_ms'] for m in corridor})==8


def test_missing_sampler_voice_evidence_abstains_instead_of_using_other_audio():
    from tools.source_spatial_direction import voice_events
    assert voice_events({},'estimated_backing')==[]
    assert voice_events({},'estimated_lead')==[]
