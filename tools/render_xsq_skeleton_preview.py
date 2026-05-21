from __future__ import annotations

import argparse
import math
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from core.lazy_imports import LazyModule

imageio = LazyModule("imageio.v2")
np = LazyModule("numpy")
Image = LazyModule("PIL.Image")
ImageDraw = LazyModule("PIL.ImageDraw")
ImageFont = LazyModule("PIL.ImageFont")


@dataclass(frozen=True)
class SkeletonPhoneme:
    index: int
    performer: str
    phoneme: str
    start: float
    duration: float
    intensity: float

    @property
    def end(self) -> float:
        return self.start + self.duration


@dataclass(frozen=True)
class PreviewEffect:
    model: str
    name: str
    label: str
    start: float
    end: float
    intensity: float

    @property
    def duration(self) -> float:
        return max(0.001, self.end - self.start)

    def active_amount(self, t: float) -> float:
        if not (self.start <= t < self.end):
            return 0.0
        phase = (t - self.start) / self.duration
        envelope = math.sin(math.pi * max(0.0, min(1.0, phase)))
        return max(0.0, min(1.0, envelope * self.intensity))


def _parse_ms(value: str | None) -> float:
    try:
        return float(value or 0.0) / 1000.0
    except ValueError:
        return 0.0


def _parse_intensity(settings: str | None) -> float:
    if not settings:
        return 0.75
    match = re.search(r"Start=([0-9]+)", settings)
    if not match:
        return 0.75
    return max(0.05, min(1.0, float(match.group(1)) / 100.0))


def parse_skeleton_xsq(path: Path) -> tuple[str, str, list[SkeletonPhoneme]]:
    root = ET.parse(path).getroot()
    if root.tag != "xsequence":
        raise ValueError("Expected xsequence root")
    timing_track = root.find("timingtrack")
    if timing_track is None:
        raise ValueError("Missing timingtrack")

    events: list[SkeletonPhoneme] = []
    for node in timing_track.findall("phoneme"):
        events.append(
            SkeletonPhoneme(
                index=int(node.attrib.get("index", "0")),
                performer=node.attrib.get("performer", "unknown"),
                phoneme=node.attrib.get("phoneme", "REST"),
                start=float(node.attrib.get("start", "0")),
                duration=float(node.attrib.get("duration", "0.001")),
                intensity=float(node.attrib.get("intensity", "1.0")),
            )
        )
    events.sort(key=lambda item: (item.start, item.index, item.performer, item.phoneme))
    return root.attrib.get("name", path.stem), root.attrib.get("model", "unknown_model"), events


def parse_preview_effects(path: Path) -> list[PreviewEffect]:
    root = ET.parse(path).getroot()
    effects: list[PreviewEffect] = []
    element_effects = root.find("ElementEffects")
    if element_effects is None:
        return effects
    for element in element_effects.findall("Element"):
        if element.attrib.get("type") != "model":
            continue
        model = element.attrib.get("name", "unknown_model")
        for layer in element.findall("EffectLayer"):
            for node in layer.findall("Effect"):
                start = _parse_ms(node.attrib.get("startTime"))
                end = _parse_ms(node.attrib.get("endTime"))
                if end <= start:
                    continue
                effects.append(
                    PreviewEffect(
                        model=model,
                        name=node.attrib.get("name", "Effect"),
                        label=node.attrib.get("label", ""),
                        start=start,
                        end=end,
                        intensity=_parse_intensity(node.attrib.get("settings")),
                    )
                )
    effects.sort(key=lambda item: (item.start, item.model, item.name, item.label))
    return effects


def _model_positions(models: Sequence[str], width: int, height: int) -> dict[str, tuple[int, int]]:
    if not models:
        return {}
    cols = max(3, math.ceil(math.sqrt(len(models))))
    rows = max(1, math.ceil(len(models) / cols))
    left, right = 96, width - 96
    top, bottom = 170, height - 180
    positions: dict[str, tuple[int, int]] = {}
    for idx, model in enumerate(models):
        col = idx % cols
        row = idx // cols
        x = int(left + (right - left) * (col + 0.5) / cols)
        y = int(top + (bottom - top) * (row + 0.5) / rows)
        positions[model] = (x, y)
    return positions


def _effect_color(name: str, amount: float, frame_idx: int) -> tuple[int, int, int]:
    pulse = 0.75 + 0.25 * math.sin(frame_idx * 0.35)
    value = int(255 * max(0.0, min(1.0, amount * pulse)))
    lower = name.lower()
    if "twinkle" in lower or "sparkle" in lower:
        return (value, value, 255)
    if "bars" in lower or "sweep" in lower:
        return (80, value, 255)
    if "spiral" in lower or "shock" in lower:
        return (255, value, 80)
    if "wash" in lower or "color" in lower:
        return (value, 80, 255)
    return (80, 220, value)


def _draw_effect(draw, model: str, effect: PreviewEffect, pos: tuple[int, int], amount: float, frame_idx: int) -> None:
    x, y = pos
    color = _effect_color(effect.name, amount, frame_idx)
    radius = int(16 + 42 * amount)
    lower = f"{effect.name} {effect.label}".lower()
    if "bars" in lower or "sweep" in lower or "chase" in lower:
        draw.rounded_rectangle((x - radius * 2, y - 14, x + radius * 2, y + 14), radius=8, fill=color, outline=(245, 248, 255), width=2)
        draw.line((x - radius * 2, y, x + radius * 2, y), fill=(255, 255, 255), width=3)
    elif "twinkle" in lower or "sparkle" in lower:
        for arm in range(8):
            angle = arm * math.pi / 4.0 + frame_idx * 0.04
            ex = x + int(math.cos(angle) * radius)
            ey = y + int(math.sin(angle) * radius)
            draw.line((x, y, ex, ey), fill=color, width=3)
        draw.ellipse((x - 9, y - 9, x + 9, y + 9), fill=(255, 255, 255))
    else:
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color, outline=(245, 248, 255), width=2)
        inner = max(4, radius // 3)
        draw.ellipse((x - inner, y - inner, x + inner, y + inner), fill=(255, 255, 255))


def render_skeleton_preview(xsq_path: Path, *, width: int = 1280, height: int = 720, fps: int = 24) -> Path:
    sequence_name, model_name, events = parse_skeleton_xsq(xsq_path)
    effects = parse_preview_effects(xsq_path)
    duration = max([event.end for event in events] + [effect.end for effect in effects], default=4.0)
    duration = max(duration, 1.0)
    frame_count = max(1, int(round(duration * fps)))
    out_path = xsq_path.with_suffix(".mp4")
    models = tuple(dict.fromkeys(effect.model for effect in effects))
    positions = _model_positions(models, width, height)

    writer = imageio.get_writer(
        out_path,
        fps=fps,
        codec="libx264",
        ffmpeg_log_level="error",
        pixelformat="yuv420p",
        macro_block_size=None,
        output_params=["-preset", "veryfast", "-crf", "20", "-movflags", "+faststart"],
    )
    try:
        font = ImageFont.load_default()
        for frame_idx in range(frame_count):
            t = frame_idx / fps
            image = Image.new("RGB", (width, height), (7, 13, 24))
            draw = ImageDraw.Draw(image)
            for x in range(0, width, 80):
                draw.line((x, 0, x, height), fill=(20, 31, 48))
            for y in range(0, height, 80):
                draw.line((0, y, width, y), fill=(18, 28, 42))

            draw.rounded_rectangle((28, 24, width - 28, 132), radius=18, fill=(10, 18, 31), outline=(120, 170, 220), width=1)
            draw.text((48, 44), f"Helix Flow visual preview: {sequence_name}", font=font, fill=(245, 248, 255))
            draw.text((48, 68), f"sequence model: {model_name} | visual models: {len(models)} | effects: {len(effects)}", font=font, fill=(190, 215, 240))
            draw.text((48, 92), f"time: {t:05.2f}s / {duration:05.2f}s", font=font, fill=(160, 205, 255))

            for model, (x, y) in positions.items():
                active = [effect for effect in effects if effect.model == model and effect.active_amount(t) > 0.0]
                draw.ellipse((x - 18, y - 18, x + 18, y + 18), fill=(25, 42, 64), outline=(86, 130, 170), width=2)
                draw.text((x - 42, y + 26), model[:18], font=font, fill=(130, 165, 200))
                for effect in active[:3]:
                    _draw_effect(draw, model, effect, (x, y), effect.active_amount(t), frame_idx)

            active_effects = [effect for effect in effects if effect.active_amount(t) > 0.0]
            if len(active_effects) >= 2:
                ordered = sorted(active_effects, key=lambda effect: (effect.start, effect.model))[:8]
                for left_effect, right_effect in zip(ordered, ordered[1:]):
                    if left_effect.model in positions and right_effect.model in positions:
                        draw.line((*positions[left_effect.model], *positions[right_effect.model]), fill=(68, 170, 255), width=2)

            left = 56
            right = width - 56
            top = height - 120
            bottom = height - 76
            draw.rounded_rectangle((left, top, right, bottom), radius=10, fill=(28, 42, 62))
            progress_x = left + int((right - left) * min(1.0, max(0.0, t / duration)))
            draw.rounded_rectangle((left, top, progress_x, bottom), radius=10, fill=(67, 173, 255))

            active_events = [event for event in events if event.start <= t < event.end]
            active_text = ", ".join(f"{event.performer}:{event.phoneme}" for event in active_events[:4]) or "REST"
            effect_text = ", ".join(f"{effect.model}:{effect.name}" for effect in active_effects[:3]) or "none"
            draw.rounded_rectangle((28, height - 220, width - 28, height - 150), radius=18, fill=(10, 18, 31), outline=(120, 170, 220), width=1)
            draw.text((48, height - 198), f"active intents: {active_text}", font=font, fill=(245, 248, 255))
            draw.text((48, height - 176), f"visible effects: {effect_text}", font=font, fill=(180, 220, 255))
            writer.append_data(np.asarray(image, dtype=np.uint8))
    finally:
        writer.close()

    return out_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render a lightweight MP4 preview from a Helix XSQ skeleton.")
    parser.add_argument("xsq", type=Path)
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--fps", type=int, default=24)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    print(render_skeleton_preview(args.xsq, width=args.width, height=args.height, fps=args.fps))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
