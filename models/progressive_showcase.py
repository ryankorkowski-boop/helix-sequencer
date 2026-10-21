"""Six separate native shows progressing from 64 AC circuits to a 3D district."""
from __future__ import annotations
from copy import deepcopy
import numpy as np
from models.ultimate_showcase import Garden, build_ultimate_garden
from models.native_review_band import allocate
from models.review_spatial_worlds import build_world
from models.approved_concepts import Structures, house

RED, WHITE, GREEN = '#FF2020', '#FFFFFF', '#20FF40'
TITLES = ('64-channel AC home', '128-channel AC home', 'AC home plus pixels',
          'Pixel village and megatrees', '3D moire and keyboard helix',
          'Native model district and forced perspective')


def ac_prop(g, name, paths, color):
    # Separate independently wired strands at shared endpoints by 1/16 foot.
    # This is actual exported bulb geometry, not coincident duplicate nodes.
    paths = [np.asarray(p) + (0, 0, i / 16) for i, p in enumerate(paths)]
    # One continuous strand can also repeat its bend endpoint.
    paths = [np.unique(p, axis=0) for p in paths]
    points = np.vstack(paths)
    m = g.custom(name, points, 'AC_HOME', name, [color] * len(points), {})
    entries = m.attrs['CustomModelCompressed'].split(';')
    circuits = np.concatenate([np.full(len(p), i + 1) for i, p in enumerate(paths)])
    m.attrs.update(CustomModelCompressed=';'.join(str(int(c)) + ',' + e.split(',', 1)[1]
        for c, e in zip(circuits, entries)), StringType='Single Color ' +
        {RED: 'Red', WHITE: 'White', GREEN: 'Green'}[color], HelixOutputMode='ac16', PixelSize='6')
    m.kind = 'ac'
    m.submodels = {f'CIRCUIT_{i + 1:02d}': [i + 1] for i in range(len(paths))}
    m.details.update(circuit_count=len(paths), point_circuits=circuits.tolist(), hardware_tested=False)
    return m


def ac_home(expanded=False):
    g = Garden(title=TITLES[int(expanded)], palette=(RED, WHITE, GREEN))
    line = lambda a, b: np.linspace(a, b, 25)
    roof = [(-55, 22, -20), (-30, 42, -20), (0, 22, -20), (35, 48, -20), (60, 22, -20)]
    ac_prop(g, 'AC_ROOFLINE', [line(roof[i // 3], roof[i // 3 + 1])[j * 8:(j + 1) * 8]
        for i, j in ((i, i % 3) for i in range(12))], WHITE)
    ac_prop(g, 'AC_MEGATREE', [line((35 + 16 * np.cos(a), 0, 10 + 16 * np.sin(a)),
        (35, 38, 10)) for a in np.linspace(0, 2 * np.pi, 16, endpoint=False)], GREEN)
    arches = []
    for k in range(4):
        t = np.linspace(0, np.pi, 100)
        p = np.c_[-48 + 24 * k + 10 * np.cos(t), 10 * np.sin(t), np.full(len(t), 35)]
        arches.extend(np.array_split(p, 4))
    ac_prop(g, 'AC_ARCHES', arches, RED)
    canes = []
    for k in range(8):
        x = -60 + k * 17
        t = np.linspace(np.pi, 0, 25)
        canes.append(np.vstack([line((x, 0, 42), (x, 11, 42)),
            np.c_[x + 2 + 2 * np.cos(t), 11 + 2 * np.sin(t), np.full(len(t), 42)]]))
    ac_prop(g, 'AC_CANDYCANES', canes, WHITE)
    ac_prop(g, 'AC_SPINNERS', [line((-34, 18, 0), (-34 + 12 * np.sin(a), 18 + 12 * np.cos(a), 0))
        for a in np.linspace(0, 2 * np.pi, 12, endpoint=False)], GREEN)
    if expanded:
        for bank, color in enumerate((RED, GREEN, WHITE, RED)):
            ac_prop(g, 'AC_WINDOW_BANK_' + str(bank + 1), [line(
                (-55 + bank * 28 + i * .65, 1, -21), (-55 + bank * 28 + i * .65, 16, -21))
                for i in range(16)], color)
    allocate(g)
    return g


def build_progressive(level):
    if not 0 <= level < 6:
        raise ValueError('Use a complexity level in 0..5')
    if level < 2:
        g = ac_home(level == 1)
    elif level == 2:
        g = ac_home(True)
        g.tree('PIXEL_HERO_TREE', -25, 12, 36, 9, 0, 16, 40, 'PIXEL_HOME')
        for i in range(6):
            g.star(f'PIXEL_STAR_{i}', -55 + i * 22, 47 + i % 2 * 6, -20, 6, 'PIXEL_HOME')
    elif level == 3:
        g = build_ultimate_garden()
        g.models = [m for m in g.models if not m.details.get('double_helix') and m.kind == 'pixel']
        s = Structures(g)
        for i in range(6):
            house(s, -135 + i * 54, -120, 43, 23, i % 3)
    else:
        g = build_world(0)
        g.models = [m for m in g.models if not m.details.get('review_role')]
        if level == 5:
            s = Structures(g)
            s.serial = 1000
            for row in range(3):
                for i in range(6):
                    house(s, -145 + i * 58, -140 - row * 40, 40, 20 + row * 4, (row + i) % 3)
            # Retain the complete stock-model gallery from the original show.
            extra = build_ultimate_garden()
            for m in extra.models:
                if m.kind != 'pixel':
                    model = deepcopy(m)
                    model.name = 'CATALOG_' + model.name
                    g.models.append(model)
    g.title = 'Helix ' + TITLES[level]
    g.slug = f'Layout_{level + 1:02d}'
    allocate(g)
    return g
