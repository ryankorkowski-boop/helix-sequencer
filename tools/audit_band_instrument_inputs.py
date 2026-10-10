"""Audit the compiled events against routes, preserved sources and actual rigs."""
from __future__ import annotations
import json
import numpy as np
from models.band_instrument_logic import event_curves,playable_pitch
from models.band_sampler_logic import bass_neck_height
from models.band_performance_scene import TUNINGS
from models.readable_band_scene import ReadableBandScene
from music.note_events import NoteEvent
from tools.readable_band_performance import ReadablePerformance,OUT,ROOT
from tools.render_readable_band import assert_pose
from tools.render_intricate_band_samplers import sha


def main():
    reports=[]
    for row in json.loads((ROOT/'outputs/Snowman_Ensemble/sources.json').read_text()):
        if row['id']=='04':continue
        path=OUT/'analysis'/row['id'];scene=ReadableBandScene('prismatic_orrery');p=ReadablePerformance(row,scene)
        events=json.loads((path/'note_events.json').read_text());report={'id':row['id'],'instruments':{}}
        previous=ROOT/'outputs/Intricate_Band_Samplers/analysis'/row['id']
        binding=json.loads((path/'verification.json').read_text())
        stems=ROOT/'outputs/Snowman_Ensemble/stems/htdemucs_6s'/__import__('pathlib').Path(row['path']).stem
        for kind in ('bass','guitar','piano'):assert sha(stems/(kind+'.wav'))==binding['stems'][kind]['sha256']
        assert sha(stems/'other.wav')==binding['mallet']['other_sha256']
        assert sha(stems/'vocals.wav')==binding['mallet']['vocal_sha256']
        assert sha(path/'vocals.json')==sha(previous/'vocals.json')
        old=np.load(previous/'performance_curves.npz')
        for name in ('mouth_lanes','vocal_energy'):assert np.array_equal(old[name],p.curves[name])
        for kind in ('bass','guitar','piano'):
            ev=[NoteEvent(**e) for e in events[kind]]
            curves=event_curves(ev,len(p.curves[kind+'_notes']),1 if kind=='bass' else 6,.22 if kind=='bass' else .16)
            for key,c in zip(('notes','note_levels','attack','phase'),curves):assert np.array_equal(c,p.curves[kind+'_'+key])
            assert all(e.source.startswith(kind+'_stem') or kind=='piano' and e.source.startswith('other_stem_screened_mallet') for e in ev)
            assert all(0<=e.velocity<=1 and e.end>e.start for e in ev)
            report['instruments'][kind]={'events':len(ev),'source_attacks':int(np.count_nonzero(p.curves[kind+'_attack'])),
                'screened_mallet_events':sum(e.source.startswith('other_stem_screened_mallet') for e in ev),
                'event_curves_exact_match':True}
            if kind in ('bass','guitar'):
                omitted=0
                for notes,route in zip(p.curves[kind+'_notes'],p.curves[kind+'_routes']):
                    route=route[route[:,0]>=0];assert len(set(route[:,0]))==len(route)
                    for s,f,n in route:assert TUNINGS[kind][s]+f==n and 0<=f<=24
                    omitted+=len(set(playable_pitch(int(n),kind) for n in notes if n>=0))-len(route)
                report['instruments'][kind]['unplayable_note_frame_omissions']=omitted
        height=2.3
        for notes,h in zip(p.curves['bass_notes'],p.curves['bass_height']):
            if notes[0]>=0:height=bass_neck_height(int(notes[0]),low=24,high=64)
            assert abs(float(h)-height)<1e-5
        # Check every source onset, plus one pose per250ms across the full song.
        frames=set(range(0,p.n,5))
        for kind in ('bass','guitar','piano'):frames.update(np.flatnonzero(p.curves[kind+'_attack']>.05).tolist())
        for i in sorted(frames):assert_pose(p,i,p.pose(i))
        report.update(actual_pose_frames_checked=len(frames),singer_inputs_preserved=True,
                      native_drummer=p.drum_proof,analysis_sha256=sha(path/'performance_curves.npz'))
        reports.append(report);print(row['id'],'source/events/poses PASS',len(frames),flush=True)
    dest=ROOT/'evidence/band_instrument_review/input_pose_audit.json'
    dest.write_text(json.dumps(reports,indent=2)+'\n')


if __name__=='__main__':main()
