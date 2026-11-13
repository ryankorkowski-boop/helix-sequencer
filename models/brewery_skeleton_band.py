"""Four independently addressable, 3D pixel-skeleton performers for native xLights.

These are actual xLights Custom models with separate static-bone and pose-state
node ranges. The animation uses source-timed illumination of alternative arm
poses, NOT a claim that a mechanical arm physically moves. Real-world actuators
and road-rated rigging require separate engineering and controller hardware.
"""
from __future__ import annotations

import math
import numpy as np

BAND_ROLES = ("drummer", "guitarist", "bassist", "frontman")
COSTUME = {"drummer": "#F0E8D5", "guitarist": "#D8EAFB",
           "bassist": "#DEFFCE", "frontman": "#FFD9E9"}
POSE_STATES = ("POSE_IDLE", "POSE_ATTACK", "POSE_ACCENT", "POSE_RECOVERY")


class _Bones:
    def __init__(self):
        self.points = []
        self.members = {}
        self.index = {}

    def add(self, group, xyz):
        key = tuple(round(float(v), 5) for v in xyz)
        n = self.index.get(key)
        if n is None:
            n = len(self.points) + 1
            self.index[key] = n
            self.points.append(key)
        self.members.setdefault(group, []).append(n)

    def line(self, group, a, b, count=15):
        for p in np.linspace(a, b, count):
            self.add(group, p)

    def hoop(self, group, center, rx, ry, *, plane="xy", count=42):
        a, b = {"xy": (0, 1), "xz": (0, 2), "yz": (2, 1)}[plane]
        for t in np.linspace(0, 2 * math.pi, count, endpoint=False):
            p = list(center)
            p[a] += rx * math.cos(t)
            p[b] += ry * math.sin(t)
            self.add(group, p)


def _skeletal_body(b, x, y, z):
    # Skull is three curved depth shells, not a flat jack-o-lantern face.
    for dz, rx in ((-.85, 2.9), (0, 3.2), (.9, 2.7)):
        b.hoop("SKULL", (x, y + 24.5, z + dz), rx, 3.45, count=42)
    for side in (-1, 1):
        eye_x = x + side * 1.25
        b.hoop("SKULL", (eye_x, y + 25.1, z + 1.05), .58, .7, count=16)
        b.line("SKULL", (eye_x - .6, y + 22.1, z + 1.2),
               (eye_x + .6, y + 22.1, z + 1.2), 7)
        b.line("STATIC_BONES", (x + side * 1.65, y + 20.4, z),
               (x + side * 2.55, y + 19.5, z), 14)
        b.line("STATIC_BONES", (x + side * 1.5, y + 11.0, z),
               (x + side * 3.1, y + 9.8, z), 12)
        b.line("LEGS", (x + side * 2.7, y + 9.6, z),
               (x + side * 2.6, y + 5, z + 1), 22)
        b.line("LEGS", (x + side * 2.6, y + 5, z + 1),
               (x + side * 3.5, y + .2, z + 2.5), 22)
        b.line("LEGS", (x + side * 3.5, y + .2, z + 2.5),
               (x + side * 5.1, y, z + 3), 10)
    b.line("STATIC_BONES", (x, y + 21, z), (x, y + 10, z), 38)
    b.hoop("STATIC_BONES", (x, y + 10, z), 3.35, 1.4, count=32)
    for j in range(6):
        height = y + 12.4 + j * 1.26
        radius = 4.6 - abs(j - 2.5) * .37
        for depth in (-.7, .7):
            b.hoop("RIB_CAGE", (x, height, z + depth), radius, .67,
                   plane="xz", count=24)
        b.line("RIB_CAGE", (x - radius, height, z), (x, height - .38, z + 1),
               10)
        b.line("RIB_CAGE", (x, height - .38, z + 1), (x + radius, height, z),
               10)


def _prop(b, role, x, y, z):
    if role in ("guitarist", "bassist"):
        # A readable long-neck string instrument, with independently routed
        # instrument illumination and neck/strum endpoints.
        b.hoop("INSTRUMENT", (x + 1, y + 11.3, z + 3), 4, 3.3, count=44)
        b.line("INSTRUMENT", (x + 3, y + 13, z + 3),
               (x + 12, y + 19, z + 3), 44)
        for offset in (-.65, 0, .65):
            b.line("INSTRUMENT", (x - 2, y + 11.3 + offset, z + 3.3),
                   (x + 11, y + 18.6 + offset, z + 3.3), 26)
    elif role == "drummer":
        for sx, sy, rad in ((-7, 8, 2.6), (7, 8, 2.6), (0, 5, 4.7)):
            b.hoop("INSTRUMENT", (x + sx, y + sy, z + 6), rad, rad,
                   count=44)
        for sx in (-9, 9):
            b.hoop("INSTRUMENT", (x + sx, y + 13, z + 4), 3.8, 1.3,
                   plane="xz", count=36)
    else:
        b.line("INSTRUMENT", (x + 6, y + .3, z + 4),
               (x + 6, y + 23, z + 4), 32)
        b.hoop("INSTRUMENT", (x + 6, y + 24, z + 4), 1.0, .8, count=22)


def _arm_poses(b, role, x, y, z):
    # Four grounded, bounded silhouettes; each arm consists of two segments
    # from a fixed shoulder. Pose layers occupy different depths so they are
    # distinct native xLights nodes and can be lit separately.
    for pose, layer in enumerate(POSE_STATES):
        dz = (pose - 1.5) * .23
        for side in (-1, 1):
            shoulder = np.array((x + side * 4.0, y + 19.1, z + dz))
            if role == "drummer":
                elbow = np.array((x + side * (7.2 - pose * .35),
                                  y + 14.8 + (pose in (1, 2)) * 2.1, z + 2 + dz))
                hand = np.array((x + side * (6.6 - pose * .7),
                                 y + (16 if pose == 2 else 11.6 if pose == 1 else 13.5),
                                 z + 5 + dz))
                tip = hand + np.array((side * 1.6, 2.2 if pose == 2 else -2.3, 1.3))
                b.line(layer, hand, tip, 12)
            elif role in ("guitarist", "bassist"):
                elbow = np.array((x + side * 5.5, y + 15.1, z + 2 + dz))
                fret = side < 0
                hand = np.array((x + (4.6 if fret else .9 + .75 * pose),
                                 y + (14.7 if fret else 10.5 + .85 * pose),
                                 z + 3.4 + dz))
            else:
                elbow = np.array((x + side * (5.8 + pose * .5),
                                  y + 17.5 + (2.0 if pose == 2 else 0), z + dz))
                hand = np.array((x + side * (6.4 + pose * .45),
                                 y + (17 if pose == 0 else 21 if pose == 1 else 26 if pose == 2 else 19),
                                 z + 1.7 + dz))
            b.line(layer, shoulder, elbow, 17)
            b.line(layer, elbow, hand, 20)
            b.hoop(layer, hand, .48, .48, count=10)


def add_four_skeletons(g):
    """Append four actual native 3D Custom skeletons with pose submodels."""
    out = []
    placements = (
        ("drummer", 0, 13, -23),
        ("guitarist", -29, 7, 10),
        ("bassist", 29, 7, 10),
        ("frontman", 0, 2, 30),
    )
    for role, x, y, z in placements:
        b = _Bones()
        _skeletal_body(b, x, y, z)
        _prop(b, role, x, y, z)
        _arm_poses(b, role, x, y, z)
        subs = {name: sorted(set(ids)) for name, ids in b.members.items()}
        subs["BODY"] = sorted(set().union(*(set(subs[k]) for k in ("SKULL", "STATIC_BONES", "RIB_CAGE", "LEGS"))))
        subs["ALL"] = list(range(1, len(b.points) + 1))
        model = g.custom("HX_DRASTIC_SKELETON_" + role.upper(),
                         b.points, "SKELETON_" + role.upper(),
                         role.title() + " 3D skeleton with four discrete illuminated poses",
                         [COSTUME[role]] * len(b.points), subs,
                         details={"skeleton_performer_role": role,
                                  "musical_role": "guitarist" if role == "frontman" else role,
                                  "source_pose_mode": "exclusive_native_3d_pixel_pose",
                                  "native_3d": True,
                                  "mechanical_actuation_verified": False,
                                  "vocal_source_required_for_mouth": True,
                                  "parade_layer": "SKELETON_" + role.upper()})
        model.attrs.update(PixelSize="7", Antialias="1", BlackTransparency="100")
        out.append(model)
    return out
