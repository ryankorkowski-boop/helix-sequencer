"""Nine native review layouts, ordered from homeowner AC to spatial showcases.

The final four use existing Helix geometry and source routing. Their actual
model/pixel counts must be measured; these are bounded pilot layouts, not a
claim of the requested million-pixel full-scale installation.
"""
import math

from models.approval_layouts import structures
from models.ultimate_showcase import Garden
from models.full_song_layouts import (
    build as full_layout, assign_routes, singing_props, canonical_owner_band,
)
from models.advanced_full_song_showcase import _megastructure, _ultimate, _music
from models.showcase_flavors import build_flavor

NAMES = (
    'Classic 16-channel AC', 'Original 256-channel AC', 'Starter RGB house',
    'Advanced RGB singing house', 'Canonical snowman band',
    'Fire & Ice', 'Celestial Orrery', 'Quantum City', 'Infinite Kingdom',
)


def build(number, plan, *, duration, native_extended_mouths=False):
    if number not in range(1, 10):
        raise ValueError('Unknown nine-panel layout')
    if number in (1, 2, 3):
        return full_layout({1: 1, 2: 3, 3: 4}[number], plan, duration=duration,
                           native_extended_mouths=native_extended_mouths)
    if number == 4:
        g, _ = full_layout(12, plan, duration=duration,
                           native_extended_mouths=native_extended_mouths)
        singing_props(g, ('bulb', 'tree'), ((-27, 2, 18), (27, 2, 18)),
                      scale=.35, native_extended_mouths=native_extended_mouths)
        return assign_routes(g), None
    if number == 5:
        g = Garden(title=NAMES[4], slug='nine_05')
        return g, canonical_owner_band(g, plan, duration=duration,
                                       native_extended_mouths=native_extended_mouths)
    if number in (6, 7):
        g = build_flavor('fire_and_ice' if number == 6 else 'celestial_orrery')
        for model in g.models:
            x, y, z = model.points.mean(axis=0)
            side = -1 if x < 0 else 1
            angle = math.atan2(float(z), float(x))
            model.details.setdefault('musical_role', 'guitarist' if side < 0 else 'bassist')
            if number == 7:
                model.details['musical_role'] = ('keyboardist', 'guitarist', 'bassist')[int((angle + math.pi) * 3 / (2 * math.pi)) % 3]
            model.details.update(spatial_phase=(angle / math.tau) % 1,
                                 spatial_direction=side, source_display_floor=.20)
        return assign_routes(g), None
    g = Garden(title=NAMES[number-1], slug=f'nine_{number:02}',
               palette=('#63E4FF', '#F68BFF', '#FFE38C'))
    s = structures(g)
    if number == 8:
        _megastructure(g, s)
        # Independently addressed matrix planes and depth tunnels; reuse
        # source-driven choreography rather than adding a fabricated clock.
    else:
        _ultimate(g, s, native_extended_mouths=native_extended_mouths)
        # Extend the central composition into separate radial districts.
        for district in range(8):
            angle = math.tau * district / 8
            x, z = 175 * math.cos(angle), 110 * math.sin(angle)
            first = len(g.models)
            for lane in range(6):
                model = s.tree(x + 13 * (lane - 2.5), z, 28 + 4 * (lane % 3), 5,
                               color=district + lane)
                model.zone = f'SPIRAL_DISTRICT_{district}'
            s.dna(f'DISTRICT_HELIX_{district}', (x, 0, z), (x, 70, z),
                  10, (-1)**district * 4, f'HELIX_DISTRICT_{district}', district)
            _music(g, first, ('guitarist', 'keyboardist', 'bassist')[district % 3],
                   phase=district / 8, direction=(-1)**district, delay=district * 20)
    return assign_routes(g), None
