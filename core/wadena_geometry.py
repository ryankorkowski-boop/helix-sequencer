"""Parametric physical geometry for the Wadena-style Helix preview.

This module deliberately separates physical geometry from electrical truth.
Traditional display props are modeled as shared geometry with independent
R/G/W AC strands.  The geometry can therefore be rendered as a blended visual
while the sequencer continues to address the three electrical channels
independently.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import cos, pi, sin


@dataclass(frozen=True)
class Point3:
    x: float
    y: float
    z: float


@dataclass(frozen=True)
class StrandPath:
    color: str
    points: tuple[Point3, ...]


@dataclass(frozen=True)
class SpiralTree:
    """A physical tree with an upward clockwise spiral and a broad apex descent."""

    center: Point3
    height: float
    base_radius: float
    up_turns: float = 3.0
    down_turns: float = 1.75
    apex_radius: float | None = None
    samples_per_turn: int = 36
    colors: tuple[str, ...] = ("red", "green", "white")
    clockwise: bool = True

    def _theta(self, fraction: float, turns: float) -> float:
        direction = -1.0 if self.clockwise else 1.0
        return direction * 2.0 * pi * turns * fraction

    def paths(self) -> tuple[StrandPath, ...]:
        if self.height <= 0 or self.base_radius < 0:
            raise ValueError("height must be positive and base_radius non-negative")
        if self.up_turns < 0 or self.down_turns < 0:
            raise ValueError("spiral turns must be non-negative")
        n_up = max(2, int(round(self.up_turns * self.samples_per_turn)))
        n_down = max(2, int(round(self.down_turns * self.samples_per_turn)))
        apex = self.apex_radius if self.apex_radius is not None else self.base_radius * 1.65

        # One canonical physical path. Color strands share the same geometry.
        points: list[Point3] = []
        for i in range(n_up + 1):
            f = i / n_up
            theta = self._theta(f, self.up_turns)
            # The radius narrows toward the top, giving the tree a conical ascent.
            r = self.base_radius * (1.0 - 0.82 * f)
            points.append(
                Point3(
                    self.center.x + r * cos(theta),
                    self.center.y + self.height * f,
                    self.center.z + r * sin(theta),
                )
            )

        # At the apex, transition into a much broader downward spiral.
        for i in range(1, n_down + 1):
            f = i / n_down
            theta = self._theta(f, self.down_turns) + self._theta(1.0, self.up_turns)
            r = apex * f
            y = self.center.y + self.height * (1.0 - f)
            points.append(
                Point3(
                    self.center.x + r * cos(theta),
                    y,
                    self.center.z + r * sin(theta),
                )
            )

        canonical = tuple(points)
        return tuple(StrandPath(color=c, points=canonical) for c in self.colors)


@dataclass(frozen=True)
class ConeTree:
    """Small yard tree represented as a tapered cone of light strands."""

    center: Point3
    height: float
    base_radius: float
    samples: int = 24
    colors: tuple[str, ...] = ("red", "green", "white")

    def paths(self) -> tuple[StrandPath, ...]:
        if self.height <= 0 or self.base_radius < 0:
            raise ValueError("height must be positive and base_radius non-negative")
        n = max(2, int(self.samples))
        points = tuple(
            Point3(
                self.center.x,
                self.center.y + self.height * (i / (n - 1)),
                self.center.z,
            )
            for i in range(n)
        )
        return tuple(StrandPath(color=c, points=points) for c in self.colors)


@dataclass(frozen=True)
class MegaTree:
    """Conical multi-string mega tree with height-addressable rings."""

    center: Point3
    height: float
    base_radius: float
    string_count: int = 24

    def string_points(self, samples: int = 32) -> tuple[tuple[Point3, ...], ...]:
        if self.height <= 0 or self.base_radius < 0:
            raise ValueError("height must be positive and base_radius non-negative")
        count = max(3, int(self.string_count))
        n = max(2, int(samples))
        strings: list[tuple[Point3, ...]] = []
        for s in range(count):
            theta = (2.0 * pi * s) / count
            points = tuple(
                Point3(
                    self.center.x + self.base_radius * (1.0 - f) * cos(theta),
                    self.center.y + self.height * f,
                    self.center.z + self.base_radius * (1.0 - f) * sin(theta),
                )
                for f in (i / (n - 1) for i in range(n))
            )
            strings.append(points)
        return tuple(strings)

    def ring(self, height_fraction: float, samples: int | None = None) -> tuple[Point3, ...]:
        """Return a horizontal circular ring intersecting the conical tree."""
        f = min(1.0, max(0.0, float(height_fraction)))
        n = max(8, int(samples or self.string_count * 2))
        radius = self.base_radius * (1.0 - f)
        return tuple(
            Point3(
                self.center.x + radius * cos(2.0 * pi * i / n),
                self.center.y + self.height * f,
                self.center.z + radius * sin(2.0 * pi * i / n),
            )
            for i in range(n)
        )
