from __future__ import annotations

from core import model_parser as xmp


def readability_score(model: xmp.Model) -> float:
    if model.total_pixels <= 0:
        return 0.2
    if model.total_pixels < 25:
        return 0.45
    if model.total_pixels < 100:
        return 0.7
    return 0.88
