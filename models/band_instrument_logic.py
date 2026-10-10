"""Source-event driven, playable instrument routes for readable band reviews."""
from __future__ import annotations

from functools import lru_cache
import itertools
import numpy as np

from models.band_performance_scene import TUNINGS
from music.note_events import NoteEvent


def playable_pitch(note: int, kind: str) -> int:
    low=min(TUNINGS[kind]);high=max(TUNINGS[kind])+24
    while note<low: note+=12
    while note>high: note-=12
    return note


@lru_cache(maxsize=4096)
def chord_route(notes: tuple[int,...], kind: str) -> tuple[tuple[int,int,int],...]:
    """Distinct physical strings with playable frets; never overwrite a chord."""
    pitches=sorted(set(playable_pitch(n,kind) for n in notes if n>=0))
    if kind=='bass': pitches=pitches[:1]
    # Prefer supported notes over fabricating a physically impossible chord.
    for count in range(min(len(pitches),len(TUNINGS[kind])),0,-1):
        best=();cost=float('inf')
        for subset in itertools.combinations(pitches,count):
            choices=[[(s,n-o,n) for s,o in enumerate(TUNINGS[kind]) if 0<=n-o<=24] for n in subset]
            for assignment in itertools.product(*choices):
                if len({x[0] for x in assignment})!=len(assignment):continue
                frets=[x[1] for x in assignment]
                candidate=(max(frets)-min(frets))*3+sum(abs(f-4) for f in frets)
                if candidate<cost:best=assignment;cost=candidate
        if best:return tuple(best)
    return ()


def compile_note_events(notes: np.ndarray, velocity: np.ndarray,
                        attacks: np.ndarray, source: str) -> list[NoteEvent]:
    """Canonical old piano events: pitch, velocity, start/end, repeated attacks."""
    events=[];n=len(notes)
    for pitch in sorted(set(int(v) for v in notes.ravel() if v>=0)):
        per_note = (np.max(np.where(notes==pitch,velocity,0),axis=1)
                    if velocity.ndim==2 else velocity)
        present=np.any(notes==pitch,axis=1)&(per_note>.06)
        start=None
        for i in range(n+1):
            active=i<n and present[i]
            repeat=active and start is not None and i-start>=2 and attacks[i]>.05
            if start is not None and (not active or repeat):
                events.append(NoteEvent(start/20,i/20,pitch,float(np.max(per_note[start:i])),
                                        source=source,confidence=None))
                start=None
            if active and start is None:start=i
    return sorted(events,key=lambda e:(e.start,e.pitch))


def event_curves(events: list[NoteEvent], n: int, columns: int,
                 release: float=.20) -> tuple[np.ndarray,np.ndarray,np.ndarray,np.ndarray]:
    """Held notes outrank release tails; newest articulation owns a pitch.

    Intervals are half-open. A released louder note must neither hide a newly
    played bass note nor boost the velocity of a quieter same-pitch retrigger.
    Only selected notes can start a gesture, including at the frame boundary.
    """
    if n < 0 or columns < 1 or release < 0:
        raise ValueError('invalid note grid dimensions or release')
    notes=np.full((n,columns),-1,dtype=np.int16)
    levels=np.zeros((n,columns),dtype=np.float32)
    attack=np.zeros(n,dtype=np.float32);phase=np.full(n,1.,dtype=np.float32)
    frames=[[] for _ in range(n)]
    for e in events:
        lo=max(0,round(e.start*20));hi=min(n,round((e.end+release)*20))
        if e.end<=e.start or not 0<e.velocity<=1:
            raise ValueError('note events require positive duration and velocity in (0,1]')
        if lo>=n:continue
        for i in range(lo,hi):
            age=i/20-e.start
            held=i/20<e.end
            decay=1 if held else max(0,1-(i/20-e.end)/release) if release else 0
            if decay>0:
                frames[i].append((e.pitch,e.velocity*decay,held,e.start,lo))
    for i,items in enumerate(frames):
        strongest={}
        for item in items:
            pitch,v,held,start,lo=item
            previous=strongest.get(pitch)
            if previous is None or (held,start,v)>(previous[2],previous[3],previous[1]):
                strongest[pitch]=item
        selected=sorted(sorted(strongest.values(),key=lambda x:(-x[2],-x[1],-x[3],x[0]))[:columns])
        for j,(pitch,v,held,start,lo) in enumerate(selected):
            notes[i,j]=pitch;levels[i,j]=v
            age=i/20-start
            if age<.20:phase[i]=min(phase[i],max(0,age/.20))
            if i==lo:attack[i]=max(attack[i],v)
    return notes,levels,attack,phase


def attack_gestures(attacks: np.ndarray, seconds: float=.20) -> np.ndarray:
    """Each onset owns its velocity; held loud notes cannot amplify a quiet hit."""
    if seconds<=0:raise ValueError('gesture duration must be positive')
    result=np.zeros(len(attacks),np.float32)
    last=None;velocity=0.
    for i,value in enumerate(attacks):
        if value>0:last=i;velocity=float(value)
        if last is not None:
            phase=min(1.,(i-last)/(20*seconds))
            result[i]=velocity*(1-phase)**2
    return result


def sparse_harmonic_notes(spectrum: np.ndarray, low: int=24,
                          max_notes: int=4) -> tuple[np.ndarray,np.ndarray]:
    """Harmonic-template pursuit with residual fundamentals, not peak=note."""
    bins,frames=spectrum.shape
    roots=np.repeat(np.arange(low,min(low+bins,85)),5)
    offsets=np.tile(np.array([-.4,-.2,0,.2,.4]),len(roots)//5)
    templates=np.zeros((bins,len(roots)))
    for j,note in enumerate(roots):
        for h in range(1,9):
            center=note-low+offsets[j]+12*np.log2(h)
            if center>=bins:continue
            x=np.arange(bins)
            templates[:,j]+=np.exp(-.5*((x-center)/.60)**2)/(h**1.30)
    norms=np.maximum(np.linalg.norm(templates,axis=0),1e-8)
    dictionary=templates/norms
    residual=np.asarray(spectrum,dtype=float).copy()
    notes=np.full((frames,max_notes),-1,np.int16);strength=np.zeros((frames,max_notes),np.float32)
    ceiling=np.maximum(spectrum.max(axis=0),1e-8)
    for k in range(max_notes):
        scores=dictionary.T@residual
        # A fundamental must remain after the previous root's overtones were
        # subtracted. This prevents a monophonic harmonic stack becoming a chord.
        fundamentals=residual[roots-low]
        scores[fundamentals<ceiling*.18]=-1
        chosen=scores.argmax(axis=0);amplitude=np.maximum(scores[chosen,np.arange(frames)],0)
        valid=(amplitude>ceiling*.35)&(fundamentals[chosen,np.arange(frames)]>ceiling*.18)
        notes[valid,k]=roots[chosen[valid]]
        strength[valid,k]=np.clip(amplitude[valid]/(ceiling[valid]*1.4),0,1)
        residual=np.maximum(0,residual-dictionary[:,chosen]*amplitude)
    return notes,strength
