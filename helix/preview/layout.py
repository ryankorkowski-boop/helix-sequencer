"""Layout abstractions for preview rendering."""

from dataclasses import dataclass, field


@dataclass
class PreviewChannel:
    name: str
    color: str | None = None


@dataclass
class PreviewLayout:
    """Minimal layout representation shared by preview engines."""

    channels: dict[str, PreviewChannel] = field(default_factory=dict)

    def add_channel(self, name: str, color: str | None = None) -> None:
        self.channels[name] = PreviewChannel(name=name, color=color)

    def has_channel(self, name: str) -> bool:
        return name in self.channels
