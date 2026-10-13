"""Combine six real Helix layout MP4s with a readable band on panel six.

All seven source videos must be supplied. The output retains the soundtrack
from the first layout video and overlays the band only on the sixth panel.
"""
from __future__ import annotations
import argparse
import subprocess
from pathlib import Path


def build_command(layouts: list[Path], band: Path, output: Path, *, fps: int = 20) -> list[str]:
    if len(layouts) != 6:
        raise ValueError("Exactly six layout MP4s are required")
    if not 1 <= fps <= 60:
        raise ValueError("Invalid FPS")
    command = ["ffmpeg", "-hide_banner", "-y"]
    for path in [*layouts, band]:
        if not path.is_file():
            raise FileNotFoundError(path)
        command.extend(["-i", str(path)])
    # 3 columns x 2 rows; 640x360 panels -> 1920x720 composite.
    chain = []
    for i in range(6):
        chain.append(f"[{i}:v]fps={fps},scale=640:360:force_original_aspect_ratio=decrease,"
                     f"pad=640:360:(ow-iw)/2:(oh-ih)/2,setsar=1[v{i}]")
    chain.append(f"[6:v]fps={fps},scale=300:230:force_original_aspect_ratio=decrease,"
                 "pad=300:230:(ow-iw)/2:(oh-ih)/2:color=black@0,"
                 "format=yuva420p[band]")
    chain.append("[v5][band]overlay=W-w-8:H-h-8:shortest=1[panel5]")
    chain.append("[v0][v1][v2][v3][v4][panel5]"
                 "xstack=inputs=6:layout=0_0|640_0|1280_0|0_360|640_360|1280_360:"
                 "fill=black[composite]")
    command += ["-filter_complex", ";".join(chain), "-map", "[composite]",
                "-map", "0:a:0", "-c:v", "libx264", "-preset", "medium",
                "-crf", "22", "-pix_fmt", "yuv420p", "-r", str(fps),
                "-c:a", "aac", "-b:a", "192k", "-shortest", str(output)]
    return command


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--layouts", type=Path, nargs=6, required=True)
    parser.add_argument("--band", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--fps", type=int, default=20)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(build_command(args.layouts, args.band, args.output, fps=args.fps),
                   check=True)


if __name__ == "__main__":
    main()
