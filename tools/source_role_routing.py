"""Route measured instrument events across physical single-circuit banks.

The old per-model exporter broadcast every source cue to every one-channel
prop. A bank is an authored spatial interpretation, not a new source event.
Vocal, band, and explicitly spatial multi-part performers keep their clocks.
"""
from __future__ import annotations

from collections import defaultdict
import re

import numpy as np


def configure_source_routes(models):
    """Attach deterministic, position-ordered routing to legacy AC circuits."""
    banks = defaultdict(list)
    for model in models:
        if model.kind != 'ac' or model.details.get('generic_singer'):
            continue
        role = model.details.get('musical_role')
        if role not in ('bassist', 'guitarist', 'keyboardist', 'drummer'):
            continue
        # Keep distinct physical strings/arches separate. Color siblings at
        # the same position belong to different banks: fixed wiring survives.
        name = model.name.lower()
        if name.isdigit():
            family = 'notes_' + str((int(name) - 1) // 16)
        else:
            family = re.sub(r'\b(red|green|white)\b|\d+', '', name)
            family = re.sub(r'\s+', ' ', family).strip()
        key = (family, role, model.attrs.get('StringType'),
               model.details.get('percussion_component'))
        banks[key].append(model)
    for key, members in banks.items():
        members.sort(key=lambda m: (*np.mean(m.points, axis=0), m.start, m.name))
        for rank, model in enumerate(members):
            model.details.update(source_route_bank='|'.join(map(str, key)),
                                 source_route_rank=rank, source_route_count=len(members))


def route_event(model, cue, onset_index, strategy):
    """Return a bank-relative propagation delay, or abstain for this circuit.

    Repeated notes retain pitch position in ordinary phrases. Builds travel
    across the bank on measured onsets; chorus responses spread to adjacent
    circuits. No event may extend past its original offset or fill a rest.
    """
    count = int(model.details.get('source_route_count', 1))
    if count <= 1:
        return 0
    rank = int(model.details['source_route_rank'])
    role = model.details['musical_role']
    if strategy['name'] == 'ascending':
        origin = onset_index % count
    elif cue.get('pitch_midi') is not None:
        low, high = {'bassist': (28, 60), 'guitarist': (40, 88),
                     'keyboardist': (48, 84)}.get(role, (21, 109))
        origin = round(float(np.clip((float(cue['pitch_midi']) - low) / (high - low), 0, 1)) * (count - 1))
    else:
        origin = onset_index % count
    # Deliberate, source-labelled accents may address the complete bank.
    # Ordinary beat/drum cues never implicitly become whole-bank accents.
    if cue.get('synchronized_accent') is True:
        return 0
    width = min(count, max(1, round(count * (.35 if strategy['name'] == 'wide_response' else .18))))
    direction = strategy['direction']
    distance = ((rank - origin) * direction) % count
    if distance >= width:
        return None
    return distance * 35
