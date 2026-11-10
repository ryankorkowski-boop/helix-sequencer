"""Frame renderer for Helix preview scenes."""

from .compositor import SpriteCompositor
from .poses import POSES
from .timeline import PreviewTimeline


class PreviewRenderer:
    def __init__(self, timeline: PreviewTimeline, asset_dir: str, width: int = 1280, height: int = 720):
        self.timeline = timeline
        self.compositor = SpriteCompositor(asset_dir, (width, height))

    def pose_for_time(self, timestamp: float):
        events = self.timeline.active_at(timestamp)
        if not events:
            return POSES["idle"]

        action = events[-1].action
        return POSES.get(action, POSES["idle"])

    def render_frame(self, timestamp: float):
        pose = self.pose_for_time(timestamp)
        return self.compositor.render(pose.active_layers)
