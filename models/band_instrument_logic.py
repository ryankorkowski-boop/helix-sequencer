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
    """Per-note brightness and attack phase, retaining source velocity and rests."""
    notes=np.full((n,columns),-1,dtype=np.int16)
    levels=np.zeros((n,columns),dtype=np.float32)
    attack=np.zeros(n,dtype=np.float32);phase=np.full(n,1.,dtype=np.float32)
    frames=[[] for _ in range(n)]
    for e in events:
        lo=max(0,round(e.start*20));hi=min(n,round((e.end+release)*20))
        if lo>=n:continue
        attack[lo]=max(attack[lo],e.velocity)
        for i in range(lo,hi):
            age=i/20-e.start
            decay=1 if i/20<=e.end else max(0,1-(i/20-e.end)/release)
            frames[i].append((e.pitch,e.velocity*decay))
            if age<.20:phase[i]=min(phase[i],max(0,age/.20))
    for i,items in enumerate(frames):
        strongest={}
        for pitch,v in items:strongest[pitch]=max(strongest.get(pitch,0),v)
        selected=sorted(sorted(strongest.items(),key=lambda x:-x[1])[:columns])
        for j,(pitch,v) in enumerate(selected):notes[i,j]=pitch;levels[i,j]=v
    return notes,levels,attack,phase


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
