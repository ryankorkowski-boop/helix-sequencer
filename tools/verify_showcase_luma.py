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
# Minimum median visible-stage bounding box dimensions as fractions of the frame.
MIN_VISIBLE_WIDTH = 0.40
MIN_VISIBLE_HEIGHT = 0.35


def evaluate_showcase_frames(frames: np.ndarray, *, static_cast: bool = False) -> dict:
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
    # A bright, moving miniature in a sea of black previously passed the luma
    # gate. Measure actual foreground extent instead of global brightness alone.
    extents=[]
    for frame in samples:
        yy,xx=np.nonzero(frame[8:82,10:150]>65)
        if len(xx)<10:
            extents.append((0.0,0.0))
        else:
            extents.append(((int(xx.max())-int(xx.min())+1)/WIDTH,
                            (int(yy.max())-int(yy.min())+1)/HEIGHT))
    visible_width=float(np.median([w for w,h in extents]))
    visible_height=float(np.median([h for w,h in extents]))
    checks=dict(
        visible_stage_width=visible_width>=MIN_VISIBLE_WIDTH,
        visible_stage_height=visible_height>=MIN_VISIBLE_HEIGHT,
        median_stage_luminance=median_luma>=MIN_MEDIAN_LUMA,
        bright_stage_area=median_bright>=MIN_BRIGHT_FRACTION,
        visible_stage_motion=median_motion>=MIN_MEDIAN_MOTION,
    )
    if static_cast:
        # Authored always-visible bodies make an opening crop a renderer
        # failure, even when later frames let the median pass. Do not apply
        # this to musical layouts that may legitimately begin in darkness.
        checks['opening_static_cast_framing']=all(w>=MIN_VISIBLE_WIDTH and h>=MIN_VISIBLE_HEIGHT
            for w,h in extents[:min(4,len(extents))])
    return dict(
        schema="helix.showcase_readability.v1",frames=len(samples),sample_fps=FPS,
        thresholds=dict(median_luma=MIN_MEDIAN_LUMA,
                        median_bright_fraction=MIN_BRIGHT_FRACTION,
                        median_motion=MIN_MEDIAN_MOTION,
                        min_visible_width=MIN_VISIBLE_WIDTH,
                        min_visible_height=MIN_VISIBLE_HEIGHT),
        measurements=dict(median_luma=round(median_luma,3),
                          median_bright_fraction=round(median_bright,5),
                          median_motion=round(median_motion,3),
                          visible_width=round(visible_width,3),
                          visible_height=round(visible_height,3)),
        checks=checks,passed=all(checks.values()),
        note="Quantitative visibility gate only; no artistic, musical or source classification approval",
    )


def verify_mp4(movie: Path, *, static_cast: bool = False) -> dict:
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
    return evaluate_showcase_frames(frames,static_cast=static_cast)


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
