"""Locked native nine-panel review, reusing the Helix layout catalog."""
import math

from models.approval_layouts import helix, structures
from models.ultimate_showcase import Garden
from models.full_song_layouts import (
    build as full_layout, assign_routes, singing_props, canonical_owner_band,
)
from models.advanced_full_song_showcase import _megastructure, _ultimate, _music
from models.showcase_flavors import build_flavor

NAMES = (
    '16-channel LOR AC', 'Original 256-channel AC', 'RGB-heavy house',
    'House with coro singing faces', 'Canonical six-snowman band',
    'Fire & Ice singing trees and matrices', 'Advanced 3D spatial matrix',
    'Sequential keyboard-driven groups', 'Ultimate xLights showcase',
)


def build(number, plan, *, duration, native_extended_mouths=False):
    if number not in range(1, 10):
        raise ValueError('Unknown nine-panel layout')
    if number in (1, 2, 3, 4):
        return full_layout({1: 1, 2: 3, 3: 12, 4: 8}[number], plan, duration=duration,
                           native_extended_mouths=native_extended_mouths)
    if number == 5:
        g = Garden(title=NAMES[4], slug='nine_05')
        return g, canonical_owner_band(g, plan, duration=duration,
                                       native_extended_mouths=native_extended_mouths)
    if number == 6:
        g = build_flavor('fire_and_ice')
        for model in g.models:
            x, _, z = model.points.mean(axis=0)
            side = -1 if x < 0 else 1
            angle = math.atan2(float(z), float(x))
            model.details.setdefault('musical_role', 'guitarist' if side < 0 else 'bassist')
            model.details.update(spatial_phase=(angle / math.tau) % 1,
                                 spatial_direction=side, source_display_floor=.20)
        singing_props(g, ('tree', 'tree'), ((-46, 0, 27), (46, 0, 27)),
                      scale=.5, native_extended_mouths=native_extended_mouths)
        s = structures(g)
        for side in (-1, 1):
            s.mesh(f'SINGING_TREE_MATRIX_{side}', (side * 44, 10, -18), 26, 30, 'MATRICES')
        return assign_routes(g), None
    g = Garden(title=NAMES[number-1], slug=f'nine_{number:02}',
               palette=('#63E4FF', '#F68BFF', '#FFE38C'))
    s = structures(g)
    if number == 7:
        _megastructure(g, s)
    elif number == 8:
        helix(g)
        for index, x in enumerate((-54, -28, 28, 54)):
            first = len(g.models)
            s.mesh(f'KEYBOARD_MATRIX_{index}', (x, 7, -12), 18, 32, 'MATRICES', index)
            _music(g, first, 'keyboardist', phase=index / 4, direction=(-1) ** index)
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
