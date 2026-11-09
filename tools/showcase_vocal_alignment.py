"""Corroborate recognized vocal text against the recording's embedded lyrics."""
from __future__ import annotations
import argparse,difflib,json,re,subprocess
from pathlib import Path
import numpy as np


def tokens(text):return re.findall(r"[a-z]+",text.lower())


def corroborated(text,reference):
    words=tokens(text)
    if len(words)<2:return False
    ref=tokens(reference)
    match=difflib.SequenceMatcher(None,words,ref,autojunk=False)
    blocks=match.get_matching_blocks()
    return max((b.size for b in blocks),default=0)>=min(3,len(words)) and sum(b.size for b in blocks)/len(words)>=.80


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--stems',type=Path,required=True);p.add_argument('--ids',nargs='*');a=p.parse_args()
    import torch,stable_whisper,cmudict
    from tools.align_snowman_lyrics import compile_mouths
    from tools.analyze_band_samplers import acoustic_vowels
    from tools.analyze_band_upgrade import mono,curve,sha
    torch.set_num_threads(3)
    model=stable_whisper.load_model('small.en',device='cpu')
    root=a.root.resolve();rows=json.loads((root/'05_Source_Excerpt_Manifests/selected_excerpts.json').read_text())
    for row in rows:
        if not row['vocals_expected']:continue
        if a.ids and row['excerpt_id'] not in a.ids:continue
        eid=row['excerpt_id'];dest=root/'analysis'/eid
        current_sha=sha(root/'07_Layouts_and_Sequences'/eid/'audio.wav')
        raw=dest/f'whisper_words_{current_sha[:16]}.json'
        if (dest/'vocal_alignment.json').exists():
            old=json.loads((dest/'vocal_alignment.json').read_text())
            if old.get('source_sha256')==current_sha:continue
        if not dest.exists():raise ValueError('Run source analysis first: '+eid)
        source=a.stems.resolve()/eid/'htdemucs_6s/audio/vocals.wav'
        bound=json.loads((dest/'verification.json').read_text())
        if bound['source_sha256']!=sha(root/'07_Layouts_and_Sequences'/eid/'audio.wav') or bound['stem_hashes']['vocals.wav']!=sha(source):
            raise ValueError('Vocal stem is not bound to the current excerpt: '+eid)
        metadata=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format_tags','-of','json',row['path']]))
        reference='\n'.join(v for k,v in metadata.get('format',{}).get('tags',{}).items() if 'lyric' in k.lower())
        (dest/'embedded_lyrics.txt').write_text(reference)
        if not raw.exists():
            result=model.transcribe(str(source),language='en',fp16=False,verbose=False,temperature=0,
                condition_on_previous_text=False,no_speech_threshold=.6,suppress_silence=True,regroup=True)
            result.save_as_json(str(raw))
        data=json.loads(raw.read_text());words=[];lines=[];rejected=[]
        for segment in data['segments']:
            ws=[w for w in segment.get('words',[]) if w['end']>w['start'] and w.get('probability',0)>=.45]
            text=' '.join(w['word'].strip() for w in ws)
            good=bool(ws and reference and corroborated(text,reference) and np.median([w.get('probability',0) for w in ws])>=.60)
            if good:
                words.extend(ws);lines.append(dict(start_ms=round(ws[0]['start']*1000),end_ms=round(ws[-1]['end']*1000),text=text,
                    source='embedded lyric text corroborated by isolated-vocal ASR; estimated word timing'))
            else:rejected.append(dict(text=text,start=segment['start'],end=segment['end']))
        vocals=dict(audio_sha256=sha(root/'07_Layouts_and_Sequences'/eid/'audio.wav'),words=words,lines=lines,
            mouths=compile_mouths(words,cmudict.dict()),lyric_reference='embedded source metadata',
            verified_lyrics=bool(lines),independent_listening_verified=False,phoneme_boundaries_acoustically_aligned=False)
        y=mono(source)
        with np.load(dest/'performance_curves.npz') as z:arrays={k:z[k].copy() for k in z.files}
        n=len(arrays['vocal_energy']);mouths,proof,rms=acoustic_vowels(y,vocals,n)
        # Retain conservative measured vowel color where no lexical evidence
        # exists; never invent a second singer from the same mixed stem.
        old=arrays['mouth_lanes'][:,0];mouths=np.where(mouths>0,mouths,old)
        energy,_,_=curve(y,n);energy*=mouths!=0
        arrays.update(vocal_energy=energy,mouth_lanes=np.column_stack((mouths,np.zeros(n,np.int8))),
            lexical_vocal_activity=np.array([any(w['start']<=i/20<w['end'] for w in words) for i in range(n)]))
        np.savez_compressed(dest/'performance_curves.npz',**arrays)
        (dest/'vocals.json').write_text(json.dumps(vocals,indent=2)+'\n')
        (dest/'vocal_alignment.json').write_text(json.dumps(dict(source_sha256=vocals['audio_sha256'],reference_available=bool(reference),
            accepted_lines=len(lines),accepted_words=len(words),rejected_segments=rejected,acoustic_vowels=proof,
            independent_voices=False,phone_boundaries_verified=False,lyrics_checked_against_embedded_reference=True),indent=2)+'\n')
        print('VOCALS_ALIGNED',eid,len(lines),len(words),flush=True)


if __name__=='__main__':main()
