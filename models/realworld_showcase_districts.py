"""Real-world, independently addressable native xLights finale installations.

These are *physical fixtures*, not overlay particles or post-production effects.
The 16-panel review uses a bounded profile; the 10,240-model Infinity profile
is deliberately opt-in until short native performance and readability gates pass.
"""
from __future__ import annotations

import math
import os


COLORS = ("#67D9FF", "#FFCE79", "#FF6FA9", "#74E3AF", "#B9A1FF")


def _fixture(garden, name, center, *, style, role, phase, district, index):
    """One visible native fixture with its own geometry, address and source lane."""
    x, y, z = center
    color = COLORS[(district + index) % len(COLORS)]
    if style == "gable":
        vertices = [(x - 4, y, z), (x, y + 5, z - 1),
                    (x + 4, y, z), (x + 4, y, z + 3)]
    elif style == "window":
        vertices = [(x - 2, y, z), (x - 2, y + 3, z),
                    (x + 2, y + 3, z), (x + 2, y, z),
                    (x - 2, y, z)]
    elif style == "fence":
        vertices = [(x - 4, y, z), (x - 4, y + 2, z),
                    (x, y + 2, z), (x + 4, y + 2, z), (x + 4, y, z)]
    elif style == "tree":
        vertices = [(x, y, z), (x - 2.8, y + 2.5, z + 1),
                    (x + 2.8, y + 2.5, z + 1),
                    (x, y + 8, z - 1.2), (x, y, z)]
    elif style == "arch":
        vertices = [(x - 4, y, z), (x - 3, y + 4, z),
                    (x, y + 6, z + 1), (x + 3, y + 4, z),
                    (x + 4, y, z)]
    elif style == "spire":
        vertices = [(x - 2, y, z - 2), (x, y + 11, z),
                    (x + 2, y, z + 2), (x, y + 3, z)]
    elif style == "orbit":
        vertices = [(x + 4 * math.cos(t), y + 4 * math.sin(t),
                     z + 2 * math.sin(t)) for t in
                    (0, math.pi / 3, 2 * math.pi / 3, math.pi,
                     4 * math.pi / 3, 5 * math.pi / 3, 2 * math.pi)]
    else:
        raise ValueError(f"Unknown physical fixture type: {style}")
    model = garden.poly(name, vertices, 16,
                        f"REALWORLD_{district:02}", f"Physical {style} lighting fixture",
                        color)
    model.details.update(
        musical_role=role,
        spatial_axis=("y" if style in ("tree", "spire") else
                      "spiral" if style == "orbit" else "x"),
        spatial_phase=phase % 1,
        spatial_direction=-1 if district % 2 else 1,
        propagation_delay_ms=(index % 8) * 11,
        source_display_floor=.20,
        advanced_spatial_routing=True,
        realworld_customer_fixture=True,
        physically_independent_address=True,
        customer_site_id=district,
        customer_fixture_style=style,
    )
    if role == "drummer":
        model.details["percussion_component"] = (
            "kick", "snare", "hihat", "cymbal")[index % 4]
    model.attrs.update(PixelSize="7", BlackTransparency="100")
    return model


def install_customer_sites(garden, panel, *, extreme=None):
    """Expand source-routed, recognizably buildable customer environments.

    13: 20 individual houses spanning a holiday neighborhood.
    14: 12 festival courts with monumental arches, trees, rings and spires.
    15: 40 decorated multi-level downtown building blocks and skywalks.
    16: 16 independently animated 3-D festival/stadium districts.

    Standard 16-panel previews remain bounded. Set HELIX_SHOWCASE_EXTREME=1
    for the complete 10,240-*model* Infinity proof, not merely 10,240 pixels.
    """
    if panel not in (13, 14, 15, 16):
        raise ValueError("Customer finale expansions apply only to panels 13-16")
    if extreme is None:
        extreme = os.environ.get("HELIX_SHOWCASE_EXTREME", "0") == "1"
    first = len(garden.models)
    if panel == 13:
        # Each lot has real separate gables, windows, porch arches and trees.
        sites, per_site, width = 20, 14, 5
        theme = ("gable", "window", "fence", "arch", "tree")
        roles = ("guitarist", "keyboardist", "bassist", "drummer")
    elif panel == 14:
        sites, per_site, width = 12, 64, 4
        theme = ("arch", "spire", "tree", "orbit", "window")
        roles = ("keyboardist", "guitarist", "drummer", "bassist")
    elif panel == 15:
        sites, per_site, width = 40, 64, 8
        theme = ("gable", "window", "spire", "arch", "orbit")
        roles = ("bassist", "keyboardist", "guitarist", "drummer")
    else:
        sites, per_site, width = 16, (640 if extreme else 192), 4
        theme = ("spire", "orbit", "arch", "tree", "window")
        roles = ("keyboardist", "guitarist", "bassist", "drummer")
    # Grid positions correspond to lots, festival courts, downtown blocks or
    # stadium/expo quadrants, rather than particles in empty space.
    rows = math.ceil(sites / width)
    for district in range(sites):
        col, row = district % width, district // width
        cx = (col - (width - 1) / 2) * (63 if panel == 13 else 70)
        cz = (row - (rows - 1) / 2) * (55 if panel == 13 else 73)
        cols = math.ceil(math.sqrt(per_site))
        nrows = math.ceil(per_site / cols)
        pitch_x = (44 if panel == 13 else 53) / max(1, cols - 1)
        pitch_z = (38 if panel == 13 else 59) / max(1, nrows - 1)
        for index in range(per_site):
            lane, rank = index % cols, index // cols
            x = cx + (lane - (cols - 1) / 2) * pitch_x
            z = cz + (rank - (nrows - 1) / 2) * pitch_z
            # Facade and foreground depths alternate, forming readable
            # architectural layers without adding any unmeasured audio cues.
            y = 4 + (index % (3 if panel <= 14 else 5)) * (4 if panel < 16 else 7)
            style = theme[(index + district) % len(theme)]
            role = roles[(index // cols + district) % len(roles)]
            _fixture(garden, f"REALWORLD_P{panel}_SITE{district:02}_FIX{index:03}",
                     (x, y, z), style=style, role=role,
                     phase=(district / sites + index / (per_site * sites)),
                     district=district, index=index)
    added = garden.models[first:]
    expected = sites * per_site
    if len(added) != expected or len({m.name for m in added}) != expected:
        raise AssertionError("Real-world native fixture inventory is incomplete")
    return added
