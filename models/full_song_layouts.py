"""Ordered native layouts for the full-song 4 by 4 comparison."""

import numpy as np

from models.approval_layouts import ac_circuits, arch, build_layout, cane, faces
from models.approval_layouts import house, structures, tree
from models.ultimate_showcase import Garden
from tools.build_current_comparison import layout as current_layout, native_band


NAMES = (
    'LOR 16 AC', 'LOR 64 AC', 'Original 256 AC', 'AC arches and canes',
    'Dual mega trees', 'RGB outline', 'RGB arches and spirals', 'Singing faces',
    'Singing pixel tree', 'RGB matrix', 'Canonical snowman band', 'Advanced RGB house',
    '3D pixel grid', 'Double helix', 'Neighborhood', 'Ultimate technical RGB',
)


def build(number, plan, *, duration):
    if number in (1, 2):
        return build_layout(number), None
    if number == 3:
        return current_layout(1, plan, duration=duration)
    if number in (14, 15, 16):
        return current_layout({14: 8, 15: 10, 16: 12}[number], plan, duration=duration)

    garden = Garden(title=NAMES[number - 1], slug=f'full_song_{number:02}')
    if number == 4:
        for x in (-27, -9, 9, 27):
            arch(garden, x, 0, width=16, height=11)
        for x in (-43, 43):
            cane(garden, x, -2, h=16)
        ac_circuits(garden, 4)
    elif number == 5:
        for x in (-19, 19):
            tree(garden, x, 0, h=34, r=12)
            structures(garden).starburst((x, 37, 0), 4)
    elif number == 6:
        house(garden)
        for model in garden.models:
            model.details['musical_role'] = 'guitarist' if 'WINDOW' in model.name else 'bassist'
    elif number == 7:
        for x in (-28, -10, 10, 28):
            arch(garden, x, 10, width=16)
        for x in (-20, 0, 20):
            structures(garden).tree(x, -10, h=26, r=7, color=(x // 20) % 3)
            garden.models[-1].details['musical_role'] = 'guitarist'
    elif number in (8, 9):
        faces(garden)
        if number == 9:
            garden.models.pop()
            from models.showcase_flavors import _move
            _move(garden.models[0], (-37, 0, 22), (0, 0, -8), 2.6)
        for x in (-23, 23):
            arch(garden, x, 30, width=18, height=6)
        if number == 8:
            for x in (-47, 47):
                tree(garden, x, 8, h=18, r=6)
    elif number == 10:
        structures(garden).mesh('RGB_MATRIX', (0, 0, 0), 55, 27, 'MATRICES')
        for x in (-35, 35):
            structures(garden).ring('MATRIX_ACCENT', (x, 14, 0), 6, 6, 'ACCENTS', plane='xy')
    elif number == 11:
        return garden, native_band(garden, plan, rock=False, duration=duration)
    elif number == 12:
        return current_layout(9, plan, duration=duration)
    elif number == 13:
        for depth in range(6):
            for row in range(6):
                points = np.column_stack((np.linspace(-20, 20, 8), np.full(8, row * 5),
                                          np.full(8, (depth - 2.5) * 7)))
                model = garden.custom(f'GRID_Z{depth}_Y{row}', points, 'MATRICES', '3D grid row',
                                      [garden.palette[depth % 3]] * len(points),
                                      {'ROW_00': list(range(1, 9))})
                model.details.update(propagation_delay_ms=depth * 20, spatial_phase=row / 6)
    else:
        raise ValueError(f'Unknown full-song layout {number}')

    for model in garden.models:
        model.attrs.setdefault('PixelSize', '17')
        model.details.setdefault('source_display_floor', .5)
    return garden, None
