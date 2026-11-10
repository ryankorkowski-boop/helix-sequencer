"""Pillow based renderer for Helix preview frames.

Designed as a lightweight renderer suitable for preview generation on modest
hardware. It composites transparent sprite layers into RGBA frames.
"""

from pathlib import Path


class PillowRenderer:
    def __init__(self, width=1920, height=1080):
        self.width = width
        self.height = height
        self._available = False
        try:
            from PIL import Image
            self.Image = Image
            self._available = True
        except ImportError:
            self.Image = None

    def load_layer(self, path):
        if not self._available:
            raise RuntimeError("Pillow is required for image rendering")
        return self.Image.open(Path(path)).convert("RGBA")

    def render(self, layers):
        if not self._available:
            raise RuntimeError("Pillow is required for image rendering")

        frame = self.Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        for layer in layers:
            if layer is not None:
                frame.alpha_composite(layer)
        return frame
