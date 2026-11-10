"""Reusable drummer animation poses."""

from dataclasses import dataclass, field


@dataclass
class Pose:
    name: str
    active_layers: list[str] = field(default_factory=list)
    duration: float = 0.1


POSES = {
    "idle": Pose("idle", ["base", "stage"], 0.25),
    "left_crash": Pose("left_crash", ["base", "left_stick", "left_crash"], 0.15),
    "right_crash": Pose("right_crash", ["base", "right_stick", "right_crash"], 0.15),
    "hihat": Pose("hihat", ["base", "hihat"], 0.08),
    "snare": Pose("snare", ["base", "snare"], 0.08),
    "left_tom": Pose("left_tom", ["base", "left_tom"], 0.12),
    "right_tom": Pose("right_tom", ["base", "right_tom"], 0.12),
    "kick": Pose("kick", ["base", "kick"], 0.08),
    "double_crash": Pose("double_crash", ["base", "left_crash", "right_crash"], 0.2),
}
