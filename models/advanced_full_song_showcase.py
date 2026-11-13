"""Four premium, physically distinct native xLights showcases for the 16-panel pilot.

Every fixture remains an editable native model. Effects are generated later from
the retained Helix source event plan, not from invented beat or random clocks.
"""
from __future__ import annotations

from models.approval_layouts import house, structures
from models.ultimate_showcase import Garden


def _music(garden, first, role, *, phase=0., direction=1, delay=0, drum=None):
    """Assign one independent source lane and spatial route to newly added props."""
    for index, model in enumerate(garden.models[first:]):
        model.details.update(
            musical_role=role,
            spatial_phase=(phase + index * .13) % 1.,
            spatial_direction=direction,
            propagation_delay_ms=delay + index * 17,
            source_display_floor=.20,
        )
        if role == 'drummer':
            model.details['percussion_component'] = drum or ('kick', 'snare', 'hihat', 'cymbal')[index % 4]
        model.attrs.setdefault('PixelSize', '8')


def _estate(g, s):
    for index, (x, z, scale) in enumerate(((0, -66, 1.30), (-84, -81, .78), (84, -81, .78))):
        first = len(g.models)
        house(g, x, z, scale, prefix=f'ESTATE_{index}')
        for model in g.models[first:]:
            name = model.name
            model.details.update(
                musical_role='guitarist' if 'ROOF' in name or 'RIDGE' in name else
                             'keyboardist' if 'WINDOW' in name else 'bassist',
                spatial_phase=(index * .3) % 1.,
                spatial_direction=-1 if index == 0 else 1,
                propagation_delay_ms=index * 85,
                source_display_floor=.20,
            )
    for row, z in enumerate((-35, -10, 17)):
        for lane, x in enumerate(range(-106, 107, 27)):
            model = s.tree(x + (row % 2) * 9, z, 13 + (row + lane) % 3 * 4, 5, color=lane + row)
            model.zone = f'SPIRAL_GROVE_{row + 1}'
            _music(g, len(g.models) - 1, ('guitarist', 'keyboardist', 'bassist')[row],
                   phase=lane / 8, direction=1 if (lane + row) % 2 else -1, delay=row * 26)
            model.details['spatial_axis'] = 'y'
    from models.full_song_layouts import mega_tree
    for x in (-126, 126):
        first = len(g.models)
        mega_tree(g, x, -58, height=52, radius=13, sculptor=s)
        _music(g, first, 'keyboardist', direction=1 if x < 0 else -1)
    for index, x in enumerate((-117, -74, -30, 30, 74, 117)):
        first = len(g.models)
        s.tree(x, -35 if index % 2 else -51, 37 + index % 3 * 7, 10, color=index)
        _music(g, first, ('guitarist', 'keyboardist', 'bassist')[index % 3],
               phase=index / 6, direction=1 if x > 0 else -1, delay=index * 31)
        first = len(g.models)
        s.starburst((x, 49 + index % 3 * 7, -35), 6, color=index)
        _music(g, first, 'drummer', phase=index / 6, drum=('kick', 'snare', 'hihat', 'cymbal')[index % 4])
    for index, x in enumerate((-100, -72, -44, -16, 16, 44, 72, 100)):
        first = len(g.models)
        s.arch((x, 0, 9 + (index % 2) * 17), 24, 23 + index % 3 * 3, color=index)
        _music(g, first, 'drummer', phase=index / 8, direction=(-1) ** index,
               delay=index * 24, drum=('kick', 'snare', 'hihat', 'cymbal')[index % 4])
    for index, x in enumerate((-88, -44, 0, 44, 88)):
        first = len(g.models)
        s.mesh(f'ESTATE_MATRIX_{index}', (x, 8, -55), 25, 32, 'MATRICES', index)
        _music(g, first, ('keyboardist', 'bassist', 'guitarist')[index % 3], phase=index / 5)
    for index, x in enumerate((-91, -31, 31, 91)):
        first = len(g.models)
        for radius in (7, 11):
            s.ring(f'ESTATE_SPINNER_{index}', (x, 33, -12), radius, radius,
                   'SPINNERS', index, plane='xy', count=120)
        _music(g, first, 'drummer', phase=index / 4,
               drum=('hihat', 'snare', 'cymbal', 'kick')[index])


def _megastructure(g, s):
    for depth, z in enumerate(range(-65, 58, 17)):
        first = len(g.models)
        s.ring(f'SPIRAL_TUNNEL_{depth}', (0, 30, z), 42, 29,
               'SPIRAL_TUNNELS', depth, plane='xy', count=100)
        _music(g, first, ('bassist', 'guitarist')[depth % 2], direction=(-1) ** depth,
               delay=depth * 20)
    for i, x in enumerate((-85, 85)):
        for j, radius in enumerate((8, 15, 22)):
            model = s.dna(f'NESTED_TOWER_{i}_{j}', (x, 0, -17), (x, 83 - j * 8, -17),
                          radius, (-1) ** j * (3 + j), 'NESTED_TOWERS', i + j)
            _music(g, len(g.models) - 1, ('guitarist', 'keyboardist', 'bassist')[j],
                   phase=i * .5, direction=(-1) ** j)
            model.details['spatial_axis'] = 'y'
    # Nine independent native matrix planes in actual X/Y/Z space, not
    # nine differently colored copies of one front-facing layout.
    for depth, z in enumerate((-72, -45, -18)):
        for lane, x in enumerate((-73, 0, 73)):
            first = len(g.models)
            s.mesh(f'UNIVERSE_GRID_Z{depth}_X{lane}', (x, 7, z),
                   54, 55, 'THREE_D_GRID', (depth + lane) % 3,
                   wave=2 + depth * 2, yaw=(lane - 1) * 14)
            _music(g, first, ('keyboardist', 'guitarist', 'bassist')[(depth + lane) % 3],
                   phase=(depth * 3 + lane) / 9, direction=1 if lane % 2 else -1,
                   delay=depth * 120 + lane * 45)
    for depth, z in enumerate((-65, -30, 5, 40)):
        first = len(g.models)
        s.arch((0, 0, z), 170 - depth * 23, 88 - depth * 12, depth, zone='DEPTH')
        _music(g, first, 'drummer', phase=depth / 4, delay=depth * 100,
               drum=('kick', 'snare', 'hihat', 'cymbal')[depth])
        for side in (-1, 1):
            first = len(g.models)
            s.dna(f'DEPTH_COLUMN_{depth}_{side}',
                  [side * (91 - depth * 12), 0, z],
                  [side * (91 - depth * 12), 63 - depth * 6, z],
                  4, 3, 'HELIX', depth + (side > 0))
            _music(g, first, 'guitarist' if side < 0 else 'bassist',
                   phase=depth / 4, direction=side, delay=depth * 80)
    for index, x in enumerate((-112, -56, 56, 112)):
        first = len(g.models)
        s.tree(x, -80 + index * 17, 52, 10, color=index)
        _music(g, first, 'keyboardist' if index % 2 else 'guitarist', phase=index / 4)
    for index, y in enumerate((15, 31, 47, 63)):
        first = len(g.models)
        s.ring(f'UNIVERSE_ORBIT_{index}', (0, y, -12), 22 + index * 12,
               16 + index * 6, 'ORBITS', index, plane='xz', count=180)
        _music(g, first, 'keyboardist', phase=index / 4, direction=(-1) ** index)


def _wonderland(g, s):
    for pair, x in enumerate((-40, 40)):
        for lane, (dx, turns) in enumerate(((-8, 3.5), (8, -3.5))):
            model = s.dna(f'WONDERLAND_HELIX_{pair}_{lane}', (x + dx, 0, -26 + lane * 14),
                          (x - dx, 74, -36 + lane * 14), 11, turns, 'TWIN_HELICES', lane)
            _music(g, len(g.models) - 1, ('guitarist', 'bassist')[lane],
                   phase=pair * .35, direction=1 - lane * 2)
            model.details['spatial_axis'] = 'y'
    for lane, x in enumerate((-103, -86, -70, -20, 0, 20, 70, 86, 103)):
        for row, z in enumerate((4, 27)):
            model = s.tree(x, z, 14 + (lane % 3) * 5, 5, color=lane + row)
            model.zone = f'COUNTER_ROTATING_GROVE_{row + 1}'
            _music(g, len(g.models) - 1, ('guitarist', 'keyboardist')[row],
                   phase=lane / 9, direction=(-1) ** row, delay=lane * 12)
            model.details['spatial_axis'] = 'y'
    for row, z in enumerate((-41, -11, 32)):
        first = len(g.models)
        s.arch((0, 0, z), 178 - row * 32, 56 - row * 15, row, zone='LAYERED_ARCHES')
        _music(g, first, ('drummer', 'guitarist', 'bassist')[row], direction=(-1) ** row)
    for i, x in enumerate((-100, -70, 70, 100)):
        first = len(g.models)
        s.starburst((x, 40, -9), 7, color=i, zone='SNOWFLAKES')
        _music(g, first, 'drummer', drum=('kick', 'snare', 'hihat', 'cymbal')[i])


def _ultimate(g, s, *, native_extended_mouths=False):
    # Keep the foreground cast and both face pairs in separate sight lines.
    from models.full_song_layouts import mega_tree, singing_props
    singing_props(g, ('bulb', 'snowman', 'tree', 'tree'),
                  ((-61, 2, 43), (61, 2, 43), (-106, 1, 30), (106, 1, 30)), scale=.67,
                  native_extended_mouths=native_extended_mouths)
    for row, z in enumerate((-37, -9, 17)):
        for lane, x in enumerate((-118, -98, -79, -44, 44, 79, 98, 118)):
            model = s.tree(x, z, 11 + (lane + row) % 4 * 4, 5, color=lane + row)
            model.zone = f'FINALE_SPIRAL_FOREST_{row + 1}'
            model.details['spatial_axis'] = 'y'
            _music(g, len(g.models) - 1, ('guitarist', 'keyboardist', 'bassist')[row],
                   direction=(-1) ** lane, phase=lane / 8, delay=row * 25)
    for i, x in enumerate((-135, -73, 73, 135)):
        first = len(g.models)
        mega_tree(g, x, -49, height=40 + (i % 2) * 10, radius=11, sculptor=s)
        _music(g, first, 'keyboardist', direction=(-1) ** i, phase=i / 4)
    for i, z in enumerate((-54, -30, -6, 18)):
        first = len(g.models)
        s.ring(f'FINALE_TUNNEL_{i}', (0, 31, z), 45 - i * 4, 31 - i * 3,
               'SPIRAL_TUNNELS', i, plane='xy')
        s.mesh(f'FINALE_DEPTH_GRID_{i}', (0, 1, z - 7), 78, 24,
               'THREE_D_GRID', i, wave=3, yaw=(-1) ** i * 12)
        _music(g, first, ('bassist', 'keyboardist')[i % 2], delay=i * 42)
    for i, x in enumerate((-120, -88, 88, 120)):
        first = len(g.models)
        s.arch((x, 0, 40), 26, 12, i, zone='FORECOURT_ARCHES')
        s.starburst((x, 25, 28), 6, color=i, zone='SNOWFLAKES')
        _music(g, first, 'drummer', drum=('kick', 'snare', 'hihat', 'cymbal')[i])
    for index, x in enumerate((-115, -72, 72, 115)):
        first = len(g.models)
        s.tree(x, -68, 50 + index % 2 * 14, 12, color=index)
        _music(g, first, ('guitarist', 'bassist', 'keyboardist')[index % 3],
               phase=index / 4, direction=1 if x > 0 else -1)
        first = len(g.models)
        s.starburst((x, 71, -68), 9, color=index)
        _music(g, first, 'drummer', drum=('kick', 'snare', 'hihat', 'cymbal')[index])
    for index, x in enumerate((-105, 105)):
        first = len(g.models)
        g.dna(f'ULTIMATE_TWIN_HELIX_{index}', x, -51, 78, 11, 5, 670, 'DNA')
        _music(g, first, 'guitarist' if x < 0 else 'bassist',
               phase=index / 2, direction=-1 if x < 0 else 1)
        first = len(g.models)
        s.mesh(f'ULTIMATE_SIDE_MATRIX_{index}', (x, 10, -82),
               40, 47, 'MATRICES', index, wave=5, yaw=-14 if x < 0 else 14)
        _music(g, first, 'keyboardist', phase=index / 2)
    for index, z in enumerate((-91, -66, -41)):
        first = len(g.models)
        s.arch((0, 0, z), 120 - index * 12, 76 - index * 7, index, zone='DEPTH')
        _music(g, first, 'drummer', phase=index / 3, delay=index * 95,
               drum=('kick', 'snare', 'cymbal')[index])
        first = len(g.models)
        s.dna(f'ULTIMATE_OVERHEAD_{index}', [-72, 65, z],
              [72, 65, z], 4, 3, 'DNA', index)
        _music(g, first, 'keyboardist', phase=index / 3, delay=index * 50)
    for index, x in enumerate((-78, 78)):
        first = len(g.models)
        house(g, x, -98, .64, prefix=f'ULTIMATE_HOME_{index}')
        for model in g.models[first:]:
            model.details.update(
                musical_role='guitarist' if 'ROOF' in model.name else 'bassist',
                spatial_phase=index / 2,
                source_display_floor=.20,
                propagation_delay_ms=index * 120,
            )
    for index, x in enumerate((-50, -25, 25, 50)):
        first = len(g.models)
        s.ring(f'ULTIMATE_FRONT_SPINNER_{index}', (x, 30, -20),
               10, 10, 'SPINNERS', index, plane='xy', count=130)
        _music(g, first, 'drummer',
               drum=('hihat', 'snare', 'cymbal', 'kick')[index], phase=index / 4)
    for index, x in enumerate((-58, -29, 29, 58)):
        first = len(g.models)
        s.mesh(f'ULTIMATE_REAR_LED_{index}', (x, 14, -107), 24, 42,
               'MATRICES', index, wave=2, yaw=(index - 1.5) * 6)
        _music(g, first, ('keyboardist', 'guitarist', 'bassist')[index % 3],
               phase=index / 4)


def build_showcase(number, plan, *, duration, native_band, native_extended_mouths=False):
    if number not in (13, 14, 15, 16):
        raise ValueError('Advanced showcase is limited to panels 13–16')
    from models.full_song_layouts import NAMES
    g = Garden(title=NAMES[number - 1], slug=f'full_song_{number:02}',
               palette=('#63E4FF', '#F68BFF', '#FFE38C'))
    s = structures(g)
    if number == 16:
        _ultimate(g, s, native_extended_mouths=native_extended_mouths)
    else:
        {13: _estate, 14: _wonderland, 15: _megastructure}[number](g, s)
    cast = None
    if number == 16:
        # Distribute pitched phrases across physical prop banks. This prevents
        # broadcasting every simultaneous pitch to every fixture in the finale.
        from collections import defaultdict
        import numpy as np

        banks = defaultdict(list)
        for model in g.models:
            role = model.details.get('musical_role')
            if role in ('guitarist', 'keyboardist', 'bassist'):
                banks[model.zone, role].append(model)
        for (zone, role), members in banks.items():
            members.sort(key=lambda model: (*np.mean(model.points, axis=0), model.name))
            for rank, model in enumerate(members):
                model.details.update(source_route_bank=f'{zone}|{role}', source_route_rank=rank,
                                     source_route_count=len(members))
        cast = native_band(g, plan, rock=False, duration=duration,
                           native_extended_mouths=native_extended_mouths)
    for model in g.models:
        model.attrs.setdefault('PixelSize', '8')
        model.attrs.setdefault('BlackTransparency', '100')
        model.details.setdefault('source_display_floor', .20)
        if not model.submodels:
            model.submodels['ALL'] = list(range(1, len(model.points) + 1))
    return g, cast
