"""Reusable native xLights layouts for the 16-panel showcase."""

from models.approval_layouts import ac_circuits, allocate, arch, cane, house, structures, tree
from models.ultimate_showcase import Garden


NAMES = (
    'Classic LOR 16 AC', '64-channel AC', 'Original 256-channel AC', 'Basic RGB house',
    'RGB arches and mini-tree forest', 'Single mega-tree residence', 'Dual mega-tree residence',
    'Singing-face house', 'Singing Christmas trees', 'Matrix-centered residence',
    'Canonical snowman band', 'Advanced RGB residence', 'Massive Spiral Forest Estate',
    'Double-Helix Wonderland', '3D Helix Megastructure', 'Ultimate Helix Universe',
)
PALETTES = (
    ('#FD4B43', '#55E56B', '#FFF1C7'),
    ('#7FE7FF', '#B598FF', '#FFD688'),
    ('#FF6B86', '#52DBC0', '#FFD076'),
    ('#6BCBFF', '#FFCF73', '#EB8AFF'),
)


def singing_props(garden, kinds, positions, *, scale):
    from models.showcase_flavors import _move
    from models.snowman_ensemble import face

    for i, (kind, position) in enumerate(zip(kinds, positions, strict=True)):
        model = face(garden, kind, 0, garden.palette[i % len(garden.palette)])
        _move(model, (0, 5, 0), position, scale)
        model.name = f'SHOWCASE_{kind.upper()}_FACE_{i + 1}'
        model.zone = 'SINGING_TREES' if kind == 'tree' else 'SINGING_FACES'
        model.details.update(generic_singer=('estimated_lead', 'estimated_backing')[i % 2],
                             showcase_face=True)
        model.attrs.update(PixelSize='18', BlackTransparency='100')


def assign_routes(garden):
    from tools.source_role_routing import configure_source_routes

    for model in garden.models:
        if model.details.get('review_role') or model.details.get('generic_singer'):
            continue
        model.attrs.setdefault('BlackTransparency', '100')
        model.attrs.setdefault('PixelSize', '15')
        model.details.setdefault('source_display_floor', .24)
        model.details.setdefault('musical_role', {
            'ARCHES': 'guitarist', 'HOUSE': 'guitarist', 'MEGA_TREES': 'keyboardist',
            'MATRICES': 'keyboardist', 'SPINNERS': 'drummer', 'SNOWFLAKES': 'drummer',
            'WREATHS': 'keyboardist',
        }.get(model.zone, 'bassist'))
        if 'WINDOW' in model.name and model.zone == 'HOUSE':
            model.details['musical_role'] = 'keyboardist'
        if model.zone == 'ARCHES':
            model.details.setdefault('spatial_axis', 'x')
    configure_source_routes(garden.models)
    return allocate(garden)


def mega_tree(garden, x, z, *, height, radius, sculptor=None):
    garden.tree(f'MEGA_TREE_{len(garden.models):02}', x, z, height, radius,
                        0, 20, 42, 'MEGA_TREES')
    # Vertical groups make climbs visible across the whole cone.
    model = garden.models[-1]
    model.details.update(spatial_axis='y', spatial_direction=1 if x < 0 else -1)
    (sculptor or structures(garden)).starburst((x, height + 4, z), 4)


def ac_house(garden, number):
    house(garden, z=-12)
    for x in (-27, -9, 9, 27):
        arch(garden, x, 14, width=15, height=8)
    for x in (-32, -20, 20, 32):
        tree(garden, x, 3, h=10, r=3)
    for x in (-43, 43):
        cane(garden, x, 10, h=10)
    ac_circuits(garden, 1 if number == 1 else 4)
    for i, model in enumerate(garden.models):
        model.attrs['PixelSize'] = '21' if number == 1 else '15'
        model.details['source_display_floor'] = .42
        if model.zone == 'ARCHES':
            model.details.update(musical_role='drummer',
                                 percussion_component=('kick', 'snare', 'hihat', 'cymbal')[(i - 6) % 4])


def residential(garden, number):
    if number in (4, 6, 7, 8, 10, 12):
        house(garden, z=-19, scale=.85 if number in (6, 7) else 1)
    if number in (4, 6, 7, 12):
        for x in (-35, 35):
            cane(garden, x, 15)
    if number in (5, 6, 7, 10, 12):
        for x in (-39, -19, 0, 19, 39):
            arch(garden, x, 21, width=16, height=7)
    if number == 5:
        for z, offset in ((-12, 0), (4, 7)):
            for x in (-42, -28, -14, 0, 14, 28, 42):
                tree(garden, x + offset, z, h=13 if z < 0 else 8, r=4)
    if number == 6:
        mega_tree(garden, 47, -8, height=46, radius=12)
    if number in (7, 12):
        for x in (-48, 48):
            mega_tree(garden, x, -14, height=41, radius=11)
    if number == 8:
        singing_props(garden, ('bulb', 'snowman'), ((-32, 0, 19), (32, 0, 19)), scale=.88)
    if number == 9:
        singing_props(garden, ('tree', 'tree'), ((-30, 0, 13), (30, 0, 13)), scale=1.05)
        for x in (-52, 0, 52):
            cane(garden, x, 22, h=10)
    if number == 10:
        structures(garden).mesh('PORCH_MATRIX', (0, 4, 9), 39, 23, 'MATRICES')
        for x in (-38, 38):
            tree(garden, x, -2, h=20, r=6)
    if number == 12:
        s = structures(garden)
        s.mesh('GARAGE_MATRIX', (0, 3, 3), 28, 15, 'MATRICES')
        s.ring('GABLE_WREATH', (0, 31, -17), 7, 7, 'WREATHS', plane='xy')
        for i, x in enumerate((-57, -26, 26, 57)):
            s.tree(x, 6, h=18, r=5, color=i)
            s.starburst((x, 25, -8), 5, color=i, zone='SNOWFLAKES')
        for i, x in enumerate((-36, 36)):
            s.starburst((x, 15, 10), 7, color=i, zone='SPINNERS')


def build(number, plan, *, duration):
    from tools.build_current_comparison import layout as current_layout

    if not 1 <= number <= len(NAMES):
        raise ValueError(f'Unknown full-song layout {number}')
    if number == 3:
        garden, band = current_layout(1, plan, duration=duration)
        configure_legacy_routes(garden)
        return garden, band
    if number >= 13:
        from models.advanced_full_song_showcase import build_showcase
        return build_showcase(number, plan, duration=duration, native_band=canonical_owner_band)

    garden = Garden(title=NAMES[number - 1], slug=f'full_song_{number:02}',
                    palette=PALETTES[0 if number <= 2 else 1 + (number % 3)])
    if number == 11:
        return garden, canonical_owner_band(garden, plan, duration=duration)
    if number <= 2:
        ac_house(garden, number)
    else:
        residential(garden, number)
    return assign_routes(garden), None


def configure_legacy_routes(garden):
    from tools.source_role_routing import configure_source_routes

    configure_source_routes(garden.models)


def canonical_owner_band(garden, plan, *, duration, rock=False):
    from tools.build_current_comparison import native_band

    return native_band(garden, plan, rock=rock, duration=duration, showcase_source=True,
                       overview=bool(garden.models))
