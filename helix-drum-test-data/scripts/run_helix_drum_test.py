#!/usr/bin/env python3
"""Run Helix drum detection against normalized ground truth."""
from __future__ import annotations
import argparse,json,statistics,sys
from collections import defaultdict
from pathlib import Path
CLASSES=('kick','snare','hihat','tom','cymbal')

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--helix-root',type=Path,required=True); ap.add_argument('--ground-truth',type=Path,required=True); ap.add_argument('--tolerance-ms',type=float,default=60); ap.add_argument('--output',type=Path); a=ap.parse_args()
 sys.path.insert(0,str(a.helix_root.resolve()))
 from audio.drum_detection import detect_drum_event_streams_from_file
 totals={c:defaultdict(int) for c in CLASSES}; timing=defaultdict(list); confusion=defaultdict(int); tracks=[]
 for gf in sorted(a.ground_truth.glob('*.json')):
  g=json.loads(gf.read_text()); apath=(a.helix_root/g['audio_path']).resolve(); gt=[(float(e['time']),e['drum']) for e in g.get('events',[]) if e.get('drum') in CLASSES]
  if not apath.exists(): tracks.append({'track_id':g.get('track_id',gf.stem),'status':'missing_audio'}); continue
  streams=detect_drum_event_streams_from_file(apath); pred=[]
  for key,events in streams.items():
   for e in events:
    d=str(getattr(e,'drum_type',key.replace('_events','')))
    if d in CLASSES: pred.append((float(e.timestamp),d))
  pred.sort(); used=set(); matched=[]
  for gi,(t,d) in enumerate(gt):
   cand=[(abs(p[0]-t),i,p) for i,p in enumerate(pred) if i not in used and abs(p[0]-t)<=a.tolerance_ms/1000 and p[1]==d]
   if cand:
    _,i,p=min(cand); used.add(i); matched.append((gi,i,p[0]-t)); totals[d]['tp']+=1; timing[d].append((p[0]-t)*1000)
  for gi,(t,d) in enumerate(gt):
   if not any(m[0]==gi for m in matched): totals[d]['fn']+=1
  for i,p in enumerate(pred):
   if i in used: continue
   totals[p[1]]['fp']+=1
   near=[(abs(p[0]-t),d) for t,d in gt if abs(p[0]-t)<=a.tolerance_ms/1000]
   if near:
    d=min(near)[1]
    if d!=p[1]: confusion[(d,p[1])]+=1
  tracks.append({'track_id':g.get('track_id',gf.stem),'status':'ok','reference_events':len(gt),'predicted_events':len(pred),'matched':len(matched)})
 summary={}
 for c in CLASSES:
  tp,fp,fn=totals[c]['tp'],totals[c]['fp'],totals[c]['fn']; p=tp/(tp+fp) if tp+fp else 0; r=tp/(tp+fn) if tp+fn else 0
  summary[c]={'tp':tp,'fp':fp,'fn':fn,'precision':round(p,4),'recall':round(r,4),'f1':round(2*p*r/(p+r),4) if p+r else 0,'mean_abs_timing_ms':round(statistics.mean(abs(x) for x in timing[c]),3) if timing[c] else None,'mean_signed_timing_ms':round(statistics.mean(timing[c]),3) if timing[c] else None}
 result={'tolerance_ms':a.tolerance_ms,'classes':summary,'confusion':{f'{x}>{y}':n for (x,y),n in sorted(confusion.items())},'tracks':tracks}
 text=json.dumps(result,indent=2); print(text)
 if a.output: a.output.write_text(text+'\n',encoding='utf-8')
if __name__=='__main__': main()
