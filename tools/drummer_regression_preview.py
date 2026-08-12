"""Generate the review MP4 through the canonical Drummer V3 renderer.

The final review video must use the same renderer that the strict acceptance gate
checks. This prevents a second preview path from reintroducing synthetic blobs or
ignoring the physical xmodel component mapping.
"""
from __future__ import annotations

import json
import subprocess
import sys
import wave
from pathlib import Path

import imageio.v2 as imageio
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from helix.preview.drummer_v3 import build_render_event
from helix.preview.pillow_renderer import PillowRenderer


def _run_base_regression(output_dir: Path) -> dict:
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools/drummer_regression.py"), "--output-dir", str(output_dir)],
        cwd=ROOT,
        text=True,
    )
    report_path = output_dir / "detection_report.json"
    if not report_path.is_file():
        raise RuntimeError("Base drummer regression did not produce detection_report.json")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if result.returncode != 0:
        raise RuntimeError("Base drummer regression failed; refusing to publish a preview")
    return report


def _wav_to_48k(src: Path, dst: Path) -> None:
    import audioop

    with wave.open(str(src), "rb") as inp:
        channels = inp.getnchannels()
        width = inp.getsampwidth()
        rate = inp.getframerate()
        frames = inp.readframes(inp.getnframes())
    converted, _ = audioop.ratecv(frames, width, channels, rate, 48000, None)
    with wave.open(str(dst), "wb") as out:
        out.setnchannels(channels)
        out.setsampwidth(width)
        out.setframerate(48000)
        out.writeframes(converted)


def _render_canonical_preview(output_dir: Path, report: dict) -> None:
    renderer = PillowRenderer(width=640, height=480)
    events = [
        build_render_event(
            timestamp_ms=int(item["timestamp_ms"]),
            drum_type=str(item["drum_type"]),
            velocity=0.8,
            index=index,
        )
        for index, item in enumerate(report["expected_events"])
    ]

    video_only = output_dir / "drummer_debug_video_only.mp4"
    with imageio.get_writer(video_only, fps=24, codec="libx264", quality=7) as writer:
        for frame_index in range(48):
            timestamp_ms = int(round(frame_index * 1000 / 24))
            frame = renderer.render_drummer_v3(ROOT, events, timestamp_ms)
            writer.append_data(np.asarray(frame.convert("RGB")))

    wav_48k = output_dir / "synthetic_2s_48k.wav"
    _wav_to_48k(output_dir / "synthetic_2s.wav", wav_48k)
    final_mp4 = output_dir / "drummer_debug.mp4"
    import imageio_ffmpeg
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    command = [
        ffmpeg, "-y", "-loglevel", "error",
        "-i", str(video_only),
        "-i", str(wav_48k),
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "copy", "-c:a", "aac", "-ar", "48000", "-ac", "1", "-b:a", "128k",
        "-shortest", str(final_mp4),
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "ffmpeg audio mux failed")

    report["review_render"] = "canonical_xmodel_v3_renderer"
    report["review_audio_sample_rate_hz"] = 48000
    report["review_mp4"] = str(final_mp4)
    (output_dir / "detection_report.json").write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")


def main() -> int:
    output_dir = Path(sys.argv[sys.argv.index("--output-dir") + 1]) if "--output-dir" in sys.argv else None
    if output_dir is None:
        raise SystemExit("--output-dir is required")
    output_dir.mkdir(parents=True, exist_ok=True)
    report = _run_base_regression(output_dir)
    _render_canonical_preview(output_dir, report)
    print(json.dumps({"ok": True, "mp4": str(output_dir / "drummer_debug.mp4")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
