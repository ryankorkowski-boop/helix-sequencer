"""Change one historical detector stage per case on the identical source audio."""
import json,subprocess,types,librosa,numpy as np
from pathlib import Path
from collections import Counter
src=subprocess.check_output(['git','show','b27e8d77:audio/drum_detection.py'],text=True)
y,sr=librosa.load('Helix Audiolights.mp3',sr=None,mono=True)
# Reuse HPSS results per signal+margin without changing any stage's calculation.
real_hpss=librosa.effects.hpss;cache={}
def cached(y,*a,**kw):
 key=(len(y),kw.get('margin',1))
 if key not in cache:cache[key]=real_hpss(y,*a,**kw)
 return cache[key]
librosa.effects.hpss=cached
cases={'oracle':src,'HPSS_margin_2':src.replace('hpss(y)','hpss(y, margin=2.0)'), 'resample_44100':src, 'hop_10ms':src.replace('hop = 512','hop = int(round(sr*0.01))'), 'onset_wait_3':src.replace('max(1, config.onset_wait)','3'),'onset_delta_006':src.replace('onset_delta: float = 0.045','onset_delta: float = 0.06')}
out={}
for name,s in cases.items():
 m=types.ModuleType(name);import sys;sys.modules[name]=m;exec(s,m.__dict__)
 yy=librosa.resample(y,orig_sr=sr,target_sr=44100) if name=='resample_44100' else y;ss=44100 if name=='resample_44100' else sr
 streams=m.detect_drum_event_streams(yy,ss);ev=sorted([e.to_dict() for v in streams.values() for e in v],key=lambda e:e['timestamp'])
 out[name]={'counts':dict(Counter(e['drum_type'] for e in ev)),'events':ev};print(name,out[name]['counts'],flush=True)
Path('test_runs/drummer_recovery/stage_ablation.json').write_text(json.dumps(out,indent=2))
