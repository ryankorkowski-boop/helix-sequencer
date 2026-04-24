from __future__ import annotations


def curve_envelope(name: str) -> list[tuple[float, float]]:
    curves = {
        "kick": [(0.0, 0.0), (0.05, 1.0), (0.22, 0.18)],
        "snare": [(0.0, 0.0), (0.02, 1.0), (0.15, 0.0)],
        "vocal": [(0.0, 0.0), (0.15, 0.68), (0.8, 0.6), (1.0, 0.0)],
        "riser": [(0.0, 0.1), (0.5, 0.42), (1.0, 1.0)],
        "drop": [(0.0, 0.0), (0.1, 0.0), (0.12, 1.0), (0.4, 0.36)],
    }
    return curves.get(name, [(0.0, 0.0), (1.0, 1.0)])
