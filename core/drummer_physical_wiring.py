"""Proposed ten-circuit physical snowman drummer with explicit idle poses.

Viewer-right means the right side of the image, not the performer's right.
Physical lighting frames are NOT motor actuation: each hit string must trace
a complete arm/hand/stick contact pose on a fixed 2D or 3D support.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

@dataclass(frozen=True)
class DrumCircuit:
    channel: int
    key: str
    physical_string: str
    behavior: str

DRUM_CIRCUITS = (
    DrumCircuit(1, "snare_right_contact", "Snare outline + right arm/hand/stick touching snare", "snare"),
    DrumCircuit(2, "left_snare_contact", "Left arm/hand/stick touching snare", "snare_alternate"),
    DrumCircuit(3, "left_cymbal_contact", "Viewer-left cymbal + left arm/hand/stick touching cymbal", "left_cymbal"),
    DrumCircuit(4, "right_cymbal_contact", "Viewer-right cymbal + right arm/hand/stick touching cymbal", "right_cymbal"),
    DrumCircuit(5, "hi_hat", "Hi-hat lighting (independent)", "hihat"),
    DrumCircuit(6, "high_tom", "Viewer-right high tom", "tom_high"),
    DrumCircuit(7, "mid_tom", "Mid tom to viewer-left of snare", "tom_mid"),
    DrumCircuit(8, "floor_tom", "Low floor tom on far viewer-left", "tom_low"),
    DrumCircuit(9, "kick", "Kick drum", "kick"),
    DrumCircuit(10, "body_kit_dim", "Snowman body + kit structural outlines", "always_dim"),
    DrumCircuit(11, "left_stick_idle", "Left arm/hand/stick raised clear of all drums", "idle_left"),
    DrumCircuit(12, "right_stick_idle", "Right arm/hand/stick raised clear of all drums", "idle_right"),
)

def build_drummer_wiring_plan() -> dict:
    """Twelve independently switched strings; four spare on a 16-bank."""
    return {
        "schema": "helix.drummer_wiring_plan.v1",
        "status": "proposed_not_production_export",
        "controller_capacity": 16,
        "circuits_used": len(DRUM_CIRCUITS),
        "spare_channels": list(range(len(DRUM_CIRCUITS) + 1, 17)),
        "circuits": [asdict(c) for c in DRUM_CIRCUITS],
        "layout_viewer_left_to_right": [
            "left_cymbal", "floor_tom", "mid_tom", "kick",
            "snare", "high_tom", "hi_hat", "right_cymbal"],
        "rules": {
            "body_kit_dim": "on at calibrated dim level throughout performance",
            "idle_left": "on unless a left-hand contact string is active",
            "idle_right": "on unless a right-hand contact string is active",
            "contact": "contact pose and corresponding drum/cymbal illuminate together where combined",
            "motion": "switched lighting poses, not mechanical arm movement",
        },
        "notes": [
            "The previous ten-channel illustration omitted independently addressable idle poses.",
            "A complete high/mid/floor tom stick-contact pose needs additional pose strings or pixels.",
            "For 2D attach strings to a nonconductive fence-safe panel; for 3D use bucket forms and protected wire mesh.",
            "Controller outputs and load ratings must be verified before connecting mains lighting.",
        ],
    }
