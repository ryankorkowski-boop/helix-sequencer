#!/usr/bin/env python3
"""Validate actual Helix showcase MP4 deliverables using ffprobe and ffmpeg.

This does not claim musical correctness, source-audio identity or physical testing.
Usage: python tools/validate_showcase_mp4.py video.mp4 [video2.mp4 ...] --report report.json
"""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


def run(command):
    return subprocess.run(command, capture_output=True, text=True, check=False)


def validate(path, minimum=30.0, maximum=42.0):
    path = Path(path)
    result = {"file": str(path), "passed": False, "errors": [], "warnings": []}
    if not path.is_file():
        result["errors"].append("File does not exist")
        return result
    if not shutil.which("ffprobe") or not shutil.which("ffmpeg"):
        result["errors"].append("ffprobe and ffmpeg must be installed")
        return result
    probe = run(["ffprobe", "-v", "error", "-show_streams", "-show_format",
                 "-of", "json", str(path)])
    if probe.returncode:
        result["errors"].append("ffprobe failed: " + probe.stderr.strip()[:500])
        return result
    try:
        metadata = json.loads(probe.stdout)
        duration = float(metadata["format"]["duration"])
    except (KeyError, ValueError, TypeError, json.JSONDecodeError):
        result["errors"].append("Invalid or missing duration metadata")
        return result
    result["duration_seconds"] = duration
    if not minimum <= duration <= maximum:
        result["errors"].append(f"Duration {duration:.3f}s outside {minimum}-{maximum}s")
    videos = [s for s in metadata.get("streams", []) if s.get("codec_type") == "video"]
    audios = [s for s in metadata.get("streams", []) if s.get("codec_type") == "audio"]
    if len(videos) != 1:
        result["errors"].append(f"Expected one video stream, found {len(videos)}")
    if len(audios) != 1:
        result["errors"].append(f"Expected one audio stream, found {len(audios)}")
    if videos:
        v = videos[0]
        result["video"] = {k: v.get(k) for k in ("codec_name", "width", "height", "avg_frame_rate", "nb_frames")}
        if v.get("codec_name") != "h264":
            result["errors"].append("Video codec is not H.264")
        if (v.get("width"), v.get("height")) != (1920, 1080):
            result["warnings"].append("Video is not preferred 1920x1080")
    if audios:
        a = audios[0]
        result["audio"] = {k: a.get(k) for k in ("codec_name", "channels", "sample_rate")}
        if a.get("codec_name") != "aac":
            result["errors"].append("Audio codec is not AAC")
        if a.get("channels") != 2:
            result["errors"].append("Audio is not stereo")
    decode = run(["ffmpeg", "-v", "error", "-xerror", "-i", str(path),
                  "-map", "0:v:0", "-map", "0:a:0", "-f", "null", "-"])
    if decode.returncode:
        result["errors"].append("Full audio/video decode failed: " + decode.stderr.strip()[:500])
    result["passed"] = not result["errors"]
    result["warnings"].append("Manual musical timing, performer motion, black-frame intent, and source-audio correspondence require separate checks")
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
