"""Shared front-view contract for flat and dimensional AC drummer builds.

The depth is construction-only: both variants reuse the same screen positions,
circuit labels and musical trigger mapping. This is not a 3D render verifier.
"""
from __future__ import annotations

from core.ctb16pc_drummer_chorus import ctb16pc_drummer_chorus_patch

# Normalized viewer coordinates, origin at upper-left, same in both builds.
FRONT_POSITIONS = {
    "CYMBAL_LEFT": (.10, .23),
    "TOM_FLOOR": (.22, .69),
    "TOM_MID": (.35, .48),
    "SNARE_LEFT": (.47, .66),
    "SNARE_RIGHT": (.53, .66),
    "KICK": (.50, .86),
    "TOM_HIGH": (.64, .48),
    "HI_HAT": (.78, .55),
    "CYMBAL_RIGHT": (.90, .23),
    "BASE_DIM": (.50, .42),
}
# Mouth geometry is anchored to the same drummer head in both variants.
HEAD_CENTER = (.50, .14)


def drummer_build_variant(kind: str) -> dict:
    if kind not in ("2d", "3d"):
        raise ValueError("kind must be 2d or 3d")
    depth = 0.0 if kind == "2d" else 0.25
    patch = ctb16pc_drummer_chorus_patch()
    return {
        "kind": kind,
        "projection": "front_orthographic",
        "unit_id": patch[0]["unit_id"],
        "channels": patch,
        "front_positions": dict(FRONT_POSITIONS),
        "head_center": HEAD_CENTER,
        "depth_fraction": depth,
        "construction": "flat nonconductive panel" if kind == "2d"
                        else "bucket drum shells and rigid insulated supports",
    }


def validate_front_parity() -> bool:
    flat = drummer_build_variant("2d")
    dimensional = drummer_build_variant("3d")
    return (flat["front_positions"] == dimensional["front_positions"]
            and flat["head_center"] == dimensional["head_center"]
            and flat["channels"] == dimensional["channels"]
            and flat["projection"] == dimensional["projection"])
