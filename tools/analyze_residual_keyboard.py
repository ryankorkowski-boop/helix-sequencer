"""Source-bound residual harmonic notes for one unified pitched performer.

This does not identify a horn/synth brand or guarantee a musical transcription.
Harmonic dominance, temporal pitch support and vocal exclusion screen candidates.
"""
from __future__ import annotations

import argparse,json,hashlib
from pathlib import Path
import librosa
import numpy as np
from tools.analyze_band_upgrade import mono
from tools.analyze_band_instruments import estimate
from models.band_instrument_logic import compile_note_events


def residual_notes(other,vocal,n):
    harmonic,percussive=librosa.effects.hpss(other)
    hop=800; size=2048
    def power(y):
        frames=librosa.util.frame(np.pad(y,(size//2,size//2)),frame_length=size,hop_length=hop).T
        result=np.mean(frames*frames,axis=1)[:n]
        return np.pad(result,(0,max(0,n-len(result))))
    hp,pp=power(harmonic),power(percussive)
    share=hp/np.maximum(hp+pp,1e-12)
    notes,velocity,attacks,stats=estimate(harmonic,n,'keyboard')
    # Local waveform agreement with the separate vocal stem is a leakage screen,
    # not source identity or gender inference.
    wave=librosa.util.frame(np.pad(other,(size//2,size//2)),frame_length=size,hop_length=hop).T[:n]
    voice=librosa.util.frame(np.pad(vocal,(size//2,size//2)),frame_length=size,hop_length=hop).T[:n]
    similarity=np.abs(np.sum(wave*voice,axis=1))/np.maximum(
        np.linalg.norm(wave,axis=1)*np.linalg.norm(voice,axis=1),1e-12)
    similarity=np.pad(similarity,(0,max(0,n-len(similarity))))
    allowed=(share>=.75)&(similarity<.65)
    notes[~allowed]=-1;velocity[~allowed]=0;attacks[~allowed]=0
    events=compile_note_events(notes,velocity,attacks,'other_harmonic_pitched_estimate')
    from music.note_events import NoteEvent
    events=[NoteEvent(e.start,e.end,e.pitch,e.velocity,source=e.source,
        confidence=float(np.min(share[max(0,round(e.start*20)):max(round(e.start*20)+1,round(e.end*20))]))) for e in events]
    return events,dict(stats,harmonic_frame_fraction=float(allowed.mean()),events=len(events),
        confidence_measure='minimum measured harmonic power share, not calibrated class probability',
        instrument_identity_verified=False,score_accuracy_verified=False)


def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True)
    p.add_argument('--stems',type=Path,required=True);p.add_argument('--analysis',type=Path,required=True)
    a=p.parse_args()
    with np.load(a.analysis/'performance_curves.npz') as arrays:n=len(arrays['bass_energy'])
    events,proof=residual_notes(mono(a.stems/'other.wav'),mono(a.stems/'vocals.wav'),n)
    path=a.analysis/'note_events.json';data=json.loads(path.read_text())
    data['other_pitched']=[e.to_dict() for e in events];path.write_text(json.dumps(data,indent=2)+'\n')
    proof['source_sha256']=hashlib.sha256(a.source.read_bytes()).hexdigest()
    (a.analysis/'residual_keyboard.json').write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(proof,indent=2))


if __name__=='__main__':main()
