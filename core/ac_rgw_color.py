"""Visual-color intent mapped to independent AC Red/Green/White strands.

This module never changes electrical truth. It only chooses an R/G/W intensity
combination that approximates a desired preview color.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import sqrt


@dataclass(frozen=True)
class RGWIntensity:
    red: float
    green: float
    white: float

    def clamped(self) -> "RGWIntensity":
        return RGWIntensity(*(max(0.0, min(1.0, v)) for v in (self.red, self.green, self.white)))


def _distance(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def quantize_rgb_to_rgw(red: float, green: float, blue: float, brightness: float = 1.0) -> RGWIntensity:
    """Approximate RGB visual intent with independently controlled R/G/W AC.

    The white channel is deliberately allowed to participate as a highlight;
    it is not treated as an RGB pixel. The result is deterministic and remains
    three independent scalar intensities suitable for AC single-color models.
    """
    r, g, b = (max(0.0, min(1.0, float(v))) for v in (red, green, blue))
    brightness = max(0.0, min(1.0, float(brightness)))
    white = min(r, g, b)
    # Because the physical display has no blue AC strand, preserve blue intent
    # primarily as white while retaining the red/green chromatic component.
    rg_scale = max(r, g, 1e-9)
    red_out = r / rg_scale
    green_out = g / rg_scale
    highlight = max(white, b * 0.72)
    return RGWIntensity(red_out * brightness, green_out * brightness, highlight * brightness).clamped()


def nearest_rgw_palette(rgb: tuple[int, int, int]) -> RGWIntensity:
    """Choose the nearest coarse R/G/W combination for preview-only color intent."""
    target = tuple(max(0, min(255, int(v))) / 255.0 for v in rgb)
    candidates = (
        RGWIntensity(0, 0, 0),
        RGWIntensity(1, 0, 0),
        RGWIntensity(0, 1, 0),
        RGWIntensity(0, 0, 1),
        RGWIntensity(1, 1, 0),
        RGWIntensity(1, 0, 1),
        RGWIntensity(0, 1, 1),
        RGWIntensity(1, 1, 1),
    )
    return min(candidates, key=lambda c: _distance((c.red, c.green, c.white), target))
