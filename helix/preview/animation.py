"""Animation state resolution from preview events."""

from .poses import get_pose


class AnimationEngine:
    def __init__(self):
        self.current_pose = get_pose("idle")

    def apply_event(self, event):
        """Apply an AnimationEvent-like object to the active pose."""
        self.current_pose = get_pose(getattr(event, "action", "idle"))
        return self.current_pose

    def active_layers(self):
        return self.current_pose.layers
