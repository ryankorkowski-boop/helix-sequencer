"""Source-bound articulation and explicit voice casting for band previews.

No beat fallback, octave folding, random duet exchange, or altered guitar score.
"""
from __future__ import annotations
import numpy as np
from models.band_sampler_logic import SHAPE_NAMES


def ringing_candidates(candidates, low=48, high=96):
    """Broaden bells/marimba coverage while retaining acoustic screening.

    These are ringing pitched attacks, not verified instrument identities.
    Range expansion represents actual extra bars rather than folded octaves.
    """
    accepted=[];rejected=[]
    for c in candidates:
        reason=None
        if not low<=c['midi']<=high:reason='outside rendered register'
        elif c['concentration']<.10:reason='broadband attack'
        elif c['decay_ratio']<1.04:reason='no measured decay'
        elif c['vocal_similarity']>.78:reason='vocal leakage'
        (rejected if reason else accepted).append(dict(c,reason=reason) if reason else dict(c))
    return accepted,rejected


def cast_source_voice(mouths, energy, assignment='male', overrides=()):
    """Keep the recorded lead on a stable avatar; explicit intervals own duets.

    Preserve recognized phones, close only over acoustic silence. Text
    repetition does not establish a second singer. Low energy consonants are
    retained between nearby voiced frames. Assignment is a character choice.
    """
    aliases={'first':'male','second':'female'}
    assignment=aliases.get(assignment,assignment)
    mouths=np.asarray(mouths,dtype=np.int8).copy();energy=np.asarray(energy)
    if assignment not in ('male','female','both'):raise ValueError('invalid singer assignment')
    if mouths.ndim!=1 or len(mouths)!=len(energy):raise ValueError('unaligned voice curves')
    audible=energy>.035
    # Bridge a single weak 50ms frame without extending across a phrase break.
    if len(audible)>2:audible[1:-1]|=audible[:-2]&audible[2:]
    mouths[~audible]=SHAPE_NAMES.index('REST')
    lanes=np.zeros((len(mouths),2),np.int8)
    slots=(0,1) if assignment=='both' else (int(assignment=='female'),)
    for k in slots:lanes[:,k]=mouths
    for cue in overrides:
        lo=max(0,round(cue['start']*20));hi=min(len(mouths),round(cue['end']*20))
        role=aliases.get(cue['role'],cue['role'])
        if role not in ('male','female','both','rest') or hi<=lo:raise ValueError('invalid singer cue')
        lanes[lo:hi]=0
        for k in ((0,1) if role=='both' else () if role=='rest' else (int(role=='female'),)):
            lanes[lo:hi,k]=mouths[lo:hi]
    return lanes


def choose_solo_windows(guitar, vocals, seconds=14, count=4):
    """Rank measured guitar activity with less voice, keeping clips distinct."""
    g=np.asarray(guitar);v=np.asarray(vocals);length=round(seconds*20)
    if len(g)!=len(v) or len(g)<length:raise ValueError('source shorter than excerpt')
    score=np.convolve(g,np.ones(length),'valid')-.35*np.convolve(v,np.ones(length),'valid')
    available=np.ones(len(score),bool);result=[]
    for _ in range(count):
        if not available.any():break
        i=int(np.argmax(np.where(available,score,-np.inf)))
        result.append(dict(start=i/20,seconds=seconds,score=float(score[i]),
            guitar_active_fraction=float(np.mean(g[i:i+length]>.12)),
            vocal_active_fraction=float(np.mean(v[i:i+length]>.12))))
        available[max(0,i-length):min(len(score),i+length+1)]=False
    return result
