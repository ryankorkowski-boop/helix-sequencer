"""Source-bound stem/performance analysis; externally installed pretrained models.

No cached performance is accepted for a different audio hash. Learned drum
families feed the existing V3 mapper. Pitch estimates animate strings/keys but
are not claimed as a polyphonic score or performer/voice identification.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def instrument_events(path, role):
    import librosa
    y,sr=librosa.load(str(path),sr=22050,mono=True)
    hop=220
    spectrum=np.abs(librosa.stft(y,n_fft=4096,hop_length=hop))
    envelope=librosa.onset.onset_strength(S=librosa.amplitude_to_db(spectrum+1e-8),sr=sr,hop_length=hop)
    frames=librosa.onset.onset_detect(onset_envelope=envelope,sr=sr,hop_length=hop,delta=.08,wait=7)
    rms=librosa.feature.rms(y=y,frame_length=4096,hop_length=hop)[0]
    scale=max(float(np.percentile(rms,95)),1e-8)
    frequencies=librosa.fft_frequencies(sr=sr,n_fft=4096)
    mask=(frequencies>=40)&(frequencies<=420) if role=='bass' else (frequencies>=80)&(frequencies<=1600)
    events=[]
    for frame in frames:
        level=float(rms[frame]/scale)
        if level<.08:continue
        # A spectral pitch proxy is auditable and fast; no score identity claim.
        signal=spectrum[mask,frame:min(frame+8,spectrum.shape[1])].mean(axis=1)
        peak=int(signal.argmax());hz=float(frequencies[mask][peak])
        midi=int(round(librosa.hz_to_midi(hz)))
        events.append(dict(start_ms=round(frame*hop/sr*1000),duration_ms=180,
                           intensity=round(float(np.clip(level,.1,1)),4),midi=midi,
                           pitch_hz=round(hz,2),source_stem=role,
                           method='separated_stem_spectral_flux_onset_and_dominant_pitch_proxy'))
    return events


def analyze_recording(row, root):
    song=root/'analysis'/row['id'];song.mkdir(parents=True,exist_ok=True)
    cached=song/'instruments.json'
    if cached.exists():
        data=json.loads(cached.read_text())
        if data['audio_sha256']!=sha(row['path']):raise ValueError('Stale performance cache')
        return
    out=root/'stems'
    stem_dir=out/'htdemucs_6s'/Path(row['path']).stem
    if not all((stem_dir/(name+'.wav')).exists() for name in ('drums','bass','guitar','piano','vocals','other')):
        env=dict(os.environ,OMP_NUM_THREADS='2',MKL_NUM_THREADS='2')
        subprocess.run([sys.executable,'-m','demucs.separate','-n','htdemucs_6s','--shifts','0',
                        '--segment','7','--overlap','.25','-j','1','-o',str(out),row['path']],check=True,env=env)
    # Record readiness before inference so the lyric worker can use the vocals.
    metadata=dict(audio_sha256=sha(row['path']),model='htdemucs_6s',
                  stems={name:dict(path=str(stem_dir/(name+'.wav')),sha256=sha(stem_dir/(name+'.wav')))
                         for name in ('drums','bass','guitar','piano','vocals','other')})
    (song/'stems.json').write_text(json.dumps(metadata,indent=2)+'\n')
    from tools.transcribe_drummer_adtof import transcribe
    transcribe(Path(row['path']),stem_dir/'drums.wav',song/'drums.json',song/'drum_activations.npy')
    payload=dict(audio_sha256=sha(row['path']),source=row,
                 bass=instrument_events(stem_dir/'bass.wav','bass'),
                 guitar=instrument_events(stem_dir/'guitar.wav','guitar'),
                 piano=instrument_events(stem_dir/'piano.wav','piano'),stem_provenance=metadata,
                 limitations=['Separation may leak instruments; pitch proxies are not a verified score.',
                              'Five-family ADTOF cannot name toms; unresolved tom identities abstain.'])
    cached.write_text(json.dumps(payload,indent=2)+'\n')
    print('ANALYSIS_READY',row['id'],flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('--ids',nargs='*')
    args=p.parse_args();rows=json.loads((args.root/'sources.json').read_text())
    # The short phoneme song is a useful end-to-end pilot.
    for row in sorted(rows,key=lambda r:(r['id']!='04',r['id'])):
        if not args.ids or row['id'] in args.ids:analyze_recording(row,args.root)


if __name__=='__main__':main()
