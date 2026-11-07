import numpy as np
from models.intricate_band_scene import IntricateBandScene, LAYOUTS
from tools.render_intricate_band_samplers import ExactDryDrummer


def test_all_six_stages_have_volumetric_layers_and_complete_band_without_replacement_drummer():
    for key in LAYOUTS:
        s=IntricateBandScene(key)
        assert s.technical_proof['finite_geometry']
        assert s.technical_proof['custom_triangles']>100000
        assert len(s.custom)>65
        assert not any('tom_' in o['name'] for o in s.instances)
        assert {r['role'] for r in s.rigs}=={'bass','guitar','lead','harmony','piano'}
        xyz=np.vstack([o['mesh'].vertices for o in s.custom if o['slot']>=64])
        assert np.ptp(xyz[:,2])>3 and np.ptp(xyz[:,1])>5
        keys=[o for o in s.instances if o['name'].startswith('piano_key_')]
        assert len(keys)==37 and all(o['matrix'][0,3]>5.0 for o in keys)


def test_exact_dry_cymbal_decay_cannot_hold_up_the_arm():
    d=ExactDryDrummer();z=np.zeros(8)
    light=z.copy();light[6]=.75
    hit=z.copy();hit[6]=1
    rest=d.frame(z,z,0);ring=d.frame(light,z,0);strike=d.frame(light,hit,0)
    assert np.any(ring!=rest) and np.any(strike!=ring)
    # A decay frame has exactly the original surface-only composition,
    # whereas the strike restores the whole source-art actuator.
    expected=np.maximum(d.idle,d.idle+(d.ringing[6]-d.idle)*.75).clip(0,255).astype('u1')
    assert np.array_equal(ring[:,:,:3],expected)
    assert not d.proof['replacement_3d_kit']


def test_key_hands_target_actual_white_and_raised_black_keys_and_idle_guitar_does_not_strum(tmp_path,monkeypatch):
    import json
    import tools.render_intricate_band_samplers as renderer
    root=tmp_path/'analysis'/'99';root.mkdir(parents=True)
    n=3;curves={'vocal_route':np.zeros(n,dtype=np.int8),'vocal_energy':np.zeros(n),
              'mouth_lanes':np.zeros((n,2),dtype=np.int8),'bass_height':np.full(n,2.5)}
    for kind in ('bass','guitar','piano'):
        curves[kind+'_energy']=np.zeros(n)
        curves[kind+'_attack']=np.zeros(n)
        curves[kind+'_notes']=np.full((n,6),-1,dtype=np.int16)
    curves['piano_notes'][:,0]=(48,49,84)
    curves['piano_energy'][:]=1
    np.savez_compressed(root/'performance_curves.npz',**curves)
    (root/'vocals.json').write_text(json.dumps({'lines':[]}))
    monkeypatch.setattr(renderer,'OUT',tmp_path)
    monkeypatch.setattr(renderer,'native_drummer',lambda row:(np.zeros((n,8)),np.zeros((n,8)),np.zeros(n),{}))
    s=IntricateBandScene('prismatic_orrery');p=renderer.SamplerPerformance({'id':'99'},s)
    piano_rigs={r['side']:r for r in s.rigs if r['role']=='piano'}
    guitar=next(r for r in s.rigs if r['role']=='guitar' and r['side']=='strum')
    guitar_idle=s.instances[guitar['ids'][2]]['matrix'].copy()
    for i,note in enumerate((48,49,84)):
        p.pose(i)
        side='left' if note<66 else 'right';piano=piano_rigs[side]
        hand=s.instances[piano['ids'][2]]['matrix'][:3,3]
        key=p.key_centers[note]
        assert abs(hand[0]-key[0])<1e-6 and abs(hand[2]-key[2]-.1)<1e-6
        assert abs(hand[1]-key[1]-.130)<1e-6
        other=piano_rigs['right' if side=='left' else 'left']
        assert np.allclose(s.instances[other['ids'][2]]['matrix'][:3,3],other['hand'],atol=1e-6)
        assert np.array_equal(s.instances[guitar['ids'][2]]['matrix'],guitar_idle)
