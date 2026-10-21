"""Shared source-clock cues for review performers and spatial channel output."""
from __future__ import annotations
from dataclasses import replace
import numpy as np
from music.note_events import NoteEvent


def vocal_clock(y, enabled=True):
    """40-ms centered vocal observations at 10-ms steps; no release tail."""
    y=np.asarray(y,dtype='f4')
    if y.ndim!=1 or not np.isfinite(y).all():raise ValueError('finite mono audio required')
    n=int(np.ceil(len(y)/160));frames=np.lib.stride_tricks.sliding_window_view(np.pad(y,(320,320)),640)[::160][:n]
    rms=np.sqrt(np.mean(frames*frames,axis=1));power=np.abs(np.fft.rfft(frames*np.hanning(640),n=1024,axis=1))**2
    ac=np.fft.irfft(power,n=1024,axis=1);periodic=ac[:,32:267].max(axis=1)/np.maximum(ac[:,0],1e-12)
    floor=max(.0015,float(np.quantile(rms,.9))*.055);top=max(floor*3,float(np.quantile(rms,.97)))
    active=(rms>floor)&(periodic>.32)&enabled
    energy=np.where(active,np.clip((rms-floor)/(top-floor),0,1)**.65,0).astype('f4')
    f=np.fft.rfftfreq(1024,1/16000)
    def band(a,b):return power[:,(f>=a)&(f<b)].sum(axis=1)
    low,mid,high=band(250,800),band(800,1500),band(1500,3000)
    shapes=np.where(high>low*1.1,3,np.where(mid>high*1.2,4,2)).astype('i1');shapes[~active]=0
    return dict(energy=energy,shapes=shapes,rms=rms,periodicity=periodic,floor=np.array(floor))


def pitched_roles(piano,residual,candidates,mallet_energy,attacks, *, duration=36):
    """Piano/sustains stay on keys; screened ringing attacks own mallets."""
    used=set();mallets=[]
    for c in candidates:
        t=c['start_ms']/1000;i=min(len(mallet_energy)-1,round(t*20))
        if c['concentration']<.20 or c['decay_ratio']<1.20 or c['vocal_similarity']>.65 or mallet_energy[i]<=.08:continue
        matches=[(j,e) for j,e in enumerate(residual) if j not in used and abs(e.start-t)<=.10
                 and min(abs(abs(e.pitch-c['midi'])-h) for h in (0,12,19,24,28))<=1]
        if matches:
            j,e=min(matches,key=lambda x:abs(x[1].start-t));used.add(j);pitch=e.pitch;velocity=e.velocity
        else:pitch=c['midi'];velocity=float(mallet_energy[i])
        if t >= duration:continue
        mallets.append(NoteEvent(t,min(duration,t+.12),pitch,min(1,velocity),source='other_stem_screened_mallet_estimate'))
    keys=list(piano)+[e for j,e in enumerate(residual) if j not in used];refined=[];corrections=[]
    for e in keys:
        nearby=np.asarray(attacks)[np.abs(np.asarray(attacks)-e.start)<=.075];start=e.start
        if len(nearby):
            candidate=max(0,float(nearby[np.argmin(abs(nearby-e.start))]))
            if candidate<e.end-.025:start=candidate
        refined.append(replace(e,start=start));corrections.append((e.start,start))
    return sorted(refined,key=lambda e:(e.start,e.pitch)),mallets,corrections


def spatial_score(performance, positions, roles, variant=0):
    """One selective musical score; no full-layout overall-volume lane.

    Source notes choose where a motif starts. Subsequent movement is a bounded
    authored propagation, like a triggered morph, rather than a new beat note.
    """
    p=performance;n=p.n;positions=np.asarray(positions,float);out=np.zeros((len(positions),n),'f4')
    # A melodic sculpture is not a dedicated physical guitarist. If this
    # recording has no supported guitar, let its actual keyboard melody use
    # those geometric paths rather than leaving an entire district dormant.
    use_keys_for_melody=np.count_nonzero(p.curves['guitar_energy']>.08)<n*.05
    melodic='piano' if use_keys_for_melody else 'guitar'
    sources=[p.curves['bass_energy'],p.curves[melodic+'_energy'],p.curves['piano_energy'],
             p.voice_energy[:,0],p.strikes[:,0],np.maximum(p.strikes[:,1],p.strikes[:,6:8].max(axis=1))]
    attacks=[p.curves['bass_attack'],p.curves[melodic+'_attack'],p.curves['piano_attack'],
             np.r_[p.voice_energy[0,0],np.maximum(0,np.diff(p.voice_energy[:,0]))],
             np.r_[p.strikes[0,0],np.maximum(0,np.diff(p.strikes[:,0]))],
             np.r_[p.strikes[0,1],np.maximum(0,np.diff(p.strikes[:,1]))]]
    ordinal=[];ages=[]
    for signal in attacks:
        count=-1;last=-100.;seq=[];age=[];previous=0
        for i,v in enumerate(signal):
            if v>.06 and (previous<=.06 or v>previous+.15):count+=1;last=i/20
            seq.append(max(0,count));age.append(i/20-last);previous=v
        ordinal.append(np.asarray(seq));ages.append(np.asarray(age))
    # Structural contrast comes from measured independent lane activity. A
    # region change is permitted only after three seconds, never every frame.
    activity=np.vstack(sources).T;regions=np.zeros(n,int);anchor=0;region=0
    for i in range(60,n):
        a=activity[max(anchor,i-40):i].mean(axis=0);b=activity[max(0,i-10):i+1].mean(axis=0)
        if i-anchor>=60 and np.linalg.norm(a-b)>.45:region+=1;anchor=i
        regions[i]=region
    for k,(pos,role) in enumerate(zip(positions,roles)):
        lane=int(role)%6;idx=np.flatnonzero(np.asarray(roles)%6==lane)
        order=sorted(idx,key=lambda j:positions[j,0] if variant%2==0 else np.linalg.norm(positions[j,[0,2]]))
        rank=order.index(k)/max(1,len(order)-1)
        if variant%3==1:rank=1-rank
        center=(ordinal[lane]*.381966+regions*.23+variant*.11)%1
        travel=np.minimum(np.maximum(ages[lane],0),.55)*(.65 if variant%3 else -.65)
        distance=np.abs((rank-center-travel+.5)%1-.5)
        mask=np.clip(1-distance/.23,0,1)**1.4
        envelope=np.asarray(sources[lane]);out[k]=envelope*mask*(.75 if lane<4 else .95)
    # A shared per-frame occupancy budget prevents layer stacking from washing
    # out spatial separation. Priority follows actual candidate brightness.
    budget=max(1,int(np.ceil(len(positions)*.46)))
    if len(positions)>budget:
        ids=np.argpartition(out,-budget,axis=0)[:-budget]
        np.put_along_axis(out,ids,0,axis=0)
    out[out<.025]=0
    return out,dict(region_boundaries_seconds=((np.flatnonzero(np.diff(regions))+1)/20).tolist(),
                    maximum_model_fraction=float(np.max(np.mean(out>.08,axis=0))),
                    mean_model_fraction=float(np.mean(out>.08)),overall_volume_broadcast=False,
                    melodic_prop_source=melodic)
