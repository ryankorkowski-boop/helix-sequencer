from __future__ import annotations

import math
from dataclasses import dataclass

from core.spatial_render_bridge import SpatialRenderScene, build_render_scene
from tools import preview_renderer as pr


@dataclass(frozen=True)
class Camera3D:
    yaw_deg: float = -18.0
    pitch_deg: float = 10.0
    distance_scale: float = 2.25
    focal_scale: float = 1.25
    target_height: float = 0.48


class Spatial3DRenderer:
    """Perspective renderer using actual xLights model geometry and XYZ depth."""

    def __init__(self, scene: SpatialRenderScene, layout: pr.LayoutData, width: int, height: int):
        self.scene = scene
        self.layout = layout
        self.width = width
        self.height = height
        self.font = pr.ImageFont.load_default()
        self.camera = Camera3D()
        self.nodes = {node.name: node for node in scene.nodes}
        self.min_x, self.min_y, self.min_z, self.max_x, self.max_y, self.max_z = scene.bounds
        self.cx = (self.min_x + self.max_x) / 2.0
        self.cy = (self.min_y + self.max_y) / 2.0
        self.cz = (self.min_z + self.max_z) / 2.0
        self.span = max(self.max_x - self.min_x, self.max_y - self.min_y, self.max_z - self.min_z, 1.0)
        self._base_canvas = self._build_base_canvas()

    def _rotate(self, x: float, y: float, z: float) -> tuple[float, float, float]:
        x -= self.cx
        y -= self.cy
        z -= self.cz
        yaw = math.radians(self.camera.yaw_deg)
        pitch = math.radians(self.camera.pitch_deg)
        cy, sy = math.cos(yaw), math.sin(yaw)
        x, z = x * cy - z * sy, x * sy + z * cy
        cp, sp = math.cos(pitch), math.sin(pitch)
        y, z = y * cp - z * sp, y * sp + z * cp
        return x, y, z

    def project(self, point: tuple[float, float, float]) -> tuple[float, float, float] | None:
        x, y, z = self._rotate(*point)
        depth = z + self.span * self.camera.distance_scale
        if depth <= 0.05:
            return None
        scale = (self.span * self.camera.focal_scale) / depth
        px = self.width / 2.0 + x * scale * self.width / self.span
        py = self.height * (0.50 + self.camera.target_height) - y * scale * self.height / self.span
        return px, py, depth

    def _build_base_canvas(self):
        image = pr.Image.new("RGBA", (self.width, self.height), (4, 7, 14, 255))
        draw = pr.ImageDraw.Draw(image)
        for row in range(self.height):
            mix = row / max(1, self.height - 1)
            draw.line((0, row, self.width, row), fill=(int(4 + 10 * mix), int(7 + 12 * mix), int(14 + 22 * mix), 255))

        ground = pr.Image.new("RGBA", image.size, (0, 0, 0, 0))
        gd = pr.ImageDraw.Draw(ground)
        horizon = int(self.height * 0.70)
        gd.line((0, horizon, self.width, horizon), fill=(110, 130, 155, 70), width=2)
        for offset in range(-self.width, self.width + 1, 120):
            gd.line((self.width / 2, horizon, self.width / 2 + offset, self.height), fill=(90, 110, 130, 25), width=1)
        image.alpha_composite(ground)

        ghost = pr.Image.new("RGBA", image.size, (0, 0, 0, 0))
        gg = pr.ImageDraw.Draw(ghost)
        for node in self.scene.nodes:
            points = node.geometry_points or (node.position,)
            projected = [self.project(point) for point in points]
            projected = [p for p in projected if p is not None]
            if not projected:
                continue
            color = pr.dim_color(self._node_color(node.name), 0.10)
            if len(projected) >= 2:
                for a, b in zip(projected, projected[1:]):
                    gg.line((a[0], a[1], b[0], b[1]), fill=color + (80,), width=2)
            else:
                x, y, _ = projected[0]
                gg.ellipse((x - 2, y - 2, x + 2, y + 2), fill=color + (100,))
        ghost = ghost.filter(pr.ImageFilter.GaussianBlur(radius=2.0))
        image.alpha_composite(ghost)
        return image

    def _node_color(self, name: str) -> tuple[int, int, int]:
        geom = self.layout.leaf_models.get(name)
        return geom.color if geom else (220, 230, 245)

    def _draw_geometry(self, glow_draw, solid_draw, node, color, value):
        points = node.geometry_points or (node.position,)
        projected = [(self.project(point), point) for point in points]
        projected = [(p, point) for p, point in projected if p is not None]
        if not projected:
            return 0, 0.0

        avg_depth = sum(p[2] for p, _ in projected) / len(projected)
        perspective = max(0.55, min(1.8, self.span / max(avg_depth, 0.1)))
        width = max(2, int(round(2.0 + 3.0 * value * perspective)))
        bright = tuple(max(0, min(255, int(c * (0.35 + 0.9 * value) + 75 * value))) for c in color)

        if len(projected) >= 2:
            for first, second in zip(projected, projected[1:]):
                x1, y1, _ = first[0]
                x2, y2, _ = second[0]
                glow_draw.line((x1, y1, x2, y2), fill=bright + (125,), width=width + 8)
                solid_draw.line((x1, y1, x2, y2), fill=bright + (255,), width=width)
            return len(projected), avg_depth

        x, y, _ = projected[0][0]
        radius = max(2.0, 2.5 * perspective + 3.0 * value)
        glow_draw.ellipse((x - radius * 2.5, y - radius * 2.5, x + radius * 2.5, y + radius * 2.5), fill=bright + (125,))
        solid_draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=bright + (255,))
        core = max(1.0, radius * 0.35)
        solid_draw.ellipse((x - core, y - core, x + core, y + core), fill=(255, 255, 255, 235))
        return 1, avg_depth

    def render_frame(self, leaf_names, frame_values, title, t_ms, duration_ms, overlays):
        base = self._base_canvas.copy()
        glow = pr.Image.new("RGBA", base.size, (0, 0, 0, 0))
        solid = pr.Image.new("RGBA", base.size, (0, 0, 0, 0))
        gd = pr.ImageDraw.Draw(glow)
        sd = pr.ImageDraw.Draw(solid)
        active: list[tuple[float, int, object, tuple[int, int, int], float]] = []

        for idx, value in enumerate(frame_values):
            value = float(value)
            if value <= 0.02:
                continue
            name = leaf_names[idx]
            node = self.nodes.get(name)
            if node is None:
                continue
            points = node.geometry_points or (node.position,)
            depths = [self.project(point)[2] for point in points if self.project(point) is not None]
            if not depths:
                continue
            active.append((sum(depths) / len(depths), idx, node, self._node_color(name), value))

        # Render complete model geometry from farthest to nearest so overlapping
        # trees, arches, canes, stars and matrices read as a spatial scene.
        active.sort(key=lambda item: item[0], reverse=True)
        active_geometry_count = 0
        for _, _, node, color, value in active:
            count, _ = self._draw_geometry(gd, sd, node, color, value)
            active_geometry_count += count

        glow = glow.filter(pr.ImageFilter.GaussianBlur(radius=8))
        base.alpha_composite(glow)
        base.alpha_composite(solid)

        hud = pr.ImageDraw.Draw(base)
        hud.rounded_rectangle((28, 20, 440, 148), radius=18, fill=(7, 10, 18, 205), outline=(190, 215, 245, 65), width=1)
        hud.text((46, 38), pr.safe_label(title, 48), font=self.font, fill=(245, 248, 255, 255))
        hud.text((46, 62), f"time {pr.format_time(t_ms)} / {pr.format_time(duration_ms)}", font=self.font, fill=(200, 216, 240, 255))
        hud.text((46, 86), f"active geometry points {active_geometry_count}", font=self.font, fill=(170, 215, 255, 255))
        hud.text((46, 110), "3D spatial preview • native model geometry", font=self.font, fill=(145, 190, 225, 255))

        right_x = self.width - 430
        hud.rounded_rectangle((right_x, 20, self.width - 28, 172), radius=18, fill=(7, 10, 18, 205), outline=(190, 215, 245, 65), width=1)
        line_y = 38
        for key in ("song part", "piano", "sweep", "drop"):
            value = overlays.get(key, "")
            if value:
                hud.text((right_x + 18, line_y), f"{key}: {pr.safe_label(value, 34)}", font=self.font, fill=(245, 248, 255, 255))
                line_y += 24
        return base


def render_3d_sequence(sequence_path, layout, audio_path, fps, width, height):
    sequence = pr.parse_sequence(sequence_path)
    leaf_names, intensity = pr.build_leaf_intensity_matrix(layout, sequence, fps)
    source_layout = getattr(layout, "source_path", None)
    if source_layout is None:
        raise RuntimeError("LayoutData does not retain its source xLights layout path")
    scene = pr.spatial_scene.build_scene(pr.xmp.parse_layout(source_layout))
    if scene.capability != pr.spatial_scene.LAYOUT_CAPABILITY_3D:
        raise RuntimeError(f"3D renderer requires a true 3D layout; detected {scene.capability!r}")
    render_scene = build_render_scene(scene)
    renderer = Spatial3DRenderer(render_scene, layout, width, height)
    tracks = {
        "song part": pr.choose_track(sequence, "song parts"),
        "piano": pr.choose_track(sequence, "piano"),
        "sweep": pr.choose_track(sequence, "sweeps"),
        "drop": pr.choose_track(sequence, "drops"),
    }
    out_path = sequence_path.with_suffix(".3d.mp4")
    temp_path = out_path.with_suffix(".3d.silent.mp4")
    writer = pr.imageio.get_writer(temp_path, fps=fps, codec="libx264", quality=8, ffmpeg_log_level="error", pixelformat="yuv420p", macro_block_size=None)
    try:
        for frame_idx in range(intensity.shape[1]):
            t_ms = int(round(frame_idx * 1000.0 / fps))
            overlays = {k: pr.active_label(v, t_ms) for k, v in tracks.items()}
            frame = renderer.render_frame(leaf_names, intensity[:, frame_idx], sequence_path.name, t_ms, sequence.duration_ms, overlays)
            writer.append_data(pr.np.asarray(frame.convert("RGB"), dtype=pr.np.uint8))
    finally:
        writer.close()
    if out_path.exists():
        out_path.unlink()
    if audio_path and audio_path.exists():
        ffmpeg = pr.imageio_ffmpeg.get_ffmpeg_exe()
        import subprocess
        subprocess.run([ffmpeg, "-y", "-i", str(temp_path), "-i", str(audio_path), "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-shortest", str(out_path)], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        temp_path.unlink(missing_ok=True)
    else:
        temp_path.replace(out_path)
    return out_path
