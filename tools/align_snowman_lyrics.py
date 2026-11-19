"""Recognize/align actual vocals and compile the existing seven-mouth contract.

Whisper supplies word timing. CMU pronunciations supply phones. Within-word
mouth durations are allocated, not acoustic phone boundaries. Embedded lyric
text is retained and forced-aligned separately for human comparison.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import time
import torch

from tools.analyze_snowman_ensemble import sha
from core.lyric_phoneme_mapper import map_lyric_to_phonemes
from core.lyric_interpreter import interpret_lyric_events
from types import SimpleNamespace

PHONE_MAP={**dict.fromkeys(('AA','AE','AH','AW','AY','ER'),'AH'),
           **dict.fromkeys(('EH','EY','IH','IY'),'EE'),
           **dict.fromkeys(('AO','OW','OY','UH','UW','W'),'OH'),
           **dict.fromkeys(('M','B','P'),'MBP'),**dict.fromkeys(('F','V'),'FV'),'L':'L'}
SYLLABLE_PHONES={'ba':['MBP','AH'],'da':['EE','AH'],'ta':['EE','AH'],
                 'ka':['EE','AH'],'ma':['MBP','AH'],'na':['EE','AH'],'la':['L','AH'],
                 'fo':['FV','OH'],'so':['EE','OH'],'zu':['EE','OH']}


def pronunciation(word, dictionary):
    token=re.sub(r"[^a-z']",'',word.lower())
    candidates=dictionary.get(token)
    if token in SYLLABLE_PHONES:
        shapes=SYLLABLE_PHONES[token];method='nonlexical_sung_syllable_rule'
    elif candidates:
        shapes=[PHONE_MAP.get(re.sub(r'\d','',p),'EE') for p in candidates[0]]
        method='cmu_pronunciation_dictionary'
    else:
        shapes=[s for s in map_lyric_to_phonemes(token) if s!='REST'] or ['AH']
        method='existing_grapheme_fallback'
    compact=[]
    for shape in shapes:
        if not compact or compact[-1]!=shape:compact.append(shape)
    return compact,method


def compile_mouths(words,dictionary):
    result=[]
    last_end=0
    for word in sorted(words,key=lambda w:w['start']):
        start=max(last_end,round(word['start']*1000/50)*50)
        end=round(word['end']*1000/50)*50
        if end<=start:continue
        phones,method=pronunciation(word['word'],dictionary)
        # Native 50ms frames cannot show more mouths than word frames.
        frames=(end-start)//50
        if len(phones)>frames:
            phones=[phones[min(len(phones)-1,round(i*(len(phones)-1)/max(frames-1,1)))] for i in range(frames)]
        for i,phone in enumerate(phones):
            a=start+round(i*frames/len(phones))*50;b=start+round((i+1)*frames/len(phones))*50
            if b>a:result.append(dict(start_ms=a,end_ms=b,phoneme=phone,word=word['word'],
                                     confidence=word.get('probability',0),pronunciation_source=method,
                                     boundary_source='word_aligned_even_phone_allocation'))
        last_end=end
    return result


def select_words(words,phoneme_exercise=False):
    # A sung sound exercise intentionally contains nonwords; low lexical
    # probability must not suppress recognized ba/ah/ee practice syllables.
    # Keep the original probabilities and make this exception explicit.
    return list(words) if phoneme_exercise else [w for w in words if w.get('probability',0)>=.25]


def main():
    import stable_whisper
    import cmudict
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('--ids',nargs='*')
    args=p.parse_args();torch.set_num_threads(1)
    model=stable_whisper.load_model('small.en',device='cpu',download_root='/workspace/runtime/whisper')
    dictionary=cmudict.dict()
    rows=json.loads((args.root/'sources.json').read_text())
    for row in sorted(rows,key=lambda r:(r['id']!='04',r['id'])):
        if args.ids and row['id'] not in args.ids:continue
        song=args.root/'analysis'/row['id'];ready=song/'stems.json';target=song/'vocals.json'
        if target.exists():
            if json.loads(target.read_text())['audio_sha256']!=sha(row['path']):raise ValueError('Stale lyric cache')
            continue
        while not ready.exists():time.sleep(5)
        stem=json.loads(ready.read_text())['stems']['vocals']['path']
        print('VOCAL_START',row['id'],flush=True)
        result=model.transcribe(stem,language='en',fp16=False,verbose=False,temperature=0,
                                condition_on_previous_text=False,no_speech_threshold=.6,
                                suppress_silence=True,regroup=True)
        result.save_as_json(str(song/'whisper_words.json'))
        data=result.to_dict();words=[w for s in data['segments'] for w in s.get('words',[]) if w['end']>w['start']]
        # Low-confidence recognition stays visible in the transcript but does
        # not trigger singing during instrumental passages.
        phoneme_exercise='phoneme' in row['title'].lower()
        accepted=select_words(words,phoneme_exercise)
        reference=row['lyrics'].replace('\\n','\n')
        reference=re.sub(r'\[[^\]]*\]','',reference).strip()
        if reference:
            aligned=model.align(stem,reference,language='en',verbose=False,original_split=True)
            if aligned is not None:aligned.save_as_json(str(song/'embedded_lyrics_aligned.json'))
            (song/'embedded_lyrics.txt').write_text(reference+'\n')
        lines=[dict(start_ms=round(s['start']*1000),end_ms=round(s['end']*1000),text=s['text'].strip()) for s in data['segments']]
        # Word starts, rather than phrase starts, place lyric accents precisely.
        triggers=interpret_lyric_events([SimpleNamespace(text=w['word'],start_ms=round(w['start']*1000),end_ms=round(w['end']*1000)) for w in accepted])
        payload=dict(audio_sha256=sha(row['path']),vocal_stem_sha256=sha(stem),
                     recognition_model='OpenAI Whisper small.en via stable-ts',words=words,lines=lines,
                     word_acceptance='all_recognized_sung_practice_syllables_with_original_confidence' if phoneme_exercise else 'probability_at_least_0.25',
                     mouths=compile_mouths(accepted,dictionary),lyric_interpretation=triggers,
                     reference_lyrics_source='MP3 embedded lyrics' if reference else None,
                     limitations=['Recognized lyrics/word timing need human review, especially sung rap.',
                                  'CMU dictionary phones are allocated inside aligned words; no measured phone boundaries.',
                                  'Male/female parts are authored shared-vocal choreography, not separated voice identities.'])
        target.write_text(json.dumps(payload,indent=2)+'\n')
        print('VOCAL_READY',row['id'],len(words),len(payload['mouths']),flush=True)


if __name__=='__main__':main()
