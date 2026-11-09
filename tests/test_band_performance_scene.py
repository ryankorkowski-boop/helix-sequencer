import numpy as np
import trimesh

from models.band_performance_scene import BandScene, string_assignment


def test_refined_scene_geometry_is_finite_and_complete(tmp_path):
    scene=BandScene('band')
    for item in scene.instances:
        assert np.isfinite(item['matrix']).all()
        assert abs(np.linalg.det(item['matrix'][:3,:3]))>1e-10
    for item in scene.custom:
        assert np.isfinite(item['mesh'].vertices).all()
        assert np.isfinite(item['mesh'].vertex_normals).all()
    path=tmp_path/'band.glb';scene.export_glb(path)
    restored=trimesh.load(path)
    assert np.isfinite(restored.bounds).all()
    keys=[i for i in scene.instances if i['name'].startswith('piano_key_')]
    assert len(keys)==37 and {i['slot'] for i in keys}==set(range(23,60))
    blacks=[i for i in keys if (i['slot']-23+48)%12 in (1,3,6,8,10)]
    assert len(blacks)==15
    assert all(i['matrix'][1,3]>1.33 for i in blacks)
    names={i['name'] for i in scene.instances}
    assert {'tom_high_head','tom_mid_head','tom_floor_head','snare_head'}<=names


def test_note_casting_respects_real_open_strings_and_frets():
    for kind,tunings in [('bass',(28,33,38,43)),('guitar',(40,45,50,55,59,64))]:
        for note in range(min(tunings),max(tunings)+25):
            chosen=string_assignment(note,kind)
            if chosen:
                string,fret=chosen
                assert tunings[string]+fret==note and 0<=fret<=24
        assert string_assignment(min(tunings)-1,kind) is None


def test_alternate_helix_faces_have_distinct_visible_shapes():
    scene=BandScene('faces')
    names={i['name'] for i in scene.custom}
    assert {'tree_helix_rail','bulb_helix_rail','pumpkin_helix_rail'}<=names
    mouths=[i for i in scene.instances if i.get('mouth_role')=='faces']
    assert len(mouths)==4
    assert len({round(i['mouth_center'][0],2) for i in mouths})==4
    # Hollow outline faces need light mouths against the dark stage; the solid
    # snowman needs a dark mouth against snow. Both must remain readable.
    hollow=[i for i in mouths if i['name']!='face_snowman_mouth']
    assert all(np.mean(i['color'])>.65 for i in hollow)
