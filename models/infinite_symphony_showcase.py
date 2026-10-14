"""A nine-district 3D Helix megagarden with native xLights coverage.

Geometry is authored from the existing verified native-model garden. Every
district is independently translated in both the pixel coordinates and the
xLights WorldPos attributes. Houses and note-rung metadata are new additions.
"""
from __future__ import annotations

import copy
import json
from collections import Counter
from pathlib import Path

import numpy as np

from models.ultimate_showcase import build_ultimate_garden, garden_manifest, CYAN, PINK, GOLD, MINT, VIOLET

PALETTES = [
    ("Prismatic Cathedral", (CYAN, VIOLET, GOLD)),
    ("Aurora Grove", (MINT, CYAN, VIOLET)),
    ("Ember Carnival", (GOLD, PINK, "#FF643C")),
    ("Cymatic Observatory", (VIOLET, CYAN, "#FFFFFF")),
    ("Helix Crown", (CYAN, PINK, GOLD)),
    ("Quasicrystal Theatre", (MINT, GOLD, "#FFAAFF")),
    ("Circuit Gardens", ("#43E6FF", "#FFCE54", VIOLET)),
    ("Glacial Palace", ("#D0F7FF", CYAN, "#718DFF")),
    ("Golden Lanterns", (GOLD, MINT, PINK)),
]


def build_megagarden():
    base = build_ultimate_garden()
    span = np.ptp(np.concatenate([m.points for m in base.models]), axis=0)
    # Three by three independently themed gardens: ~9x the original XZ area.
    dx, dz = float(span[0]), float(span[2])
    garden = copy.copy(base)
    garden.models = []
    garden.title = "Helix Infinite Symphony — Nine Worlds"
    garden.slug = "Helix_Infinite_Symphony"
    garden.description = "Nine interwoven xLights sculpture worlds, themed houses, and a keyboard-controlled central DNA tower."
    for district, (title, palette) in enumerate(PALETTES):
        col, row = district % 3 - 1, district // 3 - 1
        offset = np.array([col * dx, 0.0, row * dz])
        for original in base.models:
            m = copy.deepcopy(original)
            m.name = f"HX_D{district + 1:02d}_{original.name}"
            m.zone = f"D{district + 1:02d}_{original.zone}"
            m.design = f"{title}: {original.design}"
            m.points = m.points + offset
            for axis, delta in zip("XYZ", offset):
                key = "WorldPos" + axis
                if key in m.attrs:
                    m.attrs[key] = f"{float(m.attrs[key]) + delta:.6f}"
            # The XML serializer uses attrs for custom nodes and native models.
            # Colors are recolored in the district's coordinated palette.
            remap = {CYAN: palette[0], PINK: palette[1], GOLD: palette[2],
                     MINT: palette[0], VIOLET: palette[1]}
            m.colors = [remap.get(c, c) for c in m.colors]
            garden.models.append(m)

        hx, hz = float(offset[0]), float(offset[2])
        # Three-dimensional house wire outlines: foundations, roof ridges,
        # eaves, door frames and window frames use real native Poly Line models.
        for house_index in range(2):
            x = hx + (-0.31 if house_index == 0 else 0.32) * dx
            z = hz + (0.26 if house_index == 0 else -0.26) * dz
            w, depth, height = 18., 13., 13.
            p = palette[house_index % 3]
            corners = [(x-w/2, 0, z-depth/2), (x+w/2, 0, z-depth/2),
                       (x+w/2, 0, z+depth/2), (x-w/2, 0, z+depth/2)]
            for side in range(4):
                a, b = corners[side], corners[(side+1)%4]
                garden.poly(f"HX_HOUSE_{district+1:02d}_{house_index+1}_WALL_{side}",
                            [a, b, (b[0],height,b[2]), (a[0],height,a[2]), a],
                            80, f"D{district+1:02d}_HOUSES", title, p)
            garden.poly(f"HX_HOUSE_{district+1:02d}_{house_index+1}_ROOF",
                        [(x-w/2,height,z-depth/2),(x,height+9,z-depth/2),
                         (x+w/2,height,z-depth/2),(x+w/2,height,z+depth/2),
                         (x,height+9,z+depth/2),(x-w/2,height,z+depth/2)],
                        90, f"D{district+1:02d}_HOUSES", title, palette[2])
            garden.poly(f"HX_HOUSE_{district+1:02d}_{house_index+1}_RIDGE",
                        [(x,height+9,z-depth/2),(x,height+9,z+depth/2)],
                        28, f"D{district+1:02d}_HOUSES", title, palette[0])

    # A single towering 3D DNA hero, distinct from district helices.
    center_height = max(300., float(span[1]) * 3.5)
    garden.dna("HX_CENTER_KEYBOARD_HELIX", 0, 0, center_height, 24, 11, 1056,
               "CENTER_KEYBOARD_HELIX")
    hero = garden.models[-1]
    # Individually addressable note-rung groups, MIDI A0..C8, ordered low to high.
    rung_ids = hero.submodels["RUNGS"]
    # Each physical rung occupies a narrow horizontal height band. Group its
    # nodes together so one MIDI event lights an entire rung, not a fragment.
    rung_heights = np.asarray([hero.points[node_id - 1, 1] for node_id in rung_ids])
    unique_heights = np.unique(np.round(rung_heights, 3))
    if len(unique_heights) < 88:
        raise ValueError(f"Keyboard helix has only {len(unique_heights)} distinct rung heights; 88 required")
    assigned_heights = set()
    for midi in range(21, 109):
        target_height = unique_heights[round((midi - 21) * (len(unique_heights) - 1) / 87)]
        if float(target_height) in assigned_heights:
            raise ValueError(f"Duplicate physical rung assigned to MIDI note {midi}")
        assigned_heights.add(float(target_height))
        ids = [node_id for node_id, height in zip(rung_ids, rung_heights)
               if abs(height - target_height) < 0.005]
        if ids:
            hero.submodels[f"KEY_MIDI_{midi:03d}"] = ids
    if len([name for name in hero.submodels if name.startswith("KEY_MIDI_")]) != 88:
        raise ValueError("Keyboard helix does not contain 88 nonempty note submodels")
    hero.details["keyboard_rung_mapping"] = {
        str(midi): f"KEY_MIDI_{midi:03d}" for midi in range(21, 109)
        if f"KEY_MIDI_{midi:03d}" in hero.submodels
    }
    hero.details["note_mapping_claim"] = "Addressable note submodels; musical events must be routed by the sequencer."
    # Recalculate channels after all cloning and newly authored models.
    cursor = 1
    for model in garden.models:
        model.start = cursor
        cursor += model.channels
    return garden


def mega_manifest(garden):
    base = build_ultimate_garden()
    def footprint(g):
        all_points = np.concatenate([m.points[:, [0, 2]] for m in g.models])
        return np.ptp(all_points, axis=0)
    original, expanded = footprint(base), footprint(garden)
    result = garden_manifest(garden)
    result["footprint_ratio_xz"] = round(float(np.prod(expanded) / np.prod(original)), 3)
    result["footprint_method"] = "axis-aligned XZ bounding-box area relative to build_ultimate_garden; full node extents included"
    result["base_footprint_xz"] = original.tolist()
    result["expanded_footprint_xz"] = expanded.tolist()
    result["district_spacing_fraction"] = 1.0
    result["districts"] = [{"name": name, "palette": list(p)} for name, p in PALETTES]
    result["house_count"] = 18
    result["centerpiece"] = "HX_CENTER_KEYBOARD_HELIX"
    result["native_counts"] = dict(Counter(m.display for m in garden.models))
    result["band_stages"] = [
        {"name": "Main Rock Stage", "zone": "D05", "performance_assets": "requires band stage integration"},
        {"name": "Mirror Band Stage", "zone": "D02", "performance_assets": "requires band stage integration"},
    ]
    return result
