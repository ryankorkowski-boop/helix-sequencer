"""High-level preview simulation helpers."""

from dataclasses import dataclass

from .renderer import FrameRenderer, PreviewFrame


@dataclass
class PreviewConfig:
    duration_ms: int = 20000
    step_ms: int = 50


class PreviewSimulator:
    """Generate lightweight preview frames without opening xLights."""

    def __init__(self, renderer: FrameRenderer, config: PreviewConfig | None = None) -> None:
        self.renderer = renderer
        self.config = config or PreviewConfig()

    def generate(self) -> list[PreviewFrame]:
        return self.renderer.render_range(
            0,
            self.config.duration_ms,
            self.config.step_ms,
        )
