"""Auditable musical gesture rules for the 42-second review performances."""
from __future__ import annotations

import re
import numpy as np

SHAPE_NAMES = ('REST', 'MBP', 'AH', 'EE', 'OH', 'FV', 'L')


def bass_neck_height(note, low=28, high=64):
    """Absolute pitch: lower notes always lie nearer the sky, across strings."""
    return float(3.08 - np.clip((note-low)/(high-low), 0, 1)*1.30)


def contiguous_runs(mask):
    padded = np.r_[False, np.asarray(mask, dtype=bool), False].astype(int)
    starts = np.flatnonzero(np.diff(padded) == 1)
    ends = np.flatnonzero(np.diff(padded) == -1)
    return [(int(a), int(b)) for a,b in zip(starts, ends)]


def vowel_token(word):
    token = re.sub('[^a-z]', '', word.lower())
    if re.fullmatch('o+h*|o*u+h*|w+o+a*h*', token):
        return 'OH'
    if re.fullmatch('a+h*', token):
        return 'AH'
    return None


def sung_syllable(word):
    token=re.sub('[^a-z]','',word.lower())
    return bool(vowel_token(word) or token in ('ba','da','dah','duh','la','na','ma','fa','ta','ka'))


def cast_duet(mouths, lines):
    """Authored lead exchange and shared refrains, never inferred gender."""
    n = len(mouths)
    lanes = np.zeros((n, 2), dtype=np.int8)
    seen = {}
    casting = []
    for j, line in enumerate(lines):
        lo = max(0, line['start_ms']//50)
        hi = min(n, (line['end_ms']+49)//50)
        key = re.sub('[^a-z ]', '', line['text'].lower()).strip()
        words = key.split()
        refrain = key in seen or 'who knew' in key or 'festivus' in key or (
            len(words) > 0 and all(sung_syllable(w) for w in words))
        slot = (j//2) % 2
        lanes[lo:hi, slot] = mouths[lo:hi]
        if refrain:
            lanes[lo:hi, 1-slot] = mouths[lo:hi]
        seen[key] = j
        casting.append(dict(start_ms=lo*50, end_ms=hi*50,
                            characters=['male','female'] if refrain else [ ('male','female')[slot] ],
                            text=line['text'], reason='shared refrain' if refrain else 'authored phrase exchange'))
    # Wordless acoustic additions outside text are shared backing vocables.
    orphan = (mouths != 0) & (lanes.max(axis=1) == 0)
    lanes[orphan, :] = mouths[orphan, None]
    return lanes, casting


def held_bass_heights(notes, energy):
    """Hold the previous measured position through uncertainty, never invent notes."""
    out = np.full(len(notes), 2.50, dtype=np.float32)
    height = 2.50
    for i in range(len(notes)):
        valid = notes[i][notes[i] >= 0]
        if len(valid) and energy[i] > .09:
            height = bass_neck_height(int(valid[0]))
        out[i] = height
    return out
