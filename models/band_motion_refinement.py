"""Deterministic, source-timed joint and articulation helpers.

These helpers never synthesize musical events or infer playing technique from a beat.
"""
from __future__ import annotations
import numpy as np
from bisect import bisect_right

class EventLane:
    """One immutable sorted index instead of scanning every event every frame."""
    def __init__(self,events):
        self.events=tuple(sorted(events,key=lambda e:e['time']))
        self.times=tuple(e['time'] for e in self.events)

    def neighbors(self,time):
        i=bisect_right(self.times,time)
        return (self.events[i-1] if i else None,
                self.events[i] if i<len(self.events) else None)


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


def elbow_3d(shoulder, wrist, upper, lower, bend_hint):
    """Connected fixed-length links in a stable authored bend plane.

    A target outside reach is an error, never a silently moved fingertip.
    Projection keeps the bend perpendicular to reach even at steep frets.
    """
    shoulder=np.asarray(shoulder,float);wrist=np.asarray(wrist,float)
    delta=wrist-shoulder;distance=np.linalg.norm(delta)
    if not abs(upper-lower)+1e-7<distance<upper+lower-1e-7:
        raise ValueError('wrist outside connected arm reach')
    axis=delta/distance;hint=np.asarray(bend_hint,float)
    normal=hint-axis*np.dot(hint,axis)
    if np.linalg.norm(normal)<1e-7:
        basis=np.eye(3)[np.argmin(np.abs(axis))]
        normal=basis-axis*np.dot(basis,axis)
    normal/=np.linalg.norm(normal)
    along=(upper*upper-lower*lower+distance*distance)/(2*distance)
    height=np.sqrt(max(0.,upper*upper-along*along))
    return shoulder+along*axis+height*normal


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


def transition_targets(targets, seconds=.10, fps=20, preserve_changes=False):
    """Bounded short anticipatory transitions with optional exact contact anchors.

    Holds are stable. Interpolation is computed from source frames, so random
    access and restarting an excerpt produce identical positions. Opt-in
    preserve_changes protects close source contacts; default retains the
    approved legacy guitar transitions.
    """
    targets=np.asarray(targets,float);out=targets.copy();window=max(1,round(seconds*fps))
    changes=np.flatnonzero(np.any(np.abs(np.diff(targets,axis=0))>1e-7,axis=1))+1
    previous=0
    for index in changes:
        lo=max(previous+int(preserve_changes),index-window)
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


def constrained_keyboard_wrist_lane(targets, rest, shoulder, link_lengths,
                                   *, side, max_step=.13):
    """Make source-selected keyboard gestures possible for a humanlike snowman.

    A lit piano key is not proof a mitten can get there. Preserve note-light
    timing, but limit each wrist to its own half of the keyboard, two-link
    reach, and max 13 cm in design units per 50 ms source frame. Extreme/rapid
    notes may have no physical mitten contact; callers must report those
    omissions rather than inventing a strike.
    """
    raw=np.asarray(targets,dtype=float)
    rest=np.asarray(rest,dtype=float)
    shoulder=np.asarray(shoulder,dtype=float)
    if raw.ndim!=2 or raw.shape[1]!=3 or raw.shape[0]==0:
        raise ValueError('Keyboard wrist lane must be Nx3')
    if side not in ('left','right') or not np.isfinite(raw).all():
        raise ValueError('Invalid keyboard lane side or position')
    if max_step<=0:raise ValueError('max_step must be positive')
    upper,lower=map(float,link_lengths)
    max_reach=upper+lower-.10
    min_reach=abs(upper-lower)+.10
    if not min_reach<max_reach:raise ValueError('Invalid keyboard arm links')
    result=np.empty_like(raw)
    previous=rest.copy()
    center_x=shoulder[0]+(.36 if side=='left' else -.36)
    for index,desired in enumerate(raw):
        target=desired.copy()
        # No hand swaps/crossings during fast runs.
        target[0]=min(target[0],center_x) if side=='left' else max(target[0],center_x)
        displacement=target-shoulder
        distance=np.linalg.norm(displacement)
        if distance>max_reach:
            target=shoulder+displacement*max_reach/distance
        elif distance<min_reach:
            direction=(previous-shoulder)
            norm=np.linalg.norm(direction)
            if norm<1e-8:direction=np.array([0.,-.4,.9]);norm=np.linalg.norm(direction)
            target=shoulder+direction*min_reach/norm
        delta=target-previous
        d=np.linalg.norm(delta)
        if d>max_step:target=previous+delta*(max_step/d)
        result[index]=target
        previous=target
    return result

