#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2  # type: ignore
import numpy as np
import torch


def _safe_stem(path: Path) -> str:
    return "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in path.stem).strip("_") or "video"


def analyze_video(video_path: Path, out_root: Path, sample_every_sec: float, export_interval_sec: float) -> dict:
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    if fps <= 0:
        fps = 30.0
    duration_sec = frame_count / fps if frame_count > 0 else 0.0

    sample_step = max(1, int(round(fps * max(0.10, sample_every_sec))))
    export_step = max(1, int(round(fps * max(0.25, export_interval_sec))))

    video_dir = out_root / _safe_stem(video_path)
    frames_dir = video_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    stats: list[dict] = []
    keyframes: list[dict] = []
    prev_rgb: np.ndarray | None = None
    motion_series: list[float] = []
    idx = 0

    while True:
        ok, frame_bgr = cap.read()
        if not ok:
            break
        if (idx % sample_step) != 0:
            idx += 1
            continue

        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
        t_sec = idx / fps

        frame_tensor = torch.from_numpy(frame_rgb).to(dtype=torch.float32) / 255.0
        rgb_mean = frame_tensor.mean(dim=(0, 1)).tolist()
        luma = float((0.2126 * rgb_mean[0]) + (0.7152 * rgb_mean[1]) + (0.0722 * rgb_mean[2]))
        sat = float(np.mean(hsv[:, :, 1]) / 255.0)

        motion = 0.0
        if prev_rgb is not None:
            prev_t = torch.from_numpy(prev_rgb).to(dtype=torch.float32) / 255.0
            motion = float(torch.mean(torch.abs(frame_tensor - prev_t)).item())
        motion_series.append(motion)

        row = {
            "frame": idx,
            "time_sec": round(t_sec, 3),
            "luma": round(luma, 6),
            "saturation": round(sat, 6),
            "motion": round(motion, 6),
            "rgb_mean": [round(float(c), 6) for c in rgb_mean],
        }
        stats.append(row)

        should_export = (idx % export_step) == 0
        if len(motion_series) > 12:
            recent = motion_series[-12:]
            median_motion = float(np.median(np.asarray(recent, dtype=np.float32)))
            threshold = max(0.08, median_motion * 2.2)
            if motion >= threshold:
                should_export = True

        if should_export:
            frame_file = frames_dir / f"{_safe_stem(video_path)}_f{idx:06d}_t{t_sec:08.3f}.jpg"
            cv2.imwrite(str(frame_file), frame_bgr)
            keyframes.append(
                {
                    "frame": idx,
                    "time_sec": round(t_sec, 3),
                    "motion": round(motion, 6),
                    "luma": round(luma, 6),
                    "file": str(frame_file),
                }
            )

        prev_rgb = frame_rgb
        idx += 1

    cap.release()

    luma_values = [row["luma"] for row in stats]
    motion_values = [row["motion"] for row in stats]
    sat_values = [row["saturation"] for row in stats]

    summary = {
        "video": str(video_path),
        "fps": round(fps, 3),
        "frame_count": frame_count,
        "duration_sec": round(duration_sec, 3),
        "sample_every_sec": sample_every_sec,
        "export_interval_sec": export_interval_sec,
        "samples": len(stats),
        "keyframes": len(keyframes),
        "luma_mean": round(float(np.mean(luma_values)) if luma_values else 0.0, 6),
        "luma_std": round(float(np.std(luma_values)) if luma_values else 0.0, 6),
        "motion_mean": round(float(np.mean(motion_values)) if motion_values else 0.0, 6),
        "motion_p95": round(float(np.percentile(motion_values, 95)) if motion_values else 0.0, 6),
        "saturation_mean": round(float(np.mean(sat_values)) if sat_values else 0.0, 6),
        "stats_file": str(video_dir / "analysis.json"),
        "frames_dir": str(frames_dir),
    }

    payload = {
        "summary": summary,
        "samples": stats,
        "keyframes": keyframes,
    }
    (video_dir / "analysis.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Reference video analysis using OpenCV + Torch.")
    parser.add_argument("--video", action="append", required=True, help="Path to input video (repeat flag for multiple).")
    parser.add_argument("--out-root", default="analysis_refs/video_intel", help="Output folder for analysis JSON and frames.")
    parser.add_argument("--sample-every-sec", type=float, default=0.33, help="Seconds between sampled frames.")
    parser.add_argument("--export-interval-sec", type=float, default=2.0, help="Baseline frame export interval.")
    args = parser.parse_args()

    out_root = Path(args.out_root).resolve()
    out_root.mkdir(parents=True, exist_ok=True)
    summaries: list[dict] = []
    for raw in args.video:
        video_path = Path(raw).resolve()
        if not video_path.exists():
            print(f"[WARN] Missing video: {video_path}")
            continue
        display_name = video_path.name.encode("ascii", errors="replace").decode("ascii")
        print(f"[INFO] Analyzing: {display_name}")
        summaries.append(
            analyze_video(
                video_path=video_path,
                out_root=out_root,
                sample_every_sec=float(args.sample_every_sec),
                export_interval_sec=float(args.export_interval_sec),
            )
        )

    bundle = {
        "videos": summaries,
    }
    bundle_path = out_root / "reference_bundle.json"
    bundle_path.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
    print(f"[OK] Saved reference bundle: {bundle_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
