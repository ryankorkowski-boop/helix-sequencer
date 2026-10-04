"""Multi-detector Drummer V3 analysis for the Helix performer.

The detector is intentionally conservative on mixed music: instrument-only transients are
not drummer events. Typed events require evidence from the isolated percussive/drum signal;
full-mix features may only confirm an already-supported drum event.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable
import numpy as np

class DrumType(str, Enum):
    KICK = "kick"; SNARE = "snare"; HI_HAT = "hi_hat"; CYMBAL = "cymbal"
    TOM_HIGH = "tom_high"; TOM_MID = "tom_mid"; TOM_FLOOR = "tom_floor"

@dataclass(frozen=True)
class Candidate:
    frame: int; time: float; kind: DrumType; strength: float; source: str

@dataclass(frozen=True)
class DrumEvent:
    time: float; kind: DrumType; confidence: float; votes: tuple[str, ...] = field(default_factory=tuple)

def _adaptive_floor(x: np.ndarray, window: int = 101) -> np.ndarray:
    x=np.asarray(x,dtype=float)
    if x.size==0:return x.copy()
    window=max(3,int(window)|1); window=min(window,x.size if x.size%2 else x.size-1)
    if window<3:return np.full_like(x,np.median(x))
    pad=window//2; xp=np.pad(x,(pad,pad),mode="edge")
    return np.asarray([np.median(xp[i:i+window]) for i in range(x.size)])

def _positive_flux(x: np.ndarray) -> np.ndarray:
    e=np.maximum(np.asarray(x,dtype=float),0.0)
    if e.size==0:return e.copy()
    log_e=np.log1p(e); return np.maximum(np.diff(log_e,prepend=log_e[0]),0.0)

def _relative_strength(x: np.ndarray) -> np.ndarray:
    floor=_adaptive_floor(x); excess=np.maximum(x-floor,0.0)
    scale=np.percentile(excess,90) if excess.size else 0.0
    return excess/max(float(scale),1e-9)

def _peaks(signal: np.ndarray, threshold: np.ndarray, min_gap: int=2) -> np.ndarray:
    signal=np.asarray(signal,dtype=float); threshold=np.asarray(threshold,dtype=float)
    if signal.size<3:return np.empty(0,dtype=int)
    hits=[]; last=-10**9
    for i in range(1,signal.size-1):
        if i-last<min_gap:continue
        if signal[i]>=threshold[i] and signal[i]>=signal[i-1] and signal[i]>signal[i+1]:hits.append(i);last=i
    return np.asarray(hits,dtype=int)

def _emit_flux_family(signal,family,source,floor_offset,min_gap,times):
    flux=_positive_flux(signal); floor=_adaptive_floor(flux); peaks=_peaks(flux,floor+floor_offset,min_gap)
    strength=_relative_strength(flux)
    return [Candidate(int(i),float(times[i]),family,float(strength[i]),source) for i in peaks]

def _cluster_candidates(candidates,tolerance_s):
    clusters=[]
    for c in sorted(candidates,key=lambda z:(z.time,z.kind.value)):
        if clusters and c.kind==clusters[-1][0].kind and c.time-clusters[-1][-1].time<=tolerance_s:clusters[-1].append(c)
        else:clusters.append([c])
    return clusters

def _tom_candidates(drum_low,drum_mid,times,frame_rate):
    mid_flux=_positive_flux(drum_mid); low_flux=_positive_flux(drum_low)
    floor=_adaptive_floor(mid_flux)
    peaks=_peaks(mid_flux,floor+0.025,max(4,int(0.055*frame_rate)))
    if peaks.size==0:return []
    ratio=low_flux/np.maximum(mid_flux,1e-9); values=ratio[peaks]
    lo,hi=np.percentile(values,[25,75]) if len(values)>=3 else (float(values.min()),float(values.max()))
    strength=_relative_strength(mid_flux); out=[]
    for i in peaks:
        r=float(ratio[i])
        kind=DrumType.TOM_FLOOR if r>=hi and hi>lo else DrumType.TOM_HIGH if r<=lo else DrumType.TOM_MID
        out.append(Candidate(int(i),float(times[i]),kind,float(strength[i]),"drum.tom_band"))
    return out

def _supported_by_full_mix(candidate: Candidate, low, mid, high, rms, frame: int) -> bool:
    """Confirmation only; mixed audio is never allowed to originate a drum hit."""
    if rms is None:return True
    n=min(len(low),len(mid),len(high),len(rms))
    if frame<0 or frame>=n:return False
    band = {DrumType.KICK: low, DrumType.SNARE: mid, DrumType.TOM_HIGH: mid,
            DrumType.TOM_MID: mid, DrumType.TOM_FLOOR: low,
            DrumType.HI_HAT: high, DrumType.CYMBAL: high}[candidate.kind]
    value=float(band[frame]); local=float(np.median(band[max(0,frame-8):min(n,frame+9)]))
    rms_value=float(rms[frame]); rms_local=float(np.median(rms[max(0,frame-8):min(n,frame+9)]))
    return value>=local and rms_value>=rms_local

def analyze_drummer_features(*,low,mid,high,times=None,rms=None,drum_low=None,drum_mid=None,drum_high=None,beat_indices:Iterable[int]=(),frame_rate:float=100.0,cluster_tolerance:float=0.045):
    low=np.asarray(low,dtype=float); mid=np.asarray(mid,dtype=float); high=np.asarray(high,dtype=float)
    n=min(len(low),len(mid),len(high))
    if n<3 or drum_low is None or drum_mid is None or drum_high is None:
        # Deliberately return no drummer events without isolated drum evidence.
        return []
    low,mid,high=low[:n],mid[:n],high[:n]
    dl=np.asarray(drum_low,dtype=float)[:n]; dm=np.asarray(drum_mid,dtype=float)[:n]; dh=np.asarray(drum_high,dtype=float)[:n]
    times_arr=np.arange(n,dtype=float)/frame_rate if times is None else np.asarray(times,dtype=float)[:n]

    # The isolated percussive/drum signal is the source of truth. Full-mix analysis is
    # confirmation only; this prevents guitar/piano/vocal transients from becoming drums.
    candidates=[]
    candidates+=_emit_flux_family(dl,DrumType.KICK,"drum.low_flux",0.035,5,times_arr)
    candidates+=_emit_flux_family(dm,DrumType.SNARE,"drum.mid_flux",0.030,4,times_arr)
    candidates+=_emit_flux_family(dh,DrumType.HI_HAT,"drum.high_flux",0.020,2,times_arr)
    candidates+=_emit_flux_family(dh,DrumType.CYMBAL,"drum.high_flux_long",0.045,8,times_arr)
    candidates+=_tom_candidates(dl,dm,times_arr,frame_rate)

    beat_set=np.asarray(list(beat_indices),dtype=int); events=[]
    for cluster in _cluster_candidates(candidates,cluster_tolerance):
        kind=cluster[0].kind
        if not any(_supported_by_full_mix(c,low,mid,high,rms,c.frame) for c in cluster):
            continue
        sources=tuple(dict.fromkeys(c.source for c in cluster))
        stem_votes=len(cluster)
        confidence=min(1.0,0.32+0.15*stem_votes)
        if len(cluster)>=2:confidence=min(1.0,confidence+0.12)
        if beat_set.size and np.min(np.abs(beat_set-cluster[0].frame))<=max(1,int(0.025*frame_rate)):
            confidence=min(1.0,confidence+0.04)
        events.append(DrumEvent(cluster[0].time,kind,confidence,sources))
    return events
