"""Reusable native xLights layouts for the 16-panel showcase."""

from models.approval_layouts import ac_circuits, allocate, arch, cane, house, structures, tree
from models.ultimate_showcase import Garden


NAMES = (
    'Classic LOR 16 AC', '64-channel AC', 'Original 256-channel AC', 'Basic RGB house',
    'RGB arches and mini-tree forest', 'Single mega-tree residence', 'Dual mega-tree residence',
    'Singing-face house', 'Singing Christmas trees', 'Illuminated parade van',
    'Canonical snowman band', 'Synchronized neighborhood', 'Massive Spiral Forest Estate',
    'Double-Helix Wonderland', '3D Helix Megastructure', 'Ultimate Helix Universe',
)
PALETTES = (
    ('#FD4B43', '#55E56B', '#FFF1C7'),
    ('#7FE7FF', '#B598FF', '#FFD688'),
    ('#FF6B86', '#52DBC0', '#FFD076'),
    ('#6BCBFF', '#FFCF73', '#EB8AFF'),
)


def singing_props(garden, kinds, positions, *, scale, native_extended_mouths=False):
    from models.showcase_flavors import _move
    from models.snowman_ensemble import face

    for i, (kind, position) in enumerate(zip(kinds, positions, strict=True)):
        model = face(garden, kind, 0, garden.palette[i % len(garden.palette)],
                     native_extended_mouths=native_extended_mouths)
        _move(model, (0, 5, 0), position, scale)
        model.name = f'SHOWCASE_{kind.upper()}_FACE_{i + 1}'
        model.zone = 'SINGING_TREES' if kind == 'tree' else 'SINGING_FACES'
        model.details.update(generic_singer=('estimated_lead', 'estimated_backing')[i % 2],
                             showcase_face=True)
        model.attrs.update(PixelSize='11', BlackTransparency='100')


def assign_routes(garden, *, panel_number=None):
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
        if model.kind != 'ac':
            model.attrs['PixelSize'] = str(min(int(model.attrs['PixelSize']), 11))
            zone = model.zone
            if zone in ('ARCHES', 'TREES', 'CANES', 'MEGA_TREES', 'HOUSE'):
                x, _, z = model.points.mean(axis=0)
                layer = 'FACADE' if zone == 'HOUSE' else 'FOREGROUND' if z > 14 else 'YARD'
                model.details.setdefault('showcase_group', f'{layer}_{"LEFT" if x < -5 else "RIGHT" if x > 5 else "CENTER"}')
                model.details.setdefault('spatial_phase', (x / 110 + .5) % 1)
                model.details.setdefault('spatial_direction', 1 if x < 0 else -1)
                if zone in ('ARCHES', 'MEGA_TREES', 'TREES'):
                    model.details.setdefault('propagation_delay_ms', round(min(60, abs(x) * 1.1)))
                if zone == 'TREES':
                    model.details.setdefault('spatial_axis', 'y')
    # Reuse Helix's existing source-role choreographer, but give each native
    # layout a distinct, source-bound ensemble rather than broadcasting the
    # same mixed-bus beat across every zone. No synthetic events are added.
    ensemble = {
        4: {'HOUSE': 'guitarist', 'TREES': 'bassist'},
        5: {'ARCHES': 'keyboardist', 'TREES': 'guitarist'},
        6: {'MEGA_TREES': 'bassist', 'ARCHES': 'keyboardist'},
        7: {'MEGA_TREES': 'guitarist', 'ARCHES': 'drummer'},
        8: {'ARCHES': 'keyboardist', 'TREES': 'bassist'},
        9: {'TREES': 'guitarist', 'CANES': 'keyboardist'},
        10: {'MATRICES': 'keyboardist', 'TREES': 'bassist'},
        12: {'MATRICES': 'keyboardist', 'SPINNERS': 'drummer', 'SNOWFLAKES': 'guitarist'},
    }.get(panel_number, {})
    for model in garden.models:
        if model.details.get('review_role') or model.details.get('generic_singer'):
            continue
        if model.zone in ensemble:
            model.details['musical_role'] = ensemble[model.zone]
    configure_source_routes(garden.models)
    return allocate(garden)


def mega_tree(garden, x, z, *, height, radius, sculptor=None):
    garden.tree(f'MEGA_TREE_{len(garden.models):02}', x, z, height, radius,
                        0, 20, 42, 'MEGA_TREES')
    # Phase groups wind around the existing native cone from base to tip.
    model = garden.models[-1]
    model.details.update(spatial_axis='spiral', spatial_direction=1 if x < 0 else -1)
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


def residential(garden, number, *, native_extended_mouths=False):
    if number in (4, 6, 7, 8, 9, 10, 12):
        house(garden, z=-23, scale=.85 if number in (6, 7, 9) else 1)
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
        singing_props(garden, ('bulb', 'snowman'), ((-16, 14, -19), (16, 14, -19)),
                      scale=.25, native_extended_mouths=native_extended_mouths)
        for x in (-33, 33):
            tree(garden, x, -2, h=10, r=3)
        for x in (-19, 0, 19):
            arch(garden, x, 19, width=12, height=5)
    if number == 9:
        singing_props(garden, ('tree', 'tree'), ((-23, 0, 10), (22, 0, 6)),
                      scale=.44, native_extended_mouths=native_extended_mouths)
        for x in (-34, 0, 34):
            cane(garden, x, 20, h=7)
        for x in (-36, 35):
            tree(garden, x, -10, h=12, r=3.5)
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



def upgrade_residential(garden, number):
    """Additional native customer props; preserve fixed legacy AC budgets."""
    import math
    if number == 10:
        # Replace the house with a recognizable three-dimensional compact parade van.
        garden.models.clear()
        def line(name, points, role, axis='x', color='#65D9FF', count=100):
            m = garden.poly(name, points, count, 'SPATIAL_VEHICLE', 'Parade van RGB contour', color)
            m.details.update(musical_role=role, spatial_axis=axis, source_display_floor=.20)
            return m
        for side in (-1, 1):
            z=side*9
            line(f'VAN_BODY_{side}', [(-39,8,z),(-39,23,z),(-27,27,z),(-17,42,z),(32,42,z),(39,34,z),(39,8,z),(-39,8,z)], 'guitarist', count=220)
            line(f'VAN_WINDOW_{side}', [(-26,27,z),(-15,38,z),(5,38,z),(5,27,z),(-26,27,z)], 'keyboardist')
            for wheel,x in enumerate((-24,25)):
                pts=[(x+8*math.cos(t*2*math.pi/80),8+8*math.sin(t*2*math.pi/80),z) for t in range(81)]
                line(f'VAN_WHEEL_{side}_{wheel}',pts,'bassist','spiral','#FFCE79',80)
            structures(garden).mesh(f'VAN_SIDE_MATRIX_{side}', (19,25,z), 25, 15, 'MATRICES')
        for i,x in enumerate((-39,-17,10,39)):
            line(f'VAN_CROSSBAR_{i}',[(x,8,-9),(x,8,9)],'bassist','z')
        for i,x in enumerate((-8,9,26)):
            structures(garden).starburst((x,48,0),5,color=i,zone='SNOWFLAKES')
        for i,z in enumerate((-9,9)):
            line(f'VAN_ROOF_{i}',[(-17,42,z),(32,42,z)],'keyboardist')
        # Extravagant physical parade installation: roof rack, mounted cones,
        # layered body strips, and a wheeled concert trailer with supported arches.
        for side in (-1, 1):
            z = side * 9
            for y in (11, 15, 19, 23):
                line(f'VAN_BODY_LAYER_{side}_{y}', [(-37,y,z),(37,y,z)], 'guitarist', count=150)
            for x in (-24,25):
                for radius in (5,7):
                    line(f'VAN_WHEEL_RING_{side}_{x}_{radius}', [(x+radius*math.cos(t*math.pi/40),8+radius*math.sin(t*math.pi/40),z) for t in range(81)], 'bassist','spiral',count=80)
        for x in (-12,8,28):
            for z in (-5,5):
                line(f'ROOF_TREE_{x}_{z}', [(x+3*(1-t/240)*math.cos(t*math.pi/20),43+12*t/240,z+3*(1-t/240)*math.sin(t*math.pi/20)) for t in range(241)], 'keyboardist','spiral',count=240)
        line('TRAILER_HITCH',[(39,9,0),(51,9,0)],'bassist',count=30)
        for side in (-1,1):
            z=side*12
            line(f'TRAILER_DECK_{side}',[(51,8,z),(125,8,z),(125,12,z),(51,12,z),(51,8,z)],'bassist',count=260)
            for x in (70,108):
                line(f'TRAILER_WHEEL_{side}_{x}',[(x+7*math.cos(t*math.pi/40),7+7*math.sin(t*math.pi/40),z) for t in range(81)],'bassist','spiral',count=80)
            for x in (54,77,100,123):
                line(f'TRAILER_POST_{side}_{x}',[(x,12,z),(x,39,z)],'guitarist','y',count=100)
            line(f'TRAILER_CANOPY_RAIL_{side}',[(54,39,z),(123,39,z)],'keyboardist',count=240)
        for x in (54,77,100,123):
            line(f'TRAILER_CANOPY_ARCH_{x}',[(x,39+9*math.sin(t*math.pi/80),-12*math.cos(t*math.pi/80)) for t in range(81)],'keyboardist','z',count=160)
        for x in (60,82,104,120):
            structures(garden).starburst((x,39,-12),5,zone='SNOWFLAKES')
        for x in (65,88,111):
            structures(garden).mesh(f'TRAILER_MATRIX_{x}',(x,14,-12),19,18,'MATRICES')
        return
    if number == 12:
        for i,x in enumerate((-95,95)):
            house(garden,x,-30,.75,prefix=f'NEIGHBOR_{i}')
            mega_tree(garden,x,-5,height=30,radius=8)
        for i in range(6):
            arch(garden,-100+40*i,32,width=24,height=9)
    elif number in (4,5,6,7,8,9):
        for i,x in enumerate((-42,-28,28,42)):
            structures(garden).starburst((x,24 if number != 5 else 15,-12),4,color=i,zone='SNOWFLAKES')
        for i,x in enumerate((-30,-10,10,30)):
            cane(garden,x,29,h=7)
        if number in (6,7,9):
            for x in (-38,38):
                structures(garden).mesh(f'YARD_MATRIX_{x}',(x,4,-2),12,12,'MATRICES')
        if number in (5,7):
            for x in (-52,52):
                tree(garden,x,12,h=18,r=5)


def build(number, plan, *, duration, native_extended_mouths=False):
    from tools.build_current_comparison import layout as current_layout

    if not 1 <= number <= len(NAMES):
        raise ValueError(f'Unknown full-song layout {number}')
    if number == 3:
        garden, band = current_layout(1, plan, duration=duration)
        configure_legacy_routes(garden)
        return garden, band
    if number >= 13:
        from models.advanced_full_song_showcase import build_showcase
        return build_showcase(number, plan, duration=duration, native_band=canonical_owner_band,
                              native_extended_mouths=native_extended_mouths)

    garden = Garden(title=NAMES[number - 1], slug=f'full_song_{number:02}',
                    palette=PALETTES[0 if number <= 2 else 1 + (number % 3)])
    if number == 11:
        return garden, canonical_owner_band(garden, plan, duration=duration,
                                           native_extended_mouths=native_extended_mouths)
    if number <= 2:
        ac_house(garden, number)
    else:
        residential(garden, number, native_extended_mouths=native_extended_mouths)
    upgrade_residential(garden, number)
    result = assign_routes(garden, panel_number=number)
    if number in (10, 12):
        from tools.source_role_routing import configure_advanced_spatial_routes
        configure_advanced_spatial_routes(garden.models)
    return result, None


def configure_legacy_routes(garden):
    from tools.source_role_routing import configure_source_routes

    configure_source_routes(garden.models)


def canonical_owner_band(garden, plan, *, duration, rock=False, native_extended_mouths=False):
    from tools.build_current_comparison import native_band

    return native_band(garden, plan, rock=rock, duration=duration, showcase_source=True,
                       overview=bool(garden.models), native_extended_mouths=native_extended_mouths)
