#!/usr/bin/env python3
"""Generate small deterministic WAV fixtures and exact JSON ground truth using stdlib only."""
from __future__ import annotations
import argparse, json, math, random, struct, wave
from pathlib import Path

SR=44100; DUR=8.0

def voice(drum,t,vel,n):
    x=t-n; v=max(0.0,vel)
    if x<0 or x>=0.45: return 0.0
    if drum=='kick': return math.sin(2*math.pi*(120-70*min(1,x/.12))*x)*math.exp(-18*x)*v
    if drum=='snare': return (2*random.Random(n).random()-1)*math.exp(-28*x)*v + .18*math.sin(2*math.pi*190*x)*math.exp(-20*x)*v
    if drum=='hihat': return (2*random.Random(int(n*1000)+7).random()-1)*math.exp(-70*x)*v
    if drum=='tom': return math.sin(2*math.pi*(180-70*x)*x)*math.exp(-12*x)*v
    return (2*random.Random(int(n*1000)+13).random()-1)*math.exp(-5*x)*v

def pattern(kind):
    ev=[]
    for i in range(16):
        t=i*.5
        ev.append({'time':t,'drum':'kick','velocity':.9})
        if i%2==1: ev.append({'time':t,'drum':'snare','velocity':.8})
        ev.append({'time':t,'drum':'hihat','velocity':.5})
    if kind=='fills':
        for t,d in [(6.0,'tom'),(6.25,'tom'),(6.5,'tom'),(6.75,'tom'),(7.0,'cymbal')]: ev.append({'time':t,'drum':d,'velocity':.85})
    if kind=='sparse':
        ev=[e for e in ev if e['drum']!='hihat' or int(e['time']*2)%2==0]
    return ev

def render(events,path):
    frames=int(DUR*SR); data=[]
    for i in range(frames):
        t=i/SR; y=0.0
        for e in events:
            y+=voice(e['drum'],t,e['velocity'],e['time'])
        data.append(max(-1,min(1,y*.55)))
    with wave.open(str(path),'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(b''.join(struct.pack('<h',int(v*32767)) for v in data))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output',type=Path,required=True); a=ap.parse_args();
    for kind in ('basic','fills','sparse'):
        events=pattern(kind); wav=a.output/'audio'/'synthetic'/f'{kind}.wav'; gt=a.output/'ground_truth'/f'{kind}.json'; wav.parent.mkdir(parents=True,exist_ok=True); gt.parent.mkdir(parents=True,exist_ok=True); render(events,wav); gt.write_text(json.dumps({'track_id':f'synthetic_{kind}','audio_path':str(wav.relative_to(a.output)).replace('\\','/'),'events':events,'source_format':'synthetic'},indent=2)+'\n')
        print(wav,gt)
if __name__=='__main__': main()
