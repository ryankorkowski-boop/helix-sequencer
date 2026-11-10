"""Reusable drummer animation poses.

Poses are intentionally event-driven so the same Helix drum events can drive
both visual preview and xLights sequence generation.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Pose:
    name: str
    layers: tuple[str, ...] = field(default_factory=tuple)


POSES = {
    "idle": Pose("idle", ("base",)),
    "left_crash": Pose("left_crash", ("left_stick", "left_crash")),
    "right_crash": Pose("right_crash", ("right_stick", "right_crash")),
    "hi_hat": Pose("hi_hat", ("right_stick", "hihat")),
    "snare": Pose("snare", ("left_stick", "snare")),
    "left_tom": Pose("left_tom", ("left_stick", "left_tom")),
    "right_tom": Pose("right_tom", ("right_stick", "right_tom")),
    "kick": Pose("kick", ("kick",)),
    "double_crash": Pose("double_crash", ("left_stick", "right_stick", "left_crash", "right_crash")),
}


def get_pose(name: str) -> Pose:
    return POSES.get(name, POSES["idle"])
