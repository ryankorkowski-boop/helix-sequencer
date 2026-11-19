"""Validate and schedule Helix keyboard cues against addressable DNA rung submodels.

This is an intermediate event plan, NOT a native xLights XSQ export.
A native effect writer must consume the plan and verify output in xLights.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any


def schedule_keyboard_rungs(
    cues: list[dict[str, Any]],
    mapping: dict[str, str],
    *,
    duration: float,
) -> list[dict[str, Any]]:
    """Return deterministic per-note activation intervals with chord overlap.

    Accepted cues use pitch (or midi), start, and either duration or end.
    Notes are clamped to the sequence interval. Overlapping notes on the
    same rung are coalesced; distinct notes retain independent timelines.
    """
    if duration <= 0:
        raise ValueError("duration must be positive")
    expected = {str(n) for n in range(21, 109)}
    if set(mapping) != expected or len(set(mapping.values())) != 88:
        raise ValueError("Expected 88 unique MIDI-to-rung mappings (21..108)")
    by_rung: dict[str, list[tuple[float, float, int]]] = defaultdict(list)
    for cue in cues:
        pitch = int(cue.get("pitch", cue.get("midi", -1)))
        if not 21 <= pitch <= 108:
            continue
        start = float(cue["start"])
        end = float(cue.get("end", start + float(cue.get("duration", 0))))
        if not (0 <= start < duration) or not end > start:
            continue
        end = min(duration, end)
        by_rung[mapping[str(pitch)]].append((start, end, pitch))
    result: list[dict[str, Any]] = []
    for rung, events in by_rung.items():
        events.sort()
        intervals: list[list[float]] = []
        for start, end, _ in events:
            if intervals and start <= intervals[-1][1]:
                intervals[-1][1] = max(intervals[-1][1], end)
            else:
                intervals.append([start, end])
        for start, end in intervals:
            result.append({"submodel": rung, "pitch": events[0][2],
                           "start": start, "end": end, "duration": end - start})
    return sorted(result, key=lambda e: (e["start"], e["pitch"]))
