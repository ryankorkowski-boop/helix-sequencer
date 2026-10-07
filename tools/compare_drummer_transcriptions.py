"""Compare rejected #218 with independent model candidates, without truth quotas."""
import argparse
from collections import Counter
import csv
import json
from pathlib import Path


def compare(before_path,after_path,output):
    before=json.loads(Path(before_path).read_text());after=json.loads(Path(after_path).read_text())
    if before['audio_sha256']!=after['analysis']['audio_sha256']:
        raise ValueError('Comparison recordings differ')
    old=before['events'];new=after['event_audit'];output=Path(output);output.mkdir(parents=True,exist_ok=True)
    rows=[dict(timestamp=e['timestamp'],drum_family=e['type'],tom_class=e.get('tom_class'),
               confidence=e['confidence'],velocity=e['velocity'],source_onset_index=e['source_onset_index'],
               source_onset_frame=e.get('activation_frame'),physical_target=e['physical_component'],
               scheduled=e['scheduled']) for e in new]
    (output/'transcription_events.json').write_text(json.dumps(dict(audio_sha256=after['analysis']['audio_sha256'],events=rows),indent=2)+'\n')
    with (output/'transcription_events.csv').open('w',newline='') as handle:
        w=csv.DictWriter(handle,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    moments=[]
    for t in [11.48,12.95,13.60,15.56,18.17,21.43,22.08,23.38,24.69,31.54,31.70,65.13,198.49]:
        moments.append(dict(timestamp=t,rejected=[e['drum_family'] for e in old if abs(e['timestamp']-t)<=.05],
                            candidate=[e['type'] for e in new if e['scheduled'] and abs(e['timestamp']-t)<=.05]))
    summary=dict(before_engine='rejected_218_historical_single_family',after_engine=after['detector'],
                 before_counts=dict(Counter(e['drum_family'] for e in old if e['scheduled'])),
                 after_counts=after['scheduled_drum_type_counts'],
                 after_rejections=after['analysis']['rejection_counts'],
                 source_audio_sha256=after['analysis']['audio_sha256'],
                 disputed_moments=moments,
                 review_status='pending_human_listening',
                 note='Counts and model agreement describe changes; neither establishes correctness. Rejected historical agreement is not a target.')
    (output/'before_after_summary.json').write_text(json.dumps(summary,indent=2)+'\n');return summary

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--before',type=Path,required=True);p.add_argument('--after',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();print(json.dumps(compare(a.before,a.after,a.output),indent=2))
