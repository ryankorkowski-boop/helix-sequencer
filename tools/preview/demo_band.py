"""Small demo timeline for validating the preview pipeline."""

from .timeline import PreviewEvent, PreviewTimeline


def create_demo_timeline() -> PreviewTimeline:
    timeline = PreviewTimeline()

    events = [
        (0.0, "idle"),
        (1.0, "kick"),
        (1.5, "snare"),
        (2.0, "right_crash"),
        (3.0, "kick"),
        (3.5, "hihat"),
    ]

    for timestamp, action in events:
        timeline.add(PreviewEvent(timestamp, action, {"demo": True}))

    return timeline


if __name__ == "__main__":
    print(create_demo_timeline().events)
