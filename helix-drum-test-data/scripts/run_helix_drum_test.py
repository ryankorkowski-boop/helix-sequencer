#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, statistics, sys
from pathlib import Path
from collections import defaultdict

CLASSES=('kick','snare','hihat','tom','cymbal')

def load_gt(path): return json.loads(path.read_text(encoding='utf-8'))

def flatten(pred):
    out=[]
    for key, events in pred.items():
        for e in events:
            drum=str(getattr(e,'drum_type',key.replace('_events','')))
            if drum in CLASSES: out.append((float(e.timestamp),drum))
    return sorted(out)

def match(gt,pred,tol):
    used=set(); matches=[]
    for gi,g in enumerate(gt):
        candidates=[(abs(p[0]-g[0]),pi,p) for pi,p in enumerate(pred) if pi not in used and p[1]==g[1] and abs(p[0]-g[0])<=tol]
        if candidates:
            _,pi,p=min(candidates); used.add(pi); matches.append((gi,pi,p[0]-g[0]))
    return matches, used

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',type=Path,required=True); ap.add_argument('--ground-truth',type=Path,required=True); ap.add_argument('--tolerance-ms',type=float,default=60); ap.add_argument('--output',type=Path); ap.add_argument('--include-drum-bus',action='store_true'); a=ap.parse_args()
    root=a.root.resolve(); sys.path.insert(0,str(root.parent.resolve()))
    from audio.drum_detection import detect_drum_event_streams_from_file
    totals={c:defaultdict(int) for c in CLASSES}; timing=defaultdict(list); confusion=defaultdict(int); track_rows=[]
    for gtfile in sorted(a.ground_truth.glob('*.json')):
        gtj=load_gt(gtfile); audio=(root/gtj['audio_path']).resolve(); gt=[(float(e['time']),e['drum']) for e in gtj.get('events',[]) if e.get('drum') in CLASSES]
        if not audio.exists():
            track_rows.append({'track_id':gtj.get('track_id',gtfile.stem),'status':'missing_audio','audio':str(audio)}); continue
        streams=detect_drum_event_streams_from_file(audio)
        pred=flatten(streams)
        matches,used=match(gt,pred,a.tolerance_ms/1000.0); matched_gt={x[0] for x in matches}
        for gi,pi,err in matches: totals[gt[gi][1]]['tp']+=1; timing[gt[gi][1]].append(err*1000)
        for gi,g in enumerate(gt):
            if gi not in matched_gt: totals[g[1]]['fn']+=1
        for pi,p in enumerate(pred):
            if pi in used: continue
            totals[p[1]]['fp']+=1
            near=[(abs(p[0]-g[0]),g) for g in gt if abs(p[0]-g[0])<=a.tolerance_ms/1000.0]
            if near:
                g=min(near)[1]
                if g[1]!=p[1]: confusion[(g[1],p[1])]+=1
        track_rows.append({'track_id':gtj.get('track_id',gtfile.stem),'status':'ok','reference_events':len(gt),'predicted_events':len(pred),'matched':len(matches)})
    summary={}
    for c in CLASSES:
        tp,fp,fn=totals[c]['tp'],totals[c]['fp'],totals[c]['fn']; prec=tp/(tp+fp) if tp+fp else 0; rec=tp/(tp+fn) if tp+fn else 0; f1=2*prec*rec/(prec+rec) if prec+rec else 0
        summary[c]={'tp':tp,'fp':fp,'fn':fn,'precision':round(prec,4),'recall':round(rec,4),'f1':round(f1,4),'mean_abs_timing_ms':round(statistics.mean(abs(x) for x in timing[c]),3) if timing[c] else None,'mean_signed_timing_ms':round(statistics.mean(timing[c]),3) if timing[c] else None}
    result={'tolerance_ms':a.tolerance_ms,'classes':summary,'confusion':{f'{a}>{b}':n for (a,b),n in sorted(confusion.items())},'tracks':track_rows}
    text=json.dumps(result,indent=2)
    print(text)
    if a.output: a.output.write_text(text+'\n',encoding='utf-8')
if __name__=='__main__': main()
