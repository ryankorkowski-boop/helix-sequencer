"""Reproduce the externally installed Demucs/LarsNet evidence for transcription.

Model repositories and weights must already be installed by the caller. This
helper doesn't vendor/download models or silently substitute a different one.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


def revision(path):
    result=subprocess.run(['git','-C',str(path),'rev-parse','HEAD'],capture_output=True,text=True)
    return result.stdout.strip() if result.returncode==0 else 'not_available'


def prepare(audio,output,larsnet_code):
    import numpy as np
    import soundfile as sf
    import torch
    audio,output,code=Path(audio).resolve(),Path(output).resolve(),Path(larsnet_code).resolve()
    if not (code/'larsnet.py').is_file() or not (code/'config.yaml').is_file():
        raise FileNotFoundError('Supply the external LarsNet checkout and pretrained weights')
    output.mkdir(parents=True,exist_ok=True)
    env=dict(os.environ,OMP_NUM_THREADS='2')
    subprocess.run([sys.executable,'-m','demucs.separate','-n','htdemucs','--two-stems','drums',
                    '--shifts','0','--segment','7','--overlap','.25','-j','1','-o',str(output/'separated'),str(audio)],
                   check=True,env=env)
    drums=output/'separated'/'htdemucs'/audio.stem/'drums.wav'
    y,sr=sf.read(drums,dtype='float32',always_2d=True)
    if sr!=44100:
        raise ValueError('Unexpected Demucs sample rate')
    sys.path.insert(0,str(code))
    from larsnet import LarsNet
    torch.set_num_threads(2)
    previous=Path.cwd()
    try:
        # Upstream config checkpoint paths are relative to its checkout.
        os.chdir(code)
        model=LarsNet(device='cpu',config=code/'config.yaml')
        signals=model(torch.from_numpy(y.T.copy()).unsqueeze(0))
    finally:
        os.chdir(previous)
    stems=output/'lars_full';stems.mkdir(exist_ok=True)
    hashes={}
    for name,signal in signals.items():
        path=stems/f'{name}.wav';sf.write(path,signal.cpu().numpy().T,sr,subtype='FLOAT')
        hashes[name]=hashlib.sha256(path.read_bytes()).hexdigest()
    manifest=dict(source_audio_sha256=hashlib.sha256(audio.read_bytes()).hexdigest(),
                  drums_sha256=hashlib.sha256(drums.read_bytes()).hexdigest(),
                  family_stem_sha256=hashes,larsnet_revision=revision(code),
                  sample_rate=sr,samples=len(y),separation_model='htdemucs',
                  shifts=0,segment=7,overlap=.25,device='cpu')
    (output/'stem_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return drums,stems


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('audio',type=Path)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--larsnet-code',type=Path,required=True)
    a=p.parse_args();drums,stems=prepare(a.audio,a.output,a.larsnet_code)
    print(json.dumps(dict(drums=str(drums),family_stems=str(stems)),indent=2))
