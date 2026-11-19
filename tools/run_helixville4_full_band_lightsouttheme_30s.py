from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Sequence

from tools.build_helixville4_full_band_layout import build_full_band_layout

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT / "test_runs" / "helixville4_full_band_lightsouttheme_30s"
DEFAULT_AUDIO = ROOT / "LightsOutTheme.mp3"
DEFAULT_TEMPLATE = ROOT / "template.xsq"


def _run(command: list[str], *, dry_run: bool = False) -> None:
    print(" ".join(command), flush=True)
    if not dry_run:
        subprocess.run(command, cwd=ROOT, check=True)


def _sequence_path(output_dir: Path, audio: Path, profile: str) -> Path:
    return output_dir / f"{audio.stem},{profile}.xsq"


def _trimmed_audio_path(output_dir: Path, source_audio: Path = DEFAULT_AUDIO) -> Path:
    return output_dir / f"{source_audio.stem}_30s.mp3"


def _trim_audio_to_30s(audio: Path, output_dir: Path, *, dry_run: bool = False) -> Path:
    """Create a genuine, bounded audio excerpt; never rename a full song as 30s."""
    target = _trimmed_audio_path(output_dir, audio)
    if dry_run:
        return target
    if not audio.is_file() or not audio.stat().st_size:
        raise FileNotFoundError(f"Required source song missing or empty: {audio}")
    import imageio_ffmpeg

    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.stem + ".partial.mp3")
    try:
        command = [
            imageio_ffmpeg.get_ffmpeg_exe(), "-nostdin", "-hide_banner", "-loglevel", "error",
            "-y", "-i", str(audio), "-t", "30", "-vn",
            "-codec:a", "libmp3lame", "-qscale:a", "2", str(temporary),
        ]
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        if result.returncode or not temporary.is_file() or temporary.stat().st_size == 0:
            raise RuntimeError(f"Failed to trim real audio to a 30-second clip: {result.stderr[-2000:]}")
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)
    return target


def build_sequence_command(*, profile: str, audio: Path, layout: Path, template: Path, output_dir: Path) -> list[str]:
    return [
        sys.executable,
        "-m",
        "core.sequence_builder",
        "--profile",
        profile,
        "--",
        "--template",
        str(template),
        "--audio",
        str(audio),
        "--layout-file",
        str(layout),
        "--single",
        "--output-dir",
        str(output_dir),
        "--variants",
        "1",
        "--no-prompt",
        "--no-save-settings",
        "--no-workspace-history",
        "--no-polish",
        "--no-matrix-intelligence",
        "--audio-reactive-profile",
        "showcase",
        "--spatial-awareness",
        "0.8",
        "--chase-style",
        "top_to_bottom",
        "--polyphony",
        "6",
        "--keyboard-mix",
        "1.0",
        "--max-layers-per-prop",
        "3",
    ]


def build_render_command(*, xsq: Path, audio: Path, layout: Path, fps: int, width: int, height: int) -> list[str]:
    return [
        sys.executable,
        "-m",
        "tools.preview_renderer",
        str(xsq),
        "--layout",
        str(layout),
        "--audio",
        str(audio),
        "--fps",
        str(fps),
        "--width",
        str(width),
        "--height",
        str(height),
    ]


def run_full_band_lightsouttheme_30s(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    audio: Path = DEFAULT_AUDIO,
    template: Path = DEFAULT_TEMPLATE,
    profile: str = "v27.3",
    fps: int = 10,
    width: int = 960,
    height: int = 540,
    dry_run: bool = False,
) -> dict[str, object]:
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    layout_payload = build_full_band_layout(output_dir)
    layout = output_dir / "xlights_rgbeffects.xml"
    audio_30s = _trim_audio_to_30s(audio.resolve(), output_dir, dry_run=dry_run)
    xsq = _sequence_path(output_dir, audio_30s, profile)

    sequence_command = build_sequence_command(
        profile=profile,
        audio=audio_30s,
        layout=layout,
        template=template.resolve(),
        output_dir=output_dir,
    )
    render_command = build_render_command(
        xsq=xsq,
        audio=audio_30s,
        layout=layout,
        fps=fps,
        width=width,
        height=height,
    )

    if not dry_run:
        _run(sequence_command)
        _run(render_command)

    payload: dict[str, object] = {
        "schema": "helixville4.full_band_lightsouttheme_30s.v1",
        "status": "commands_completed" if not dry_run else "dry_run",
        "audio_trim_method": "ffmpeg_30s_transcode" if not dry_run else "planned",
        "duration_seconds_target": 30,
        "audio": str(audio_30s),
        "layout": str(layout),
        "sequence": str(xsq),
        "preview": str(output_dir / f"{audio_30s.stem},{profile}.mp4"),
        "profile": profile,
        "fps": fps,
        "width": width,
        "height": height,
        "approved_full_band_export": layout_payload.get("approved_full_band_export", {}),
        "commands": {
            "sequence": sequence_command,
            "render": render_command,
        },
        "notes": [
            "The generated layout uses the approved Helixville4 full snowman band custom models.",
            "The input is transcoded to an actual at-most-30-second MP3 segment; no full-song placeholder is accepted.",
        ],
    }
    report = output_dir / "full_band_lightsouttheme_30s.run.json"
    report.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a Helixville4 full-band 30-second LightsOutTheme smoke test.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--audio", type=Path, default=DEFAULT_AUDIO)
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE)
    parser.add_argument("--profile", default="v27.3")
    parser.add_argument("--fps", type=int, default=10)
    parser.add_argument("--width", type=int, default=960)
    parser.add_argument("--height", type=int, default=540)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = run_full_band_lightsouttheme_30s(
        output_dir=args.output_dir,
        audio=args.audio,
        template=args.template,
        profile=args.profile,
        fps=args.fps,
        width=args.width,
        height=args.height,
        dry_run=args.dry_run,
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
