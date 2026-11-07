"""Explicit DIY AC pose plan; independent of the legacy outline-channel map.

These are logical switched circuits, not verified xLights/LOR addresses.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PhysicalCircuit:
    member: str
    name: str
    elements: tuple[str, ...]
    dim_base: bool = False


DRUMMER = (
    PhysicalCircuit("drummer", "BASE_DIM", ("body", "head", "hat", "stationary_kit_outline"), True),
    PhysicalCircuit("drummer", "CYMBAL_LEFT", ("left_cymbal", "left_arm_contact", "left_stick_contact")),
    PhysicalCircuit("drummer", "TOM_FLOOR", ("floor_tom", "right_arm_low_contact", "right_stick_contact")),
    PhysicalCircuit("drummer", "TOM_MID", ("mid_left_tom", "left_arm_contact", "left_stick_contact")),
    PhysicalCircuit("drummer", "SNARE_LEFT", ("snare_surface", "left_arm_snare_contact", "left_stick_snare_contact")),
    PhysicalCircuit("drummer", "SNARE_RIGHT", ("snare_surface", "right_arm_snare_contact", "right_stick_snare_contact")),
    PhysicalCircuit("drummer", "KICK", ("kick", "foot_or_beater_contact")),
    PhysicalCircuit("drummer", "TOM_HIGH", ("high_right_tom", "right_arm_contact", "right_stick_contact")),
    PhysicalCircuit("drummer", "HI_HAT", ("hi_hat", "right_arm_hat_contact", "right_stick_hat_contact")),
    PhysicalCircuit("drummer", "CYMBAL_RIGHT", ("right_cymbal", "right_arm_high_contact", "right_stick_contact")),
)

VOCAL_STATES = ("REST", "AH", "EE", "OH", "MBP", "FV", "L")


def physical_drummer_plan(start_channel: int = 1) -> tuple[dict[str, object], ...]:
    if start_channel < 1:
        raise ValueError("start_channel must be positive")
    return tuple({
        "channel": start_channel + index,
        "member": circuit.member,
        "name": circuit.name,
        "elements": circuit.elements,
        "dim_base": circuit.dim_base,
    } for index, circuit in enumerate(DRUMMER))


def validate_drummer_plan() -> None:
    assert len(DRUMMER) == 10
    assert len({c.name for c in DRUMMER}) == len(DRUMMER)
    assert sum(c.dim_base for c in DRUMMER) == 1
    for circuit in DRUMMER[1:]:
        assert any("contact" in element for element in circuit.elements)
    assert DRUMMER[4].name == "SNARE_LEFT"
    assert DRUMMER[5].name == "SNARE_RIGHT"
    assert "snare_surface" in DRUMMER[4].elements
    assert "snare_surface" in DRUMMER[5].elements


def singer_pose_plan(member: str, start_channel: int = 1) -> tuple[dict[str, object], ...]:
    """Seven exclusive physical mouth poses; other singer motion not included."""
    if member not in ("snowman_singer", "snowman_singer_female"):
        raise ValueError("unknown singer")
    if start_channel < 1:
        raise ValueError("start_channel must be positive")
    return tuple({"channel": start_channel + i, "member": member, "name": f"MOUTH_{state}"}
                 for i, state in enumerate(VOCAL_STATES))
