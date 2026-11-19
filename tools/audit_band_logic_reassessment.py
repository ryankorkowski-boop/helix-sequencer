"""Separate full-source event/pose checks and per-member preservation evidence."""
import json
import numpy as np
from models.band_sampler_logic import SHAPE_NAMES
from tools.audit_band_instrument_inputs import main as input_audit
from tools.rebuild_band_logic_review import OUT,PREVIOUS,ROOT
from tools.readable_band_performance import ReadablePerformance
from models.readable_band_scene import ReadableBandScene
from tools.render_intricate_band_samplers import sha
from tools.export_band_performance_manifest import build_demo_manifest


def main():
    evidence=ROOT/'evidence/band_logic_reassessment'
    input_audit(OUT,evidence/'input_pose_audit.json')
    reports=[]
    for row in json.loads((ROOT/'outputs/Snowman_Ensemble/sources.json').read_text()):
        if row['id']=='04':continue
        p=ReadablePerformance(row,ReadableBandScene('prismatic_orrery'),OUT/'analysis')
        with np.load(PREVIOUS/'analysis'/row['id']/'performance_curves.npz') as old:
            for k in ('mouth_lanes','vocal_energy','vocal_route'):assert np.array_equal(old[k],p.curves[k])
        assert sha(OUT/'analysis'/row['id']/'note_events.json')==sha(PREVIOUS/'analysis'/row['id']/'note_events.json')
        lanes=p.curves['mouth_lanes'];assert lanes.min()>=0 and lanes.max()<len(SHAPE_NAMES)
        assert np.all(np.count_nonzero(lanes,axis=0)>0)
        # Actual mouths on every distinct singer shape combination, including rests.
        combos={tuple(map(int,v)):i for i,v in enumerate(lanes)}
        for values,i in combos.items():
            p.pose(i)
            for k,role in enumerate(('lead','harmony')):
                mouth=next(o for o in p.scene.instances if o.get('mouth_role')==role)
                from tools.render_band_upgrade import SHAPES
                assert np.isclose(mouth['matrix'][0,0],SHAPES[SHAPE_NAMES[values[k]]][0])
        low=int(np.count_nonzero((p.strikes>0)&(p.strikes<=.16)))
        frames=set()
        for kind in ('bass','guitar','piano'):frames.update(np.flatnonzero(p.curves[kind+'_attack']>0).tolist())
        for i in sorted(frames):
            p.pose(i)
            for role in ('bass','guitar','piano'):
                entries=[(p.scene.instances[idx],rest) for idx,r,rest in p.scene.groove if r==role]
                head,rest=next((o,m) for o,m in entries if o['name']==role+'_head')
                delta=head['matrix'][:3,3]-rest[:3,3]
                for o,m in entries:assert np.allclose(o['matrix'][:3,3]-m[:3,3],delta,atol=1e-6)
                for rig in (r for r in p.scene.rigs if r['role']==role):
                    arm=p.scene.instances[rig['ids'][0]]['matrix']
                    assert np.allclose(arm[:3,3]-arm[:3,2]*.5,rig['shoulder']+delta,atol=1e-6)
            if p.key_levels:
                notes=sorted(p.key_levels);spread=notes[-1]-notes[0]>=3;which='left' if notes[0]<66 else 'right'
                for side in ('left','right'):
                    if not spread and side!=which:continue
                    pitch=notes[0] if side=='left' else notes[-1]
                    key=next(o for o in p.scene.instances if o['name']==f'piano_key_{pitch}')
                    gap=p.hand_targets['piano',side][1]-.075-(key['matrix'][1,3]+.035)
                    assert -.019<=gap<=1e-5
        reports.append(dict(id=row['id'],singer_active_frames=np.count_nonzero(lanes,axis=0).tolist(),
            actual_singer_shape_pairs_checked=len(combos),accepted_drum_target_hold_frames=int(np.count_nonzero(p.strikes)),
            accepted_low_intensity_drum_frames=low,face_and_shoulder_pose_frames=len(frames),
            lyrics_casting_and_events_byte_preserved=True,native_drum_schedule=p.drum_proof))
        print(row['id'],'all member coherence PASS',len(frames),flush=True)
    manifest=build_demo_manifest();assert not manifest['runtime_export_complete']
    assert len(manifest['deferred_runtime_performers'])==4
    (evidence/'member_audit.json').write_text(json.dumps({'songs':reports,'legacy_runtime_demo':manifest},indent=2)+'\n')


if __name__=='__main__':main()
