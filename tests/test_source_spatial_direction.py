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


def test_native_ultimate_families_do_not_all_fall_back_to_bass():
    from tools.source_spatial_direction import parts_for
    g=build_layout(12);models={m.name:m for m in g.models}
    assert role_for(models['HX_SPIRAL_W_1_1'])=='guitarist'
    assert role_for(models['HX_DNA_TOWER_WEST'])=='keyboardist'
    assert role_for(models['HX_AURORA_HORIZONTAL'])=='keyboardist'
    assert role_for(models['HX_SOLAR_SPINNER_-1'])=='drummer'
    assert role_for(models['HX_NORTH_STAR'])=='lead'
    matrix=models['HX_AURORA_HORIZONTAL'];parts=parts_for(matrix)
    assert len(parts)>1 and all(p.startswith('ROW_') for p in parts)
    assert sorted(n for p in parts for n in matrix.submodels[p])==list(range(1,len(matrix.points)+1))
    hero=models['HX_DNA_CATHEDRAL']
    assert hero.details['keyboard_pitch_rungs']
    assert all(hero.submodels[f'KEY_MIDI_{p:03}'] for p in range(21,109))


def test_section_changes_split_surface_phrases_and_change_pixel_interpretation():
    g=build_layout(10);m=next(m for m in g.models if m.name=='MOIRE_LINE_LATTICE_0')
    sequence=NativeSequence(g,3,'','section transition')
    cues=[dict(start_ms=a,end_ms=b,pitch_midi=60,velocity=.8,section=section)
          for a,b,section in [(0,600,'verse'),(600,1200,'pre_chorus'),
                              (1200,1800,'chorus'),(1800,2400,'breakdown')]]
    report=export_model(sequence,m,dict(cues={'keyboardist':cues}),{},g.palette)
    assert len({e['color'] for e in report['events']})==3
    effects=sequence.root.findall('./ElementEffects//Effect')
    bars=[e for e in effects if e.get('name')=='Bars']
    assert {(e.get('sourceStartMs'),e.get('sourceEndMs'),e.get('sourceSection')) for e in bars}=={
        ('0','600','verse'),('600','1200','pre_chorus'),('1200','1800','chorus')}
    assert {e['source_start_ms'] for e in report['events']}=={0,600,1200,1800}
    assert not any(e.get('sourceSection')=='breakdown' for e in bars)


def test_section_colors_never_recolor_a_fixed_ac_circuit():
    g=build_layout(1);m=next(m for m in g.models if m.kind=='ac')
    role=role_for(m);sequence=NativeSequence(g,2,'','fixed color')
    cues=[dict(start_ms=a,end_ms=a+400,pitch_midi=60,velocity=.8,section=section)
          for a,section in [(0,'verse'),(500,'pre_chorus'),(1000,'chorus')]]
    report=export_model(sequence,m,dict(cues={role:cues}),{},g.palette)
    assert len({e['color'] for e in report['events']})==1
    expected={'Single Color Red':'#FF4040','Single Color Green':'#40FF60','Single Color White':'#FFFFFF'}
    assert {e['color'] for e in report['events']}=={expected[m.attrs['StringType']]}
