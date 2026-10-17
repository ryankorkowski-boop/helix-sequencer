#!/usr/bin/env python3
"""Assemble a review-only advertisement from verified native Helix MP4 clips.

Manifest example:
{"clips":[{"file":"review/clip1.mp4","start":2,"duration":8},
          {"file":"review/clip2.mp4","start":5,"duration":7}]}
Never substitutes synthetic footage or music. Requires original audio embedded in clips.
"""
import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path


def run(args):
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout


def probe(path):
    data = json.loads(run(["ffprobe", "-v", "error", "-show_streams",
                           "-show_format", "-of", "json", str(path)]))
    streams = data.get("streams", [])
    if not any(s.get("codec_type") == "video" for s in streams):
        raise ValueError(f"Missing video: {path}")
    if not any(s.get("codec_type") == "audio" for s in streams):
        raise ValueError(f"Missing original soundtrack: {path}")
    return float(data["format"]["duration"])


def assemble(manifest, output):
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise RuntimeError("ffmpeg and ffprobe are required")
    spec = json.loads(Path(manifest).read_text(encoding="utf-8"))
    clips = spec.get("clips")
    if not isinstance(clips, list) or not clips:
        raise ValueError("Manifest requires a nonempty clips list")
    output = Path(output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="helix-ad-") as temp:
        pieces = []
        expected = 0.0
        for i, clip in enumerate(clips):
            source = Path(clip["file"])
            if not source.is_absolute():
                source = (Path(manifest).resolve().parent / source).resolve()
            if not source.is_file():
                raise FileNotFoundError(source)
            total = probe(source)
            start = float(clip.get("start", 0))
            duration = float(clip["duration"])
            if start < 0 or duration <= 0 or start + duration > total + 0.02:
                raise ValueError(f"Invalid excerpt boundaries: {source}")
            expected += duration
            piece = Path(temp) / f"{i:04d}.mkv"
            # Decode and re-encode each cut to avoid AAC packet-boundary offsets.
            run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                 "-ss", str(start), "-i", str(source), "-t", str(duration),
                 "-map", "0:v:0", "-map", "0:a:0",
                 "-vf", "fps=40,scale=1920:1080:flags=lanczos,format=yuv420p",
                 "-af", "aresample=48000,asetpts=PTS-STARTPTS",
                 "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                 "-c:a", "pcm_s24le", "-ar", "48000", "-ac", "2", str(piece)])
            pieces.append(piece)
        concat = Path(temp) / "concat.txt"
        concat.write_text("".join("file '" + str(p) + "'\n" for p in pieces),
                          encoding="utf-8")
        # PCM is continuous during the edit; encode AAC once at the end.
        candidate = Path(temp) / "final.mp4"
        run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
             "-f", "concat", "-safe", "0", "-i", str(concat),
             "-c:v", "copy", "-c:a", "aac", "-b:a", "320k",
             "-movflags", "+faststart", str(candidate)])
        actual = probe(candidate)
        if abs(actual - expected) > 0.15:
            raise ValueError(f"Duration mismatch: {actual:.3f}s vs {expected:.3f}s")
        import os
        os.replace(candidate, output)
    return {"output": str(output), "clips": len(clips),
            "expected_seconds": expected, "actual_seconds": actual,
            "note": "Technical assembly only; human artistic and rights review required"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    print(json.dumps(assemble(args.manifest, args.output), indent=2))


if __name__ == "__main__":
    main()
