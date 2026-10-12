"""Deterministic, source-timed joint and articulation helpers.

These helpers never synthesize musical events or infer playing technique from a beat.
"""
from __future__ import annotations
import numpy as np


def smoothstep(x):
    x=np.clip(x,0.,1.)
    return x*x*(3-2*x)


def elbow_2d(shoulder, wrist, upper, lower, bend=1):
    """Fixed-length two-link IK, with an explicit reach failure."""
    shoulder=np.asarray(shoulder,float);wrist=np.asarray(wrist,float)
    delta=wrist-shoulder;distance=np.linalg.norm(delta)
    if not abs(upper-lower)+1e-7<distance<upper+lower-1e-7:
        raise ValueError('wrist outside connected arm reach')
    axis=delta/distance
    along=(upper*upper-lower*lower+distance*distance)/(2*distance)
    height=np.sqrt(max(0.,upper*upper-along*along))
    normal=np.array([-axis[1],axis[0]])
    return shoulder+along*axis+bend*height*normal


def signed_gestures(attacks, duration=.18, fps=20):
    """Alternating artistic stroke directions, explicitly not inferred up/down strokes."""
    attacks=np.asarray(attacks);out=np.zeros(len(attacks),np.float32)
    last=None;velocity=0.;direction=-1
    for i,value in enumerate(attacks):
        if value>0:last=i;velocity=float(value);direction=-direction
        if last is not None:
            phase=(i-last)/(fps*duration)
            if phase<1:out[i]=direction*velocity*np.sin(np.pi*(.5+.5*phase))*(1-phase)
    return out


def transition_targets(targets, seconds=.10, fps=20):
    """Bounded short anticipatory transitions; exact target on every change frame.

    Holds are stable. Interpolation is computed from source frames, so random
    access and restarting an excerpt produce identical positions.
    """
    targets=np.asarray(targets,float);out=targets.copy();window=max(1,round(seconds*fps))
    changes=np.flatnonzero(np.any(np.abs(np.diff(targets,axis=0))>1e-7,axis=1))+1
    previous=0
    for index in changes:
        lo=max(previous,index-window)
        for j in range(lo,index):
            weight=smoothstep((j-lo+1)/(index-lo+1))
            out[j]=targets[lo]*(1-weight)+targets[index]*weight
        previous=index
    return out


def mallet_events(events, low=60, high=84):
    """Keep only separately screened mallet provenance; never octave-fold bars."""
    accepted=[];omitted=[]
    for event in events:
        if event.source!='other_stem_screened_mallet_estimate':continue
        (accepted if low<=event.pitch<=high else omitted).append(event)
    return accepted,omitted
