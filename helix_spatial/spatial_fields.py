from __future__ import annotations

from dataclasses import asdict, dataclass
from math import sqrt


@dataclass(frozen=True)
class PulseField:
    center: tuple[float, float, float]
    radius: float
    intensity: float

    def sample(self, point: tuple[float, float, float]) -> float:
        distance = sqrt(sum((a - b) ** 2 for a, b in zip(self.center, point)))
        if distance > self.radius:
            return 0.0
        return max(0.0, self.intensity * (1.0 - (distance / max(0.0001, self.radius))))


@dataclass(frozen=True)
class SweepField:
    start: tuple[float, float, float]
    end: tuple[float, float, float]
    width: float

    def sample(self, point: tuple[float, float, float]) -> float:
        axis = max(0.0001, self.end[0] - self.start[0])
        offset = abs(point[0] - self.start[0])
        return max(0.0, 1.0 - (offset / axis))


@dataclass(frozen=True)
class AttractorField:
    center: tuple[float, float, float]
    strength: float

    def sample(self, point: tuple[float, float, float]) -> float:
        distance = sqrt(sum((a - b) ** 2 for a, b in zip(self.center, point)))
        return max(0.0, self.strength / max(1.0, distance * 4.0))


@dataclass(frozen=True)
class TrailField:
    path: list[tuple[float, float, float]]
    fade: float

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
