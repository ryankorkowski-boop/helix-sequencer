"""Map screened pitched events onto one physical two-mallet performer."""
from __future__ import annotations

from collections import defaultdict
import math
from music.magic_keyboard import magic_keyboard_events


def bar_pitch(pitch, low=48, high=96):
    """Retain pitch class and choose the nearest playable octave when needed."""
    if high-low < 11:
        raise ValueError("A chromatic octave is required")
    pitch = int(pitch)
    while pitch < low: pitch += 12
    while pitch > high: pitch -= 12
    return pitch


def unified_mallet_schedule(events, *, duration, low=48, high=96, fps=20, reachable=None):
    if not math.isfinite(duration) or duration <= 0 or fps <= 0:
        raise ValueError("Finite positive duration and frame rate required")
    groups = defaultdict(dict)
    for event in magic_keyboard_events(events, duration=duration):
        frame = round(event.start*fps)
        if frame >= math.ceil(duration*fps):
            continue
        pitch = bar_pitch(event.pitch, low, high)
        previous = groups[frame].get(pitch)
        if previous is None or previous.velocity < event.velocity:
            groups[frame][pitch] = event
    schedule, omitted = [], []
    previous_side = "right"
    for frame, notes in sorted(groups.items()):
        # At most two simultaneous mallet contacts. Extra notes still illuminate
        # their bars/rungs; report the motion limitation, never invent hands.
        chosen = sorted(sorted(notes.items(), key=lambda pair: (-pair[1].velocity, pair[0]))[:2])
        if reachable is not None:
            options = [(p,e,side) for p,e in chosen for side in ('left','right') if p in reachable[side]]
            pairs = [(a,b) for a in options for b in options if a[0]!=b[0] and a[2]!=b[2]]
            if pairs:
                best = max(pairs,key=lambda pair: sum(x[1].velocity for x in pair))
                assigned = sorted(best, key=lambda x:x[0])
            elif options:
                assigned = [max(options,key=lambda x:x[1].velocity)]
            else:
                assigned = []
            chosen = [(p,e) for p,e,_ in assigned]
        omitted.extend(dict(time=frame/fps, pitch=e.pitch, reason="more than two simultaneous mallet contacts")
                       for p, e in notes.items() if p not in {p for p, _ in chosen})
        if not chosen:
            continue
        if reachable is not None:
            sides = [side for _,_,side in assigned]
        elif len(chosen) == 2:
            sides = ("left", "right")
        else:
            pitch = chosen[0][0]; middle = (low+high)/2
            previous_side = "left" if pitch < middle-6 else "right" if pitch > middle+6 else (
                "left" if previous_side == "right" else "right")
            sides = (previous_side,)
        for side, (pitch, event) in zip(sides, chosen):
            schedule.append(dict(time=frame/fps, source_time=event.start,
                display_error_ms=(frame/fps-event.start)*1000, side=side, pitch=pitch,
                source_pitch=event.pitch, velocity=event.velocity, source=event.source))
    return schedule, omitted
