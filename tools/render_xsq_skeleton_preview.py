from __future__ import annotations

import argparse
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


def render_skeleton_preview(xsq_path: Path, *, width: int = 1280, height: int = 720, fps: int = 24) -> Path:
    sequence_name, model_name, events = parse_skeleton_xsq(xsq_path)
    duration = max((event.end for event in events), default=4.0)
    duration = max(duration, 1.0)
    frame_count = max(1, int(round(duration * fps)))
    out_path = xsq_path.with_suffix(".mp4")

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
            draw.text((48, 44), f"Helix XSQ preview: {sequence_name}", font=font, fill=(245, 248, 255))
            draw.text((48, 68), f"model: {model_name}", font=font, fill=(190, 215, 240))
            draw.text((48, 92), f"time: {t:05.2f}s / {duration:05.2f}s", font=font, fill=(160, 205, 255))

            left = 56
            right = width - 56
            top = height - 120
            bottom = height - 76
            draw.rounded_rectangle((left, top, right, bottom), radius=10, fill=(28, 42, 62))
            progress_x = left + int((right - left) * min(1.0, max(0.0, t / duration)))
            draw.rounded_rectangle((left, top, progress_x, bottom), radius=10, fill=(67, 173, 255))

            lane_top = 178
            lane_height = 30
            for idx, event in enumerate(events[:16]):
                y = lane_top + idx * lane_height
                start_x = left + int((right - left) * event.start / duration)
                end_x = max(start_x + 4, left + int((right - left) * event.end / duration))
                active = event.start <= t < event.end
                fill = (180, 230, 255) if active else (55, 85, 120)
                outline = (245, 248, 255) if active else (95, 125, 160)
                draw.rounded_rectangle((start_x, y, end_x, y + 20), radius=5, fill=fill, outline=outline)
                label = f"{event.index:02d} {event.performer} {event.phoneme} intensity={event.intensity:.2f}"
                draw.text((48, y + 3), label, font=font, fill=(235, 242, 255) if active else (150, 170, 195))

            active_events = [event for event in events if event.start <= t < event.end]
            active_text = ", ".join(f"{event.performer}:{event.phoneme}" for event in active_events[:4]) or "REST"
            draw.rounded_rectangle((28, height - 220, width - 28, height - 150), radius=18, fill=(10, 18, 31), outline=(120, 170, 220), width=1)
            draw.text((48, height - 194), f"active: {active_text}", font=font, fill=(245, 248, 255))
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
