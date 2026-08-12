"""Pillow based renderer for Helix preview frames.

Designed as a lightweight renderer suitable for preview generation on modest
hardware. It composites transparent sprite layers into RGBA frames.
"""

from pathlib import Path
import re
import xml.etree.ElementTree as ET


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

    @staticmethod
    def _parse_ranges(value):
        indices = []
        for token in str(value or "").split(","):
            token = token.strip()
            if not token:
                continue
            if "-" in token:
                start, end = token.split("-", 1)
                indices.extend(range(int(start), int(end) + 1))
            else:
                indices.append(int(token))
        return indices

    def _xmodel_submodel_indices(self, asset_root, target_names):
        """Read the authoritative V3 xmodel node membership for target submodels."""
        xmodel = Path(asset_root) / "fixtures/band_geometry/models/HX_SNOWMAN_DRUMMER_V3.xmodel"
        if not xmodel.is_file() or not target_names:
            return []

        wanted = set(target_names)
        # Reactive cue IDs historically used the HIT_* aliases. Normalize them
        # to the physical xmodel submodel names without changing the event API.
        aliases = {
            "HX_SNOWMAN_DRUMMER_V3_HIT_KICK": "HX_SNOWMAN_DRUMMER_V3_KICK",
            "HX_SNOWMAN_DRUMMER_V3_HIT_SNARE": "HX_SNOWMAN_DRUMMER_V3_SNARE",
            "HX_SNOWMAN_DRUMMER_V3_HIT_HIHAT": "HX_SNOWMAN_DRUMMER_V3_HI_HAT",
            "HX_SNOWMAN_DRUMMER_V3_HIT_TOM_LEFT": "HX_SNOWMAN_DRUMMER_V3_TOM_LEFT",
            "HX_SNOWMAN_DRUMMER_V3_HIT_TOM_RIGHT": "HX_SNOWMAN_DRUMMER_V3_TOM_RIGHT",
            "HX_SNOWMAN_DRUMMER_V3_HIT_LEFT_CRASH": "HX_SNOWMAN_DRUMMER_V3_CYMBAL_LEFT",
            "HX_SNOWMAN_DRUMMER_V3_HIT_RIGHT_CRASH": "HX_SNOWMAN_DRUMMER_V3_CYMBAL_RIGHT",
        }
        wanted = {aliases.get(name, name) for name in wanted}

        try:
            root = ET.parse(xmodel).getroot()
        except (ET.ParseError, OSError):
            return []

        indices = []
        for element in root.findall(".//subModel"):
            if element.get("name") in wanted:
                indices.extend(self._parse_ranges(element.get("line0", "")))
        return sorted(set(indices))

    def _draw_xmodel_submodel_illumination(self, frame, indices, intensity):
        """Illuminate the exact node cells belonging to an xmodel submodel."""
        if not indices or intensity <= 0.0:
            return frame

        overlay = self.Image.new("RGBA", frame.size, (0, 0, 0, 0))
        draw = self.ImageDraw.Draw(overlay)
        # HX_SNOWMAN_DRUMMER_V3 declares a 96 x 72 node grid.
        cols, rows = 96, 72
        cell_w = self.width / cols
        cell_h = self.height / rows
        alpha = max(0, min(255, int(round(225 * intensity))))
        fill = (255, 245, 120, alpha)

        for index in indices:
            if index < 0 or index >= cols * rows:
                continue
            x = index % cols
            y = index // cols
            left = int(round(x * cell_w))
            top = int(round(y * cell_h))
            right = max(left + 1, int(round((x + 1) * cell_w)))
            bottom = max(top + 1, int(round((y + 1) * cell_h)))
            draw.rectangle((left, top, right - 1, bottom - 1), fill=fill)

        glow = overlay.filter(self.ImageFilter.GaussianBlur(max(1.0, min(self.width, self.height) * 0.004)))
        frame.alpha_composite(glow)
        frame.alpha_composite(overlay)
        return frame

    def _draw_drummer_illumination(self, frame, commands, intensity):
        """Fallback additive illumination for isolated renderer unit tests."""
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
        """Render authored V3 artwork with illumination from real xmodel submodels.

        The authored backdrop is always the base. For real V3 assets, active
        events illuminate the exact node membership declared by the xmodel.
        The normalized manifest commands remain only as a fallback for small
        isolated renderer tests that intentionally omit the xmodel.
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
            indices = self._xmodel_submodel_indices(root, event.submodels)
            if indices:
                self._draw_xmodel_submodel_illumination(frame, indices, float(event.intensity))
            else:
                commands = illumination_specs_for_pose(root, event.pose)
                self._draw_drummer_illumination(frame, commands, float(event.intensity))
        return frame
