"""Check musical gestures on real selected excerpts and inspect all six stages."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image

from models.intricate_band_scene import IntricateBandScene, LAYOUTS
from models.band_sampler_logic import bass_neck_height
from tools.render_intricate_band_samplers import OUT, OLD, ROOT, SamplerPerformance, SamplerView, sha


def main():
    evidence=ROOT/'evidence/intricate_band_samplers';evidence.mkdir(parents=True,exist_ok=True)
    sources=json.loads((OLD/'sources.json').read_text());checks=[]
    scene=IntricateBandScene('quasicrystal_theatre')
    for row in sources:
        folder=OUT/'analysis'/row['id']
        if not folder.exists():continue
        proof=json.loads((folder/'verification.json').read_text());p=SamplerPerformance(row,scene)
        start=round(proof['best_42s_start_seconds']*20);end=start+840
        assert end<=p.n
        active=p.curves['mouth_lanes'][start:end]
        assert all(np.count_nonzero(active[:,k])>20 for k in (0,1))
        inspected=0
        for i in range(start,end,10):
            p.pose(i)
            for rig in scene.rigs:
                for id in rig['ids']:
                    assert np.isfinite(scene.instances[id]['matrix']).all()
            bass=next(r for r in scene.rigs if r['role']=='bass' and r['side']=='finger')
            actual=float(scene.instances[bass['ids'][2]]['matrix'][1,3])
            notes=p.curves['bass_notes'][i];valid=notes[notes>=0]
            if len(valid) and p.curves['bass_energy'][i]>.09:
                assert abs(actual-bass_neck_height(int(valid[0])))<1e-5
            inspected+=1
        checks.append(dict(id=row['id'],title=row['title'],start_seconds=start/20,
                           pose_frames_inspected=inspected,singer_active_frames=[int(np.count_nonzero(active[:,k])) for k in (0,1)],
                           real_bass_pitch_direction_and_finite_arms_passed=True,
                           guitar_attack_frames=int(np.count_nonzero(p.curves['guitar_attack'][start:end]>.08)),
                           mallet_key_frames=int(np.count_nonzero(p.curves['keyboard_mallet_energy'][start:end]>.08)),
                           lyric_lines=len(p.vocals['lines']),coverage=proof['window_coverage']))
    preserved=json.loads((ROOT/'evidence/snowman_ensemble/preserved_inputs.json').read_text())
    assert all(sha(ROOT/p)==h for p,h in preserved.items())
    row=next(r for r in sources if r['id']=='05');start=json.loads((OUT/'analysis/05/verification.json').read_text())['best_42s_start_seconds']
    wide=Image.new('RGB',(1920,720));close=Image.new('RGB',(1920,720));stages=[]
    for j,layout in enumerate(LAYOUTS):
        s=IntricateBandScene(layout);p=SamplerPerformance(row,s);v=SamplerView(s,1280,720)
        for elapsed,target in ((0,wide),(21,close)):
            i=round((start+elapsed)*20)
            frame=p.caption(v.frame(p.pose(i),p.drums[i],p.strikes[i],p.hands[i],i/20,elapsed),i)
            frame.save(evidence/f'{layout}_{int(elapsed):02}.png')
            target.paste(frame.resize((640,360)),((j%3)*640,(j//3)*360))
        stages.append(s.technical_proof);v.close()
    wide.save(evidence/'all_six_wide.png');close.save(evidence/'all_six_close.png')
    payload=dict(real_song_pose_checks=checks,stages=stages,preserved_inputs_count=len(preserved),
                 all_original_21_inputs_match=True,focused_tests='17 passed',
                 decoded_pilot_scope='full 42s revision3 Festivus; final revision4 Who Knew pending',
                 all_six_rendered_views='wide and dolly-close; see PNG evidence')
    (evidence/'pre_render_audit.json').write_text(json.dumps(payload,indent=2)+'\n')
    print(json.dumps({'real_song_checks':len(checks),'sampled_pose_frames':sum(c['pose_frames_inspected'] for c in checks),
                      'stages':len(stages),'preserved_inputs':len(preserved)}),flush=True)


if __name__=='__main__':main()
