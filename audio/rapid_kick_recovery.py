"""Opt-in, recording-calibrated kick recovery on an isolated drum stem.

Only measured low-band transients matching existing accepted kicks are added.
The explicit review window and unchanged detector output remain auditable.
This acoustic similarity is not a calibrated instrument-class probability.
"""
from __future__ import annotations

import math
import numpy as np
from scipy.ndimage import uniform_filter1d
from scipy.signal import butter, sosfiltfilt, find_peaks


def recover_kicks(samples, sr, events, *, start, end):
    if not all(math.isfinite(v) for v in (sr,start,end)) or sr < 1000 or not 0 <= start < end:
        raise ValueError('Finite sample rate and explicit review window required')
    y=np.asarray(samples,dtype=float)
    if y.ndim==2: y=y.mean(axis=1)
    if y.ndim!=1 or not np.isfinite(y).all() or end>len(y)/sr:
        raise ValueError('Invalid or shorter-than-requested drum stem')
    refs=[e for e in events if e['drum_family']=='kick' and start<=e['timestamp']<end
          and e['confidence']>=.35]
    report=dict(method='isolated drum-stem 40–180 Hz attack/decay similarity to accepted kicks',
        window=[start,end],reference_events=len(refs),added=[],
        timing_source='measured RMS peak minus median accepted-kick attack delay',
        class_probability_calibrated=False,beat_filler=False)
    if len(refs)<3:
        report['abstention']='fewer than three accepted recording-specific kick references'
        return list(events),report
    if end-start < .06:
        report['abstention']='review window too short for reliable attack/decay analysis'
        return list(events),report
    hop=max(1,round(sr*.005));step=hop/sr
    # Limit filtering and analysis to the caller's window plus decay support.
    lo=max(0,math.floor((start-.2)*sr));hi=min(len(y),math.ceil((end+.2)*sr))
    # filtfilt requires sufficient samples for its padding; a tiny review window
    # must abstain rather than abort a full sequencing run.
    sos=butter(4,[40,180],fs=sr,btype='band',output='sos')
    padlen=3*(2*len(sos)+1-min((sos[:,2]==0).sum(),(sos[:,5]==0).sum()))
    if hi-lo<=padlen or (hi-lo)//hop<3:
        report['abstention']='review window too short for zero-phase low-band analysis'
        return list(events),report
    low=sosfiltfilt(sos,y[lo:hi])
    low=low[:len(low)//hop*hop]
    env=uniform_filter1d(np.sqrt(np.mean(low.reshape(-1,hop)**2,axis=1)),3)
    offset=lo/sr;length=max(3,round(.06/step));reference_peaks=[];delays=[]
    for ref in refs:
        a=max(0,round((ref['timestamp']-offset)/step));b=min(len(env)-length,a+round(.045/step))
        if b<=a: continue
        p=a+int(np.argmax(env[a:b]));reference_peaks.append(p);delays.append(offset+p*step-ref['timestamp'])
    if len(reference_peaks)<3:
        report['abstention']='insufficient reference attack/decay samples'
        return list(events),report
    scale=float(np.median(env[reference_peaks]))
    if not math.isfinite(scale) or scale<=1e-12:
        report['abstention']='accepted references contain no measurable low-band energy'
        return list(events),report
    template=np.mean([env[p:p+length]/max(env[p],1e-12) for p in reference_peaks],axis=0)
    delay=float(np.median(delays))
    peaks,_=find_peaks(env,distance=max(1,round(.05/step)),height=scale*.50,prominence=scale*.28)
    result=list(events)
    for peak in peaks:
        time=offset+peak*step-delay
        if not start<=time<end or peak+length>len(env): continue
        if any(abs(e['timestamp']-time)<.04 for e in result if e['drum_family']=='kick'): continue
        shape=env[peak:peak+length]/max(env[peak],1e-12)
        similarity=float(np.corrcoef(template,shape)[0,1])
        if not math.isfinite(similarity) or similarity<.88 or shape[-1]>.65: continue
        evidence=dict(acoustic_similarity=similarity,low_band_peak_rms=float(env[peak]),
            reference_peak_rms=scale,measured_peak_time=offset+peak*step,
            timing_calibration_seconds=delay,kick_recovery_window=[start,end],
            timing_source='recording_calibrated_lowband_transient',independent_listening_verified=False)
        event=dict(timestamp=round(time,6),drum_family='kick',tom_class=None,
            confidence=round(similarity,6),velocity=round(float(np.clip(np.sqrt(env[peak]/scale),.12,1)),4),
            source_onset_index=round((offset+peak*step)*100)*5,
            rejection_reason=None,evidence=evidence)
        result.append(event);report['added'].append(event)
    report.update(reference_peak_rms=scale,timing_calibration_seconds=delay,
        candidate_count=len(peaks),added_count=len(report['added']))
    return sorted(result,key=lambda e:(e['timestamp'],e['drum_family'])),report
