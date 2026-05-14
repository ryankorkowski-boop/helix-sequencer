from __future__ import annotations

from dataclasses import dataclass
from typing import Any


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


@dataclass(frozen=True)
class Color:
    r: int
    g: int
    b: int

    def scaled(self, amount: float) -> "Color":
        scale = _clamp01(amount)
        return Color(
            r=max(0, min(255, int(round(self.r * scale)))),
            g=max(0, min(255, int(round(self.g * scale)))),
            b=max(0, min(255, int(round(self.b * scale)))),
        )

    def as_tuple(self) -> tuple[int, int, int]:
        return (self.r, self.g, self.b)


PALETTES: dict[str, tuple[Color, ...]] = {
    "cool": (Color(60, 180, 255), Color(0, 120, 220), Color(160, 230, 255)),
    "dream": (Color(170, 90, 255), Color(80, 220, 255), Color(255, 140, 220)),
    "energy": (Color(255, 70, 40), Color(255, 190, 35), Color(255, 255, 120)),
    "festive": (Color(255, 30, 55), Color(40, 220, 90), Color(255, 245, 210)),
    "sparkle": (Color(255, 240, 170), Color(180, 245, 255), Color(255, 255, 255)),
}


MOTIF_PALETTES: dict[str, str] = {
    "wave_sweep": "cool",
    "spiral": "dream",
    "pulse_cascade": "energy",
    "orbit": "festive",
    "sparkle_field": "sparkle",
}


class ColorEngine:
    def __init__(self) -> None:
        self.palette_name = "cool"
        self.intensity = 1.0

    def update(self, phrase: Any, intensity: float) -> None:
        motif = str(getattr(phrase, "motif", phrase) or "wave_sweep")
        self.palette_name = MOTIF_PALETTES.get(motif, "cool")
        self.intensity = _clamp01(float(intensity))

    def pick_color(self, model_name: str, energy: float) -> tuple[int, int, int]:
        palette = PALETTES.get(self.palette_name, PALETTES["cool"])
        index = stable_index(str(model_name), len(palette))
        brightness = _clamp01(0.35 + (_clamp01(float(energy)) * 0.45) + (self.intensity * 0.20))
        return palette[index].scaled(brightness).as_tuple()


def stable_index(text: str, modulo: int) -> int:
    if modulo <= 0:
        return 0
    return sum((idx + 1) * ord(char) for idx, char in enumerate(text)) % modulo
