"""Source-bound voice role preparation for mixed or independently isolated stems.

Usage: python -m tools.prepare_vocal_roles config.json --analysis-folder path
Config: source_audio, duration, tracks[{name,path,evidence,role?,phonemes?}].
All tracks start at the same excerpt-local zero. No source audio is modified.
"""
from pathlib import Path
import argparse,json,hashlib
import numpy as np
import soundfile as sf
from music.vocal_roles import VoiceTrack,route_voices


def prepare(config_path,output):
    config_path=Path(config_path);config=json.loads(config_path.read_text());base=config_path.parent
    def path(value):
        p=Path(value);return p if p.is_absolute() else base/p
    source=path(config['source_audio']);duration=float(config['duration'])
    if abs(sf.info(source).duration-duration)>.025:raise ValueError('Source excerpt duration mismatch')
    tracks=[];hashes={}
    for row in config['tracks']:
        p=path(row['path']);y,sr=sf.read(p,dtype='float32',always_2d=True)
        if abs(len(y)/sr-duration)>.025:raise ValueError('Stems must use the same excerpt-local zero and duration')
        tracks.append(VoiceTrack(row['name'],y,sr,row.get('evidence','mixed'),row.get('role'),tuple(row.get('phonemes',()))))
        hashes[row['name']]=hashlib.sha256(p.read_bytes()).hexdigest()
    lanes,modes,report=route_voices(tracks,duration=duration)
    # Seven-person preview has two visible singers. Keep a full per-track
    # archive, and refuse to silently collapse three voices onto one mouth.
    if len(lanes)>2:raise ValueError('More than two independent vocal tracks require separate backing-face models; no silent mouth merging')
    energy=np.zeros((round(duration*20),2),'f4');shapes=np.zeros_like(energy,dtype='i1')
    ordered=sorted(lanes,key=lambda lane:{'lead':0,'second':1,'background':2}[lane['role']])
    for i,lane in enumerate(ordered):energy[:,i]=lane['energy'];shapes[:,i]=lane['shapes']
    if config.get('known_instrumental'):
        energy[:]=0;shapes[:]=0;modes[:]='silence';report['instrumental_source_guard']=True
    report.update(source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),stem_file_sha256=hashes,
        model_lanes=[dict(name=l['name'],role=l['role']) for l in ordered],
        preview_classifications={str(k):int(np.sum(modes==k)) for k in np.unique(modes)})
    output=Path(output);output.mkdir(exist_ok=True,parents=True)
    np.savez_compressed(output/'voice_roles.npz',energy=energy,shapes=shapes,modes=modes)
    (output/'voice_roles.json').write_text(json.dumps(report,indent=2)+'\n')
    return report

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('config',type=Path);a.add_argument('--analysis-folder',type=Path,required=True);args=a.parse_args();prepare(args.config,args.analysis_folder)
