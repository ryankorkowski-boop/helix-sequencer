"""Rendering backend abstraction for Helix previews."""


class RenderBackend:
    def __init__(self, width=1920, height=1080):
        self.width = width
        self.height = height

    def create_frame(self):
        """Create a blank frame placeholder.

        Kept lightweight so preview generation can run on lower-end systems.
        """
        return {
            "width": self.width,
            "height": self.height,
            "layers": [],
        }

    def render_layers(self, layers):
        frame = self.create_frame()
        frame["layers"] = list(layers)
        return frame
