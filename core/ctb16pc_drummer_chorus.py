"""CTB16PC drummer-plus-chorus-singer logical 16-output layout.

This is a proposed LOR circuit plan, not a live hardware protocol driver.
Only one of the six mouth channels should be on at any moment.
"""
from __future__ import annotations

from core.physical_band_circuits import DRUMMER

MOUTH_POSES = ("AH", "EE", "OH", "MBP", "FV", "L")


def ctb16pc_drummer_chorus_patch(unit_id: str = "01") -> tuple[dict[str, object], ...]:
    if len(unit_id) != 2 or any(c not in "0123456789ABCDEFabcdef" for c in unit_id):
        raise ValueError("LOR unit_id must be two hexadecimal characters")
    rows = []
    for i, circuit in enumerate(DRUMMER, start=1):
        rows.append({"unit_id": unit_id.upper(), "circuit": i,
                     "function": circuit.name, "group": "drums",
                     "default_on": circuit.dim_base})
    for i, mouth in enumerate(MOUTH_POSES, start=11):
        rows.append({"unit_id": unit_id.upper(), "circuit": i,
                     "function": f"MOUTH_{mouth}", "group": "backing_vocal",
                     "default_on": False})
    return tuple(rows)


def backing_vocal_mouth_state(*, chorus: bool, vocal_layers: int,
                             detected_phoneme: str | None) -> str | None:
    """Only sing on confirmed layered/group vocal passages.

    This intentionally does not invent backing-vocal detection: callers must
    supply chorus and vocal_layers from a separate validated analysis stage.
    """
    if not chorus and vocal_layers <= 2:
        return None
    if detected_phoneme is None or detected_phoneme.upper() == "REST":
        return None
    pose = detected_phoneme.upper()
    return pose if pose in MOUTH_POSES else None


def active_mouth_circuit(**kwargs) -> int | None:
    pose = backing_vocal_mouth_state(**kwargs)
    return 11 + MOUTH_POSES.index(pose) if pose is not None else None
