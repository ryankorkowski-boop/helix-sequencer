#!/usr/bin/env python3
"""Validate actual Helix showcase MP4 deliverables with bounded FFmpeg checks.

This validates encoding, duration and decodability, not musical synchronization,
copyright, performer animation, or source-audio correspondence.
"""
import argparse
import json
import math
import shutil
import subprocess
import sys
from fractions import Fraction
from pathlib import Path


def run(command, timeout=180):
    return subprocess.run(command, capture_output=True, text=True, check=False,
                          timeout=timeout, stdin=subprocess.DEVNULL)


def validate(path, minimum=30.0, maximum=42.0):
    path = Path(path)
    result = {"file": str(path), "passed": False, "errors": [], "warnings": []}
    errors = result["errors"]
    if not path.is_file():
        errors.append("File does not exist")
        return result
    if not shutil.which("ffprobe") or not shutil.which("ffmpeg"):
        errors.append("ffprobe and ffmpeg must be installed")
        return result
    try:
        probe = run(["ffprobe", "-v", "error", "-show_streams", "-show_format",
                     "-of", "json", str(path)], timeout=30)
    except subprocess.TimeoutExpired:
        errors.append("ffprobe timed out")
        return result
    if probe.returncode:
        errors.append("ffprobe failed: " + probe.stderr.strip()[:500])
        return result
    try:
        metadata = json.loads(probe.stdout)
        duration = float(metadata["format"]["duration"])
        if not math.isfinite(duration):
            raise ValueError("Non-finite duration")
    except (KeyError, ValueError, TypeError, json.JSONDecodeError):
        errors.append("Invalid or missing duration metadata")
        return result
    result["duration_seconds"] = duration
    if not minimum <= duration <= maximum:
        errors.append(f"Duration {duration:.3f}s outside {minimum}-{maximum}s")
    streams = metadata.get("streams", [])
    videos = [s for s in streams if s.get("codec_type") == "video"]
    audios = [s for s in streams if s.get("codec_type") == "audio"]
    if len(videos) != 1:
        errors.append(f"Expected one video stream, found {len(videos)}")
    if len(audios) != 1:
        errors.append(f"Expected one audio stream, found {len(audios)}")
    if videos:
        v = videos[0]
        result["video"] = {k: v.get(k) for k in
                           ("codec_name", "width", "height", "avg_frame_rate", "nb_frames")}
        if v.get("codec_name") != "h264":
            errors.append("Video codec is not H.264")
        if (v.get("width"), v.get("height")) != (1920, 1080):
            result["warnings"].append("Video is not preferred 1920x1080")
        try:
            fps = float(Fraction(v.get("avg_frame_rate", "0/1")))
            if not math.isfinite(fps) or fps <= 0:
                raise ValueError("Invalid frame rate")
            result["video"]["fps"] = fps
            if fps < 24:
                result["warnings"].append("Frame rate below 24 fps")
        except (ValueError, TypeError, ZeroDivisionError):
            errors.append("Invalid video frame rate")
    if audios:
        a = audios[0]
        result["audio"] = {k: a.get(k) for k in
                           ("codec_name", "channels", "sample_rate")}
        if a.get("codec_name") != "aac":
            errors.append("Audio codec is not AAC")
        if a.get("channels") != 2:
            errors.append("Audio is not stereo")
    # Avoid mapping nonexistent streams; the explicit count errors above are sufficient.
    if videos and audios:
        try:
            decode = run(["ffmpeg", "-nostdin", "-v", "error", "-xerror", "-i",
                          str(path), "-map", "0:v:0", "-map", "0:a:0",
                          "-f", "null", "-"], timeout=180)
            if decode.returncode:
                errors.append("Full audio/video decode failed: " +
                              decode.stderr.strip()[:500])
        except subprocess.TimeoutExpired:
            errors.append("Full audio/video decode timed out after 180 seconds")
    result["passed"] = not errors
    result["warnings"].append(
        "Manual musical timing, performer motion and source-audio matching require separate checks")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("videos", nargs="+")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    results = [validate(p) for p in args.videos]
    report = {"results": results, "passed": all(r["passed"] for r in results)}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
