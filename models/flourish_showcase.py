"""Ordered musical sculpture paths, extending the existing native-family garden."""
from __future__ import annotations
import math
import numpy as np
from models.ultimate_showcase import build_ultimate_garden, CYAN, PINK, GOLD, VIOLET


def build_flourish_garden():
    g = build_ultimate_garden()
    g.title = 'Helix Spiral Symphony'
    g.slug = 'Helix_Spiral_Symphony'
    g.description = 'Four interwoven spiral runs and paired wave promenades around the complete sculpture garden.'
    for arm, color in enumerate((CYAN, PINK, GOLD, VIOLET)):
        for order in range(12):
            u = np.linspace(order / 12, (order + .96) / 12, 48)
            r = 22 + 158 * u
            angle = 1.55 * math.tau * u + arm * math.pi / 2
            points = np.c_[r * np.cos(angle), 49 + .25 * r * np.sin(angle), -83 + .32 * r * np.sin(angle)]
            g.custom(f'HX_FLOW_SPIRAL_{arm+1}_{order+1:02d}', points,
                     f'FLOW_SPIRAL_{arm+1}', 'Ordered inner-to-outer spiral run',
                     [color] * len(points), {'RUN': list(range(1, len(points)+1))},
                     details={'flow_order': order, 'flow_lane': arm, 'musical_flow': 'spiral'})
    for lane, color in enumerate((CYAN, GOLD)):
        for order in range(16):
            u = np.linspace(order / 16, (order + .96) / 16, 32)
            points = np.c_[-182 + 364*u, 11 + 7*np.sin(2*math.tau*u + lane*math.pi), np.full(len(u), -126+lane*11)]
            g.custom(f'HX_FLOW_WAVE_{lane+1}_{order+1:02d}', points,
                     f'FLOW_WAVE_{lane+1}', 'Ordered west-to-east wave promenade',
                     [color] * len(points), {'RUN': list(range(1, len(points)+1))},
                     details={'flow_order': order, 'flow_lane': lane, 'musical_flow': 'wave'})
    start = 1
    for model in g.models:
        model.start = start
        start += model.channels
    return g


def envelope(model, count, attacks, energy, fps=20):
    """Source-driven delayed flourishes; order is artistic, attacks are measured."""
    time = np.arange(count)/fps
    flow = model.details.get('musical_flow')
    if flow:
        order = model.details['flow_order']
        delay = .055*order if flow == 'spiral' else .045*order
        values = np.full(count, .07, np.float32)
        for onset, strength in attacks:
            age = time - onset - delay
            hit = (age >= 0) & (age < .42)
            values[hit] = np.maximum(values[hit], .07 + .90*strength*np.exp(-age[hit]/.14))
        return values
    # Quiet foundation with measured phrase dynamics; control fixtures stay idle.
    return np.clip(.08 + .68*energy, .08, .76).astype(np.float32)
