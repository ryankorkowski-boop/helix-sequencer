"""Procedural solid geometry and physical RGB attachment points, in metres."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from math import cos, pi, sin

import numpy as np


MATERIALS = {
    # sRGB base, metallic, roughness
    "lawn": ("263d31", 0, .95), "hedge": ("355b3f", 0, .87),
    "pine": ("345649", 0, .86), "fern": ("548044", 0, .78),
    "bark": ("69504e", 0, .85), "sand": ("747080", 0, .88),
    "road": ("303343", 0, .83), "paving": ("797b84", 0, .79),
    "marble": ("e1ded1", 0, .37), "trim": ("fff5e4", 0, .39),
    "slate": ("37415c", .15, .7), "gold": ("cb965a", .7, .32),
    "water": ("347997", .78, .14), "glass": ("47718c", .65, .22),
    "warm_glass": ("cf9c68", .42, .27), "stone": ("665971", .05, .71),
    "dark_stone": ("4d4757", .05, .82), "copper": ("657f80", .5, .42),
    "ruby": ("a93272", .3, .35), "violet": ("674aa0", .3, .35),
    "mint": ("50a98e", .2, .41), "peach": ("e28a75", .15, .5),
    "coral": ("dd4d86", .15, .42), "cream": ("f3c89c", .05, .57),
    "chrome": ("b2bfd0", .85, .26), "graphite": ("23263b", .45, .48),
    "rubber": ("24252b", 0, .89), "screen": ("293f59", .35, .42),
    "ceramic": ("deddf1", .16, .39), "black": ("1d2430", .1, .56),
}


@dataclass(frozen=True)
class Prop:
    name: str
    district: str
    family: str
    points: np.ndarray
    radius: float
    row_width: int = 0


def bezier(control, samples):
    p0, p1, p2, p3 = map(np.asarray, control)
    t = np.linspace(0, 1, samples)[:, None]
    return (1-t)**3*p0 + 3*(1-t)**2*t*p1 + 3*(1-t)*t*t*p2 + t**3*p3


def ring(x, y, z, rx, rz=None, *, n=24, vertical=False, closed=False):
    rz = rx if rz is None else rz
    angles = np.linspace(0, 2*pi, n + int(closed), endpoint=closed)
    return np.array([(x+rx*cos(a), y if vertical else y+rz*sin(a),
                      z+rz*sin(a) if vertical else z) for a in angles])


class Scene:
    def __init__(self):
        self.pieces = defaultdict(list)
        self.props = []
        self._names = set()

    def mesh(self, district, material, points, faces):
        triangles = [(face[0], face[i], face[i+1]) for face in faces for i in range(1, len(face)-1)]
        self.pieces[district, material].append((np.asarray(points), np.asarray(triangles)))

    def box(self, district, material, center, size, angle=0):
        x, y, z = np.asarray(size) / 2
        points = np.array([(-x,-y,-z), (x,-y,-z), (x,y,-z), (-x,y,-z),
                           (-x,-y,z), (x,-y,z), (x,y,z), (-x,y,z)])
        rotation = np.array([[cos(angle), sin(angle), 0], [-sin(angle), cos(angle), 0], [0, 0, 1]])
        self.mesh(district, material, points @ rotation + center,
                  [(3,2,1,0), (4,5,6,7), (0,1,5,4), (1,2,6,5), (2,3,7,6), (3,0,4,7)])

    def shell(self, district, material, rings, *, caps=True):
        rings = np.asarray(rings)
        levels, sides, _ = rings.shape
        faces = [(i*sides + j, i*sides + (j+1)%sides, (i+1)*sides + (j+1)%sides, (i+1)*sides + j)
                 for i in range(levels-1) for j in range(sides)]
        if caps:
            faces += [tuple(reversed(range(sides))), tuple(range((levels-1)*sides, levels*sides))]
        self.mesh(district, material, rings.reshape(-1, 3), faces)

    def profile(self, district, material, xy, levels, *, sides=24):
        x, y = xy
        self.shell(district, material, [ring(x, y, z, radius, n=sides) for z, radius in levels])

    def tube(self, district, material, points, radius, *, sides=6):
        points = np.asarray(points)
        # A sweep with local frame transport keeps continuous rails, stems and arches.
        tangent = np.gradient(points, axis=0)
        tangent /= np.maximum(1e-8, np.linalg.norm(tangent, axis=1, keepdims=True))
        normal = np.empty_like(tangent)
        axis = np.eye(3)[np.abs(tangent[0]).argmin()]
        for i, direction in enumerate(tangent):
            axis = axis - direction * np.dot(axis, direction)
            axis /= max(1e-8, np.linalg.norm(axis))
            normal[i] = axis
        binormal = np.cross(tangent, normal)
        angles = np.arange(sides) * (2*pi/sides)
        self.shell(district, material, points[:, None, :] + radius *
                   (normal[:, None, :] * np.cos(angles)[None, :, None] +
                    binormal[:, None, :] * np.sin(angles)[None, :, None]))

    def roof(self, district, material, center, size, ridge):
        x, y, z = center
        w, d, height = size
        self.shell(district, material, [
            [(x-w/2,y-d/2,z), (x+w/2,y-d/2,z), (x+w/2,y+d/2,z), (x-w/2,y+d/2,z)],
            [(x-ridge/2,y-.035,z+height), (x+ridge/2,y-.035,z+height),
             (x+ridge/2,y+.035,z+height), (x-ridge/2,y+.035,z+height)],
        ])

    def light(self, district, family, label, points, radius=.145, *, row_width=0):
        name = "_".join((district, family, label))
        points = np.asarray(points, dtype=float).reshape(-1, 3)
        if name in self._names or len(points) < 2 or not np.isfinite(points).all():
            raise ValueError(f"Invalid light installation {name}")
        if np.any(np.linalg.norm(np.diff(points, axis=0), axis=1) < 1e-6):
            raise ValueError(f"Adjacent RGB nodes coincide in {name}")
        self._names.add(name)
        self.props.append(Prop(name, district, family, points, radius, row_width))

    def strip(self, district, family, label, start, end, n, radius=.145):
        self.light(district, family, label, np.linspace(start, end, n), radius)

    def surface(self, district, family, label, center, width, height, columns, rows, *, curve=0, angle=0):
        x, y, z = center
        points = []
        for j, dy in enumerate(np.linspace(-height/2, height/2, rows)):
            xs = np.linspace(-width/2, width/2, columns)
            if j % 2:
                xs = xs[::-1]
            points.extend((x+u*cos(angle), y+u*sin(angle)+curve*(2*u/width)**2, z+dy) for u in xs)
        self.light(district, family, label, points, min(.18, width/columns*.31), row_width=columns)
