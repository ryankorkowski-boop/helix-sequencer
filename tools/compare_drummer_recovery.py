"""Export comparable event streams, oracle disagreements and gate ablations."""
import argparse
from collections import Counter
import csv
import json
from pathlib import Path
import hashlib


def compare(output):
    historical=json.loads((output/'historical.json').read_text())
    rejected=json.loads((output/'rejected.json').read_text())
    report=json.loads((output/'recovery_report.json').read_text())
    audio=Path(report['audio']);digest=hashlib.sha256(audio.read_bytes()).hexdigest()
    assert digest==historical['audio_sha256']==rejected['audio_sha256'], 'Audio identity differs'
    after=report['event_audit']
    def canonical(e,kind,reason=None):
        info=e.get('frequency_band_info',e)
        return dict(timestamp=e['timestamp'],drum_family=e[kind],tom_class=info.get('tom_class'),
                    confidence=e['confidence'],velocity=e['velocity'],
                    source_onset_index=info.get('onset_index',e.get('source_onset_index')),
                    source_onset_frame=info.get('event_frame',round(e['timestamp']*48000/512)),
                    rejection_reason=reason,physical_target=e.get('physical_component'),
                    scheduled=e.get('scheduled',True))
    streams={'historical':[canonical(e,'drum_type') for e in historical['events']],
             'rejected':[canonical(e,'drum_type') for e in rejected['events']],
             'recovery':[canonical(e,'type') for e in after]}
    columns=list(streams['recovery'][0])
    for name,rows in streams.items():
        (output/f'{name}_events.json').write_text(json.dumps(dict(audio_sha256=digest,events=rows),indent=2)+'\n')
        with (output/f'{name}_events.csv').open('w',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=columns);writer.writeheader();writer.writerows(rows)
    differences=[]
    for e in historical['events']:
        old_time=e['timestamp'];old_kind=e['drum_type']
        candidates=[r for r in rejected['candidates'] if abs(r['timestamp']-old_time)<=.04]
        nearest=min(candidates,key=lambda r:abs(r['timestamp']-old_time)) if candidates else None
        before=[r['drum_type'] for r in rejected['events'] if abs(r['frequency_band_info']['coarse_timestamp_ms']/1000-old_time)<=.04]
        new=[r['type'] for r in after if r['scheduled'] and abs(r['timestamp']-old_time)<=.04]
        differences.append(dict(timestamp=old_time,historical_family=old_kind,rejected_families=before,
                                rejected_candidate_time=nearest['timestamp'] if nearest else None,
                                rejected_reason=nearest['rejection_reason'] if nearest else 'no_onset_candidate',
                                rejected_primary_body=nearest['body'] if nearest else None,
                                rejected_context_body=nearest['context_body'] if nearest else None,
                                recovery_families=new))
    (output/'historical_disagreements.json').write_text(json.dumps(differences,indent=2)+'\n')
    ablations={}
    for omit in [None,'short_quality','context_quality','local_support','release_edge','consensus']:
        ev=[]
        for r in rejected['candidates']:
            if r['percussive_ratio']<.36 and omit!='short_quality':continue
            if r['context_percussive_ratio']<.34 and omit!='context_quality':continue
            if not r['local_support'] and omit!='local_support':continue
            if r['attack_contrast']<1.05 and omit!='release_edge':continue
            body=r['body'];context=r['context_body']
            if body!=context and omit!='consensus':body='kick' if context=='kick' and body in (None,'snare') else None
            if body:ev.append(body)
            if r['metal']:ev.append(r['metal'])
        ablations[str(omit)]=dict(total=len(ev),families=dict(Counter(ev)))
    def agreement(rows,kind,timestamp):
        available=list(rows);count=0
        for old in historical['events']:
            matches=[(i,row) for i,row in enumerate(available) if row[kind]==old['drum_type'] and abs(timestamp(row)-old['timestamp'])<=.04]
            if matches:
                i,_=min(matches,key=lambda pair:abs(timestamp(pair[1])-old['timestamp']))
                available.pop(i);count+=1
        return count
    summary=dict(audio_sha256=digest,count_stages={'historical':'raw including diagnostic bus','rejected':'detected, identical to scheduled','recovery':'scheduled physical'},counts={k:dict(Counter(e['drum_family'] for e in v if e['scheduled'])) for k,v in streams.items()},
                 rejected_candidate_reasons=dict(Counter(e['rejection_reason'] for e in rejected['candidates'])),
                 removed_gate_ablations=ablations,recovery_reasons=report['analysis']['rejection_counts'],
                 historical_family_recovered=agreement([r for r in after if r['scheduled']],'type',lambda r:r['timestamp']),
                 historical_family_retained_by_rejected=agreement(rejected['events'],'drum_type',lambda r:r['frequency_band_info']['coarse_timestamp_ms']/1000),
                 reference_note='Historical agreement is behavioral evidence, not independent drum labels. Bus and unsupported toms do not emit.',
                 human_approval='pending')
    (output/'comparison_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))
    return summary

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=Path('test_runs/drummer_recovery'));a=p.parse_args();compare(a.output)
