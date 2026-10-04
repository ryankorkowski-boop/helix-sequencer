#!/usr/bin/env python3
"""Select a compact deterministic GMD MIDI benchmark subset and emit Helix GT JSON."""
from __future__ import annotations
import argparse, json, shutil
from pathlib import Path

GM = {35:'kick',36:'kick',37:'snare',38:'snare',39:'snare',40:'snare',41:'tom',43:'tom',45:'tom',47:'tom',48:'tom',50:'tom',42:'hihat',44:'hihat',46:'hihat',49:'cymbal',51:'cymbal',52:'cymbal',53:'cymbal',55:'cymbal',57:'cymbal',59:'cymbal'}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--gmd-root',type=Path,required=True); ap.add_argument('--output',type=Path,default=Path('helix-drum-test-data')); ap.add_argument('--count',type=int,default=5); args=ap.parse_args()
    try: import pretty_midi
    except ImportError as e: raise SystemExit('GMD requires pretty_midi: pip install pretty_midi') from e
    files=sorted(args.gmd_root.rglob('*.mid'))+sorted(args.gmd_root.rglob('*.midi'))
    if not files: raise SystemExit('No MIDI files found')
    # Prefer short files with actual drum notes; scan all until enough are found.
    candidates=[]
    for p in files:
        try: pm=pretty_midi.PrettyMIDI(str(p))
        except Exception: continue
        notes=[n for i in pm.instruments if i.is_drum for n in i.notes if n.pitch in GM]
        if notes:
            duration=max((n.end for n in notes),default=0)-min((n.start for n in notes),default=0)
            candidates.append((duration,str(p),p,notes))
    candidates.sort(key=lambda x:(x[0],x[1]))
    selected=candidates[:args.count]
    if len(selected)<args.count: print(f'Warning: found only {len(selected)} usable MIDI files')
    out_audio=args.output/'audio'/'gmd'; out_ann=args.output/'annotations'/'gmd'; out_gt=args.output/'ground_truth'; out_audio.mkdir(parents=True,exist_ok=True); out_ann.mkdir(parents=True,exist_ok=True); out_gt.mkdir(parents=True,exist_ok=True)
    manifest=[]
    for _,_,src,notes in selected:
        dst=out_ann/src.name; shutil.copy2(src,dst)
        events=[{'time':round(float(n.start),6),'drum':GM[n.pitch],'velocity':round(n.velocity/127,4)} for n in notes]
        gt=out_gt/f'{src.stem}.json'; gt.write_text(json.dumps({'track_id':src.stem,'audio_path':None,'events':sorted(events,key=lambda e:(e['time'],e['drum'])),'source_format':'gmd_midi','midi_path':f'annotations/gmd/{src.name}'},indent=2)+'\n')
        manifest.append({'track_id':src.stem,'midi_path':f'annotations/gmd/{src.name}','ground_truth':f'ground_truth/{gt.name}','audio_path':None,'events':len(events)})
    (args.output/'annotations'/'gmd_selection.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(f'Selected {len(manifest)} GMD MIDI files')

if __name__=='__main__': main()
