"""Reassess instrument stems and compile the repository's canonical note events."""
from __future__ import annotations

import json
from pathlib import Path
import shutil

import librosa
import numpy as np
from scipy.signal import find_peaks

from models.band_instrument_logic import sparse_harmonic_notes, compile_note_events, event_curves, chord_route,playable_pitch
from tools.analyze_band_upgrade import mono,curve,sha
from tools.analyze_band_samplers import mallet_cues

ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT/'outputs/Snowman_Ensemble'
PREVIOUS=ROOT/'outputs/Intricate_Band_Samplers/analysis'
OUT=ROOT/'outputs/Band_Instrument_Review'


def estimate(a,n,kind):
    spectrum=np.abs(librosa.cqt(a,sr=16000,hop_length=800,
                               fmin=librosa.midi_to_hz(24),n_bins=72))[:,:n]
    if spectrum.shape[1]<n:spectrum=np.pad(spectrum,((0,0),(0,n-spectrum.shape[1])))
    notes,relative=sparse_harmonic_notes(spectrum,max_notes=1 if kind=='bass' else 4)
    energy,_,rms=curve(a,n)
    notes[energy<.09]=-1
    # Two adjacent observations support a note; isolate one-frame spectral
    # speckles instead of sending a spurious guitar/keyboard gesture.
    valid=np.zeros(notes.shape,bool)
    for pitch in set(notes.ravel())-{-1}:
        present=np.any(notes==pitch,axis=1)
        stable=present&(np.r_[False,present[:-1]]|np.r_[present[1:],False])
        valid|=(notes==pitch)&stable[:,None]
    notes[~valid]=-1
    novelty=librosa.onset.onset_strength(y=a,sr=16000,hop_length=160,n_fft=1024)
    peaks,_=find_peaks(novelty,distance=8,prominence=max(.6,float(np.quantile(novelty,.90))*.22))
    impulses=np.zeros(n,np.float32)
    for p in peaks:
        i=round(p/5)
        if i<n and energy[i]>.09:impulses[i]=energy[i]
    velocity=np.sqrt(energy)[:,None]*relative
    velocity[np.all(notes<0,axis=1)]=0
    return notes,velocity,impulses,dict(active_stem_frames=int((energy>.09).sum()),
                                      measured_attacks=int(np.count_nonzero(impulses)),
                                      supported_note_frames=int(np.any(notes>=0,axis=1).sum()),
                                      raw_rms_peak=float(rms.max()))


def main():
    sources=json.loads((OLD/'sources.json').read_text())
    for row in sources:
        if row['id']=='04':continue
        dest=OUT/'analysis'/row['id'];dest.mkdir(parents=True,exist_ok=True)
        prior=PREVIOUS/row['id']
        old=np.load(prior/'performance_curves.npz');arrays={k:old[k].copy() for k in old.files}
        n=len(arrays['bass_energy']);stems=OLD/'stems/htdemucs_6s'/Path(row['path']).stem
        proof={'source_sha256':row['sha256'],'method':'residual harmonic-template notes; separate source stems; canonical NoteEvent velocity/hold/release',
               'verified_musical_score':False,'stems':{},'event_counts':{},'routing':{}}
        all_events={};waves={}
        for kind in ('bass','guitar','piano'):
            path=stems/(kind+'.wav');waves[kind]=mono(path)
            notes,velocity,attacks,stats=estimate(waves[kind],n,kind)
            events=compile_note_events(notes,velocity,attacks,kind+'_stem_harmonic_estimate')
            if kind=='piano':
                other=mono(stems/'other.wav');vocal=mono(stems/'vocals.wav')
                mallet,_,_,mallet_proof=mallet_cues(other,vocal,n)
                mnotes,mvel,matk,mstats=estimate(other,n,'mallet')
                mnotes[mallet<.08]=-1;mvel[mallet<.08]=0;matk[mallet<.08]=0
                events+=compile_note_events(mnotes,mvel,matk,'other_stem_screened_mallet_estimate')
                proof['mallet']={'accepted_attack_windows':len(mallet_proof),'notes':mstats,
                                 'other_sha256':sha(stems/'other.wav'),'vocal_sha256':sha(stems/'vocals.wav')}
            events.sort(key=lambda e:(e.start,e.pitch))
            all_events[kind]=[e.to_dict() for e in events]
            note_grid,note_levels,attack,phase=event_curves(events,n,1 if kind=='bass' else 6,
                                                          release=.22 if kind=='bass' else .16)
            arrays[kind+'_notes']=note_grid;arrays[kind+'_note_levels']=note_levels
            arrays[kind+'_attack']=attack;arrays[kind+'_phase']=phase
            arrays[kind+'_energy']=note_levels.max(axis=1)
            proof['stems'][kind]=dict(stats,sha256=sha(path))
            proof['event_counts'][kind]=len(events)
            if kind in ('bass','guitar'):
                route=np.full((n,1 if kind=='bass' else 6,3),-1,np.int16)
                omitted=0
                for i in range(n):
                    chosen=chord_route(tuple(int(x) for x in note_grid[i] if x>=0),kind)
                    for j,value in enumerate(chosen):route[i,j]=value
                    omitted+=len(set(playable_pitch(int(x),kind) for x in note_grid[i] if x>=0))-len(chosen)
                arrays[kind+'_routes']=route
                proof['routing'][kind]={'unplayable_note_frame_omissions':omitted,'distinct_physical_strings':True,
                    'register_folding':'octaves only; original absolute pitch controls bass height'}
        # Absolute measured pitch always sets bass hand height (low up/high down),
        # regardless of an explicitly folded playable string register.
        from models.band_sampler_logic import bass_neck_height
        height=2.30;heights=[]
        for notes in arrays['bass_notes']:
            if notes[0]>=0:height=bass_neck_height(notes[0],low=24,high=64)
            heights.append(height)
        arrays['bass_height']=np.asarray(heights,np.float32)
        np.savez_compressed(dest/'performance_curves.npz',**arrays)
        (dest/'note_events.json').write_text(json.dumps(all_events,indent=2)+'\n')
        (dest/'verification.json').write_text(json.dumps(proof,indent=2)+'\n')
        shutil.copyfile(prior/'vocals.json',dest/'vocals.json')
        print(row['id'],proof['event_counts'],flush=True)


if __name__=='__main__':main()
