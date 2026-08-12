"""Pillow based renderer for Helix preview frames.

Designed as a lightweight renderer suitable for preview generation on modest
hardware. It composites transparent sprite layers into RGBA frames.
"""

from pathlib import Path
import json
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
            if str(element.get("name") or "") in wanted:
                indices.extend(self._parse_ranges(element.get("line0", "")))
        return sorted(set(indices))

    def _load_component_masks(self, asset_root):
        """Build exact reusable component masks from the authored V3 pose spec.

        The pose spec is also the source used to make the approved sprite sheet.
        We rasterize its component geometry once, then illuminate only those
        pixels. No xmodel grid, ellipse overlay, or whole-component fill is used
        in the production preview path.
        """
        spec_path = Path(asset_root) / "fixtures/band_geometry/drummer_v3_pose_spec.json"
        if not spec_path.is_file():
            return {}
        try:
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        masks = {}
        for zone in spec.get("zones", []):
            if not isinstance(zone, dict) or not zone.get("id"):
                continue
            mask = self.Image.new("L", (self.width, self.height), 0)
            draw = self.ImageDraw.Draw(mask)
            for command in zone.get("commands", []):
                self._draw_mask_command(draw, command)
            masks[str(zone["id"])] = mask
        composites = {}
        for composite in spec.get("composites", []):
            if not isinstance(composite, dict) or not composite.get("id"):
                continue
            mask = self.Image.new("L", (self.width, self.height), 0)
            for member in composite.get("members", []):
                member_mask = masks.get(str(member))
                if member_mask is not None:
                    mask = self.ImageChops.lighter(mask, member_mask) if hasattr(self, "ImageChops") else self._lighter(mask, member_mask)
            composites[str(composite["id"])] = mask
        return {**masks, **composites}

    def _lighter(self, a, b):
        import PIL.ImageChops as ImageChops
        return ImageChops.lighter(a, b)

    def _draw_mask_command(self, draw, command):
        shape = str(command.get("shape", ""))
        width, height = self.width, self.height
        if shape in {"ellipse", "ellipse_outline", "rectangle_outline"}:
            x0, y0, x1, y1 = [float(v) for v in command.get("box", [0, 0, 0, 0])]
            box = (round(x0 * width), round(y0 * height), round(x1 * width), round(y1 * height))
            if shape == "ellipse":
                draw.ellipse(box, fill=255)
            elif shape == "ellipse_outline":
                draw.ellipse(box, outline=255, width=max(1, round(float(command.get("width", 0.01)) * min(self.width, self.height))))
            else:
                draw.rectangle(box, outline=255, width=max(1, round(float(command.get("width", 0.01)) * min(self.width, self.height))))
        elif shape == "line":
            x0, y0, x1, y1 = [float(v) for v in command.get("points", [0, 0, 0, 0])]
            draw.line((round(x0 * width), round(y0 * height), round(x1 * width), round(y1 * height)), fill=255, width=max(1, round(float(command.get("width", 0.01)) * min(width, height))))

    def _illuminate_component_mask(self, frame, mask, intensity):
        if mask is None or intensity <= 0:
            return frame
        strength = max(0.0, min(1.0, float(intensity)))
        brighter = self.ImageEnhance.Brightness(frame).enhance(1.0 + 1.6 * strength)
        brighter = self.ImageEnhance.Color(brighter).enhance(1.0 + 0.55 * strength)
        frame = self.Image.composite(brighter, frame, mask.point(lambda v: int(v * strength)))
        # Halo is derived from the exact component silhouette, never from a box.
        halo = mask.filter(self.ImageFilter.GaussianBlur(max(1.0, min(self.width, self.height) * 0.0012)))
        glow = self.Image.new("RGBA", frame.size, (255, 224, 72, 0))
        glow.putalpha(halo.point(lambda v: int(v * 0.12 * strength)))
        frame.alpha_composite(glow)
        return frame

    def _draw_drummer_illumination(self, frame, commands, intensity):
        """Legacy fallback for isolated renderer tests only."""
        if not commands or intensity <= 0.0:
            return frame
        overlay = self.Image.new("RGBA", frame.size, (0, 0, 0, 0))
        draw = self.ImageDraw.Draw(overlay)
        w, h = frame.size
        for command in commands:
            rgba = tuple(int(v) for v in command.get("rgba", (255, 245, 120, 200)))
            alpha = max(0, min(255, int(round(rgba[3] * intensity))))
            fill = (rgba[0], rgba[1], rgba[2], alpha)
            shape = command.get("shape")
            if shape in {"ellipse", "rectangle_outline"}:
                box = command.get("box", (0.0, 0.0, 1.0, 1.0))
                xy = (int(round(float(box[0]) * w)), int(round(float(box[1]) * h)), int(round(float(box[2]) * w)), int(round(float(box[3]) * h)))
                if shape == "ellipse":
                    draw.ellipse(xy, fill=fill)
                else:
                    width = max(1, int(round(float(command.get("width", 0.008)) * min(w, h))))
                    draw.rectangle(xy, outline=fill, width=width)
            elif shape == "line":
                points = command.get("points", [])
                if len(points) == 4:
                    xy = (int(round(float(points[0]) * w)), int(round(float(points[1]) * h)), int(round(float(points[2]) * w)), int(round(float(points[3]) * h)))
                    width = max(1, int(round(float(command.get("width", 0.01)) * min(w, h))))
                    draw.line(xy, fill=fill, width=width)
        frame.alpha_composite(overlay)
        return frame

    def render_drummer_v3(self, asset_root, events, timestamp_ms):
        """Render the authored component silhouette at its exact sprite-sheet position."""
        if not self._available:
            raise RuntimeError("Pillow is required for image rendering")
        from .drummer_v3 import DRUMMER_V3_BACKDROP, active_events
        from PIL import ImageChops
        self.ImageChops = ImageChops
        root = Path(asset_root)
        backdrop = self.load_layer(root / DRUMMER_V3_BACKDROP)
        if backdrop.size != (self.width, self.height):
            backdrop = backdrop.resize((self.width, self.height), self.Image.Resampling.LANCZOS)
        frame = backdrop.copy()
        masks = self._load_component_masks(root)
        pose_to_composite = {
            "kick_hit": "HIT_KICK",
            "snare_hit": "HIT_SNARE",
            "hi_hat_pulse": "HIT_HIHAT",
            "left_tom_hit": "HIT_LEFT_TOM",
            "right_tom_hit": "HIT_RIGHT_TOM",
            "left_crash": "HIT_LEFT_CRASH",
            "right_crash": "HIT_RIGHT_CRASH",
            "both_crash": "HIT_BOTH_CRASH",
        }
        for event in active_events(list(events), int(timestamp_ms)):
            mask = masks.get(pose_to_composite.get(event.pose, ""))
            if mask is not None:
                frame = self._illuminate_component_mask(frame, mask, float(event.intensity))
        return frame
