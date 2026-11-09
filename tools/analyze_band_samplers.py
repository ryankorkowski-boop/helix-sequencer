"""Refine source-bound vowels and mallet cues before choosing review excerpts."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
from pathlib import Path

import librosa
import numpy as np
from scipy.ndimage import median_filter
from scipy.signal import find_peaks
import soundfile as sf

from models.band_sampler_logic import SHAPE_NAMES, cast_duet, contiguous_runs, held_bass_heights, vowel_token, sung_syllable
from tools.analyze_band_upgrade import curve, mono, pitch_notes
from tools.align_snowman_lyrics import compile_mouths

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT/'outputs/Snowman_Ensemble'
PREVIOUS = ROOT/'outputs/Snowman_Band_Upgrade'
OUT = ROOT/'outputs/Intricate_Band_Samplers'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def refine_lyrics(row,vocals):
    """Prefer credible embedded-reference timing, never a failed forced segment."""
    import cmudict
    result=copy.deepcopy(vocals)
    proof={'method':'retain recognized vocables; adopt screened embedded-reference alignments where available',
           'accepted_reference_segments':[],'rejected_reference_segments':[]}
    aligned=OLD/'analysis'/row['id']/'embedded_lyrics_aligned.json'
    second=OUT/'analysis'/row['id']/'recognition_second_pass.json'
    if aligned.exists():
        segments=json.loads(aligned.read_text())['segments']
        good=[]
        def tokens(text):return set(re.findall('[a-z]+',text.lower()))
        for segment in segments:
            words=[w for w in segment.get('words',[]) if w['end']>w['start']]
            confidence=float(np.median([w.get('probability',0) for w in words])) if words else 0
            duration=segment['end']-segment['start']
            recognized_near=[w for w in vocals['words'] if segment['start']-.3<=w['start']<=segment['end']+.3]
            agreement=len(tokens(segment['text']) & tokens(' '.join(w['word'] for w in recognized_near)))
            max_conf=max((w.get('probability',0) for w in words),default=0)
            recognized_conf=max((w.get('probability',0) for w in recognized_near),default=0)
            corroborated=bool(agreement>=2 and max(max_conf,recognized_conf)>=.85 and .6<=duration<=8)
            accepted=bool(len(words)>=2 and (confidence>=.35 or corroborated) and duration<=max(12,len(words)*1.2))
            item=dict(start_ms=round(segment['start']*1000),end_ms=round(segment['end']*1000),
                      text=segment['text'].strip(),median_word_confidence=confidence,
                      independent_recognized_token_agreement=agreement)
            proof['accepted_reference_segments' if accepted else 'rejected_reference_segments'].append(item)
            if accepted:good.append((segment,words))
        # Keep the explicitly sung nonlexical syllables that embedded text omits.
        vocables=[w for w in vocals['words'] if sung_syllable(w['word']) and not any(
            w['start']>=s['start'] and w['end']<=s['end'] for s,_ in good)]
        words=sorted([w for _,ws in good for w in ws]+vocables,key=lambda w:w['start'])
        lines=[dict(start_ms=round(s['start']*1000),end_ms=round(s['end']*1000),text=s['text'].strip(),
                    lyric_source='screened_embedded_reference_alignment') for s,_ in good]
        # A failed forced segment must not erase an independently recognized
        # matching lyric. Conversely generic hallucinations in an instrumental
        # intro have little agreement with the actual supplied lyric text.
        all_reference=tokens(' '.join(s['text'] for s in segments))
        fallback=[]
        for line in vocals['lines']:
            lo,hi=line['start_ms']/1000,line['end_ms']/1000
            if any(lo>=s['start']-.3 and hi<=s['end']+.3 for s,_ in good):continue
            lexical=tokens(line['text'])
            original=[w for w in vocals['words'] if lo<=w['start']<hi and w['end']>w['start']]
            conf=float(np.median([w.get('probability',0) for w in original])) if original else 0
            if len(lexical)>=3 and len(lexical & all_reference)/len(lexical)>=.65 and conf>=.60:
                free=[w for w in original if not any(s['start']<=w['start']<=s['end'] for s,_ in good)]
                if free:
                    words+=free;fallback.append(dict(line,lyric_source='corroborated recognized fallback for failed reference'))
        lines+=fallback;words=sorted(words,key=lambda w:w['start'])
        lines += [dict(start_ms=round(w['start']*1000),end_ms=round(w['end']*1000),text=w['word'].strip(),
                       lyric_source='recognized_nonlexical_vocable') for w in vocables if w['end']>w['start']]
        result.update(words=words,lines=sorted(lines,key=lambda l:l['start_ms']),mouths=compile_mouths(words,cmudict.dict()))
        proof['embedded_alignment_sha256']=sha(aligned)
        proof['corroborated_recognized_fallback_lines']=fallback
    elif second.exists():
        data=json.loads(second.read_text());words=[];lines=[]
        title_corrections=[]
        for s in data['segments']:
            ws=[w for w in s.get('words',[]) if w['end']>w['start']]
            if not ws:continue
            conf=float(np.median([w.get('probability',0) for w in ws]))
            # Reject low-information hallucinated generic speech on music.
            if conf<.30 or re.search(r"I'm not a|thank you for watching|subscribe",s['text'],re.I):
                continue
            # User-supplied title plus the repeatedly recognized exact refrain
            # resolves the homophonic "Best diverse" without changing timing.
            if row['id']=='05' and re.search(r'for the rest of us',s['text'],re.I):
                split=next((j for j,w in enumerate(ws) if w['word'].strip().lower()=='for'),None)
                if split and split<=3:
                    title_corrections.append(dict(before=s['text'].strip(),after='Festivus for the rest of us',
                                                  start_ms=round(s['start']*1000),source='user-supplied song title and repeated refrain'))
                    ws=[dict(word=' Festivus',start=ws[0]['start'],end=ws[split-1]['end'],
                             probability=min(w.get('probability',0) for w in ws[:split]),
                             spelling_source='title/reference correction')]+ws[split:]
                    s=dict(s,text='Festivus for the rest of us')
            words+=ws
            lines.append(dict(start_ms=round(s['start']*1000),end_ms=round(s['end']*1000),text=s['text'].strip(),
                              lyric_source='second recognition on original mix with title context'))
        vocables=[w for w in vocals['words'] if sung_syllable(w['word']) and not any(
            w['start']*1000>=s['start_ms'] and w['end']*1000<=s['end_ms'] for s in lines)]
        words=sorted(words+vocables,key=lambda w:w['start'])
        lines += [dict(start_ms=round(w['start']*1000),end_ms=round(w['end']*1000),text=w['word'].strip(),
                       lyric_source='recognized_nonlexical_vocable') for w in vocables if w['end']>w['start']]
        result.update(words=words,lines=sorted(lines,key=lambda l:l['start_ms']),mouths=compile_mouths(words,cmudict.dict()))
        proof.update(method='second Whisper recognition on original mix with title context',
                     second_recognition_sha256=sha(second),accepted_segments=len(lines),title_spelling_corrections=title_corrections)
    result['lyric_refinement']=proof
    return result


def acoustic_vowels(a, vocals, n):
    """Recover voiced gaps; calibrate rounded/open color from existing vowel events.

    This is an acoustic viseme estimate, not a new lexical transcription.
    Existing lexical events retain priority. Known sung vowel tokens are kept
    even below a generic word-confidence filter and use one sustained shape.
    """
    mouths = np.zeros(n, dtype=np.int8)
    for e in vocals['mouths']:
        mouths[max(0,e['start_ms']//50):min(n,(e['end_ms']+49)//50)] = SHAPE_NAMES.index(e['phoneme'])
    token_fixes = []
    for w in vocals['words']:
        shape = vowel_token(w['word'])
        if not shape:
            continue
        lo, hi = max(0,round(w['start']*20)), min(n,round(w['end']*20))
        if hi > lo:
            mouths[lo:hi] = SHAPE_NAMES.index(shape)
            token_fixes.append(dict(start_ms=lo*50,end_ms=hi*50,shape=shape,word=w['word'],
                                    original_confidence=w.get('probability',0)))
    frames = librosa.util.frame(np.pad(a, (1024,1024)),frame_length=2048,hop_length=800).T[:n]
    frames = np.pad(frames,((0,max(0,n-len(frames))),(0,0)))
    windowed = frames*np.hanning(2048)
    power = np.abs(np.fft.rfft(windowed,n=4096,axis=1))**2
    ac = np.fft.irfft(power,n=4096,axis=1)[:,:2048]
    # Exclude the unvoiced short-lag lobe; a periodic sung signal needs a
    # significant repeat at a plausible voice period, not just stem energy.
    periodicity = ac[:,18:267].max(axis=1)/np.maximum(ac[:,0],1e-8)
    rms = np.sqrt(np.mean(frames*frames,axis=1))
    mfcc = librosa.feature.mfcc(y=a,sr=16000,n_mfcc=16,n_fft=2048,hop_length=800)[:, :n].T
    mfcc = np.pad(mfcc,((0,max(0,n-len(mfcc))),(0,0)))[:,1:13]
    scale = np.maximum(np.std(mfcc,axis=0),2)
    feature = mfcc/scale
    templates = {}
    for shape in ('OH','AH','EE'):
        ids = (mouths == SHAPE_NAMES.index(shape)) & (rms>.007) & (periodicity>.48)
        if ids.sum() >= 8:
            templates[shape] = np.median(feature[ids],axis=0)
    voiced = (rms>max(.006,float(np.quantile(rms,.90))*.065)) & (periodicity>.58)
    voiced = median_filter(voiced.astype(np.uint8),size=3).astype(bool)
    inferred = []
    for lo,hi in contiguous_runs(voiced & (mouths==0)):
        if hi-lo < 3:
            continue
        vector = np.median(feature[lo:hi],axis=0)
        distances = sorted((float(np.linalg.norm(vector-v)),k) for k,v in templates.items())
        if not distances or distances[0][0] > 5.0:
            continue
        shape = distances[0][1]
        mouths[lo:hi] = SHAPE_NAMES.index(shape)
        inferred.append(dict(start_ms=lo*50,end_ms=hi*50,shape=shape,
                             method='periodic vocal gap / recording-calibrated spectral vowel color',
                             spectral_distance=round(distances[0][0],4),
                             periodicity=round(float(np.median(periodicity[lo:hi])),4),
                             lexical_word_inferred=False))
    # Do not leave mouths open over stem silence; conservative -46dBFS floor.
    mouths[rms < .005] = 0
    return mouths, dict(sustained_vowel_token_fixes=token_fixes,acoustic_gap_visemes=inferred,
                       templates=list(templates),phone_boundaries_acoustically_aligned=False,
                       lexical_text_preserved=True), rms


def mallet_cues(other, vocal, n):
    """Select pitched, ringing attacks in 'other', excluding broadband/noisy hits.

    Estimates xylophone/bell-like articulation; does not identify a specific
    instrument or treat the entire other bus as a keyboard.
    """
    energy,attack,rms = curve(other,n)
    spectrum = np.abs(librosa.stft(other,n_fft=2048,hop_length=800)).T[:n]
    frequencies = librosa.fft_frequencies(sr=16000,n_fft=2048)
    vocal_s = np.abs(librosa.stft(vocal,n_fft=2048,hop_length=800)).T[:n]
    onset = librosa.onset.onset_detect(y=other,sr=16000,hop_length=800,delta=.06,wait=3)
    gate = np.zeros(n,dtype=np.float32)
    notes = np.full((n,6),-1,dtype=np.int16)
    accepted = []
    for i in onset:
        if i+5 >= min(n,len(spectrum)) or energy[i]<.10:
            continue
        col = spectrum[i:i+2].mean(axis=0)
        power = col**2
        bright = (frequencies>=400)&(frequencies<=2600)
        peaks,_ = find_peaks(col,distance=8)
        peaks = [k for k in peaks if bright[k]]
        if not peaks:
            continue
        k = max(peaks,key=lambda p:col[p])
        concentration = float(power[max(0,k-3):k+4].sum()/max(power.sum(),1e-9))
        early = float(rms[i:min(n,i+2)].mean())
        late = float(rms[i+3:min(n,i+7)].mean())
        v = vocal_s[i:i+2].mean(axis=0)
        similarity = float(np.dot(col,v)/max(np.linalg.norm(col)*np.linalg.norm(v),1e-9))
        # A ringing narrow-band peak, decaying after the attack, without a
        # spectrum nearly identical to the simultaneous vocal leakage.
        if concentration<.10 or early<late*1.04 or similarity>.82:
            continue
        midi = int(round(librosa.hz_to_midi(frequencies[k])))
        if not 60<=midi<=96:
            continue
        length = min(n-i,10)
        env = energy[i]*np.exp(-np.arange(length)/4)
        gate[i:i+length] = np.maximum(gate[i:i+length],env)
        for j in range(length):
            if env[j]>.08:
                notes[i+j,0] = midi
        accepted.append(dict(start_ms=int(i*50),midi=midi,concentration=round(concentration,4),
                             decay_ratio=round(early/max(late,1e-9),3),
                             vocal_similarity=round(similarity,3)))
    return gate,attack*(gate>.08),notes,accepted


def choose_window(arrays,n,minimum_lyrics=.35):
    best = (-1,0,None)
    for lo in range(0,n-840+1,10):
        hi = lo+840
        coverage = {k:float(np.mean(arrays[k+'_energy'][lo:hi]>.12)) for k in ('bass','guitar','piano','vocal')}
        lyric_coverage=float(np.mean(arrays['lexical_vocal_activity'][lo:hi]))
        if lyric_coverage<minimum_lyrics:
            continue
        # Strong actual note/attack evidence has more value than normalized RMS.
        guitar = float(np.mean(arrays['guitar_attack'][lo:hi]>.08))
        keys = float(np.mean(np.any(arrays['piano_notes'][lo:hi]>=0,axis=1)))
        score = (min(coverage['guitar'],coverage['piano'])*5+coverage['guitar']+
                 coverage['piano']+coverage['vocal']*.4+coverage['bass']*.2+guitar*.1+keys*.1)
        coverage['lexical_vocals']=lyric_coverage
        if score > best[0]:
            best = (score,lo,coverage)
    return best


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--ids',nargs='+',default=['00','01','02','03','05'])
    args=parser.parse_args();OUT.mkdir(parents=True,exist_ok=True)
    sources=json.loads((OLD/'sources.json').read_text());report=[]
    for row in sources:
        if row['id'] not in args.ids:
            continue
        target=OUT/'analysis'/row['id'];target.mkdir(parents=True,exist_ok=True)
        previous=PREVIOUS/'analysis'/row['id']/'performance_curves.npz'
        arrays={k:v.copy() for k,v in np.load(previous).items()}
        n=len(arrays['vocal_energy'])
        stem=OLD/'stems/htdemucs_6s'/Path(row['path']).stem
        original=OLD/'shows'/f'{row["id"]}_band/media/song.mp3'
        assert sha(original)==row['sha256']
        print('ANALYZE',row['id'],row['title'],flush=True)
        v=mono(stem/'vocals.wav');other=mono(stem/'other.wav')
        source_vocals=refine_lyrics(row,json.loads((OLD/'analysis'/row['id']/'vocals.json').read_text()))
        mouths,vowel_proof,rms=acoustic_vowels(v,source_vocals,n)
        lanes,casting=cast_duet(mouths,source_vocals['lines'])
        arrays['mouth_lanes']=lanes
        lexical=np.zeros(n,dtype=bool)
        for line in source_vocals['lines']:
            words=re.findall('[a-z]+',line['text'].lower())
            if words and not all(sung_syllable(w) for w in words):
                lexical[max(0,line['start_ms']//50):min(n,(line['end_ms']+49)//50)]=True
        arrays['lexical_vocal_activity']=lexical & (rms>.005)
        arrays['bass_height']=held_bass_heights(arrays['bass_notes'],arrays['bass_energy'])
        mallet,mallet_attack,mallet_notes,mallet_proof=mallet_cues(other,v,n)
        arrays['keyboard_mallet_energy']=mallet
        arrays['piano_energy']=np.maximum(arrays['piano_energy'],mallet)
        arrays['piano_attack']=np.maximum(arrays['piano_attack'],mallet_attack)
        for i in np.flatnonzero(mallet>.08):
            candidates=list(dict.fromkeys(int(x) for x in np.r_[arrays['piano_notes'][i],mallet_notes[i]] if x>=0))
            arrays['piano_notes'][i]=-1;arrays['piano_notes'][i,:len(candidates[:6])]=candidates[:6]
        np.savez_compressed(target/'performance_curves.npz',**arrays)
        payload=copy.deepcopy(source_vocals);payload['sampler_vowel_refinement']=vowel_proof
        payload['authored_singer_casting']=casting
        (target/'vocals.json').write_text(json.dumps(payload,indent=2)+'\n')
        score,start,coverage=choose_window(arrays,n,.55 if row['id']=='02' else .35)
        stems={k:dict(sha256=sha(stem/(k+'.wav')),rms=round(float(np.sqrt(np.mean(sf.read(stem/(k+'.wav'),dtype='float32')[0]**2))),5)) for k in ('bass','guitar','piano','other','vocals','drums')}
        proof=dict(id=row['id'],title=row['title'],source_sha256=row['sha256'],frames=n,
                   previous_analysis_sha256=sha(previous),source_vocals_sha256=sha(OLD/'analysis'/row['id']/'vocals.json'),
                   stems=stems,vowels=vowel_proof,mallet_attacks=mallet_proof,
                   lyric_refinement=source_vocals['lyric_refinement'],
                   singer_casting='authored alternating phrases / shared refrains and backing vocables; no gender or identity inference',
                   singer_active_frames=[int(np.count_nonzero(lanes[:,k])) for k in (0,1)],
                   best_42s_start_seconds=start/20,window_coverage=coverage,window_score=score)
        (target/'verification.json').write_text(json.dumps(proof,indent=2)+'\n');report.append(proof)
        print('READY',row['id'],'vowel gaps',len(vowel_proof['acoustic_gap_visemes']),'mallets',len(mallet_proof),
              'both singers',proof['singer_active_frames'],'window',start/20,flush=True)
    (OUT/'analysis_verification.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
