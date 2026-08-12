"""Strict acceptance gate for the authored Drummer V3 preview.

Every rendered hit must illuminate the exact authored component silhouette,
simultaneous hits must remain independently visible, and the final MP4 must
contain both playable video and audio streams.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
from PIL import Image, ImageDraw

BACKDROP = ROOT / "fixtures/band_geometry/source/drummerbg_preview_backdrop.png"
POSE_SPEC = ROOT / "fixtures/band_geometry/drummer_v3_pose_spec.json"
LAYERS = ROOT / "fixtures/band_geometry/layers"

EVENTS = [
    (150, "kick", 0),
    (350, "hihat", 1),
    (550, "snare", 2),
    (750, "hihat", 3),
    (950, "kick", 4),
    (950, "hihat", 5),
    (1150, "tom", 6),
    (1350, "tom", 7),
    (1550, "cymbal", 8),
    (1750, "kick", 9),
    (1750, "snare", 10),
]
POSES = {
    "kick": lambda i: "kick_hit",
    "snare": lambda i: "snare_hit",
    "hihat": lambda i: "hi_hat_pulse",
    "tom": lambda i: "right_tom_hit" if i % 2 else "left_tom_hit",
    "cymbal": lambda i: ("left_crash", "right_crash", "both_crash")[i % 3],
}
POSE_TO_COMPOSITE = {
    "kick_hit": "HIT_KICK",
    "snare_hit": "HIT_SNARE",
    "hi_hat_pulse": "HIT_HIHAT",
    "left_tom_hit": "HIT_LEFT_TOM",
    "right_tom_hit": "HIT_RIGHT_TOM",
    "left_crash": "HIT_LEFT_CRASH",
    "right_crash": "HIT_RIGHT_CRASH",
    "both_crash": "HIT_BOTH_CRASH",
}


def _load_spec() -> dict:
    return json.loads(POSE_SPEC.read_text(encoding="utf-8"))


def _pose_for(kind: str, index: int) -> str:
    return POSES[kind](index)


def _draw_command(draw: ImageDraw.ImageDraw, command: dict, width: int, height: int) -> None:
    shape = command.get("shape")
    if shape in {"ellipse", "ellipse_outline", "rectangle_outline"}:
        b = command["box"]
        box = [int(b[0] * width), int(b[1] * height), int(b[2] * width), int(b[3] * height)]
        if shape == "ellipse":
            draw.ellipse(box, fill=255)
        elif shape == "ellipse_outline":
            draw.ellipse(box, outline=255, width=max(1, int(command.get("width", 0.01) * min(width, height))))
        else:
            draw.rectangle(box, outline=255, width=max(1, int(command.get("width", 0.01) * min(width, height))))
    elif shape == "line":
        p = command["points"]
        draw.line([int(p[0] * width), int(p[1] * height), int(p[2] * width), int(p[3] * height)], fill=255, width=max(1, int(command.get("width", 0.01) * min(width, height))))


def _component_masks(width: int, height: int) -> dict[str, np.ndarray]:
    spec = _load_spec()
    zones = {}
    for zone in spec.get("zones", []):
        mask = Image.new("L", (width, height), 0)
        draw = ImageDraw.Draw(mask)
        for command in zone.get("commands", []):
            _draw_command(draw, command, width, height)
        zones[zone["id"]] = np.asarray(mask) > 0
    composites = {}
    for composite in spec.get("composites", []):
        mask = np.zeros((height, width), dtype=bool)
        for member in composite.get("members", []):
            if member in zones:
                mask |= zones[member]
        composites[composite["id"]] = mask
    return composites


def _frame_delta(base: Image.Image, active: Image.Image) -> np.ndarray:
    a = np.asarray(base.convert("RGB"), dtype=np.int16)
    b = np.asarray(active.convert("RGB"), dtype=np.int16)
    return np.max(np.abs(a - b), axis=2)


def _stream_check(mp4: Path) -> tuple[bool, bool, float]:
    import imageio_ffmpeg
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    probe = subprocess.run([ffmpeg, "-v", "error", "-i", str(mp4), "-f", "null", "-"], capture_output=True, text=True)
    if probe.returncode != 0:
        raise AssertionError(f"MP4 cannot be decoded: {probe.stderr.strip()}")
    video = subprocess.run([ffmpeg, "-v", "error", "-i", str(mp4), "-map", "0:v:0", "-f", "null", "-"], capture_output=True, text=True).returncode == 0
    audio = subprocess.run([ffmpeg, "-v", "error", "-i", str(mp4), "-map", "0:a:0", "-f", "null", "-"], capture_output=True, text=True).returncode == 0
    duration = 0.0
    try:
        import imageio.v2 as imageio
        reader = imageio.get_reader(mp4)
        duration = float(reader.get_meta_data().get("duration", 0.0) or 0.0)
        reader.close()
    except Exception:
        pass
    return video, audio, duration


def run(mp4: Path | None = None) -> dict:
    from helix.preview.drummer_v3 import build_render_event
    from helix.preview.pillow_renderer import PillowRenderer

    if not BACKDROP.is_file() or not POSE_SPEC.is_file():
        raise AssertionError("Authored Drummer V3 preview contract is incomplete")

    renderer = PillowRenderer(width=640, height=480)
    base = renderer.load_layer(BACKDROP).resize((640, 480), Image.Resampling.LANCZOS)
    masks = _component_masks(640, 480)
    pose_records = []
    failures = []
    render_events = [build_render_event(timestamp_ms=ms, drum_type=kind, velocity=0.8, index=index) for ms, kind, index in EVENTS]

    for (ms, kind, index), event in zip(EVENTS, render_events):
        pose = _pose_for(kind, index)
        if event.pose != pose:
            failures.append({"event": [ms, kind], "reason": "wrong_pose", "expected": pose, "actual": event.pose})
            continue
        layer_name = {
            "kick_hit": "drummer_hit_kick.png", "snare_hit": "drummer_hit_snare.png", "hi_hat_pulse": "drummer_hit_hi_hat.png",
            "left_tom_hit": "drummer_hit_left_tom.png", "right_tom_hit": "drummer_hit_right_tom.png", "left_crash": "drummer_hit_left_crash.png",
            "right_crash": "drummer_hit_right_crash.png", "both_crash": "drummer_hit_both_crash.png",
        }.get(pose)
        if layer_name and not (LAYERS / layer_name).is_file():
            failures.append({"event": [ms, kind], "reason": "missing_layer", "pose": pose})
            continue
        active = renderer.render_drummer_v3(ROOT, [event], ms)
        delta = _frame_delta(base, active)
        changed = delta >= 8
        target = masks[POSE_TO_COMPOSITE[pose]]
        changed_count = int(changed.sum())
        target_count = int((changed & target).sum())
        outside_count = int((changed & ~target).sum())
        inside_ratio = target_count / max(1, changed_count)
        record = {"timestamp_ms": ms, "drum_type": kind, "pose": pose, "changed_pixels": changed_count, "target_pixels": target_count, "outside_pixels": outside_count, "target_capture_ratio": round(inside_ratio, 4)}
        pose_records.append(record)
        if changed_count < 100 or inside_ratio < 0.98 or outside_count > max(5, int(target_count * 0.02)):
            failures.append({**record, "reason": "component_shape_mismatch"})
        before = renderer.render_drummer_v3(ROOT, [event], max(0, ms - 1))
        after = renderer.render_drummer_v3(ROOT, [event], event.end_ms)
        if np.any(_frame_delta(base, before) >= 8) or np.any(_frame_delta(base, after) >= 8):
            failures.append({**record, "reason": "hit_window_leak"})

    simultaneous = [render_events[4], render_events[5]]
    both_delta = _frame_delta(base, renderer.render_drummer_v3(ROOT, simultaneous, 950)) >= 8
    kick_target = masks["HIT_KICK"]
    hat_target = masks["HIT_HIHAT"]
    kick_capture = int((both_delta & kick_target).sum()) / max(1, int(kick_target.sum()))
    hat_capture = int((both_delta & hat_target).sum()) / max(1, int(hat_target.sum()))
    if kick_capture < 0.98 or hat_capture < 0.98:
        failures.append({"reason": "simultaneous_target_missing", "kick_capture": kick_capture, "hihat_capture": hat_capture})

    quiet = renderer.render_drummer_v3(ROOT, render_events, 100)
    if np.any(_frame_delta(base, quiet) >= 8):
        failures.append({"reason": "misfire_before_first_event"})

    report: dict[str, object] = {"acceptance": "PASS" if not failures else "FAIL", "event_count": len(EVENTS), "poses": pose_records, "simultaneous": {"kick_capture": kick_capture, "hihat_capture": hat_capture}, "failures": failures}
    if mp4 is not None:
        if not mp4.is_file() or mp4.stat().st_size < 10_000:
            failures.append({"reason": "missing_or_empty_mp4"})
        else:
            video, audio, duration = _stream_check(mp4)
            report["video_stream"] = video
            report["audio_stream"] = audio
            report["duration_seconds"] = duration
            if not video or not audio:
                failures.append({"reason": "missing_video_or_audio_stream", "video": video, "audio": audio})
            if duration and duration < 1.8:
                failures.append({"reason": "mp4_too_short", "duration_seconds": duration})
    report["acceptance"] = "PASS" if not failures else "FAIL"
    if failures:
        raise AssertionError(json.dumps(report, indent=2))
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mp4", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = run(args.mp4)
    print(json.dumps(report, indent=2, sort_keys=True))
    if args.report:
        args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
