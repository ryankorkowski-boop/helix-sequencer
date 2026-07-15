"""Fast, dependency-free preview frame renderer."""

from dataclasses import dataclass, field

from .timeline import Timeline


@dataclass
class Frame:
    timestamp_ms: int
    channels: dict[str, float] = field(default_factory=dict)


class PreviewRenderer:
    """Convert a timeline into channel intensity frames."""

    def __init__(self, timeline: Timeline):
        self.timeline = timeline

    def render_frame(self, timestamp_ms: int) -> Frame:
        channels: dict[str, float] = {}
        for event in self.timeline.at(timestamp_ms):
            channels[event.target] = max(
                channels.get(event.target, 0.0), event.intensity
            )
        return Frame(timestamp_ms=timestamp_ms, channels=channels)

    def render(self, duration_ms: int, step_ms: int = 50) -> list[Frame]:
        return [self.render_frame(t) for t in range(0, duration_ms, step_ms)]
