"""Build rendered frame sequences from timeline events."""


class FrameSequence:
    def __init__(self, fps=30):
        self.fps = fps
        self.frames = []

    def add(self, frame):
        self.frames.append(frame)

    def duration_seconds(self):
        if not self.fps:
            return 0
        return len(self.frames) / self.fps

    def __len__(self):
        return len(self.frames)
