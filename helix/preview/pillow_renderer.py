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
            from PIL import Image, ImageDraw, ImageFilter
            self.Image = Image
            self.ImageDraw = ImageDraw
            self.ImageFilter = ImageFilter
            self._available = True
        except ImportError:
            self.Image = None
            self.ImageDraw = None
            self.ImageFilter = None

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

    def _draw_drummer_illumination(self, frame, commands, intensity):
        """Additive submodel-targeted illumination from the V3 layer contract."""
        if not commands or intensity <= 0.0:
            return frame

        overlay = self.Image.new("RGBA", frame.size, (0, 0, 0, 0))
        draw = self.ImageDraw.Draw(overlay)
        w, h = frame.size

        for command in commands:
            rgba = tuple(int(v) for v in command.get("rgba", (255, 245, 120, 200)))
            alpha = max(0, min(255, int(round(rgba[3] * intensity))))
            fill = (rgba[0], rgba[1], rgba[2], alpha)
            glow = float(command.get("glow", 0.0) or 0.0)
            shape = command.get("shape")

            if shape in {"ellipse", "rectangle_outline"}:
                box = command.get("box", (0.0, 0.0, 1.0, 1.0))
                xy = (
                    int(round(float(box[0]) * w)),
                    int(round(float(box[1]) * h)),
                    int(round(float(box[2]) * w)),
                    int(round(float(box[3]) * h)),
                )
                if shape == "ellipse":
                    draw.ellipse(xy, fill=fill)
                else:
                    width = max(1, int(round(float(command.get("width", 0.008)) * min(w, h))))
                    draw.rectangle(xy, outline=fill, width=width)
            elif shape == "line":
                points = command.get("points", [])
                if len(points) == 4:
                    xy = (
                        int(round(float(points[0]) * w)),
                        int(round(float(points[1]) * h)),
                        int(round(float(points[2]) * w)),
                        int(round(float(points[3]) * h)),
                    )
                    width = max(1, int(round(float(command.get("width", 0.01)) * min(w, h))))
                    draw.line(xy, fill=fill, width=width)

            if glow > 0.0:
                blurred = overlay.filter(
                    self.ImageFilter.GaussianBlur(max(1.0, glow * min(w, h)))
                )
                frame.alpha_composite(blurred)

        frame.alpha_composite(overlay)
        return frame

    def render_drummer_v3(self, asset_root, events, timestamp_ms):
        """Render the authored V3 drummer with additive submodel illumination.

        The authored backdrop is always the base. Active drum events illuminate
        only their named physical V3 targets using the normalized submodel
        commands in the V3 manifest. Hit PNGs are intentionally NOT composited
        here; they remain compatibility assets, not the canonical hit renderer.
        """
        if not self._available:
            raise RuntimeError("Pillow is required for image rendering")

        from .drummer_v3 import (
            DRUMMER_V3_BACKDROP,
            active_events,
            illumination_specs_for_pose,
        )

        root = Path(asset_root)
        backdrop = self.load_layer(root / DRUMMER_V3_BACKDROP)
        if backdrop.size != (self.width, self.height):
            backdrop = backdrop.resize((self.width, self.height), self.Image.Resampling.LANCZOS)

        frame = backdrop.copy()
        for event in active_events(list(events), int(timestamp_ms)):
            commands = illumination_specs_for_pose(root, event.pose)
            self._draw_drummer_illumination(frame, commands, float(event.intensity))
        return frame
