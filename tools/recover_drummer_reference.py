"""Reproduce the b27e8d77 detector and scheduler without legacy visual mapping."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import types

ORACLE='b27e8d77a63027ed32bcf6851dcff3925472c155'


def historical(audio, output):
    # Frozen, repository-owned source. The current classifier is not the oracle.
    modules=[]
    for name,path in [('_drummer_oracle_classification','audio/drum_classification.py'),
                      ('_drummer_oracle_detection','audio/drum_detection.py'),
                      ('_drummer_oracle_mapping','mapping/drum_mapper.py')]:
        source=subprocess.check_output(['git','show',f'{ORACLE}:{path}'],text=True)
        source=source.replace('from audio.drum_classification import','from _drummer_oracle_classification import')
        module=types.ModuleType(name);sys.modules[name]=module
        exec(compile(source,f'{ORACLE}:{path}','exec'),module.__dict__)
        modules.append(module)
    _,detector,mapper=modules
    streams=detector.detect_drum_event_streams_from_file(audio,log_fn=print)
    events=mapper.flatten_drum_streams(streams)
    if not events:raise RuntimeError('Historical analysis produced no events')
    import librosa
    sample_rate=librosa.get_samplerate(audio)
    def row(event):
        return {**event.to_dict(), 'source_onset_frame':round(event.timestamp*sample_rate/512),
                'tom_class':None, 'rejection_reason':None}
    # Scheduling only: do not restore fabricated bus distributions or old poses.
    payload=dict(commit=ORACLE,audio_sha256=hashlib.sha256(audio.read_bytes()).hexdigest(),
                 events=[row(e) for e in events],scheduled=[row(e) for e in mapper.schedule_drum_events(events)],
                 raw_counts=dict(Counter(e.drum_type for e in events)))
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(payload,indent=2)+'\n')
    return payload

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--audio',type=Path,default=Path('Helix Audiolights.mp3'));p.add_argument('--output',type=Path,default=Path('test_runs/drummer_recovery/historical.json'))
    a=p.parse_args();historical(a.audio,a.output)
