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

    def render_drummer_v3(self, asset_root, events, timestamp_ms):
        """Render the authored Drummer V3 prop at a point in time.

        The authored backdrop is always present. Hit PNGs are composited only
        while their corresponding V3 pose event is active, with intensity used
        as layer opacity. This intentionally mirrors the approved ground-truth
        preview instead of drawing a procedural snowman substitute.
        """
        if not self._available:
            raise RuntimeError("Pillow is required for image rendering")

        from .drummer_v3 import DRUMMER_V3_BACKDROP, layer_path, active_events

        root = Path(asset_root)
        backdrop = self.load_layer(root / DRUMMER_V3_BACKDROP)
        if backdrop.size != (self.width, self.height):
            backdrop = backdrop.resize((self.width, self.height), self.Image.Resampling.LANCZOS)

        frame = backdrop.copy()
        for event in active_events(list(events), int(timestamp_ms)):
            layer = self.load_layer(layer_path(root, event.pose))
            if layer.size != frame.size:
                layer = layer.resize(frame.size, self.Image.Resampling.LANCZOS)
            intensity = max(0.0, min(1.0, float(event.intensity)))
            if intensity < 0.999:
                alpha = layer.getchannel("A").point(lambda value: int(round(value * intensity)))
                layer.putalpha(alpha)
            frame.alpha_composite(layer)
        return frame
