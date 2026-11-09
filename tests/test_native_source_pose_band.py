import numpy as np
import pytest
from tools.native_source_pose_band import select_states,vertices,select_cast,configure_native_keyboard_motion,native_motion_rigs
from models.band_performance_scene import line_matrix
from tools.native_source_pose_band import retain_native_materials


def test_states_are_actual_source_frames_and_preserve_frame_clock():
    poses=np.zeros((720,3,3),'f4')
    poses[120:240,:,0]=1;poses[240:360,:,1]=2;poses[360:,:,2]=3
    selected,states,error=select_states(poses,8)
    assert len(states)==720 and len(selected)==4 and error==0
    np.testing.assert_array_equal(poses[selected][states],poses)
    assert np.flatnonzero(np.diff(states)).tolist()==[119,239,359]


def test_more_states_reduce_measured_geometry_error_deterministically():
    t=np.linspace(0,2*np.pi,720)
    p=np.stack((np.sin(t),np.cos(t),t/10),axis=1)[:,None,:]
    a=select_states(p,8);b=select_states(p,24);c=select_states(p,24)
    assert b[2]<=a[2]
    np.testing.assert_array_equal(b[0],c[0]);np.testing.assert_array_equal(b[1],c[1])


def test_source_rod_endpoints_reach_the_authored_contact_plane():
    a=np.array([1.,2.,3.]);b=np.array([4.,6.,8.])
    pts=vertices(dict(kind='cylinder',matrix=line_matrix(a,b,.04)))
    direction=(b-a)/np.linalg.norm(b-a)
    projection=(pts-a)@direction
    assert projection.min()==pytest.approx(0,abs=1e-5)
    assert projection.max()==pytest.approx(np.linalg.norm(b-a),abs=1e-5)


@pytest.mark.parametrize('poses,limit',[(np.zeros((0,3,3)),8),
    (np.ones((5,3)),8),(np.full((5,3,3),np.nan),8),
    (np.zeros((5,3,3)),0),(np.zeros((5,3,3)),129)])
def test_invalid_pose_input_rejects(poses,limit):
    with pytest.raises(ValueError):select_states(poses,limit)



def test_native_default_cast_has_one_pitched_member_and_legacy_stays_opt_in():
    from types import SimpleNamespace
    roles=('drummer','bass','guitar','piano','xylophone','lead','harmony')
    models=[SimpleNamespace(name='HX_SNOW_'+role.upper(),details={'review_role':role})
            for role in roles]
    default=select_cast(models)
    assert len(default)==6
    assert {m.details['review_role'] for m in default} == set(roles)-{'xylophone'}
    assert [m.name for m in select_cast(models,legacy_xylophone=True)] == [
        m.name for m in models
    ]
    assert len(models)==7  # no mutation of legacy catalog


def test_invalid_native_cast_fails_closed_before_any_export():
    from types import SimpleNamespace
    import pytest
    roles=('drummer','bass','guitar','piano','lead','harmony')
    models=[SimpleNamespace(details={'review_role':role}) for role in roles]
    with pytest.raises(ValueError,match='cast'):
        select_cast(models[:-1])
    with pytest.raises(ValueError,match='cast'):
        select_cast(models,legacy_xylophone=True)


def test_native_pianist_uses_short_fixed_links_without_retiming_source_notes():
    from types import SimpleNamespace
    from music.note_events import NoteEvent
    events=[NoteEvent(.173,.420,64,.8,source='piano')]
    left=dict(role='piano',side='left',link_lengths=(.80,.78))
    right=dict(role='piano',side='right',link_lengths=(.80,.78))
    scene=SimpleNamespace(rigs=[left,right])
    class Performer:
        keyboard_events=events
        count=0
        def _install_keyboard_events(self,ev):
            assert ev is self.keyboard_events
            self.count+=1
            self.keyboard_motion_report=dict(left={'contact_frames':7},
                                              right={'contact_frames':6})
    performer=Performer()
    proof=configure_native_keyboard_motion(scene,performer)
    assert performer.count==1
    assert left['link_lengths']==right['link_lengths']==(.52,.50)
    assert scene.legacy_mallet_player is False
    assert proof['maximum_step']==.030 and proof['maximum_acceleration']==.010
    assert (events[0].start,events[0].end,events[0].pitch)==(.173,.420,64)
    assert proof['keyboard_contact_report']['left']['contact_frames']==7


def test_native_legacy_cast_keeps_original_arm_length_and_source_clock():
    from types import SimpleNamespace
    original=dict(role='piano',side='left',link_lengths=(.80,.78))
    scene=SimpleNamespace(rigs=[original])
    class Performer:
        def _install_keyboard_events(self,ev):
            raise AssertionError('Legacy performance must not be modified')
    proof=configure_native_keyboard_motion(scene,Performer(),legacy_xylophone=True)
    assert proof['short_piano_arms'] is False
    assert original['link_lengths']==(.80,.78)
    assert not hasattr(scene,'legacy_mallet_player')


def test_native_source_pose_samples_only_visible_character_motion():
    from types import SimpleNamespace
    scene=SimpleNamespace(
        rigs=[dict(role='piano',side='left',ids=(1,2,3)),
              dict(role='piano',side='right',ids=(4,5,6)),
              dict(role='xylophone',side='left',ids=(7,8,9),mallet_ids=(10,11))],
        drummer_rigs={'left':dict(ids=(12,13)), 'right':dict(ids=(14,15))},
        kick_beater=16,hihat_foot=17,hihat_pedal=18,
    )
    roles=[r['role'] for r in native_motion_rigs(scene)]
    assert roles.count('piano')==2 and roles.count('drummer')==4
    assert 'xylophone' not in roles
    legacy=[r['role'] for r in native_motion_rigs(scene,legacy_xylophone=True)]
    assert legacy.count('xylophone')==1


def test_native_house_preview_nodes_remain_visible_at_hd_resolution():
    """Guard against tiny, jagged xLights RGB nodes returning to the showcase."""
    from pathlib import Path
    source=(Path(__file__).resolve().parents[1]/'tools'/'native_source_pose_band.py').read_text()
    assert "PixelSize='12'" in source
    assert "Antialias='1'" in source
    assert "BlackTransparency='100'" in source


def test_native_static_materials_preserve_colors_coverage_and_musical_clock():
    from types import SimpleNamespace
    model = SimpleNamespace(details={'review_role': 'piano'},
        colors=['#FFFFFF', '#632D98', '#282A43', '#E7E7D6'],
        submodels={'BODY': [1, 2, 3], 'NOTE_MIDI_60': [4]})
    note = np.array([0, .8, .8, 0], dtype='f4')
    body = np.full(4, .85, dtype='f4')
    cues = {'BODY': body.copy(), 'NOTE_MIDI_60': note.copy()}
    addresses = {name: list(nodes) for name, nodes in model.submodels.items()}
    report = retain_native_materials(model, cues)
    assert report['BODY'] == {'#282A43': 1, '#632D98': 1, '#FFFFFF': 1}
    for color in report['BODY']:
        part = 'BODY_RGB_' + color[1:]
        np.testing.assert_array_equal(cues[part], body)
        assert {model.colors[n - 1] for n in model.submodels[part]} == {color}
    assert sorted(n for part, nodes in model.submodels.items()
                  if part.startswith('BODY_RGB_') for n in nodes) == [1, 2, 3]
    np.testing.assert_array_equal(cues['NOTE_MIDI_60'], note)
    np.testing.assert_array_equal(cues['KEY_IDLE_60_RGB_E7E7D6'], [.16, 0, 0, .16])
    for name, nodes in addresses.items():
        assert model.submodels[name] == nodes
    assert 'BODY' not in cues  # no first-node-color overlay can erase materials


def test_native_kit_idle_is_separate_from_real_hit_lanes():
    from types import SimpleNamespace
    model = SimpleNamespace(details={'review_role': 'drummer'},
        colors=['#86C6E7', '#BDA665', '#357DA9'],
        submodels={'BASE_DIM': [1], 'CYMBAL_LEFT': [2], 'KICK': [3]})
    cues = {'BASE_DIM': np.full(4, .85),
            'CYMBAL_LEFT': np.array([0, 1., .5, 0]),
            'KICK': np.zeros(4)}
    hits = cues['CYMBAL_LEFT'].copy()
    retain_native_materials(model, cues)
    np.testing.assert_array_equal(cues['CYMBAL_LEFT'], hits)
    np.testing.assert_array_equal(cues['KICK'], np.zeros(4))
    np.testing.assert_array_equal(cues['KIT_IDLE_CYMBAL_LEFT_RGB_BDA665'], [.18, 0, 0, .18])
    assert all('RGB' not in name for name in ('CYMBAL_LEFT', 'KICK'))


def test_native_piano_includes_authored_keyboard_case_and_both_stands():
    from models.native_review_band import _role_parts
    from models.review_3d_scene import Review3DScene
    from models.final_band_native import SurfaceParts
    scene = Review3DScene()
    actual = _role_parts(scene, 'piano', (0, 0, 75), 5)
    expected = SurfaceParts((0, 0, 75), scale=5)
    structure = [item for item in scene.instances
                 if item['name'] in {'keyboard_case', 'keyboard_stand_left', 'keyboard_stand_right'}]
    assert len(structure) == 3
    for item in structure:
        expected.primitive('BODY', item)
    body = {tuple(actual.points[node - 1]) for node in actual.parts['BODY']}
    assert set(map(tuple, expected.points)) <= body
    assert any(name.startswith('NOTE_MIDI_') for name in actual.parts)
