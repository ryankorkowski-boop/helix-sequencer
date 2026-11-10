"""Render Helix preview timelines into frame sequences."""


class FrameSequenceRenderer:
    def __init__(self, renderer, fps: int = 30):
        self.renderer = renderer
        self.fps = fps

    def render(self, duration: float) -> list:
        frames = []
        total_frames = int(duration * self.fps)

        for index in range(total_frames):
            timestamp = index / self.fps
            frames.append(self.renderer.render_frame(timestamp))

        return frames
