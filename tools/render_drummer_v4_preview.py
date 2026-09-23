from __future__ import annotations

import argparse
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from audio.drum_detection import detect_drum_event_streams_from_file
from mapping.drum_mapper import flatten_drum_streams, schedule_drum_events
from mapping.drum_performance import active_hits, build_performance, stick_pose

ROOT = Path(__file__).resolve().parents[1]


def _xy(size: tuple[int, int], x: float, y: float) -> tuple[int, int]:
    return int(x * size[0]), int(y * size[1])


def _draw_glow(base: Image.Image, point: tuple[int, int], radius: int, alpha: int = 210) -> None:
    glow = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(glow)
    x, y = point
    d.ellipse((x-radius, y-radius, x+radius, y+radius), fill=(255, 245, 120, alpha))
    glow = glow.filter(ImageFilter.GaussianBlur(max(2, radius // 2)))
    base.alpha_composite(glow)


def _draw_stick(canvas: Image.Image, size: tuple[int, int], side: str, pose) -> None:
    draw = ImageDraw.Draw(canvas)
    sx, sy = _xy(size, pose.x, pose.y)
    if side == "L":
        elbow = _xy(size, pose.x + 0.035, pose.y - 0.11)
    else:
        elbow = _xy(size, pose.x - 0.035, pose.y - 0.11)
    shoulder = _xy(size, 0.36 if side == "L" else 0.64, 0.38)
    width = max(5, size[0] // 190)
    draw.line([shoulder, elbow, (sx, sy)], fill=(255, 255, 225, 245), width=width, joint="curve")
    tip_r = max(4, width + 2)
    draw.ellipse((sx-tip_r, sy-tip_r, sx+tip_r, sy+tip_r), fill=(255, 245, 160, 250))


def _draw_instrument_flash(canvas: Image.Image, size: tuple[int, int], target: str, velocity: float) -> None:
    points = {
        "snare": (0.43, 0.58), "hihat": (0.21, 0.46),
        "tom_left": (0.38, 0.51), "tom_right": (0.61, 0.51),
        "crash_left": (0.20, 0.30), "crash_right": (0.80, 0.30),
        "kick": (0.50, 0.78),
    }
    point = points.get(target)
    if point:
        _draw_glow(canvas, _xy(size, *point), int(18 + 18 * velocity), int(150 + 90 * velocity))


def _parse_xsq_duration(xsq: Path) -> int:
    root = ET.parse(xsq).getroot()
    return int(float(root.get("sequenceDuration", "20000")))


def render(xsq: Path, audio: Path, output: Path, fps: int, duration_s: float) -> None:
    bg = Image.open(ROOT / "fixtures/band_geometry/source/drummerbg.png").convert("RGBA")
    events = schedule_drum_events(flatten_drum_streams(detect_drum_event_streams_from_file(audio)))
    performance = build_performance(events)
    if not performance:
        raise SystemExit("FAIL: no classified drum events available for performance render")

    duration_ms = min(int(duration_s * 1000), max(1000, _parse_xsq_duration(xsq)))
    output.parent.mkdir(parents=True, exist_ok=True)
    writer = imageio.get_writer(output, fps=fps, codec="libx264", quality=8, macro_block_size=None)
    try:
        for i in range(int(duration_ms / 1000 * fps)):
            now = int(i * 1000 / fps)
            frame = bg.copy()
            size = frame.size
            active = active_hits(performance, now)

            # Draw instrument response first, then the performer so the sticks visibly
            # land on the hit instead of looking like independent blinking overlays.
            for hit in active:
                _draw_instrument_flash(frame, size, hit.target, hit.velocity)

            for side in ("L", "R"):
                relevant = [h for h in active if h.hand == side]
                if relevant:
                    hit = max(relevant, key=lambda h: h.velocity)
                    _draw_stick(frame, size, side, stick_pose(hit, now, side))
                else:
                    # Keep the resting arms visible so the performer does not disappear.
                    pose = stick_pose(performance[0], -1, side)
                    _draw_stick(frame, size, side, pose)

            # Kick pedal/leg response: a compact vertical pulse tied to the actual kick.
            kick = [h for h in active if h.drum_type == "kick"]
            if kick:
                strength = max(h.velocity for h in kick)
                draw = ImageDraw.Draw(frame)
                cx, cy = _xy(size, 0.50, 0.78)
                r = int(18 + 18 * strength)
                draw.ellipse((cx-r, cy-r, cx+r, cy+r), outline=(255, 245, 120, 245), width=max(4, size[0]//220))

            # Small live performance readout, useful for debugging and visually
            # proving that the animation is driven by classified events.
            draw = ImageDraw.Draw(frame)
            labels = [h.drum_type for h in active]
            draw.rounded_rectangle((20, 20, 590, 72), radius=10, fill=(0, 0, 0, 185))
            draw.text((34, 35), "HELIX DRUMMER V4  |  " + (", ".join(labels) if labels else "idle"), fill=(255,255,255,255))
            writer.append_data(np.asarray(frame.convert("RGB")))
    finally:
        writer.close()

    import imageio_ffmpeg
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    silent = output.with_suffix(".silent.mp4")
    output.replace(silent)
    proc = subprocess.run([
        ff, "-y", "-i", str(silent), "-i", str(audio),
        "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
        "-c:a", "aac", "-shortest", "-movflags", "+faststart", str(output)
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    silent.unlink(missing_ok=True)
    if proc.returncode:
        raise SystemExit(proc.stderr[-4000:])
    if not output.exists() or output.stat().st_size < 10000:
        raise SystemExit("FAIL: V4 MP4 missing/empty")
    print(f"PASS: drummer V4 MP4 {output} events={len(performance)} duration_ms={duration_ms}")


def main() -> int:
    p = argparse.ArgumentParser(description="Render event-driven Helix Drummer V4 preview.")
    p.add_argument("xsq", type=Path)
    p.add_argument("--audio", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--fps", type=int, default=30)
    p.add_argument("--duration", type=float, default=20)
    a = p.parse_args()
    render(a.xsq, a.audio, a.output, a.fps, a.duration)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
