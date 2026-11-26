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


def test_technical_worlds_have_separate_actual_percussion_owners():
    for number in (9,10,11):
        g=build_layout(number)
        components={m.details.get('percussion_component') for m in g.models if role_for(m)=='drummer'}
        assert {'kick','snare'}<=components
        assert all(m.details.get('source_display_floor')==.5 for m in g.models)
    g=build_layout(10)
    original_planes=[m for m in g.models if 'MOIRE_LAYER' in m.name]
    assert len({role_for(m) for m in original_planes})==4


def test_native_surface_never_bridges_short_source_rests():
    g=build_layout(10);m=next(m for m in g.models if m.name=='MOIRE_LINE_LATTICE_0')
    sequence=NativeSequence(g,2,'','source rest')
    cues=[dict(start_ms=a,end_ms=b,pitch_midi=60,velocity=.8,section='verse',
               confidence=.73,source='retained_notes') for a,b in [(0,500),(600,1100)]]
    report=export_model(sequence,m,dict(cues={'keyboardist':cues}),{},g.palette)
    bars=[e for e in sequence.root.findall('./ElementEffects//Effect') if e.get('name')=='Bars']
    assert {(e.get('sourceStartMs'),e.get('sourceEndMs')) for e in bars}=={('0','500'),('600','1100')}
    assert all(e['source_confidence']==.73 for e in report['events'])
    assert all(e['source_method']=='retained_notes' for e in report['events'])


def test_sustained_note_cannot_hide_a_new_section_surface():
    from tools.source_spatial_direction import supported_phrases
    events=[dict(source_start_ms=0,source_end_ms=1200,section='verse'),
            dict(source_start_ms=600,source_end_ms=1800,section='chorus')]
    assert supported_phrases(events)==[[0,600,'verse'],[600,1800,'chorus']]


def test_advanced_customer_routes_move_between_physical_props_without_global_broadcast():
    from tools.source_role_routing import configure_advanced_spatial_routes,route_event
    g=build_layout(11)
    configure_advanced_spatial_routes(g.models)
    members=[m for m in g.models if m.details.get('source_route_bank','').startswith('advanced_spatial_keyboardist')]
    assert len(members)>=3
    assert len({m.details['source_route_rank'] for m in members})==len(members)
    cue=dict(start_ms=100,end_ms=600,pitch_midi=62,velocity=.8)
    strategy=dict(name='note_trace',direction=1)
    active=[m for m in members if route_event(m,cue,0,strategy) is not None]
    assert 0<len(active)<len(members)
    original={m.name:m.details['source_route_rank'] for m in members}
    g.models.reverse()
    configure_advanced_spatial_routes(g.models)
    assert {m.name:m.details['source_route_rank'] for m in members}==original
    starter=build_layout(4)
    configure_advanced_spatial_routes(starter.models)
    assert not any(m.details.get('advanced_spatial_routing') for m in starter.models)
    legacy=build_layout(1)
    configure_advanced_spatial_routes(legacy.models)
    assert not any(m.details.get('advanced_spatial_routing') for m in legacy.models)


def test_shared_onset_index_preserves_exact_schedule():
    from tools.source_spatial_direction import onset_index
    from tools.source_role_routing import configure_advanced_spatial_routes
    g=build_layout(11)
    configure_advanced_spatial_routes(g.models)
    cues=[dict(start_ms=a,end_ms=a+300,pitch_midi=p,velocity=.8,section=section)
          for a,p,section in [(500,60,'verse'),(100,48,'verse'),(500,64,'verse'),(900,72,'chorus')]]
    plan=dict(cues={'keyboardist':cues})
    shared={'keyboardist':onset_index(cues)}
    members=[m for m in g.models if role_for(m)=='keyboardist']
    assert members
    for m in members:
        assert schedule(m,plan,{},2000)==schedule(m,plan,{},2000,shared_onsets=shared)


def test_advanced_bank_travel_fits_short_real_note_without_changing_legacy_ac():
    from tools.source_role_routing import route_event

    cue = dict(start_ms=100, end_ms=160, pitch_midi=28)
    strategy = dict(name='wide_response', direction=1)
    def prop(rank, advanced):
        return SimpleNamespace(details=dict(
            source_route_count=100, source_route_rank=rank,
            musical_role='bassist', advanced_spatial_routing=advanced))
    delays = [route_event(prop(rank, True), cue, 0, strategy) for rank in range(100)]
    assert sum(delay is not None for delay in delays) == 35
    assert delays[0] == 0
    assert max(delay for delay in delays if delay is not None) <= 29
    assert delays[35] is None
    assert route_event(prop(1, False), cue, 0, strategy) == 35
    assert route_event(prop(1, True), dict(cue, end_ms=5000), 0, strategy) == 35
    assert route_event(prop(99, True), dict(cue, synchronized_accent=True), 0, strategy) == 0


def test_advanced_surface_uses_distinct_native_bars_directions_by_section():
    from tools.source_spatial_direction import native_bars_direction,section_strategy
    g=build_layout(10)
    model=next(m for m in g.models if m.name=='MOIRE_LINE_LATTICE_0')
    model.details['spatial_direction']=1
    model.zone='OPTICAL'
    assert native_bars_direction(model,section_strategy('verse','keyboardist'))=='Left'
    assert native_bars_direction(model,section_strategy('pre_chorus','keyboardist'))=='H-expand'
    assert native_bars_direction(model,section_strategy('chorus','keyboardist'))=='Alternate Right'
    model.details['spatial_direction']=-1
    assert native_bars_direction(model,section_strategy('pre_chorus','keyboardist'))=='H-compress'
    assert native_bars_direction(model,section_strategy('chorus','keyboardist'))=='Alternate Left'
    model.details['spatial_direction']=1
    seq=NativeSequence(g,3,'','native bars directions')
    cues=[dict(start_ms=a,end_ms=b,pitch_midi=60,velocity=.8,section=section)
          for a,b,section in [(0,600,'verse'),(600,1200,'pre_chorus'),
                              (1200,1800,'chorus'),(1900,2500,'breakdown')]]
    export_model(seq,model,dict(cues={'keyboardist':cues}),{},g.palette)
    settings=seq.root.findall('./EffectDB/Effect')
    bars=[e for e in seq.root.findall('./ElementEffects//Effect') if e.get('name')=='Bars']
    assert [e.get('nativeBarsDirection') for e in bars]==['Left','H-expand','Alternate Right']
    for e in bars:
        assert 'E_CHOICE_Bars_Direction='+e.get('nativeBarsDirection')+',' in settings[int(e.get('ref'))].text
    assert all(int(e.get('endTime'))<=1800 for e in bars)
    simple=SimpleNamespace(zone='HOUSE',details={})
    assert native_bars_direction(simple,section_strategy('pre_chorus','keyboardist'))=='Left'


def test_native_surface_buffer_preserves_physical_rows_and_every_channel():
    from tools.build_helpers.ultimate_showcase import model_xml,surface_buffer_rows
    g=build_layout(10)
    model=next(m for m in g.models if m.name=='MOIRE_LINE_LATTICE_0')
    seq=NativeSequence(g,2,'','physical buffer')
    plan={'cues':{'keyboardist':[dict(start_ms=100,end_ms=700,pitch_midi=60,velocity=.8)]}}
    export_model(seq,model,plan,{},g.palette)
    root=model_xml(model)
    surface=root.find("./subModel[@name='SPATIAL_SURFACE']")
    rows=[list(map(int,surface.get(key).split(','))) for key in
          sorted((k for k in surface.attrib if k.startswith('line')),key=lambda k:int(k[4:]))]
    assert len(rows)>1 and {len(row) for row in rows}=={240}
    assert sorted(n for row in rows for n in row)==model.submodels['SPATIAL_SURFACE']
    assert all(np.all(np.diff(model.points[np.asarray(row)-1,0])>=0) for row in rows)
    assert np.all(np.diff([model.points[np.asarray(row)-1,1].mean() for row in rows])>0)
    assert root.find("./subModel[@name='ROW_00']").get('line1') is None
    assert surface_buffer_rows(model,model.submodels['SPATIAL_SURFACE'][:-1])==[]
    assert any(e.get('name')=='Bars' for e in seq.root.findall('./ElementEffects//Effect'))


def test_advanced_combined_delay_budget_preserves_short_notes_and_rests():
    m=SimpleNamespace(name='DISTANT_GRID',zone='THREE_D_GRID',kind='pixel',
        points=np.asarray([[x,0,0] for x in range(12)],dtype=float),
        submodels={f'ROW_{i:02}':[i+1] for i in range(12)},
        details=dict(musical_role='keyboardist',advanced_showcase_clock=True,
                     propagation_delay_ms=360,source_route_count=12,
                     source_route_rank=11,advanced_spatial_routing=True))
    cue=dict(start_ms=100,end_ms=160,pitch_midi=48,velocity=.9,section='chorus')
    events=schedule(m,dict(cues={'keyboardist':[cue]}),{},1000)
    assert len(events)==5
    assert all(100<=e['start_ms']<=129 and e['end_ms']==160 for e in events)
    assert [e['start_ms'] for e in events]==sorted(e['start_ms'] for e in events)
    assert len({e['part'] for e in events})==5
    assert all(e['source_start_ms']==100 and e['source_end_ms']==160 for e in events)
    m.details['source_route_rank']=5
    assert not schedule(m,dict(cues={'keyboardist':[cue]}),{},1000)
    assert not schedule(m,dict(cues={'keyboardist':[]}),{},1000)


def test_long_advanced_note_retains_authored_delay_and_legacy_is_unchanged():
    m=SimpleNamespace(name='DEPTH_GRID',zone='DEPTH',kind='pixel',
        points=np.asarray([[x,0,0] for x in range(4)],dtype=float),
        submodels={f'ROW_{i}':[i+1] for i in range(4)},
        details=dict(musical_role='bassist',advanced_showcase_clock=True,
                     propagation_delay_ms=120))
    plan=dict(cues={'bassist':[dict(start_ms=100,end_ms=1100,section='verse',pitch_midi=40)]})
    events=schedule(m,plan,{},2000)
    assert [e['propagation_delay_ms'] for e in events]==[120,170]
    assert all(e['end_ms']==1100 for e in events)
    m.details.pop('advanced_showcase_clock')
    assert [e['end_ms'] for e in schedule(m,plan,{},2000)]==[1220,1270]
