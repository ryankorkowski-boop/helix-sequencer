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
        model.attrs.setdefault('PixelSize', '16')


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


def _universe(g, s):
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


def _neighborhood(g, s):
    for index, (x, z) in enumerate(((-112, -55), (-56, -72), (0, -55),
                                   (56, -72), (112, -55))):
        first = len(g.models)
        house(g, x, z, .57, prefix=f'NEIGHBORHOOD_{index}')
        for model in g.models[first:]:
            role = 'guitarist' if 'ROOF' in model.name or 'RIDGE' in model.name else (
                'keyboardist' if 'WINDOW' in model.name else 'bassist')
            model.details.update(musical_role=role, spatial_phase=index / 5,
                                 spatial_direction=1 if index % 2 else -1,
                                 propagation_delay_ms=index * 95,
                                 source_display_floor=.20)
        for j, dx in enumerate((-22, 0, 22)):
            first = len(g.models)
            s.arch((x + dx, 0, z + 34), 17, 14 + j * 2, (index + j) % 3)
            _music(g, first, 'drummer', phase=(index * 3 + j) / 15,
                   delay=index * 95 + j * 24,
                   drum=('kick', 'snare', 'hihat')[j])
        for j, dx in enumerate((-28, 28)):
            first = len(g.models)
            s.tree(x + dx, z + 11, 26 + 5 * j, 6, color=index + j)
            _music(g, first, 'guitarist' if j == 0 else 'bassist',
                   phase=(index + j) / 6, delay=index * 95)
        first = len(g.models)
        s.mesh(f'NEIGHBORHOOD_MATRIX_{index}', (x, 4, z + 5),
               20, 23, 'MATRICES', index)
        _music(g, first, 'keyboardist', phase=index / 5, delay=index * 95)
        first = len(g.models)
        s.starburst((x, 44, z), 6, color=index)
        _music(g, first, 'drummer', phase=index / 5, drum='cymbal')
    for index, z in enumerate((3, 22, 40)):
        first = len(g.models)
        s.path(f'NEIGHBORHOOD_TRAVEL_{index}',
               [(-138, 2 + index * 5, z), (-70, 6 + index * 5, z),
                (0, 9 + index * 5, z), (70, 6 + index * 5, z),
                (138, 2 + index * 5, z)],
               'TRAVEL', index, count=320)
        _music(g, first, ('keyboardist', 'guitarist', 'bassist')[index],
               phase=index / 3, direction=1 if index % 2 else -1)


def _ultimate(g, s):
    # Preserve a clear central foreground for the original canonical cast.
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


def build_showcase(number, plan, *, duration, native_band):
    if number not in (13, 14, 15, 16):
        raise ValueError('Advanced showcase is limited to panels 13–16')
    names = {13: 'Mega RGB Estate', 14: '3D Pixel Universe',
             15: 'Synchronized Neighborhood', 16: 'Ultimate Helix Showcase'}
    g = Garden(title=names[number], slug=f'full_song_{number:02}',
               palette=('#63E4FF', '#F68BFF', '#FFE38C'))
    s = structures(g)
    {13: _estate, 14: _universe, 15: _neighborhood, 16: _ultimate}[number](g, s)
    cast = native_band(g, plan, rock=False, duration=duration) if number == 16 else None
    for model in g.models:
        model.attrs.setdefault('PixelSize', '16')
        model.details.setdefault('source_display_floor', .20)
        if not model.submodels:
            model.submodels['ALL'] = list(range(1, len(model.points) + 1))
    return g, cast
