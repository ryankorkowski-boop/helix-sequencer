"""Integration coverage for preview render pipeline."""

from .frame_sequence import FrameSequenceRenderer
from .render_demo import demo_timeline
from .renderer import PreviewRenderer


def test_preview_pipeline():
    timeline = demo_timeline()
    assert timeline.events

    renderer = PreviewRenderer(timeline, "assets")
    frame = renderer.render_frame(1.0)
    assert frame is not None

    frames = FrameSequenceRenderer(renderer, fps=10).render(1.0)
    assert len(frames) == 10
