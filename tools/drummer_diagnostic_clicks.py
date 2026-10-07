"""Overlay family-coded diagnostic tones on a real-song excerpt for listening."""
import argparse
import json
from pathlib import Path
import librosa
import numpy as np
import soundfile as sf

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('events',type=Path);p.add_argument('--audio',type=Path,default=Path('Helix Audiolights.mp3'));p.add_argument('--output',type=Path,required=True);p.add_argument('--start',type=float,default=9.5);p.add_argument('--duration',type=float,default=25)
    a=p.parse_args();sr=22050
    y,_=librosa.load(a.audio,sr=sr,mono=True,offset=a.start,duration=a.duration)
    click=np.zeros_like(y)
    rows=json.loads(a.events.read_text())['events']
    freqs={'kick':90,'snare':700,'hihat':6500,'cymbal':2400,'tom':320}
    for event in rows:
        time=event['timestamp']-a.start
        family=event['drum_family']
        if not 0<=time<a.duration or family not in freqs:continue
        hz={'high':480,'mid':310,'floor':150}.get(event.get('tom_class'),freqs[family])
        t=np.arange(round(.055*sr))/sr
        tone=np.sin(2*np.pi*hz*t)*np.exp(-t*85)*.22
        start=round(time*sr);length=min(len(tone),len(y)-start)
        click[start:start+length]+=tone[:length]
    a.output.parent.mkdir(parents=True,exist_ok=True)
    sf.write(a.output,np.clip(y*.65+click,-1,1),sr)
    print(f'Wrote {a.output}: real source offset {a.start}s + diagnostic family tones; not an independent drum annotation')
