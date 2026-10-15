"""Build fresh final-band inputs from selected real-audio excerpts."""
from __future__ import annotations
import argparse, hashlib, json, math, subprocess
from dataclasses import replace
from pathlib import Path
import librosa
import numpy as np
import soundfile as sf
from scipy.ndimage import median_filter
from tools.analyze_band_instruments import estimate
from tools.analyze_band_upgrade import mono, curve, sha
from tools.analyze_band_samplers import mallet_cues
from models.band_instrument_logic import compile_note_events,event_curves,chord_route
from models.band_sampler_logic import held_bass_heights


def vocal_shapes(y,n,enabled):
    """Acoustic vowel-color estimates only; no words or independent voices."""
    energy,_,rms=curve(y,n)
    frames=librosa.util.frame(np.pad(y,(1024,1024)),frame_length=2048,hop_length=800).T[:n]
    spec=np.abs(np.fft.rfft(frames*np.hanning(2048),n=4096,axis=1))**2
    ac=np.fft.irfft(spec,n=4096,axis=1)
    periodic=ac[:,18:267].max(axis=1)/np.maximum(ac[:,0],1e-9)
    f=np.fft.rfftfreq(4096,1/16000)
    def band(a,b):return spec[:,(f>=a)&(f<b)].sum(axis=1)
    low=band(250,800);high=band(1500,3000);mid=band(800,1500)
    # Broad vowel color, never described as a word-level phoneme alignment.
    shapes=np.where(high>low*1.1,3,np.where(mid>high*1.2,4,2)).astype(np.int8)
    active=(rms>max(.006,float(np.quantile(rms,.9))*.12))&(periodic>.48)&enabled
    shapes[~median_filter(active.astype('u1'),size=3).astype(bool)]=0
    shapes=median_filter(shapes,size=3)
    lanes=np.column_stack((shapes,np.zeros(n,np.int8)))
    energy*=shapes!=0
    return energy,lanes,dict(method='isolated vocal RMS/periodicity and broad acoustic vowel color',
        active_frames=int((shapes!=0).sum()),exact_phonemes_verified=False,
        independent_voice_sources=False,verified_lyrics=False,on_screen_words=False)


def analyze(root, row, stems):
    eid=row['excerpt_id'];folder=root/'07_Layouts_and_Sequences'/eid
    audio=folder/'audio.wav';dest=root/'analysis'/eid;dest.mkdir(parents=True,exist_ok=True)
    n=round(sf.info(audio).duration*20);arrays={};events={};proof={}
    vocal=mono(stems/'vocals.wav');other=mono(stems/'other.wav')
    gate,_,_,mallet=mallet_cues(other,vocal,n);arrays['keyboard_mallet_energy']=gate
    for kind in ('bass','guitar','piano'):
        notes,vel,atk,stats=estimate(mono(stems/(kind+'.wav')),n,kind)
        ev=compile_note_events(notes,vel,atk,kind+'_stem_harmonic_estimate')
        events[kind]=[e.to_dict() for e in ev]
        grid,levels,attack,phase=event_curves(ev,n,1 if kind=='bass' else 6,.22 if kind=='bass' else .16)
        for k,v in [('notes',grid),('note_levels',levels),('attack',attack),('phase',phase),('energy',levels.max(axis=1))]:arrays[kind+'_'+k]=v
        if kind!='piano':
            routes=np.full((n,1 if kind=='bass' else 6,3),-1,np.int16)
            for i,ns in enumerate(grid):
                for j,r in enumerate(chord_route(tuple(int(x) for x in ns if x>=0),kind)):routes[i,j]=r
            arrays[kind+'_routes']=routes
        proof[kind]=dict(stats,event_count=len(ev),stem_sha256=sha(stems/(kind+'.wav')))
    # The residual may contain synths, horns and bells: route supported harmonic
    # notes to the unified performer, without claiming a named instrument.
    harmonic=librosa.effects.harmonic(other)
    notes,vel,atk,stats=estimate(harmonic,n,'pitched_other')
    hspec=np.abs(librosa.stft(harmonic,n_fft=2048,hop_length=800))[:,:n]
    vspec=np.abs(librosa.stft(vocal,n_fft=2048,hop_length=800))[:,:n]
    similarity=(hspec*vspec).sum(axis=0)/np.maximum(np.linalg.norm(hspec,axis=0)*np.linalg.norm(vspec,axis=0),1e-9)
    notes[similarity>.65]=-1;vel[similarity>.65]=0
    ev=[replace(e,confidence=.80) for e in compile_note_events(notes,vel,atk,'other_stem_screened_harmonic_estimate') if e.end-e.start>=.10]
    events['pitched_other']=[e.to_dict() for e in ev]
    arrays['bass_height']=held_bass_heights(arrays['bass_notes'],arrays['bass_energy'])
    energy,lanes,vproof=vocal_shapes(vocal,n,row['vocals_expected'])
    arrays.update(vocal_energy=energy,mouth_lanes=lanes,vocal_route=np.zeros(n,np.int8),lexical_vocal_activity=np.zeros(n,bool))
    np.savez_compressed(dest/'performance_curves.npz',**arrays)
    (dest/'note_events.json').write_text(json.dumps(events,indent=2)+'\n')
    (dest/'vocals.json').write_text(json.dumps(dict(audio_sha256=sha(audio),words=[],lines=[],mouths=[],verified_lyrics=False,acoustic_estimates=vproof),indent=2)+'\n')
    proof=dict(source_sha256=sha(audio),original_audio_sha256=row['sha256'],excerpt=row,
        stems=proof,stem_hashes={p.name:sha(p) for p in stems.glob('*.wav')},mallet_attacks=mallet,
        pitched_other=dict(stats,events=len(ev),vocal_similarity_ceiling=.65,percussion_exclusion='HPSS harmonic component',instrument_identity_verified=False),
        vocals=vproof,detection_accuracy_independently_verified=False,
        source_separation=dict(model='htdemucs_6s',shifts=0,overlap=.1,weights='5c90dfd2-34c22ccb.th',leakage_possible=True))
    (dest/'verification.json').write_text(json.dumps(proof,indent=2)+'\n')
    from tools.transcribe_drummer_adtof import transcribe
    transcribe(audio,stems/'drums.wav',dest/'drums.json',dest/'drum_activations.npy')
    from tools.integrate_drummer_v3_into_xsq import inject_drummer_v3
    # Inject into a copy of the current native template; never edit source input.
    report=inject_drummer_v3(Path(__file__).resolve().parents[1]/'template.xsq',folder/'drummer.xsq',audio,transcription_path=dest/'drums.json')
    (dest/'drummer_report.json').write_text(json.dumps(report,indent=2)+'\n')
    (folder/'source.json').write_text(json.dumps(dict(row,excerpt_wav_sha256=sha(audio)),indent=2)+'\n')
    return proof


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--stems',type=Path,required=True);p.add_argument('--ids',nargs='*');a=p.parse_args()
    root=a.root.resolve();rows=json.loads((root/'05_Source_Excerpt_Manifests/selected_excerpts.json').read_text())
    for row in rows:
        eid=row['excerpt_id']
        if a.ids and eid not in a.ids:continue
        audio=root/'07_Layouts_and_Sequences'/eid/'audio.wav'
        if sha(Path(row['path']))!=row['sha256']:
            raise ValueError('Original recording hash changed: '+eid)
        if not audio.exists() or audio.stat().st_size<100:
            audio.parent.mkdir(parents=True,exist_ok=True)
            # Attached cover pictures must never be selected as an output stream.
            subprocess.run(['ffmpeg','-v','error','-y','-i',row['path'],'-ss',str(row['start_seconds']),
                '-t',str(row['seconds']),'-map','0:a:0','-vn','-ar','44100','-ac','2','-c:a','pcm_s16le',str(audio)],check=True)
        if abs(sf.info(audio).duration-row['seconds'])>1/44100:
            raise ValueError('Decoded excerpt duration mismatch: '+eid)
        dest=a.stems.resolve()/eid;stems=dest/'htdemucs_6s/audio'
        receipt=root/'analysis'/eid/'drummer_report.json'
        if receipt.exists() and (root/'analysis'/eid/'verification.json').exists():
            previous=json.loads((root/'analysis'/eid/'verification.json').read_text())
            if previous['source_sha256']==sha(audio):print('cached verified source analysis',eid,flush=True);continue
        stemreceipt=dest/'source_sha256.txt'
        bound=stemreceipt.exists() and stemreceipt.read_text().strip()==sha(audio)
        prior=root/'analysis'/eid/'verification.json'
        if not bound and prior.exists():
            old=json.loads(prior.read_text())
            bound=old['source_sha256']==sha(audio) and all((stems/name).exists() and sha(stems/name)==digest for name,digest in old['stem_hashes'].items())
        if not (stems/'vocals.wav').exists() or not bound:
            subprocess.run(['python','-m','demucs.separate','-n','htdemucs_6s','--device','cpu','--shifts','0','--overlap','.1','-j','2','--out',str(dest),str(audio)],check=True)
        dest.mkdir(parents=True,exist_ok=True);stemreceipt.write_text(sha(audio)+'\n')
        proof=analyze(root,row,stems)
        print('ANALYZED',eid,row['filename'],{k:v['event_count'] for k,v in proof['stems'].items()},proof['vocals']['active_frames'],flush=True)


if __name__=='__main__':main()
