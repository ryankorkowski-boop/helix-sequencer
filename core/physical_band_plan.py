"""Explicit physical planning allocation for seven Helix band performers.

This is a PROPOSAL, not a native controller export or verified build.
Logical submodels and physical circuits are deliberately kept separate.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

from models.helixville4_band_assets import HELIXVILLE4_BAND_ASSETS

# Ordered according to the user's seven-person band configuration.
PERFORMERS = (
    ("snowman_drummer", "Drummer", 200),
    ("snowman_guitarist", "Guitarist", 150),
    ("snowman_bassist", "Upright bassist", 150),
    ("snowman_keyboardist", "Keyboardist", 200),
    ("snowman_xylophonist", "Xylophonist / mallets", 160),
    ("snowman_singer", "Lead singer", 120),
    ("snowman_singer_female", "Secondary singer", 120),
)

@dataclass(frozen=True)
class PerformerAllocation:
    member_id: str
    label: str
    logical_submodels: int | None
    ac_controller: int
    ac_start: int
    ac_end: int
    ac_reserved: int
    proposed_pixels: int
    pixel_start: int
    pixel_end: int

def build_physical_band_plan() -> dict:
    catalog = {asset.member_id: len(asset.submodel_order) for asset in HELIXVILLE4_BAND_ASSETS}
    allocations = []
    pixel_next = 1
    for index, (member_id, label, pixels) in enumerate(PERFORMERS):
        logical = catalog.get(member_id)
        start = index * 16 + 1
        allocations.append(PerformerAllocation(
            member_id, label, logical, index + 1, start, start + 15,
            16 - logical if logical is not None else 16,
            pixels, pixel_next, pixel_next + pixels - 1))
        pixel_next += pixels
    return {
        "schema": "helix.physical_band_plan.v1",
        "status": "proposed_not_hardware_verified",
        "ac": {"controller_banks": 7, "channels_per_bank": 16, "total_capacity": 112},
        "rgb": {"pixel_count": pixel_next - 1, "rgb_channel_values": (pixel_next - 1) * 3,
                "voltage": "12V proposed; verify selected pixel specifications"},
        "performers": [asdict(item) for item in allocations],
        "warnings": [
            "Logical submodels do not automatically equal independently wired AC loads.",
            "Keyboardist and xylophonist lack entries in the existing five-member outline catalog.",
            "RGB pixel counts are estimates, not a bill of materials or power budget.",
            "Never connect pixel data or low-voltage wiring to AC switching outputs.",
            "AC circuits must be wired to the controller manufacturer's electrical instructions.",
        ],
    }
