"""Forensic replay of rejected #217; never used by production detection."""
import json,subprocess,types,hashlib
from pathlib import Path
import librosa,numpy as np
from mapping.drum_mapper import schedule_drum_events,DrumMappingConfig
import argparse
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--audio',type=Path,default=Path('Helix Audiolights.mp3'))
parser.add_argument('--output',type=Path,default=Path('test_runs/drummer_recovery'))
args=parser.parse_args()
out=args.output;out.mkdir(parents=True,exist_ok=True)
src=subprocess.check_output(['git','show','3e860542:audio/drummer_v3.py'],text=True)
start='''        frame = int(frame)
'''
inject='''        frame = int(frame)
        attack0 = float(np.mean(p_rms[frame:min(n, frame+3)]))
        d100 = float(np.mean(p_rms[min(n, frame+5):min(n, frame+12)])) / max(attack0,1e-9) if frame+5<n else 0.0
        d300 = float(np.mean(p_rms[min(n, frame+15):min(n, frame+35)])) / max(attack0,1e-9) if frame+15<n else 0.0
        features0 = dict(low_ratio=float(low_ratio[frame]),low_mid_ratio=float(low_mid_ratio[frame]),mid_ratio=float(mid_ratio[frame]),high_ratio=float(high_ratio[frame]),centroid_hz=float(centroid[frame]),low_centroid_hz=float(low_centroid[frame]),decay_100ms=d100,decay_300ms=d300)
        features1 = dict(low_ratio=float(context_low_ratio[frame]),low_mid_ratio=float(context_low_mid_ratio[frame]),mid_ratio=float(context_mid_ratio[frame]),high_ratio=float(context_high_ratio[frame]),centroid_hz=float(context_centroid[frame]),low_centroid_hz=float(context_low_centroid[frame]),decay_100ms=d100,decay_300ms=d300)
        b0,m0,t0 = _classify_onset(**features0)
        b1,m1,t1 = _classify_onset(**features1)
        rs,ac = _refine_attack_sample(y,sr,frame*hop)
        auditrow = dict(onset_index=onset_index,frame=frame,timestamp=frame*hop/sr,refined_timestamp=rs/sr,attack_contrast=ac,primary=features0,context=features1,body=b0,metal=m0,tom_class=t0,context_body=b1,percussive_ratio=float(drum_quality[frame]),context_percussive_ratio=float(context_drum_quality[frame]),local_support=bool(full_rms[frame]>=np.median(full_rms[max(0,frame-8):min(n,frame+9)])),rejection_reason=None)
        AUDIT.append(auditrow)
'''
src=src.replace(start,inject)
for counter,reason in [('rejected_quality','short_percussive_quality'),('rejected_context_quality','context_percussive_quality'),('rejected_support','local_support'),('rejected_release_edge','release_edge'),('rejected_unclassified','unclassified_or_context_disagreement')]:
    src=src.replace(f'{counter} += 1',f'{counter} += 1\n            auditrow["rejection_reason"] = "{reason}"')
src=src.replace('        if body is None and metal is None:', '        auditrow["final_body"] = body\n        auditrow["final_metal"] = metal\n        if body is None and metal is None:')
m=types.ModuleType('rejected');m.AUDIT=[];exec(compile(src,'<rejected>','exec'),m.__dict__)
p=args.audio;e,d=m.analyze_drummer_audio(p)
s=schedule_drum_events(e,DrumMappingConfig(intro_gate_enabled=False))
out.joinpath('rejected.json').write_text(json.dumps(dict(commit='3e8605421990e435700da1a7470d13fd09d193bb',audio_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),diagnostics=d,events=[x.to_dict() for x in e],scheduled=[x.to_dict() for x in s],candidates=m.AUDIT),indent=2));print(d)
