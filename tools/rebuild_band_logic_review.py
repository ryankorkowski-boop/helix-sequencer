"""Recompile retained source events without mutating published review inputs."""
from __future__ import annotations
import json,shutil
from pathlib import Path
import numpy as np
from models.band_instrument_logic import event_curves,chord_route,playable_pitch
from models.band_sampler_logic import bass_neck_height
from music.note_events import NoteEvent
from tools.readable_band_performance import ROOT,OUT as PREVIOUS
from tools.render_intricate_band_samplers import sha

OUT=ROOT/'outputs/Band_Logic_Reassessment'


def main():
    reports=[]
    for row in json.loads((ROOT/'outputs/Snowman_Ensemble/sources.json').read_text()):
        if row['id']=='04':continue
        prior=PREVIOUS/'analysis'/row['id'];dest=OUT/'analysis'/row['id'];dest.mkdir(parents=True,exist_ok=True)
        with np.load(prior/'performance_curves.npz') as data:arrays={k:data[k].copy() for k in data.files}
        events=json.loads((prior/'note_events.json').read_text());proof=json.loads((prior/'verification.json').read_text())
        changes={};n=len(arrays['bass_notes'])
        for kind in ('bass','guitar','piano'):
            ev=[NoteEvent(**e) for e in events[kind]];cols=1 if kind=='bass' else 6
            notes,levels,attack,phase=event_curves(ev,n,cols,.22 if kind=='bass' else .16)
            before=arrays[kind+'_notes']
            changes[kind]={'changed_pitch_frames':int(np.any(before!=notes,axis=1).sum()),
                'hidden_onset_frames_before':sum(e.pitch not in before[round(e.start*20)] for e in ev if round(e.start*20)<n),
                'hidden_onset_frames_after':sum(e.pitch not in notes[round(e.start*20)] for e in ev if round(e.start*20)<n)}
            for key,value in [('notes',notes),('note_levels',levels),('attack',attack),('phase',phase)]:arrays[kind+'_'+key]=value
            arrays[kind+'_energy']=levels.max(axis=1)
            if kind!='piano':
                routes=np.full((n,cols,3),-1,np.int16);omitted=0
                for i,grid in enumerate(notes):
                    chosen=chord_route(tuple(int(x) for x in grid if x>=0),kind)
                    for j,value in enumerate(chosen):routes[i,j]=value
                    omitted+=len(set(playable_pitch(int(x),kind) for x in grid if x>=0))-len(chosen)
                arrays[kind+'_routes']=routes
                proof['routing'][kind]['unplayable_note_frame_omissions']=omitted
        height=2.3;heights=[]
        for notes in arrays['bass_notes']:
            if notes[0]>=0:height=bass_neck_height(int(notes[0]),low=24,high=64)
            heights.append(height)
        arrays['bass_height']=np.asarray(heights,np.float32)
        np.savez_compressed(dest/'performance_curves.npz',**arrays)
        for name in ('vocals.json','note_events.json'):shutil.copyfile(prior/name,dest/name)
        proof['reassessment']={'prior_inputs_sha256':{p.name:sha(p) for p in prior.glob('*')},
            'detections_and_lyrics_reestimated':False,'changes':changes,
            'method':'active-before-release / newest articulation owns pitch; selected notes own gestures'}
        (dest/'verification.json').write_text(json.dumps(proof,indent=2)+'\n')
        reports.append({'id':row['id'],**proof['reassessment']});print(row['id'],changes,flush=True)
    dest=ROOT/'evidence/band_logic_reassessment/recompiled_inputs.json'
    dest.write_text(json.dumps(reports,indent=2)+'\n')


if __name__=='__main__':main()
