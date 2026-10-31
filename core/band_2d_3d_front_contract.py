"""Shared 2D/3D front-on band asset projection.

Depth is an installation parameter, never a change to the musical
submodel contract. This covers all existing Helixville4 performers and
supports a separately authored mallet player when that asset is added.
"""
from __future__ import annotations

from models.helixville4_band_assets import HELIXVILLE4_BAND_ASSETS
from models.helixville4_mallet_asset import mallet_performer_asset

ALL_BAND_ASSETS = (*HELIXVILLE4_BAND_ASSETS, mallet_performer_asset())


def band_member_variant(member_id: str, kind: str) -> dict:
    if kind not in ("2d", "3d"):
        raise ValueError("kind must be 2d or 3d")
    assets = {asset.member_id: asset for asset in ALL_BAND_ASSETS}
    if member_id not in assets:
        raise ValueError(f"unknown band member: {member_id}")
    asset = assets[member_id]
    segments = tuple(
        {
            "name": segment.name,
            "submodel": segment.submodel,
            "points": tuple((p.x / asset.width_px, p.y / asset.height_px)
                            for p in segment.points),
            "closed": segment.closed,
        }
        for segment in asset.outline_segments
    )
    return {
        "member_id": member_id,
        "kind": kind,
        "projection": "front_orthographic",
        "front_segments": segments,
        "submodels": asset.submodel_order,
        "depth_fraction": 0.0 if kind == "2d" else 0.25,
        "construction": "flat insulated panel" if kind == "2d"
                        else "dimensional insulated armature",
    }


def verify_band_front_parity() -> dict[str, bool]:
    result = {}
    for asset in ALL_BAND_ASSETS:
        flat = band_member_variant(asset.member_id, "2d")
        dimensional = band_member_variant(asset.member_id, "3d")
        result[asset.member_id] = (
            flat["front_segments"] == dimensional["front_segments"]
            and flat["submodels"] == dimensional["submodels"]
            and flat["projection"] == dimensional["projection"]
        )
    return result
