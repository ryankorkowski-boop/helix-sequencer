"""Pillow based renderer for Helix preview frames.

Designed as a lightweight renderer suitable for preview generation on modest
hardware. It composites transparent sprite layers into RGBA frames.
"""

from pathlib import Path
import xml.etree.ElementTree as ET


class PillowRenderer:
    def __init__(self, width=1920, height=1080):
        self.width = width
        self.height = height
        self._available = False
        try:
            from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
            self.Image = Image
            self.ImageDraw = ImageDraw
            self.ImageFilter = ImageFilter
            self.ImageEnhance = ImageEnhance
            self._available = True
        except ImportError:
            self.Image = None
            self.ImageDraw = None
            self.ImageFilter = None
            self.ImageEnhance = None
            self._available = False

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
        """Read authoritative V3 xmodel node membership for target submodels."""
        xmodel = Path(asset_root) / "fixtures/band_geometry/models/HX_SNOWMAN_DRUMMER_V3.xmodel"
        if not xmodel.is_file() or not target_names:
            return []

        aliases = {
            "HX_SNOWMAN_DRUMMER_V3_HIT_KICK": "HX_SNOWMAN_DRUMMER_V3_KICK",
            "HX_SNOWMAN_DRUMMER_V3_HIT_SNARE": "HX_SNOWMAN_DRUMMER_V3_SNARE",
            "HX_SNOWMAN_DRUMMER_V3_HIT_HIHAT": "HX_SNOWMAN_DRUMMER_V3_HI_HAT",
            "HX_SNOWMAN_DRUMMER_V3_HIT_TOM_LEFT": "HX_SNOWMAN_DRUMMER_V3_TOM_LEFT",
            "HX_SNOWMAN_DRUMMER_V3_HIT_TOM_RIGHT": "HX_SNOWMAN_DRUMMER_V3_TOM_RIGHT",
            "HX_SNOWMAN_DRUMMER_V3_HIT_LEFT_CRASH": "HX_SNOWMAN_DRUMMER_V3_CYMBAL_LEFT",
            "HX_SNOWMAN_DRUMMER_V3_HIT_RIGHT_CRASH": "HX_SNOWMAN_DRUMMER_V3_CYMBAL_RIGHT",
        }
        wanted = {aliases.get(str(name), str(name)) for name in target_names}

        try:
            root = ET.parse(xmodel).getroot()
        except (ET.ParseError, OSError):
            return []

        indices = []
        for element in root.findall(".//subModel"):
            name = str(element.get("name") or "")
            if name in wanted:
                indices.extend(self._parse_ranges(element.get("line0", "")))
        return sorted(set(indices))

    def _draw_xmodel_submodel_illumination(self, frame, indices, intensity):
        """Light exact xmodel nodes while keeping the authored artwork visible.

        The xmodel node membership remains the source of truth. The logical
        96x72 mask is expanded only for preview legibility, so sparse physical
        nodes do not disappear after rasterization to a small preview frame.
        """
        if not indices or intensity <= 0.0:
            return frame

        grid_w, grid_h = 96, 72
        logical = self.Image.new("L", (grid_w, grid_h), 0)
        draw = self.ImageDraw.Draw(logical)
        mask_value = max(0, min(255, int(round(255 * intensity))))
        total_nodes = grid_w * grid_h
        for index in indices:
            # xLights custom-model line0 ranges are one-based. Accept zero-based
            # indices too for older hand-authored fixtures, but prefer the
            # authoritative one-based convention emitted by the V3 builder.
            if 1 <= index <= total_nodes:
                node = index - 1
            elif 0 <= index < total_nodes:
                node = index
            else:
                continue
            draw.point((node % grid_w, node // grid_w), fill=mask_value)

        # Expand sparse node points into a clearly visible but still localized
        # preview footprint. This does not invent target membership: every
        # illuminated footprint originates from an xmodel node in the target.
        logical = logical.filter(self.ImageFilter.MaxFilter(5))
        mask = logical.resize((self.width, self.height), self.Image.Resampling.BILINEAR)
        mask = mask.filter(self.ImageFilter.GaussianBlur(max(0.6, min(self.width, self.height) * 0.001)))

        strength = max(0.0, min(1.0, float(intensity)))
        brighter = self.ImageEnhance.Brightness(frame).enhance(1.0 + 1.15 * strength)
        brighter = self.ImageEnhance.Color(brighter).enhance(1.0 + 0.30 * strength)
        frame = self.Image.composite(brighter, frame, mask)

        # Add an unmistakable warm emissive component, but keep the source
        # artwork underneath rather than replacing it with synthetic shapes.
        glow_mask = mask.filter(self.ImageFilter.GaussianBlur(max(2.0, min(self.width, self.height) * 0.004)))
        glow = self.Image.new("RGBA", frame.size, (255, 224, 72, 0))
        glow.putalpha(glow_mask.point(lambda value: int(value * (0.30 * strength))))
        frame.alpha_composite(glow)
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
        events illuminate the physical instrument targets declared by the V3
        pose contract, resolving those names into authoritative xmodel nodes.
        The normalized manifest commands remain only as a fallback for small
        isolated renderer tests that intentionally omit the xmodel.
        """
        if not self._available:
            raise RuntimeError("Pillow is required for image rendering")

        from .drummer_v3 import (
            DRUMMER_V3_BACKDROP,
            active_events,
            illumination_specs_for_pose,
            illumination_targets_for_pose,
        )

        root = Path(asset_root)
        backdrop = self.load_layer(root / DRUMMER_V3_BACKDROP)
        if backdrop.size != (self.width, self.height):
            backdrop = backdrop.resize((self.width, self.height), self.Image.Resampling.LANCZOS)

        frame = backdrop.copy()
        for event in active_events(list(events), int(timestamp_ms)):
            # Prefer the physical V3 target mapping. Event submodels are kept
            # as a compatibility fallback because older cue streams use HIT_*
            # aliases rather than the physical xmodel names.
            target_names = illumination_targets_for_pose(root, event.pose) or event.submodels
            indices = self._xmodel_submodel_indices(root, target_names)
            if indices:
                self._draw_xmodel_submodel_illumination(frame, indices, float(event.intensity))
            else:
                commands = illumination_specs_for_pose(root, event.pose)
                self._draw_drummer_illumination(frame, commands, float(event.intensity))
        return frame
