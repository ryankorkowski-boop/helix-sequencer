"""Repeatable, source-bound activity ranking; spectral bands are not instruments."""
from __future__ import annotations
import argparse, hashlib, json, subprocess
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import numpy as np
from scipy import signal


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pcm(path, rate=8000):
    raw = subprocess.check_output(['ffmpeg','-v','error','-threads','1','-i',str(path),
        '-ar',str(rate),'-ac','2','-f','f32le','-'])
    return np.frombuffer(raw, '<f4').reshape(-1,2).copy()


def rank_one(args):
    row, directory = args
    path = Path(directory)/(row['id']+('.wav' if row['mime_type']=='audio/wav' else '.mp3'))
    y = pcm(path); rate=8000; duration=len(y)/rate
    mono=y.mean(axis=1)
    f,t,z=signal.stft(mono,rate,nperseg=1024,noverlap=624,boundary='zeros')
    mag=np.abs(z); power=mag**2
    bands=np.stack([power[(f>=lo)&(f<hi)].sum(axis=0) for lo,hi in
                    [(30,160),(160,500),(500,1800),(1800,3500)]])
    norm=bands/np.maximum(np.quantile(bands,.95,axis=1)[:,None],1e-12)
    flux=np.maximum(np.diff(np.log1p(mag*100),axis=1,prepend=0),0).mean(axis=0)
    attacks,_=signal.find_peaks(flux,distance=2,prominence=max(.0001,float(np.quantile(flux,.8))*.35))
    pulse=np.zeros(len(t));pulse[attacks]=1
    rms=np.sqrt(power.sum(axis=0)); energy=rms/max(float(np.quantile(rms,.95)),1e-9)
    probabilities=mag/np.maximum(mag.sum(axis=0),1e-9)
    entropy=-(probabilities*np.log(probabilities+1e-12)).sum(axis=0)/np.log(len(f))
    chroma=np.zeros((12,len(t)))
    good=f>30; pitches=np.rint(69+12*np.log2(f[good]/440)).astype(int)%12
    for k in range(12):chroma[k]=mag[good][pitches==k].sum(axis=0)
    chroma/=np.maximum(np.linalg.norm(chroma,axis=0),1e-9)
    motion=np.linalg.norm(np.diff(chroma,axis=1,prepend=chroma[:,:1]),axis=0)
    candidates=[]
    # Exclude the first/last two seconds, unless the source is too short.
    for start in np.arange(2,max(2,duration-36-1.999),2):
        end=start+36; ix=(t>=start)&(t<end)
        if not ix.any():continue
        seg=y[round(start*rate):round(end*rate)]
        width=float(np.sqrt(np.mean((seg[:,0]-seg[:,1])**2))/max(np.sqrt(np.mean(seg**2)),1e-9))
        metrics=dict(attacks_per_second=float(pulse[ix].sum()/36),
            active_band_fraction=float((norm[:,ix]>.20).mean()),
            spectral_diversity=float(entropy[ix].mean()),pitch_class_motion=float(motion[ix].mean()),
            energy_coverage=float((energy[ix]>.25).mean()),dynamic_contrast=float(np.std(energy[ix])),
            stereo_width=width)
        score=(.27*min(metrics['attacks_per_second']/6,1)+.23*metrics['active_band_fraction']+
               .15*metrics['spectral_diversity']+.13*min(metrics['pitch_class_motion']/.4,1)+
               .10*metrics['energy_coverage']+.07*min(metrics['dynamic_contrast']/.3,1)+.05*min(width,1))
        candidates.append(dict(start_seconds=float(start),end_seconds=float(end),seconds=36.,score=score,metrics=metrics))
    candidates.sort(key=lambda x:x['score'],reverse=True)
    selected=[]
    for c in candidates:
        if all(abs(c['start_seconds']-s['start_seconds'])>=28 for s in selected):selected.append(c)
        if len(selected)==3:break
    # Fingerprint includes normalized chroma trajectory, not a filename guess.
    fingerprint=np.rint(chroma[:,::20]*100).astype('u1')
    return dict(id=row['id'],filename=row['title'],folder=row['folder'],path=str(path.resolve()),
        bytes=path.stat().st_size,sha256=sha(path),pcm_8k_stereo_sha256=hashlib.sha256(y.tobytes()).hexdigest(),
        duration_seconds=duration,audio_fingerprint_sha256=hashlib.sha256(fingerprint.tobytes()).hexdigest(),
        fingerprint_chroma=fingerprint.tolist(),candidates=selected,
        classification='mixed-source spectral activity; instrument identities unverified')


def main():
    p=argparse.ArgumentParser();p.add_argument('--music',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    inv=json.loads((a.music/'inventory.json').read_text());rows=[]
    with ProcessPoolExecutor(max_workers=4) as pool:
        for row in pool.map(rank_one,[(r,str(a.music)) for r in inv]):
            rows.append(row);print('ranked',row['filename'],len(row['candidates']),flush=True)
            (a.output/'recordings.json').write_text(json.dumps(rows,indent=2)+'\n')
    groups={}
    for r in rows:groups.setdefault(r['pcm_8k_stereo_sha256'],[]).append(r['id'])
    duplicates=[g for g in groups.values() if len(g)>1]
    # Similar fingerprints are review candidates, never automatically deleted.
    near=[]
    for i,x in enumerate(rows):
        for y in rows[i+1:]:
            if abs(x['duration_seconds']-y['duration_seconds'])>.3:continue
            u=np.asarray(x['fingerprint_chroma'],float);v=np.asarray(y['fingerprint_chroma'],float)
            n=min(u.shape[1],v.shape[1]);similarity=float(np.sum(u[:,:n]*v[:,:n])/max(np.linalg.norm(u[:,:n])*np.linalg.norm(v[:,:n]),1e-9))
            if similarity>.96:near.append(dict(ids=[x['id'],y['id']],chroma_cosine=similarity,exact_pcm=x['pcm_8k_stereo_sha256']==y['pcm_8k_stereo_sha256']))
    (a.output/'duplicate_review.json').write_text(json.dumps(dict(exact_decoded_duplicates=duplicates,similar_arrangement_candidates=near,originals_modified=False),indent=2)+'\n')
    unique=[];seen=set()
    for r in sorted(rows,key=lambda r:r['candidates'][0]['score'] if r['candidates'] else -1,reverse=True):
        if not r['candidates'] or r['pcm_8k_stereo_sha256'] in seen:continue
        seen.add(r['pcm_8k_stereo_sha256']);unique.append(r)
    # Ten different vocal titles plus twelve varied instrumental arrangements.
    vocals=[r for r in unique if r['folder']!='Xmas Instrumentals']
    inst=[r for r in unique if r['folder']=='Xmas Instrumentals']
    def varied(rows,count):
        out=[];families=set()
        for r in rows:
            family=Path(r['filename']).stem.split('(')[0].strip().lower()
            if family in families:continue
            families.add(family);out.append(r)
            if len(out)==count:break
        return out
    chosen=varied(inst,12)+varied(vocals,10)
    selections=[]
    for i,r in enumerate(chosen):
        c=r['candidates'][0]
        selections.append(dict(**{k:v for k,v in r.items() if k not in ('candidates','fingerprint_chroma')},
            excerpt_id=f'E{i+1:02}',**c,vocals_expected=r['folder']!='Xmas Instrumentals',
            rationale='Highest weighted activity window for this recording; title-family diversity across the collection. Spectral bands are proxies, not confirmed stems.'))
    (a.output/'selected_excerpts.json').write_text(json.dumps(selections,indent=2)+'\n')
    (a.output/'scoring.json').write_text(json.dumps(dict(schema='helix.activity.rank.v1',window_seconds=36,stride_seconds=2,
        weights=dict(onset_density=.27,active_spectral_bands=.23,spectral_diversity=.15,pitch_class_motion=.13,energy_coverage=.10,dynamic_contrast=.07,stereo_width=.05),
        instrument_identity_verified=False,source_separation=False,exact_duplicate_policy='bytes and decoded PCM; near chroma matches only flagged for review'),indent=2)+'\n')


if __name__=='__main__':main()
