"""Physical XYZ installations for Helix's 16-panel owner review.

These fixtures are native xLights models, not compositor effects. All motion
is attached to existing, measured source-role cues by source_spatial_direction.
No source events, lyric events, beat clocks or white washes are generated here.
"""
from __future__ import annotations

import math
import numpy as np


def _register(model, *, role, axis, phase, direction=1, depth=0):
    model.details.update(
        musical_role=role,
        spatial_axis=axis,
        spatial_phase=phase % 1.0,
        spatial_direction=direction,
        propagation_delay_ms=min(96, max(0, depth * 16)),
        source_display_floor=.20,
        advanced_spatial_routing=True,
        spatial_showcase_native_xyz=True,
    )
    model.attrs.setdefault("BlackTransparency", "100")
    model.attrs.setdefault("PixelSize", "8")
    return model


def _voxel(garden, name, center, *, size, count=5, role="keyboardist", axis="z", phase=0):
    """A single genuinely volumetric CustomModel with separated XYZ nodes."""
    cx, cy, cz = center
    coordinates = np.linspace(-size / 2, size / 2, count)
    points = np.asarray([(cx + x, cy + y, cz + z)
                         for z in coordinates for y in coordinates for x in coordinates])
    model = garden.custom(name, points, "SPATIAL_VOXEL_FIELD", "3D source-routed pixel lattice",
                          ["#65D9FF"] * len(points), {})
    return _register(model, role=role, axis=axis, phase=phase, depth=round((cz + 120) / 25))


def _orbit(garden, name, center, *, radius, inclination, role, phase, direction=1):
    """A true 3-axis orbital ring rather than a flat face-on spinner."""
    cx, cy, cz = center
    t = np.linspace(0, 2 * math.pi, 161)
    coordinates = [(cx + radius * math.cos(v),
                    cy + radius * math.sin(v) * math.cos(inclination),
                    cz + radius * math.sin(v) * math.sin(inclination)) for v in t]
    model = garden.poly(name, coordinates, 160, "SPATIAL_ORBIT_3D",
                        "Inclined three-dimensional orbital trace", "#FF91DE")
    return _register(model, role=role, axis="spiral", phase=phase, direction=direction,
                     depth=round((cz + 100) / 24))


def _bridge(garden, name, start, end, *, role, phase, direction=1):
    p = np.linspace(np.asarray(start, dtype=float), np.asarray(end, dtype=float), 80)
    mid = len(p) // 2
    p[:, 1] += 4 * np.sin(np.linspace(0, math.pi, len(p)))
    model = garden.poly(name, p, 80, "SPATIAL_SKY_BRIDGE",
                        "3D architectural cross-property route", "#FFCE79")
    return _register(model, role=role, axis="x", phase=phase,
                     direction=direction, depth=round((start[2] + 100) / 25))


def _vortex(garden, name, center, *, radius, role, phase, direction=1):
    cx, cy, cz = center
    samples = np.linspace(0, 1, 240)
    path = [(cx + radius * (1 - .6 * t) * math.cos(direction * 8 * math.pi * t),
             cy + 65 * t, cz + radius * (1 - .6 * t) * math.sin(direction * 8 * math.pi * t))
            for t in samples]
    model = garden.poly(name, path, 240, "SPATIAL_VORTEX_3D",
                        "Ascending volumetric helix", "#8BE9CD")
    return _register(model, role=role, axis="spiral", phase=phase, direction=direction,
                     depth=round((cz + 100) / 25))


def install_spatial_gallery(garden, number):
    """Add distinct playable XYZ architecture to panels 13–16.

    Panel 13: volumetric wave field with identifiable front/back movement.
    Panel 14: pitched counterpoint along inclined 3D orbits.
    Panel 15: routed metropolis, vertical towers and cross-building bridges.
    Panel 16: multiple voxel districts, orbital paths and spatial vortices.
    The separate 10,240-prop Infinity generator is deliberately NOT replaced.
    """
    if number not in (13, 14, 15, 16):
        raise ValueError("Only the advanced four layouts accept XYZ gallery")
    first = len(garden.models)
    if number == 13:
        for row, z in enumerate((-48, -16, 16)):
            for column, x in enumerate((-90, -30, 30, 90)):
                _voxel(garden, f"SPATIAL_REDESIGN_FIELD_{row}_{column}",
                       (x, 17 + (column % 2) * 4, z), size=24, count=5,
                       role=("keyboardist", "guitarist", "bassist")[row],
                       axis=("z", "x", "y")[row], phase=(row * 4 + column) / 12)
        for lane, x in enumerate((-76, 0, 76)):
            _bridge(garden, f"SPATIAL_REDESIGN_FIELD_WAVE_{lane}",
                    (x - 25, 7, -61), (x + 25, 33, 46),
                    role=("bassist", "guitarist", "keyboardist")[lane],
                    phase=lane / 3)
    elif number == 14:
        for district, x in enumerate((-84, -28, 28, 84)):
            for ring in range(3):
                _orbit(garden, f"SPATIAL_REDESIGN_ORBIT_{district}_{ring}",
                       (x, 29 + ring * 4, -24 + (district % 2) * 38),
                       radius=12 + ring * 5, inclination=.45 + ring * .65,
                       role=("keyboardist", "guitarist", "bassist")[ring],
                       phase=(district * 3 + ring) / 12, direction=(-1) ** ring)
            _vortex(garden, f"SPATIAL_REDESIGN_ORBIT_AXIS_{district}",
                    (x, 5, -25), radius=10, role="keyboardist",
                    phase=district / 4, direction=(-1) ** district)
    elif number == 15:
        for row, z in enumerate((-78, -44, -10)):
            for column, x in enumerate((-90, -30, 30, 90)):
                height = 24 + 8 * ((row + column) % 3)
                vertices = [(x-8, 0, z-8), (x-8, height, z-8),
                            (x+8, height, z-8), (x+8, 0, z-8),
                            (x+8, 0, z+8), (x+8, height, z+8),
                            (x-8, height, z+8), (x-8, 0, z+8)]
                tower = garden.poly(f"SPATIAL_REDESIGN_CITY_TOWER_{row}_{column}",
                                    vertices, 224, "SPATIAL_METROPOLIS",
                                    "Three-axis illuminated skyline", "#77DEFF")
                _register(tower, role=("bassist", "guitarist", "keyboardist")[row],
                          axis="y", phase=(row * 4 + column) / 12, depth=row + 1)
            for col in range(3):
                _bridge(garden, f"SPATIAL_REDESIGN_CITY_BRIDGE_{row}_{col}",
                        (-90 + 60 * col, 20 + row * 3, z),
                        (-30 + 60 * col, 29 + row * 3, z),
                        role="keyboardist", phase=(row * 3 + col) / 9)
    else:
        for row, z in enumerate((-85, -49, -13, 23)):
            for column, x in enumerate((-87, -29, 29, 87)):
                _voxel(garden, f"SPATIAL_REDESIGN_INFINITY_GRID_{row}_{column}",
                       (x, 20 + 6 * (column % 2), z), size=21, count=4,
                       role=("keyboardist", "guitarist", "bassist")[row % 3],
                       axis=("x", "z", "y")[(row + column) % 3],
                       phase=(row * 4 + column) / 16)
        for layer in range(4):
            for ring in range(3):
                _orbit(garden, f"SPATIAL_REDESIGN_INFINITY_PORTAL_{layer}_{ring}",
                       (0, 32 + layer * 9, -77 + layer * 30),
                       radius=13 + ring * 8, inclination=.3 + ring * .55,
                       role=("keyboardist", "guitarist", "bassist")[ring],
                       phase=(layer * 3 + ring) / 12, direction=(-1) ** (ring + layer))
        for lane, x in enumerate((-106, -53, 53, 106)):
            _vortex(garden, f"SPATIAL_REDESIGN_INFINITY_VORTEX_{lane}",
                    (x, 3, -39 + 15 * lane), radius=12,
                    role=("guitarist", "bassist", "keyboardist")[lane % 3],
                    phase=lane / 4, direction=(-1) ** lane)
    added = garden.models[first:]
    assert len({model.name for model in added}) == len(added)
    assert all(sum(float(np.ptp(model.points[:, axis])) > 0 for axis in range(3)) >= 2
               for model in added)
    assert any(all(float(np.ptp(model.points[:, axis])) > 0 for axis in range(3))
               for model in added)
    return added
