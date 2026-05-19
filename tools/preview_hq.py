from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass, replace
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import preview_renderer as pr  # noqa: E402


@dataclass(frozen=True)
class Preset:
    width: int
    height: int
    fps: int
    crf: int
    preset: str


PRESETS = {
    "draft": Preset(1280, 720, 15, 23, "veryfast"),
    "standard": Preset(1280, 720, 30, 20, "fast"),
    "xlights": Preset(1920, 1080, 30, 18, "fast"),
    "archival": Preset(2560, 1440, 30, 16, "medium"),
}


def even(n: int) -> int:
    n = max(2, int(n))
    return n + (n % 2)


def ffmpeg_params(p: Preset, codec: str, bitrate: str | None, faststart: bool) -> list[str]:
    args = ["-preset", p.preset]
    args += ["-b:v", bitrate] if bitrate else ["-crf", str(p.crf)]
    args += ["-g", "40", "-bf", "0"]
    args += ["-color_range", "pc", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709"]
    if faststart:
        args += ["-movflags", "+faststart"]
    return args


def render_one(seq_path: Path, layout: pr.LayoutData, audio: Path | None, p: Preset, codec: str, bitrate: str | None, faststart: bool) -> Path:
    seq = pr.parse_sequence(seq_path)
    leaf_names, intensity = pr.build_leaf_intensity_matrix(layout, seq, p.fps)
    tracks = {
        "song part": pr.choose_track(seq, "song parts"),
        "piano": pr.choose_track(seq, "piano"),
        "sweep": pr.choose_track(seq, "sweeps"),
        "drop": pr.choose_track(seq, "drops"),
    }
    renderer = pr.HouseRenderer(layout, width=p.width, height=p.height)
    out_path = seq_path.with_suffix(".mp4")
    temp_path = out_path.with_suffix(".silent.mp4")
    writer = pr.imageio.get_writer(
        temp_path,
        fps=p.fps,
        codec=codec,
        ffmpeg_log_level="error",
        pixelformat="yuv420p",
        macro_block_size=None,
        output_params=ffmpeg_params(p, codec, bitrate, faststart),
    )
    try:
        for frame_idx in range(intensity.shape[1]):
            t_ms = int(round(frame_idx * 1000.0 / p.fps))
            frame = renderer.render_frame(
                leaf_names=leaf_names,
                frame_values=intensity[:, frame_idx],
                title=seq_path.name,
                t_ms=t_ms,
                duration_ms=seq.duration_ms,
                overlays={k: pr.active_label(v, t_ms) for k, v in tracks.items()},
            )
            writer.append_data(pr.np.asarray(frame.convert("RGB"), dtype=pr.np.uint8))
    finally:
        writer.close()

    if out_path.exists():
        out_path.unlink()
    if audio and audio.exists():
        cmd = [
            pr.imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-i", str(temp_path), "-i", str(audio),
            "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-shortest",
        ]
        if faststart:
            cmd += ["-movflags", "+faststart"]
        cmd.append(str(out_path))
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        temp_path.unlink(missing_ok=True)
    else:
        temp_path.replace(out_path)
    return out_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render higher-quality Helix preview MP4s.")
    parser.add_argument("xsq", nargs="*")
    parser.add_argument("--layout", default=pr.DEFAULT_LAYOUT)
    parser.add_argument("--audio", default="13.wav")
    parser.add_argument("--quality-preset", choices=PRESETS, default="xlights")
    parser.add_argument("--width", type=int)
    parser.add_argument("--height", type=int)
    parser.add_argument("--fps", type=int)
    parser.add_argument("--codec", default="libx264")
    parser.add_argument("--video-bitrate")
    parser.add_argument("--no-faststart", action="store_true")
    parser.add_argument("--validate-quality-presets", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.validate_quality_presets:
        for name, p in PRESETS.items():
            print(f"{name}: {p.width}x{p.height} {p.fps}fps crf={p.crf} preset={p.preset}")
        return 0
    base = PRESETS[args.quality_preset]
    p = replace(base, width=even(args.width or base.width), height=even(args.height or base.height), fps=args.fps or base.fps)
    layout_path = (ROOT / args.layout).resolve() if not Path(args.layout).is_absolute() else Path(args.layout)
    audio = (ROOT / args.audio).resolve() if args.audio else None
    targets = [(ROOT / x).resolve() if not Path(x).is_absolute() else Path(x) for x in args.xsq] or pr.default_targets(ROOT)
    if not targets:
        raise RuntimeError("No XSQ files found to render.")
    layout = pr.parse_models(layout_path)
    print(f"HQ preview encode: {p.width}x{p.height} {p.fps}fps codec={args.codec} crf={p.crf} preset={p.preset}")
    for target in targets:
        print(f"Rendering {target.name} ...", flush=True)
        print(f"Created {render_one(target, layout, audio, p, args.codec, args.video_bitrate, not args.no_faststart)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
