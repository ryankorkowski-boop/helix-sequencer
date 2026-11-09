"""Source front parity, real closed depth, and unchanged articulated clocks."""
import numpy as np
from pathlib import Path
from PIL import Image

from models.band_performance_scene import BandScene
from models.source_drummer_3d import closed_component,source_components,SourceDrummer3D
from tools.render_drummer_v3_preview import TARGETS


def test_construction_depth_never_changes_front_positions_or_materials():
    rgb=np.asarray(Image.open('fixtures/band_geometry/source/drummerbg.png').convert('RGB'))[124:380,99:494]
    mask=np.zeros(rgb.shape[:2],bool);mask[20:100,45:125]=True
    flat=closed_component(mask,rgb,.001);deep=closed_component(mask,rgb,60)
    a=flat.vertices[flat.vertices[:,2]==0];b=deep.vertices[deep.vertices[:,2]==0]
    np.testing.assert_array_equal(a,b)
    np.testing.assert_array_equal(flat.visual.vertex_colors,deep.visual.vertex_colors)
    assert deep.is_watertight and deep.volume>flat.volume>0
    assert np.ptp(deep.vertices[:,2])>40


def test_every_source_component_has_closed_positive_volume_and_no_billboard():
    parts=source_components()
    assert len(parts)==10
    assert {p['name'] for p in parts[:8]}==set(TARGETS)
    for item in parts:
        mesh=item['mesh']
        assert mesh.is_watertight and mesh.volume>0
        assert np.ptp(mesh.vertices[:,2])>=5
        assert np.isfinite(mesh.vertices).all()


def test_dynamic_mesh_arms_share_original_2d_joints_and_foot_events_do_not_move_them():
    # An empty existing scene receives only the source-preserving drummer.
    scene=BandScene.__new__(BandScene);scene.instances=[];scene.custom=[]
    hits=[dict(time=.25,target=TARGETS[2],side='left',velocity=.8),
          dict(time=.5,target=TARGETS[0],side='left',velocity=.9),
          dict(time=1.,target=TARGETS[1],side='left',velocity=.7)]
    rig=SourceDrummer3D(scene,hits)
    for t in np.linspace(0,1.5,46):
        rig.pose(float(t))
        for side,indices in rig.rigs.items():
            joints=rig.player.last_joints[side]
            s,e,w,tip=[rig.point(joints[k]) for k in ('shoulder','elbow','wrist','tip')]
            upper,forearm,grip,stick=indices
            np.testing.assert_allclose(scene.instances[upper]['matrix'][:3,3],(s+e)/2,atol=1e-6)
            np.testing.assert_allclose(scene.instances[forearm]['matrix'][:3,3],(e+w)/2,atol=1e-6)
            np.testing.assert_allclose(scene.instances[grip]['matrix'][:3,3],w,atol=1e-6)
            np.testing.assert_allclose(scene.instances[stick]['matrix'][:3,3],(w+tip)/2,atol=1e-6)
    assert not rig.player.motion_rejections
    assert not any(h['target'] in (TARGETS[0],TARGETS[2]) for h in rig.player.hits)
    assert len(rig.player.foot_hits)==len(rig.player.kick_hits)==1


def test_comparison_original_ac_addresses_keep_name_to_circuit_identity():
    from tools.build_current_comparison import layout
    from core.model_parser import parse_layout
    g,_=layout(1,{})
    original=parse_layout(Path('xlights_rgbeffects.xml'))
    assert len(g.models)==256 and sum(m.channels for m in g.models)==256
    for model in g.models:
        assert model.start==original.models[model.name].start_channel
        assert model.channels==1
