"""Derive independent playable roles and a tightly bounded vocal clock."""
import argparse,hashlib,json
from pathlib import Path
import librosa,numpy as np,soundfile as sf
from scipy.signal import find_peaks
from music.note_events import NoteEvent
from music.review_score import vocal_clock,pitched_roles


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def prepare(root,eid):
    folder=root/'analysis'/eid;audio=root/'sources'/eid/'audio.wav';stems=root/'stems'/eid
    bound=json.loads((stems/'source.json').read_text())
    if bound['source_sha256']!=sha(audio):raise ValueError('stem/audio mismatch')
    for name,digest in bound['stem_hashes'].items():
        if sha(stems/(name+'.wav'))!=digest:raise ValueError('changed stem')
    original=folder/'baseline_note_events.json'
    if not original.exists():original.write_bytes((folder/'note_events.json').read_bytes())
    events=json.loads(original.read_text());proof=json.loads((folder/'verification.json').read_text())
    with np.load(folder/'performance_curves.npz') as z:curves={k:z[k].copy() for k in z.files}
    def wave(name):
        y,sr=sf.read(stems/(name+'.wav'),dtype='float32',always_2d=True)
        return librosa.resample(y.mean(axis=1),orig_sr=sr,target_sr=16000)
    other=wave('other');vocal=wave('vocals')
    flux=librosa.onset.onset_strength(y=other,sr=16000,hop_length=160,n_fft=1024)
    peaks,_=find_peaks(flux,distance=7,prominence=max(.35,float(np.quantile(flux,.9))*.18))
    keys,mallets,corrections=pitched_roles([NoteEvent(**e) for e in events.get('piano',[])],
        [NoteEvent(**e) for e in events.get('pitched_other',[])],proof['mallet_attacks'],curves['keyboard_mallet_energy'],peaks/100)
    events['piano']=[e.to_dict() for e in keys]
    (folder/'note_events.json').write_text(json.dumps(events,indent=2)+'\n')
    selected=next(x for x in json.loads((root/'sources/selected_excerpts.json').read_text()) if x['excerpt_id']==eid)
    track=vocal_clock(vocal,selected['vocals_expected']);np.savez_compressed(folder/'vocal_clock.npz',**track)
    report=dict(source_sha256=sha(audio),keyboard=[e.to_dict() for e in keys],mallets=[e.to_dict() for e in mallets],
        onset_corrections=corrections,vocal_clock_ms=10,vocal_window_ms=40,release_tail_ms=0,
        even_phone_durations_used=False,separate_voice_sources=False,instrument_identity_verified=False,
        provenance='source-bound harmonic residual notes and screened ringing attacks; role assignment estimates')
    (folder/'pitched_roles.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PREPARED',eid,len(keys),'keyboard notes;',len(mallets),'mallet attacks',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);a=p.parse_args()
    for eid in ['E03','E14']:prepare(a.root.resolve(),eid)
