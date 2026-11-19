"""Fresh source-bound learned drums, harmonic notes and screened vocal cues."""
from __future__ import annotations
import argparse,json,math,re
from pathlib import Path
import numpy as np
import soundfile as sf
from tools.build_prior_sampler_layouts import SAMPLER_SHA
from tools.analyze_band_upgrade import mono,curve,sha
from tools.analyze_band_instruments import estimate
from tools.analyze_band_samplers import mallet_cues,acoustic_vowels
from tools.align_snowman_lyrics import compile_mouths
from models.band_instrument_logic import compile_note_events,event_curves,chord_route
from models.band_sampler_logic import held_bass_heights,cast_duet


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('audio',type=Path);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert sha(a.audio)==SAMPLER_SHA
    root=a.output.resolve();dest=root/'analysis/sampler';dest.mkdir(parents=True,exist_ok=True)
    stems=root/'stems/htdemucs_6s'/a.audio.stem;n=math.ceil(sf.info(a.audio).duration*20)
    vocal=mono(stems/'vocals.wav'); other=mono(stems/'other.wav');arrays={};events={};proof={}
    gate,_,_,mallet_proof=mallet_cues(other,vocal,n);arrays['keyboard_mallet_energy']=gate
    for kind in ('bass','guitar','piano'):
        signal=mono(stems/(kind+'.wav'));notes,velocity,attacks,stats=estimate(signal,n,kind)
        ev=compile_note_events(notes,velocity,attacks,kind+'_stem_harmonic_estimate');events[kind]=[e.to_dict() for e in ev]
        grid,vel,attack,phase=event_curves(ev,n,1 if kind=='bass' else 6,.22 if kind=='bass' else .16)
        for key,val in [('notes',grid),('note_levels',vel),('attack',attack),('phase',phase),('energy',vel.max(axis=1))]:arrays[kind+'_'+key]=val
        proof[kind]=dict(stats,events=len(ev),stem_sha256=sha(stems/(kind+'.wav')))
        if kind!='piano':
            routes=np.full((n,1 if kind=='bass' else 6,3),-1,np.int16)
            for i,row in enumerate(grid):
                for j,route in enumerate(chord_route(tuple(int(x) for x in row if x>=0),kind)):routes[i,j]=route
            arrays[kind+'_routes']=routes
        print(kind,len(ev),flush=True)
    arrays['bass_height']=held_bass_heights(arrays['bass_notes'],arrays['bass_energy'])
    import torch,stable_whisper,cmudict
    torch.set_num_threads(2)
    raw=dest/'whisper_words.json'
    if not raw.exists():
        model=stable_whisper.load_model('small.en',device='cpu')
        result=model.transcribe(str(stems/'vocals.wav'),language='en',fp16=False,verbose=False,temperature=0,
            condition_on_previous_text=False,no_speech_threshold=.6,suppress_silence=True,regroup=True)
        result.save_as_json(str(raw))
    data=json.loads(raw.read_text());words=[];lines=[];rejected=[]
    energy,_,rms=curve(vocal,n)
    for segment in data['segments']:
        ws=[w for w in segment.get('words',[]) if w['end']>w['start'] and w.get('probability',0)>=.40]
        lo,hi=max(0,round(segment['start']*20)),min(n,round(segment['end']*20))
        accepted=bool(ws and hi>lo and np.mean(rms[lo:hi]>.006)>.35
            and np.median([w['probability'] for w in ws])>=.55
            and not re.search('thank you|subscribe|watching',segment['text'],re.I))
        if not accepted:rejected.append(segment);continue
        words.extend(ws);lines.append(dict(start_ms=round(ws[0]['start']*1000),end_ms=round(ws[-1]['end']*1000),
            text=' '.join(w['word'].strip() for w in ws),source='screened_whisper_not_verified_lyrics'))
    vocals=dict(audio_sha256=SAMPLER_SHA,words=words,lines=lines,mouths=compile_mouths(words,cmudict.dict()),
        recognition_model='small.en / stable-ts',rejected_segments=len(rejected),verified_lyrics=False)
    mouths,vowel_proof,rms=acoustic_vowels(vocal,vocals,n);lanes,casting=cast_duet(mouths,lines)
    arrays.update(vocal_route=np.zeros(n,np.int8),vocal_energy=energy,mouth_lanes=lanes,lexical_vocal_activity=np.any(lanes!=0,axis=1))
    np.savez_compressed(dest/'performance_curves.npz',**arrays)
    (dest/'note_events.json').write_text(json.dumps(events,indent=2)+'\n')
    (dest/'vocals.json').write_text(json.dumps(vocals,indent=2)+'\n')
    (dest/'verification.json').write_text(json.dumps(dict(source_sha256=SAMPLER_SHA,stems=proof,mallet_attacks=mallet_proof,
        vocal_stem_sha256=sha(stems/'vocals.wav'),vowels=vowel_proof,casting=casting,
        detection_accuracy_independently_verified=False,mallet_instrument_identity_verified=False),indent=2)+'\n')
    print('Analysis complete',len(words),'accepted words',len(mallet_proof),'mallet candidates',flush=True)


if __name__=='__main__':main()
