"""Ten-circuit physical AC drummer patch, compatible with 16-output AC controllers.

This generates a wiring/label manifest. It does not energize hardware or alter
the existing xLights/Light-O-Rama production output path.
"""
from __future__ import annotations

import csv
from pathlib import Path

from core.physical_band_circuits import DRUMMER


def ac_drummer_patch(start_channel: int = 1) -> list[dict[str, object]]:
    if start_channel < 1:
        raise ValueError("start_channel must be positive")
    return [
        {
            "ac_channel": start_channel + index,
            "controller_output": index + 1,
            "circuit": circuit.name,
            "lighting_elements": "; ".join(circuit.elements),
            "base_dim": circuit.dim_base,
        }
        for index, circuit in enumerate(DRUMMER)
    ]


def write_ac_drummer_patch(path: str | Path, start_channel: int = 1) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    rows = ac_drummer_patch(start_channel)
    with target.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return target
