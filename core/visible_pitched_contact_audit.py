"""Report only visible pitched-player contacts, not hidden compatibility rigs."""
from __future__ import annotations

import math


def visible_pitched_contacts(performance, frame: int) -> dict:
    """Counts are modeled visual contacts, never acoustically verified strikes."""
    if not performance.scene.legacy_mallet_player:
        assignments=performance.key_assignments
        contacts=sum(
            int(frame < len(assignments.get(side, ()))
                and assignments[side][frame] is not None)
            for side in ('left','right')
            if side in assignments
        )
        return dict(key_contact_frames=contacts, mallet_contacts=0,
                    maximum_mallet_contact_error=0.0)
    contacts=0
    error=0.0
    for hit in performance.mallet_schedule:
        if abs(hit['time']-frame/20)>1e-7:
            continue
        tip=performance.mallet_targets[hit['side']][1]
        center=performance.scene.bars[hit['pitch']]
        expected=(center[0],center[1]+.0845,center[2])
        error=max(error,math.dist(tip,expected))
        contacts+=1
    return dict(key_contact_frames=0, mallet_contacts=contacts,
                maximum_mallet_contact_error=error)
