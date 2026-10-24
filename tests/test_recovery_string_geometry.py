import numpy as np
from models.final_band_scene import FinalBandScene
from models.approval_layouts import build_layout


def test_strings_keep_authored_bridge_and_nut_in_front_of_instruments():
    scene=FinalBandScene()
    for role,strings in scene.strings.items():
        for number,string in enumerate(strings):
            original=next(o for o in scene.instances if o['name']==f'{role}_string_{number}')
            matrix=original['matrix']
            assert original['kind']=='hidden'
            if role=='guitar':
                assert np.allclose(string['a'][:2],(matrix[:3,3]-.5*matrix[:3,2])[:2])
                assert np.allclose(string['b'][:2],(matrix[:3,3]+.5*matrix[:3,2])[:2])
                bridge=next(o for o in scene.instances if o['name']=='bridge')['matrix']
                assert np.isclose(string['a'][2],bridge[2,3]+abs(bridge[2,2])*.5)
            else:
                bridge=next(o for o in scene.instances if o['name']=='bass_bridge')['matrix']
                assert abs(string['a'][0]-bridge[0,3])<=abs(bridge[0,0])*.251
                assert string['a'][2]>bridge[2,3]+abs(bridge[2,2])*.5
                assert string['a'][2]==string['b'][2]
            assert string['radius']<=.0045
            scene.vibrate(role,number,1,.123)
            first=scene.instances[string['ids'][0]]['matrix']
            last=scene.instances[string['ids'][-1]]['matrix']
            assert np.allclose(first[:3,3]-.5*first[:3,2],string['a'],atol=1e-6)
            assert np.allclose(last[:3,3]+.5*last[:3,2],string['b'],atol=1e-6)
            assert all(np.isclose(np.linalg.norm(scene.instances[i]['matrix'][:3,0]),string['radius']) for i in string['ids'])


def test_native_strings_are_thin_ordered_paths_and_body_does_not_light_them():
    scene=FinalBandScene()
    garden=build_layout(7)
    for role in ('bass','guitar'):
        model=next(m for m in garden.models if m.details.get('review_role')==role)
        for number,geometry in enumerate(scene.strings[role]):
            nodes=model.submodels['STRING_'+str(number)]
            assert 20<=len(nodes)<=80
            assert set(nodes).isdisjoint(model.submodels['BODY'])
            # Native stage placement adds a shared transform; shape remains a
            # line to within grid precision, rather than cylindrical loops.
            points=model.points[np.array(nodes)-1]
            _,singular,_=np.linalg.svd(points-points.mean(0),full_matrices=False)
            assert singular[1]/singular[0]<.025


def test_portable_band_retains_exact_referenced_editor_source_art(tmp_path):
    from pathlib import Path
    from tools.build_helpers.ultimate_showcase import write_layout
    from tools.phoneme_source import digest
    garden=build_layout(7);write_layout(garden,tmp_path,include_demo=False)
    drummer=next(m for m in garden.models if m.details.get('review_role')=='drummer')
    root=Path(__file__).resolve().parents[1]
    for key in ('CustomBkgImage','HelixVisualSource'):
        relative=drummer.attrs[key]
        assert digest(tmp_path/relative)==digest(root/'fixtures/band_geometry/source'/Path(relative).name)
