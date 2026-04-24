from __future__ import annotations

import argparse
import math
import subprocess
import sys
import tempfile
import unicodedata
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

from core.lazy_imports import LazyModule
from core import model_parser as xmp
from core import spatial_scene


ROOT = Path(__file__).resolve().parent.parent
PREVIEW_DEPS = ROOT / ".previewdeps"
DEFAULT_LAYOUT = "xlights_rgbeffects.xbkp" if (ROOT / "xlights_rgbeffects.xbkp").exists() else "xlights_rgbeffects.xml"
if PREVIEW_DEPS.exists():
    sys.path.insert(0, str(PREVIEW_DEPS))

imageio = LazyModule("imageio.v2")
imageio_ffmpeg = LazyModule("imageio_ffmpeg")
np = LazyModule("numpy")
Image = LazyModule("PIL.Image")
ImageDraw = LazyModule("PIL.ImageDraw")
ImageFilter = LazyModule("PIL.ImageFilter")
ImageFont = LazyModule("PIL.ImageFont")


def safe_label(text: str, limit: int = 72) -> str:
    text = text.replace("\u266f", "#").replace("\u266d", "b")
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def hex_to_rgb(value: str | None, default: tuple[int, int, int]) -> tuple[int, int, int]:
    if not value:
        return default
    raw = value.strip()
    if raw.startswith("#") and len(raw) == 7:
        try:
            return tuple(int(raw[i : i + 2], 16) for i in (1, 3, 5))
        except ValueError:
            return default
    lower = raw.lower()
    if "red" in lower:
        return (255, 70, 70)
    if "green" in lower or "lime" in lower:
        return (90, 255, 140)
    if "white" in lower:
        return (245, 245, 255)
    if "blue" in lower:
        return (90, 165, 255)
    return default


def dim_color(color: tuple[int, int, int], factor: float) -> tuple[int, int, int]:
    return tuple(max(0, min(255, int(round(channel * factor)))) for channel in color)


@dataclass
class ModelGeom:
    name: str
    x1: float
    y1: float
    x2: float
    y2: float
    points: tuple[tuple[float, float], ...]
    display_as: str
    color: tuple[int, int, int]


@dataclass
class GroupGeom:
    name: str
    members: list[str]
    center_x: float
    center_y: float
    min_x: float
    min_y: float
    max_x: float
    max_y: float


@dataclass
class LayoutData:
    leaf_models: dict[str, ModelGeom]
    groups: dict[str, GroupGeom]
    bounds: tuple[float, float, float, float]

    def resolve_leaves(self, name: str) -> list[str]:
        if name in self.leaf_models:
            return [name]
        if name not in self.groups:
            return []
        resolved: list[str] = []
        seen: set[str] = set()

        def visit(node: str) -> None:
            if node in seen:
                return
            seen.add(node)
            if node in self.leaf_models:
                resolved.append(node)
                return
            group = self.groups.get(node)
            if not group:
                return
            for member in group.members:
                visit(member)

        visit(name)
        unique: list[str] = []
        dedupe: set[str] = set()
        for leaf in resolved:
            if leaf not in dedupe:
                dedupe.add(leaf)
                unique.append(leaf)
        return unique


@dataclass
class EffectRecord:
    name: str
    start_ms: int
    end_ms: int
    settings: str | None = None
    palette: str | None = None


@dataclass
class TimingTrack:
    name: str
    events: list[EffectRecord] = field(default_factory=list)


@dataclass
class SequenceData:
    duration_ms: int
    model_effects: dict[str, list[EffectRecord]]
    timing_tracks: dict[str, TimingTrack]


def parse_models(layout_xml: Path) -> LayoutData:
    parsed_layout = xmp.parse_layout(layout_xml)
    scene = spatial_scene.build_scene(parsed_layout)
    leaf_models: dict[str, ModelGeom] = {}
    groups: dict[str, GroupGeom] = {}
    xs: list[float] = []
    ys: list[float] = []

    for name in parsed_layout.root_models():
        parsed_model = parsed_layout.models.get(name)
        node = scene.nodes.get(name)
        if parsed_model is None or node is None:
            continue
        points = tuple(node.projected_outline_xy or (node.projected_xy,))
        if len(points) >= 2:
            x1, y1 = points[0]
            x2, y2 = points[-1]
        else:
            x1, y1 = node.projected_xy
            x2, y2 = node.projected_xy
            points = ((x1, y1), (x2, y2))
        color = hex_to_rgb(parsed_model.raw_attrs.get("CustomColor"), (230, 235, 245))
        color = hex_to_rgb(parsed_model.raw_attrs.get("TagColour"), color)
        color = hex_to_rgb(parsed_model.raw_attrs.get("StringType"), color)
        leaf_models[name] = ModelGeom(
            name=name,
            x1=x1,
            y1=y1,
            x2=x2,
            y2=y2,
            points=points,
            display_as=parsed_model.display_as,
            color=color,
        )
        xs.extend([point[0] for point in points])
        ys.extend([point[1] for point in points])

    for group_name, group in parsed_layout.groups.items():
        node = scene.group_nodes.get(group_name)
        if node is None:
            continue
        min_x, min_y, max_x, max_y = node.projected_bounds_xy
        center_x, center_y = node.projected_xy
        members = list(scene.groups.get(group_name, ()))
        groups[group_name] = GroupGeom(
            name=group_name,
            members=members,
            center_x=center_x,
            center_y=center_y,
            min_x=min_x,
            min_y=min_y,
            max_x=max_x,
            max_y=max_y,
        )
        xs.extend([min_x, max_x, center_x])
        ys.extend([min_y, max_y, center_y])

    if not xs or not ys:
        raise RuntimeError(f"No geometry found in {layout_xml}")

    return LayoutData(
        leaf_models=leaf_models,
        groups=groups,
        bounds=(min(xs), min(ys), max(xs), max(ys)),
    )


def parse_sequence(path: Path) -> SequenceData:
    tree = ET.parse(path)
    root = tree.getroot()
    duration_ms = 0
    dur_node = root.find("./head/sequenceDuration")
    if dur_node is not None and dur_node.text:
        duration_ms = int(round(float(dur_node.text.strip()) * 1000))

    model_effects: dict[str, list[EffectRecord]] = {}
    timing_tracks: dict[str, TimingTrack] = {}

    effects_root = root.find("./ElementEffects")
    if effects_root is None:
        raise RuntimeError(f"No ElementEffects block found in {path}")

    for element in effects_root.findall("Element"):
        name = (element.attrib.get("name") or "").strip()
        kind = (element.attrib.get("type") or "").strip().lower()
        if not name:
            continue
        layer_records: list[EffectRecord] = []
        for layer in element.findall("EffectLayer"):
            for effect in layer.findall("Effect"):
                eff_name = (effect.attrib.get("name") or effect.attrib.get("label") or "").strip()
                start_ms = int(float(effect.attrib.get("startTime", "0") or 0))
                end_ms = int(float(effect.attrib.get("endTime", "0") or 0))
                if end_ms <= start_ms:
                    end_ms = start_ms + 1
                duration_ms = max(duration_ms, end_ms)
                layer_records.append(
                    EffectRecord(
                        name=eff_name,
                        start_ms=start_ms,
                        end_ms=end_ms,
                        settings=effect.attrib.get("settings"),
                        palette=effect.attrib.get("palette"),
                    )
                )
        if kind == "timing":
            if layer_records:
                timing_tracks[name] = TimingTrack(name=name, events=layer_records)
        else:
            if layer_records:
                model_effects[name] = layer_records

    return SequenceData(duration_ms=duration_ms, model_effects=model_effects, timing_tracks=timing_tracks)


def ramp_intensity(effect: EffectRecord, frame_times_ms: np.ndarray) -> np.ndarray:
    start = effect.start_ms
    end = max(start + 1, effect.end_ms)
    span = max(1.0, float(end - start))
    progress = np.clip((frame_times_ms - start) / span, 0.0, 1.0)
    start_level = 0.25
    end_level = 1.0
    settings = effect.settings or ""
    if "End=0" in settings and "Start=100" in settings:
        start_level = 1.0
        end_level = 0.0
    elif "End=100" in settings and "Start=0" in settings:
        start_level = 0.0
        end_level = 1.0
    values = start_level + (end_level - start_level) * progress
    mask = (frame_times_ms >= start) & (frame_times_ms < end)
    return np.where(mask, values, 0.0)


def build_leaf_intensity_matrix(
    layout: LayoutData,
    sequence: SequenceData,
    fps: int,
) -> tuple[list[str], np.ndarray]:
    leaf_names = sorted(layout.leaf_models)
    leaf_index = {name: idx for idx, name in enumerate(leaf_names)}
    frame_count = max(1, int(math.ceil(sequence.duration_ms / (1000.0 / fps))))
    frame_times_ms = (np.arange(frame_count, dtype=np.float32) * (1000.0 / fps)).astype(np.float32)
    intensities = np.zeros((len(leaf_names), frame_count), dtype=np.float32)

    for target_name, effects in sequence.model_effects.items():
        leaves = layout.resolve_leaves(target_name)
        if not leaves:
            continue
        indexes = [leaf_index[leaf] for leaf in leaves if leaf in leaf_index]
        if not indexes:
            continue
        for effect in effects:
            eff_name = effect.name.strip().lower()
            start_frame = max(0, int(math.floor(effect.start_ms * fps / 1000.0)))
            end_frame = min(frame_count, int(math.ceil(effect.end_ms * fps / 1000.0)))
            if end_frame <= start_frame:
                end_frame = min(frame_count, start_frame + 1)
            if eff_name == "ramp":
                curve = ramp_intensity(effect, frame_times_ms[start_frame:end_frame])
            else:
                curve = np.ones((end_frame - start_frame,), dtype=np.float32)
            for idx in indexes:
                intensities[idx, start_frame:end_frame] = np.maximum(
                    intensities[idx, start_frame:end_frame], curve
                )

    return leaf_names, intensities


def choose_track(sequence: SequenceData, prefix: str) -> TimingTrack | None:
    lowered = prefix.lower()
    for name, track in sequence.timing_tracks.items():
        if lowered in name.lower():
            return track
    return None


def active_label(track: TimingTrack | None, t_ms: int) -> str:
    if not track:
        return ""
    for event in track.events:
        if event.start_ms <= t_ms < event.end_ms:
            return safe_label(event.name)
    return ""


def format_time(ms_value: int) -> str:
    total_seconds = max(0, int(round(ms_value / 1000.0)))
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes:02d}:{seconds:02d}"


class HouseRenderer:
    def __init__(self, layout: LayoutData, width: int = 1280, height: int = 720, margin: int = 60):
        self.layout = layout
        self.width = width
        self.height = height
        self.margin = margin
        self.font = ImageFont.load_default()
        min_x, min_y, max_x, max_y = layout.bounds
        span_x = max(1.0, max_x - min_x)
        span_y = max(1.0, max_y - min_y)
        self.scale = min((width - margin * 2) / span_x, (height - margin * 2) / span_y)
        self.min_x = min_x
        self.min_y = min_y
        self.projected_models: dict[str, tuple[float, float, float, float, tuple[int, int, int]]] = {}
        self.projected_paths: dict[str, tuple[tuple[float, float], ...]] = {}
        for name, geom in self.layout.leaf_models.items():
            x1, y1 = self.project(geom.x1, geom.y1)
            x2, y2 = self.project(geom.x2, geom.y2)
            projected_points = tuple(self.project(px, py) for px, py in geom.points)
            if len(projected_points) < 2:
                projected_points = ((x1, y1), (x2, y2))
            self.projected_paths[name] = projected_points
            self.projected_models[name] = (x1, y1, x2, y2, geom.color)
        self._base_canvas = self._build_base_canvas()

    def project(self, x: float, y: float) -> tuple[float, float]:
        px = self.margin + (x - self.min_x) * self.scale
        py = self.height - self.margin - (y - self.min_y) * self.scale
        return px, py

    def _build_base_canvas(self) -> Image.Image:
        image = Image.new("RGBA", (self.width, self.height), (7, 13, 24, 255))
        draw = ImageDraw.Draw(image)
        for row in range(self.height):
            mix = row / max(1, self.height - 1)
            r = int(7 + mix * 14)
            g = int(13 + mix * 17)
            b = int(24 + mix * 28)
            draw.line((0, row, self.width, row), fill=(r, g, b, 255))
        grid = Image.new("RGBA", image.size, (0, 0, 0, 0))
        grid_draw = ImageDraw.Draw(grid)
        for x in range(self.margin, self.width - self.margin, 90):
            grid_draw.line((x, self.margin // 2, x, self.height - self.margin // 2), fill=(255, 255, 255, 18), width=1)
        for y in range(self.margin // 2, self.height - self.margin // 2, 90):
            grid_draw.line((self.margin // 2, y, self.width - self.margin // 2, y), fill=(255, 255, 255, 14), width=1)
        image.alpha_composite(grid)

        ghost = Image.new("RGBA", image.size, (0, 0, 0, 0))
        ghost_draw = ImageDraw.Draw(ghost)
        for name, geom in self.layout.leaf_models.items():
            self.draw_model(ghost_draw, name, dim_color(geom.color, 0.14), glow=False, width_boost=0)
        ghost = ghost.filter(ImageFilter.GaussianBlur(radius=0.8))
        image.alpha_composite(ghost)
        return image

    def draw_model(
        self,
        draw: ImageDraw.ImageDraw,
        model_name: str,
        color: tuple[int, int, int],
        glow: bool = True,
        width_boost: int = 2,
    ) -> None:
        x1, y1, x2, y2, _ = self.projected_models[model_name]
        path = self.projected_paths.get(model_name, ((x1, y1), (x2, y2)))
        length = 0.0
        for idx in range(len(path) - 1):
            ax, ay = path[idx]
            bx, by = path[idx + 1]
            length += math.hypot(bx - ax, by - ay)
        if length < 8:
            radius = 4 + width_boost
            px, py = path[0]
            draw.ellipse((px - radius, py - radius, px + radius, py + radius), fill=color + (255,))
            return
        width = max(2, int(round(2.2 + width_boost)))
        if glow:
            draw.line(path, fill=color + (110,), width=width + 6)
        draw.line(path, fill=color + (255,), width=width)

    def render_frame(
        self,
        leaf_names: list[str],
        frame_values: np.ndarray,
        title: str,
        t_ms: int,
        duration_ms: int,
        overlays: dict[str, str],
    ) -> Image.Image:
        base = self._base_canvas.copy()
        glow_layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow_layer)
        solid_layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
        solid_draw = ImageDraw.Draw(solid_layer)

        active_count = 0
        for idx, value in enumerate(frame_values):
            if value <= 0.02:
                continue
            active_count += 1
            model_name = leaf_names[idx]
            geom = self.layout.leaf_models[model_name]
            boost = int(round(3 * float(value)))
            bright = tuple(
                max(0, min(255, int(round(channel * (0.4 + 0.7 * float(value)) + 70 * float(value)))))
                for channel in geom.color
            )
            self.draw_model(glow_draw, model_name, bright, glow=True, width_boost=boost + 2)
            self.draw_model(solid_draw, model_name, bright, glow=False, width_boost=boost)

        glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=7))
        base.alpha_composite(glow_layer)
        base.alpha_composite(solid_layer)

        hud = ImageDraw.Draw(base)
        hud.rounded_rectangle((28, 20, 420, 148), radius=20, fill=(8, 12, 20, 206), outline=(200, 220, 255, 70), width=1)
        hud.text((46, 38), safe_label(title, 48), font=self.font, fill=(245, 248, 255, 255))
        hud.text((46, 62), f"time {format_time(t_ms)} / {format_time(duration_ms)}", font=self.font, fill=(200, 216, 240, 255))
        hud.text((46, 86), f"active models {active_count}", font=self.font, fill=(170, 215, 255, 255))
        hud.text((46, 110), "preview source xlights_rgbeffects.xml", font=self.font, fill=(145, 165, 188, 255))

        right_x = self.width - 430
        hud.rounded_rectangle((right_x, 20, self.width - 28, 172), radius=20, fill=(8, 12, 20, 206), outline=(200, 220, 255, 70), width=1)
        line_y = 38
        for key in ("song part", "piano", "sweep", "drop"):
            value = overlays.get(key, "")
            if not value:
                continue
            hud.text((right_x + 18, line_y), f"{key}: {safe_label(value, 34)}", font=self.font, fill=(245, 248, 255, 255))
            line_y += 24
        if line_y == 38:
            hud.text((right_x + 18, line_y), "no active timing label", font=self.font, fill=(185, 195, 210, 255))

        bar_left = 34
        bar_top = self.height - 42
        bar_right = self.width - 34
        bar_bottom = self.height - 22
        hud.rounded_rectangle((bar_left, bar_top, bar_right, bar_bottom), radius=8, fill=(35, 46, 63, 255))
        progress = 0.0 if duration_ms <= 0 else max(0.0, min(1.0, t_ms / duration_ms))
        fill_right = bar_left + int(round((bar_right - bar_left) * progress))
        hud.rounded_rectangle((bar_left, bar_top, fill_right, bar_bottom), radius=8, fill=(67, 173, 255, 255))
        hud.text((bar_left, bar_top - 18), "sequence progress", font=self.font, fill=(170, 215, 255, 255))

        return base


def render_sequence_to_mp4(
    sequence_path: Path,
    layout: LayoutData,
    audio_path: Path | None,
    fps: int,
    width: int,
    height: int,
) -> Path:
    sequence = parse_sequence(sequence_path)
    leaf_names, intensity = build_leaf_intensity_matrix(layout, sequence, fps)
    part_track = choose_track(sequence, "song parts")
    piano_track = choose_track(sequence, "piano")
    sweep_track = choose_track(sequence, "sweeps")
    drop_track = choose_track(sequence, "drops")
    renderer = HouseRenderer(layout, width=width, height=height)

    out_path = sequence_path.with_suffix(".mp4")
    temp_path = out_path.with_suffix(".silent.mp4")
    frame_count = intensity.shape[1]
    writer = imageio.get_writer(
        temp_path,
        fps=fps,
        codec="libx264",
        quality=8,
        ffmpeg_log_level="error",
        pixelformat="yuv420p",
        macro_block_size=None,
    )
    try:
        for frame_idx in range(frame_count):
            t_ms = int(round(frame_idx * 1000.0 / fps))
            overlays = {
                "song part": active_label(part_track, t_ms),
                "piano": active_label(piano_track, t_ms),
                "sweep": active_label(sweep_track, t_ms),
                "drop": active_label(drop_track, t_ms),
            }
            frame = renderer.render_frame(
                leaf_names=leaf_names,
                frame_values=intensity[:, frame_idx],
                title=sequence_path.name,
                t_ms=t_ms,
                duration_ms=sequence.duration_ms,
                overlays=overlays,
            )
            writer.append_data(np.asarray(frame.convert("RGB"), dtype=np.uint8))
    finally:
        writer.close()

    if out_path.exists():
        out_path.unlink()

    if audio_path and audio_path.exists():
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        cmd = [
            ffmpeg,
            "-y",
            "-i",
            str(temp_path),
            "-i",
            str(audio_path),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-shortest",
            str(out_path),
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        temp_path.unlink(missing_ok=True)
    else:
        temp_path.replace(out_path)

    return out_path


def default_targets(root: Path) -> list[Path]:
    targets: list[Path] = []
    v1 = root / "13v1.xsq"
    if v1.exists():
        targets.append(v1)
    for folder in ("v2", "v3"):
        for path in sorted((root / folder).glob("*.xsq")):
            targets.append(path)
    return targets


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render MP4 previews from xLights XSQ files.")
    parser.add_argument("xsq", nargs="*", help="Specific XSQ files to render. Defaults to the current v1/v2/v3 outputs.")
    parser.add_argument("--layout", default=DEFAULT_LAYOUT, help="Path to xlights_rgbeffects.xml or xlights_rgbeffects.xbkp")
    parser.add_argument("--audio", default="13.wav", help="Optional audio file to mux into the preview MP4")
    parser.add_argument("--fps", type=int, default=15, help="Output frame rate")
    parser.add_argument("--width", type=int, default=1280, help="Video width")
    parser.add_argument("--height", type=int, default=720, help="Video height")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    layout_path = (ROOT / args.layout).resolve() if not Path(args.layout).is_absolute() else Path(args.layout)
    audio_path = (ROOT / args.audio).resolve() if args.audio else None
    targets = [((ROOT / item).resolve() if not Path(item).is_absolute() else Path(item)) for item in args.xsq]
    if not targets:
        targets = default_targets(ROOT)
    if not targets:
        raise RuntimeError("No XSQ files found to render.")

    layout = parse_models(layout_path)
    print(f"Loaded layout: {layout_path.name} with {len(layout.leaf_models)} leaf models and {len(layout.groups)} groups.", flush=True)
    for path in targets:
        print(f"Rendering preview for {path.name} ...", flush=True)
        out_path = render_sequence_to_mp4(
            sequence_path=path,
            layout=layout,
            audio_path=audio_path,
            fps=args.fps,
            width=args.width,
            height=args.height,
        )
        print(f"Created {out_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
