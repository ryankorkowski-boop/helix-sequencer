#!/usr/bin/env python3
"""Normalize MIDI, IDMT XML/SVL, or simple MDB annotations into Helix GT JSON."""
from __future__ import annotations
import argparse, csv, json, re, xml.etree.ElementTree as ET
from pathlib import Path

MAP = {35:'kick',36:'kick',38:'snare',37:'snare',39:'snare',40:'snare',42:'hihat',44:'hihat',46:'hihat',41:'tom',43:'tom',45:'tom',47:'tom',48:'tom',50:'tom',49:'cymbal',51:'cymbal',52:'cymbal',53:'cymbal',55:'cymbal',57:'cymbal',59:'cymbal'}

def midi_events(path: Path):
    try:
        import pretty_midi
    except ImportError as exc:
        raise SystemExit('GMD conversion requires pretty_midi (pip install pretty_midi)') from exc
    pm = pretty_midi.PrettyMIDI(str(path)); out=[]
    for inst in pm.instruments:
        if not inst.is_drum: continue
        for n in inst.notes:
            drum = MAP.get(int(n.pitch))
            if drum:
                out.append({'time':round(float(n.start),6),'drum':drum,'velocity':round(float(n.velocity)/127.0,4)})
    return sorted(out,key=lambda x:(x['time'],x['drum']))

def tabular_events(path: Path):
    text=path.read_text(encoding='utf-8-sig');
    if path.suffix.lower()=='.json':
        obj=json.loads(text); rows=obj.get('events',obj if isinstance(obj,list) else [])
    else:
        rows=list(csv.DictReader(text.splitlines(), delimiter='\t' if '\t' in text.splitlines()[0] else ','))
    out=[]
    aliases={'kick':'kick','bassdrum':'kick','snare':'snare','hihat':'hihat','hi-hat':'hihat','hh':'hihat','tom':'tom','cymbal':'cymbal','crash':'cymbal','ride':'cymbal'}
    for r in rows:
        low={str(k).lower():v for k,v in r.items()}
        t=low.get('time',low.get('timestamp',low.get('onset'))); d=low.get('drum',low.get('instrument',low.get('class')))
        if t is None or d is None: continue
        d=aliases.get(str(d).strip().lower());
        if d: out.append({'time':round(float(t),6),'drum':d,'velocity':round(float(low.get('velocity',1.0)),4)})
    return sorted(out,key=lambda x:(x['time'],x['drum']))

def idmt_xml(path: Path):
    root=ET.parse(path).getroot(); out=[]
    # IDMT releases have used slightly different XML/SVL wrappers; accept any element
    # whose attributes expose a timestamp/onset and an instrument label.
    aliases={'kick':'kick','snare':'snare','hihat':'hihat','hi-hat':'hihat','hat':'hihat'}
    for e in root.iter():
        attrs={str(k).lower().split('}')[-1]:v for k,v in e.attrib.items()}
        t=next((attrs[k] for k in ('time','timestamp','onset','start') if k in attrs),None)
        label=next((attrs[k] for k in ('drum','instrument','class','label','name') if k in attrs),None)
        if t is None or label is None: continue
        d=aliases.get(str(label).strip().lower());
        if not d: continue
        out.append({'time':round(float(t),6),'drum':d,'velocity':round(float(attrs.get('velocity',1.0)),4)})
    if not out: raise ValueError(f'No supported onset records found in {path}; inspect the release-specific XML/SVL schema.')
    return sorted(out,key=lambda x:(x['time'],x['drum']))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--format',choices=['gmd','idmt','mdb'],required=True); ap.add_argument('--source',type=Path,required=True); ap.add_argument('--audio',required=True); ap.add_argument('--output',type=Path,required=True); ap.add_argument('--track-id'); a=ap.parse_args()
    events = midi_events(a.source) if a.format=='gmd' else idmt_xml(a.source) if a.format=='idmt' else tabular_events(a.source)
    payload={'track_id':a.track_id or a.source.stem,'audio_path':a.audio,'events':events,'source_format':a.format}
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8')
    print(f'Wrote {len(events)} events -> {a.output}')
if __name__=='__main__': main()
