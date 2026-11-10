"""Generate a small Helix preview animation clip."""

from pathlib import Path

from .export import PreviewExporter
from .frame_sequence import FrameSequenceRenderer
from .renderer import PreviewRenderer
from .timeline import PreviewEvent, PreviewTimeline


def demo_timeline() -> PreviewTimeline:
    timeline = PreviewTimeline()
    timeline.add(PreviewEvent(0.0, "idle"))
    timeline.add(PreviewEvent(1.0, "kick", {"instrument": "kick", "strength": 0.9}))
    timeline.add(PreviewEvent(2.0, "snare", {"instrument": "snare", "strength": 0.7}))
    timeline.add(PreviewEvent(3.0, "idle"))
    return timeline


def main() -> None:
    timeline = demo_timeline()
    renderer = PreviewRenderer(timeline, str(Path("assets")))
    sequence = FrameSequenceRenderer(renderer, fps=30)
    frames = sequence.render(4.0)

    exporter = PreviewExporter("preview_output")
    exporter.save_frames(frames)
    exporter.export_gif(frames)
    exporter.export_mp4(frames)
    print("Preview generated: preview_output/preview.gif")


if __name__ == "__main__":
    main()
