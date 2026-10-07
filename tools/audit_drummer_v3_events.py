"""Write transparent typed-event evidence and a compact first-section timeline."""
from pathlib import Path
import argparse
import collections
import csv
import json
from PIL import Image, ImageDraw, ImageFont


def audit(report_path: Path, output: Path, start: float=10, end: float=30) -> dict:
    report=json.loads(report_path.read_text());events=report['event_audit']
    output.mkdir(parents=True,exist_ok=True)
    columns=['timestamp','type','confidence','velocity','physical_component','scheduled','source_onset_index','tom_class','tom_peak_hz','tom_class_confidence','rejection_reason','percussive_ratio','low_ratio','mid_low_ratio','mid_ratio','high_ratio','centroid_hz','low_centroid_hz','percussive_flatness','decay_profile']
    with (output/'Drummer_Event_Audit.csv').open('w',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=columns,extrasaction='ignore');writer.writeheader();writer.writerows(events)
    section=[e for e in events if start<=e['timestamp']<=end]
    meaningful=[e for e in events if 10<=e['timestamp']<=71]
    summary={'full_song_counts':report['scheduled_drum_type_counts'],
             'first_event_seconds':report['first_scheduled_event_ms']/1000,
             'events_before_10s':report['early_event_count_10s'],
             '10_to_71s_counts':dict(collections.Counter(e['type'] for e in meaningful)),
             '10_to_71s_low_confidence_below_045':sum(e['confidence']<.45 for e in meaningful),
             'simultaneous_onsets_10_to_71s':sum(n>1 for n in collections.Counter(e['timestamp'] for e in meaningful).values()),
             'max_hits_per_second':{k:max((sum(e['timestamp']<=o['timestamp']<e['timestamp']+1 for o in events if o['type']==k) for e in events if e['type']==k),default=0) for k in report['scheduled_drum_type_counts']},
             'note':'Confidence is a historical heuristic family score, not calibrated probability. Counts and timing checks are not musical approval. No auditory ground-truth annotation has been made.'}
    (output/'Drummer_Audit_Summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    names=['KICK','SNARE','HI_HAT','TOM_HIGH','TOM_MID','TOM_FLOOR','CYMBAL_LEFT','CYMBAL_RIGHT']
    colors=['#ed573c','#de7acb','#e8bd40','#60d278','#60d278','#60d278','#e8bd40','#e8bd40']
    image=Image.new('RGB',(1500,670),'#101621');draw=ImageDraw.Draw(image);font=ImageFont.load_default(size=17)
    draw.text((25,20),f'Drummer event audit | {start:g} to {end:g} seconds | Helix Audiolights',fill='white',font=font)
    draw.text((25,48),'Circles: scheduled events. Open circles: confidence below 0.45. Coincident hits stay separate.',fill='#b8c5d8',font=font)
    x=lambda time:round(210+(time-start)/(end-start)*1230)
    for second in range(int(start),int(end)+1):
        draw.line((x(second),95,x(second),570),fill='#283445')
        draw.text((x(second)-8,590),str(second),fill='#b8c5d8',font=font)
    for i,name in enumerate(names):
        y=110+i*60;draw.text((25,y-8),name,fill=colors[i],font=font);draw.line((210,y,1440,y),fill='#283445')
        for e in section:
            if e['physical_component']==f'HX_SNOWMAN_DRUMMER_V3_{name}':
                xx=x(e['timestamp']);draw.ellipse((xx-6,y-6,xx+6,y+6),outline=colors[i],fill=colors[i] if e['confidence']>=.45 else None,width=2)
    draw.text((25,635),'Evidence review only: musical correctness remains unverified; no thresholds changed to force desired totals.',fill='#b8c5d8',font=font)
    image.save(output/'Drummer_Event_Timeline.png')
    return summary

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('report',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();print(json.dumps(audit(a.report,a.output),indent=2))
