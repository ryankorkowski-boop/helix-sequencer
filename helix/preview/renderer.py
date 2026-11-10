"""Frame renderer for Helix preview output."""


class FrameRenderer:
    def __init__(self, sprites=None, width=1920, height=1080):
        self.sprites = sprites
        self.width = width
        self.height = height

    def render_frame(self, timestamp_ms, events=()):
        """Render a frame from active animation events.

        Rendering backend intentionally remains isolated so the same event
        stream can later drive Pillow, Qt, or GPU rendering.
        """
        return {
            "timestamp_ms": timestamp_ms,
            "events": list(events),
            "size": (self.width, self.height),
        }
