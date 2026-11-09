"""Twelve-circuit physical snowman drummer with explicit idle poses.

Viewer-right means the right side of the image, not the performer's right.
Physical lighting frames are NOT motor actuation: each hit string must trace
a complete arm/hand/stick contact pose on a fixed 2D or 3D support.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math

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


def compile_contact_intervals(hits: list[dict], *, duration: float,
                              contact_hold: float = .035, dim: float = .18) -> dict:
    """Compile fixed lighting strings from already-classified onsets.

    The twelve-string plan has cymbal and snare contact arms. Tom channels
    illuminate surfaces only; articulated tom contact poses still need more
    strings or addressable pixels. No physical LOR Unit IDs are guessed.
    """
    if not math.isfinite(duration) or duration <= 0 or not 0 < contact_hold <= .1 or not 0 < dim < 1:
        raise ValueError("Invalid physical drummer duration, hold, or dim level")
    channels = {c.key: [] for c in DRUM_CIRCUITS}
    route = {"kick": "kick", "hi_hat": "hi_hat", "hihat": "hi_hat",
             "tom_high": "high_tom", "tom_mid": "mid_tom", "tom_floor": "floor_tom",
             "tom_low": "floor_tom", "cymbal_left": "left_cymbal_contact",
             "cymbal_right": "right_cymbal_contact"}
    contacts = {"left": [], "right": []}
    source_onsets = []
    for hit in sorted(hits, key=lambda h: float(h["time"])):
        time = float(hit["time"])
        if not math.isfinite(time) or not 0 <= time < duration:
            continue
        target = hit["target"].lower().removeprefix("hx_snowman_drummer_v3_hit_")
        side = hit.get("side")
        if target == "snare":
            if side not in ("left", "right"):
                raise ValueError("Snare contact export requires an explicit source hand")
            key = "left_snare_contact" if side == "left" else "snare_right_contact"
        elif target in route:
            key = route[target]
            if target.startswith("cymbal_"):
                side = target.split("_")[-1]
        else:
            raise ValueError(f"Unmapped physical drum target: {target}")
        end = min(duration, time + contact_hold)
        velocity = float(hit.get("velocity", 1))
        if not math.isfinite(velocity) or velocity <= 0:
            continue
        channels[key].append(dict(start=time, end=end, brightness=min(1., velocity)))
        source_onsets.append(dict(time=time, key=key))
        if key in ("left_snare_contact", "snare_right_contact", "left_cymbal_contact", "right_cymbal_contact"):
            contacts[side].append((time, end))
    channels["body_kit_dim"] = [dict(start=0., end=duration, brightness=dim)]
    for side in ("left", "right"):
        cursor = 0.
        for start, end in sorted(contacts[side]):
            if start > cursor:
                channels[side + "_stick_idle"].append(dict(start=cursor, end=start, brightness=1.))
            cursor = max(cursor, end)
        if cursor < duration:
            channels[side + "_stick_idle"].append(dict(start=cursor, end=duration, brightness=1.))
    return {"circuits": channels, "source_onsets": source_onsets,
            "duration": duration, "controller_addresses_assigned": False,
            "tom_contact_pose_exported": False}
