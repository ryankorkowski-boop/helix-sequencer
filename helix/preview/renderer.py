"""Minimal renderer abstraction for Helix preview frames."""

from dataclasses import dataclass, field

from .timeline import Timeline


@dataclass
class PreviewFrame:
    """A generated preview frame."""

    time_ms: int
    channels: dict[str, float] = field(default_factory=dict)


class FrameRenderer:
    """Convert timeline events into lightweight preview frames."""

    def __init__(self, timeline: Timeline) -> None:
        self.timeline = timeline

    def render_frame(self, time_ms: int) -> PreviewFrame:
        channels: dict[str, float] = {}
        for event in self.timeline.at(time_ms):
            channel = event.payload.get("channel")
            level = event.payload.get("level", 1.0)
            if channel:
                channels[str(channel)] = float(level)
        return PreviewFrame(time_ms=time_ms, channels=channels)

    def render_range(self, start_ms: int, end_ms: int, step_ms: int = 50) -> list[PreviewFrame]:
        return [
            self.render_frame(t)
            for t in range(start_ms, end_ms + 1, step_ms)
        ]
