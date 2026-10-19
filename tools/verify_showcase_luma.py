"""Fail closed when a decoded real-show MP4 is nearly black or mostly static.

This image QC is deliberately independent of audio provenance, which the
native preview workflow verifies separately. It prevents a readable codec
from being mistaken for readable choreography.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import numpy as np

WIDTH, HEIGHT, FPS = 160, 90, 2
MIN_MEDIAN_LUMA = 12.0
MIN_BRIGHT_FRACTION = 0.012
MIN_MEDIAN_MOTION = 0.65


def evaluate_showcase_frames(frames: np.ndarray) -> dict:
    samples=np.asarray(frames)
    if samples.ndim!=3 or samples.shape[1:]!=(HEIGHT,WIDTH) or len(samples)<10:
        raise ValueError("Need at least ten decoded 160x90 grayscale frames")
    if samples.dtype!=np.uint8:
        raise ValueError("8-bit grayscale frames required")
    # Ignore text/caption borders; evaluate the actual performer/stage area.
    stage=samples[:,8:82,10:150]
    median_luma=float(np.median(stage.mean(axis=(1,2))))
    median_bright=float(np.median((stage>65).mean(axis=(1,2))))
    deltas=np.abs(np.diff(stage.astype(np.int16),axis=0))
    median_motion=float(np.median(deltas.mean(axis=(1,2))))
    checks=dict(
        median_stage_luminance=median_luma>=MIN_MEDIAN_LUMA,
        bright_stage_area=median_bright>=MIN_BRIGHT_FRACTION,
        visible_stage_motion=median_motion>=MIN_MEDIAN_MOTION,
    )
    return dict(
        schema="helix.showcase_readability.v1",frames=len(samples),sample_fps=FPS,
        thresholds=dict(median_luma=MIN_MEDIAN_LUMA,
                        median_bright_fraction=MIN_BRIGHT_FRACTION,
                        median_motion=MIN_MEDIAN_MOTION),
        measurements=dict(median_luma=round(median_luma,3),
                          median_bright_fraction=round(median_bright,5),
                          median_motion=round(median_motion,3)),
        checks=checks,passed=all(checks.values()),
        note="Quantitative visibility gate only; no artistic, musical or source classification approval",
    )


def verify_mp4(movie: Path) -> dict:
    if not movie.is_file():
        raise FileNotFoundError(movie)
    payload=subprocess.run(
        ["ffmpeg","-v","error","-xerror","-i",str(movie),"-vf",
         f"fps={FPS},scale={WIDTH}:{HEIGHT}","-pix_fmt","gray",
         "-f","rawvideo","-"],
        check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
    ).stdout
    area=WIDTH*HEIGHT
    if len(payload)%area:
        raise ValueError("Truncated grayscale stream")
    frames=np.frombuffer(payload,dtype=np.uint8).reshape(-1,HEIGHT,WIDTH)
    return evaluate_showcase_frames(frames)


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mp4",type=Path)
    parser.add_argument("--report",type=Path)
    args=parser.parse_args()
    result=verify_mp4(args.mp4)
    if args.report:
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2),flush=True)
    if not result["passed"]:
        raise SystemExit("Showcase unreadable or frozen; reject delivery, never label as native approval MP4")


if __name__=="__main__":
    main()
