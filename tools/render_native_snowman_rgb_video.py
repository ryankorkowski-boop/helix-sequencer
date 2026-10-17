"""Render actual native xLights RGB frame data on audited HX_SNOW geometry.

Input is an explicit raw RGB frame dump exported by a real xLights render:
one contiguous RGB byte stream per frame in native pixel order. This tool
does not synthesize cues or derive lights from audio amplitude. It fails
closed on missing/mismatched frame data. It is a review projection, not
a physically calibrated photograph.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

ROLES = ("drummer", "bass", "guitar", "piano", "xylophone", "lead", "harmony")


def layout(audit_dir):
    audit = json.loads((audit_dir / "audit.json").read_text())
    models = [m for m in audit["models"] if m["mode"] == "pixel"]
    if len(models) != 7 or set(m["role"] for m in models) != set(ROLES):
        raise ValueError("Exactly seven native HX_SNOW pixel models required")
    result = []
    for m in models:
        with (audit_dir / m["coordinate_csv"]).open(newline="") as f:
            rows = list(csv.DictReader(f))
        if len(rows) != m["geometry_positions"]:
            raise ValueError("Native coordinate count mismatch: " + m["name"])
        ids = [int(row["node_or_circuit"]) for row in rows]
        if sorted(ids) != list(range(1, len(ids) + 1)):
            raise ValueError("Pixel IDs must be unique contiguous native nodes")
        points = np.array([[float(row["design_x"]), float(row["design_y"])] for row in rows])
        result.append((m["name"], ids, points))
    return result


def render(audit_dir, frames_path, audio, output, fps=20, width=1280, height=720):
    if fps not in (20, 40) or width < 640 or height < 360:
        raise ValueError("Unsupported render geometry or frame rate")
    models = layout(Path(audit_dir))
    nodes = sum(len(ids) for _, ids, _ in models)
    frame_bytes = nodes * 3
    size = Path(frames_path).stat().st_size
    if size == 0 or size % frame_bytes:
        raise ValueError("RGB byte stream does not contain complete seven-model frames")
    count = size // frame_bytes
    if count > 40 * 60 * 60 * 4:
        raise ValueError("Unreasonably large RGB frame stream")
    if not Path(audio).is_file():
        raise FileNotFoundError(audio)
    probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=codec_name,duration", "-of", "json", str(audio)], capture_output=True, text=True)
    if probe.returncode or not json.loads(probe.stdout or "{}").get("streams"):
        raise ValueError("Source audio has no readable audio stream")
    positions = np.concatenate([points for _, _, points in models])
    lo = positions.min(axis=0)
    span = np.maximum(positions.max(axis=0) - lo, 1e-8)
    scale = min((width - 120) / span[0], (height - 120) / span[1])
    xy = np.rint((positions - lo) * scale).astype(int)
    xy[:, 0] += (width - int(span[0] * scale)) // 2
    xy[:, 1] = height - ((height - int(span[1] * scale)) // 2 + xy[:, 1])
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo",
           "-pixel_format", "rgb24", "-video_size", f"{width}x{height}",
           "-framerate", str(fps), "-i", "-", "-i", str(audio),
           "-map", "0:v:0", "-map", "1:a:0", "-c:v", "libx264",
           "-pix_fmt", "yuv420p", "-crf", "19", "-c:a", "aac",
           "-shortest", str(output)]
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    try:
        with Path(frames_path).open("rb") as stream:
            for _ in range(count):
                data = stream.read(frame_bytes)
                if len(data) != frame_bytes:
                    raise ValueError("Truncated RGB stream")
                colors = np.frombuffer(data, dtype=np.uint8).reshape(nodes, 3)
                canvas = Image.new("RGB", (width, height), (0, 0, 0))
                draw = ImageDraw.Draw(canvas)
                for (x, y), rgb in zip(xy, colors):
                    if np.any(rgb):
                        color = tuple(int(v) for v in rgb)
                        draw.ellipse((int(x)-2,int(y)-2,int(x)+2,int(y)+2), fill=color)
                proc.stdin.write(canvas.tobytes())
    finally:
        proc.stdin.close()
    if proc.wait():
        raise RuntimeError("Native RGB MP4 encoding failed")
    subprocess.run(["ffmpeg", "-v", "error", "-xerror", "-i", str(output),
                    "-f", "null", "-"], check=True)
    report = dict(layout_source="native_HX_SNOW", roles=list(ROLES),
                  model_names=[m[0] for m in models], frames=count, fps=fps,
                  frame_data_sha256=hashlib.sha256(Path(frames_path).read_bytes()).hexdigest(),
                  source_audio_sha256=hashlib.sha256(Path(audio).read_bytes()).hexdigest(),
                  video_sha256=hashlib.sha256(Path(output).read_bytes()).hexdigest(),
                  full_decode_passed=True, musical_accuracy_independently_verified=False,
                  audio_synchronized=False, full_song_showcase_complete=False,
                  projection="orthographic native XY; not calibrated physical lighting",
                  source_analysis_provenance="native xLights rendered RGB frames; musical accuracy not independently verified")
    Path(str(output) + ".json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--audit-dir", type=Path, required=True)
    p.add_argument("--frames-rgb", type=Path, required=True)
    p.add_argument("--audio", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--fps", type=int, default=20)
    args = p.parse_args()
    render(args.audit_dir, args.frames_rgb, args.audio, args.output, args.fps)


if __name__ == "__main__":
    main()
