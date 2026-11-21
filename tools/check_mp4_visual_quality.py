"""Check a rendered MP4's sampled decoded RGB output before owner review.

Usage: python -m tools.check_mp4_visual_quality video.mp4 --report receipt.json
This is a visual diagnostic, NOT a substitute for native XSQ/FSEQ verification.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import numpy as np

from core.native_rgb_quality import evaluate_rgb_frames


def sampled_frames(video: Path, *, fps: int = 2, width: int = 160, height: int = 90):
    import imageio_ffmpeg
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    command = [ffmpeg, "-hide_banner", "-loglevel", "error", "-i", str(video),
               "-vf", f"fps={fps},scale={width}:{height}",
               "-an", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    frame_size = width * height * 3
    try:
        while True:
            data = process.stdout.read(frame_size)
            if not data:
                break
            if len(data) != frame_size:
                raise ValueError("Truncated RGB frame from ffmpeg")
            yield np.frombuffer(data, dtype=np.uint8).reshape(height, width, 3)
        stderr = process.stderr.read().decode("utf-8", errors="replace")
        if process.wait() != 0:
            raise RuntimeError(f"ffmpeg decode failed: {stderr[-1500:]}")
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
        process.stdout.close()
        process.stderr.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("video", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--fps", type=int, default=2)
    args = parser.parse_args()
    if not args.video.is_file() or args.video.stat().st_size == 0:
        parser.error("video must be an existing nonempty file")
    if args.fps < 1 or args.fps > 30:
        parser.error("--fps must be 1..30")
    report = evaluate_rgb_frames(sampled_frames(args.video, fps=args.fps))
    report["video"] = str(args.video)
    report["sample_fps"] = args.fps
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
