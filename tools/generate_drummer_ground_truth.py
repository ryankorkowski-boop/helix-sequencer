#!/usr/bin/env python3
"""Generate a deterministic drum clip with known ground-truth events."""
from __future__ import annotations
import argparse, json, wave
from pathlib import Path
import numpy as np

def generate(wav_path: Path, events_path: Path) -> None:
    sr=44100; duration=12.0; n=int(sr*duration); bpm=120; beat=.5
    audio=np.zeros(n,dtype=np.float32); rng=np.random.default_rng(42); events=[]
    def add(t, freq=None, amp=.5, decay=.1, noise=False):
        s=int(t*sr); L=min(int(decay*sr),n-s)
        if L<=0:return
        tt=np.arange(L)/sr; env=np.exp(-tt/decay)
        y=(rng.normal(size=L) if noise else np.sin(2*np.pi*freq*tt))*env*amp
        audio[s:s+L]+=y
    for bar in range(6):
        b=bar*2
        for t in [b,b+.5,b+1,b+1.5]: events.append((t,'kick')); add(t,58,.9,.18)
        for t in [b+.5,b+1.5]: events.append((t,'snare')); add(t,190,.25,.1); add(t,None,.65,.08,True)
        for i in range(8):
            t=b+i*.25; events.append((t,'hat')); add(t,None,.25,.025,True)
        events.append((b,'crash')); add(b,None,.75,.35,True)
    fill=8
    for i,(name,f) in enumerate([('tom_low',90),('tom_mid',125),('tom_high',175),('snare',190),('kick',58),('crash',None)]):
        t=fill+i*.125; events.append((t,name))
        if name=='crash': add(t,None,.75,.35,True)
        elif name=='snare': add(t, f,.2,.08); add(t,None,.6,.07,True)
        elif name=='kick': add(t,f,.9,.18)
        else: add(t,f,.7,.16)
    audio=np.clip(audio,-.95,.95); wav_path.parent.mkdir(parents=True,exist_ok=True); events_path.parent.mkdir(parents=True,exist_ok=True)
    with wave.open(str(wav_path),'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((audio*32767).astype(np.int16).tobytes())
    events_path.write_text(json.dumps([{'time':round(t,4),'event':k} for t,k in events],indent=2)+'\n')
    print(f'Generated {wav_path} and {events_path}; {len(events)} known events')

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--wav',type=Path,required=True); p.add_argument('--events',type=Path,required=True); a=p.parse_args(); generate(a.wav,a.events)
