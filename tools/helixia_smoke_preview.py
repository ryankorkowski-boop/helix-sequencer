from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_AUDIO = ROOT / "LightsOutTheme.mp3"
DEFAULT_LAYOUT = ROOT / "helixville4" / "xlights_rgbeffects.xml"
DEFAULT_TEMPLATE = ROOT / "template.xsq"
DEFAULT_OUTPUT_DIR = ROOT / "test_runs" / "helixia_layout_smoke_lightsouttheme"


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def sequence_path(output_dir: Path, audio: Path, profile: str) -> Path:
    return output_dir / f"{audio.stem},{profile}.xsq"


def report_path(output_dir: Path, audio: Path, profile: str) -> Path:
    return output_dir / f"{audio.stem},{profile}.report.json"


def mp4_path(output_dir: Path, audio: Path, profile: str) -> Path:
    return output_dir / f"{audio.stem},{profile}.mp4"


def build_sequence_command(args: argparse.Namespace) -> list[str]:
    return [
        sys.executable,
        "-m",
        "core.sequence_builder",
        "--profile",
        args.profile,
        "--",
        "--template",
        str(args.template),
        "--audio",
        str(args.audio),
        "--layout-file",
        str(args.layout),
        "--single",
        "--output-dir",
        str(args.output_dir),
        "--variants",
        "1",
        "--no-prompt",
        "--no-save-settings",
        "--no-workspace-history",
        "--no-polish",
        "--no-matrix-intelligence",
        "--audio-reactive-profile",
        args.audio_reactive_profile,
        "--spatial-awareness",
        str(args.spatial_awareness),
        "--chase-style",
        args.chase_style,
        "--polyphony",
        str(args.polyphony),
        "--keyboard-mix",
        str(args.keyboard_mix),
        "--max-layers-per-prop",
        str(args.max_layers_per_prop),
    ]


def build_render_command(args: argparse.Namespace, xsq_path: Path) -> list[str]:
    return [
        sys.executable,
        "-m",
        "tools.preview_renderer",
        str(xsq_path),
        "--layout",
        str(args.layout),
        "--audio",
        str(args.audio),
        "--fps",
        str(args.fps),
        "--width",
        str(args.width),
        "--height",
        str(args.height),
    ]


def load_report_summary(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"report": str(path), "exists": False}
    data = json.loads(path.read_text(encoding="utf-8"))
    quality = data.get("quality", {})
    top_show = quality.get("top_show_benchmark", {})
    parsed = data.get("parsed_layout", {})
    validation = data.get("validation", {})
    return {
        "report": str(path),
        "exists": True,
        "quality_score": quality.get("score"),
        "quality_grade": quality.get("grade"),
        "top_show_score": top_show.get("score"),
        "top_show_grade": top_show.get("grade"),
        "aggregate_changes_per_second": top_show.get("aggregate_changes_per_second")
        or quality.get("density_per_second"),
        "flash_like_changes_per_second": top_show.get("flash_like_changes_per_second"),
        "effects_total": data.get("effects_total"),
        "root_models": parsed.get("root_model_count"),
        "models_including_submodels": parsed.get("model_count"),
        "groups": parsed.get("group_count"),
        "validation_issues": len(validation.get("issues", [])),
    }


def write_contact_sheet(video_path: Path, out_path: Path, samples: int) -> Path | None:
    if samples <= 0 or not video_path.exists():
        return None
    try:
        import imageio.v2 as imageio
        from PIL import Image, ImageDraw
    except Exception as exc:  # pragma: no cover - optional preview dependency
        print(f"Contact sheet skipped: missing image dependency ({exc})")
        return None

    try:
        reader = imageio.get_reader(str(video_path), "ffmpeg")
        meta = reader.get_meta_data()
        fps = float(meta.get("fps") or 10.0)
        duration = float(meta.get("duration") or 0.0)
        if duration <= 0:
            return None
        times = [duration * (idx + 1) / (samples + 1) for idx in range(samples)]
        frames = []
        for seconds in times:
            frame = reader.get_data(max(0, int(seconds * fps)))
            image = Image.fromarray(frame).resize((320, 180))
            frames.append((seconds, image))
        reader.close()
    except Exception as exc:  # pragma: no cover - ffmpeg/runtime dependent
        print(f"Contact sheet skipped: could not sample video ({exc})")
        return None

    cols = min(4, max(1, len(frames)))
    rows = (len(frames) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 320, rows * 208), (18, 20, 24))
    draw = ImageDraw.Draw(sheet)
    for idx, (seconds, image) in enumerate(frames):
        x = (idx % cols) * 320
        y = (idx // cols) * 208
        sheet.paste(image, (x, y))
        draw.text((x + 8, y + 184), f"{seconds:06.1f}s", fill=(235, 238, 245))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path, quality=88)
    return out_path


def run_command(command: list[str], dry_run: bool) -> None:
    print(" ".join(command), flush=True)
    if not dry_run:
        subprocess.run(command, cwd=ROOT, check=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build and render the repeatable Helixia LightsOutTheme smoke preview."
    )
    parser.add_argument("--profile", default="v27.3")
    parser.add_argument("--audio", type=Path, default=DEFAULT_AUDIO)
    parser.add_argument("--layout", type=Path, default=DEFAULT_LAYOUT)
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--audio-reactive-profile", default="showcase")
    parser.add_argument("--spatial-awareness", type=float, default=0.8)
    parser.add_argument("--chase-style", default="top_to_bottom")
    parser.add_argument("--polyphony", type=int, default=6)
    parser.add_argument("--keyboard-mix", type=float, default=1.0)
    parser.add_argument("--max-layers-per-prop", type=int, default=3)
    parser.add_argument("--fps", type=int, default=10)
    parser.add_argument("--width", type=int, default=960)
    parser.add_argument("--height", type=int, default=540)
    parser.add_argument("--contact-sheet-samples", type=int, default=8)
    parser.add_argument("--skip-sequence", action="store_true")
    parser.add_argument("--skip-render", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.audio = args.audio.resolve()
    args.layout = args.layout.resolve()
    args.template = args.template.resolve()
    args.output_dir = args.output_dir.resolve()

    xsq = sequence_path(args.output_dir, args.audio, args.profile)
    report = report_path(args.output_dir, args.audio, args.profile)
    mp4 = mp4_path(args.output_dir, args.audio, args.profile)

    if not args.skip_sequence:
        run_command(build_sequence_command(args), args.dry_run)
    if not args.skip_render:
        run_command(build_render_command(args, xsq), args.dry_run)

    sheet = None
    if not args.dry_run:
        sheet = write_contact_sheet(
            mp4,
            args.output_dir / f"{args.audio.stem},{args.profile}.contact-sheet.jpg",
            args.contact_sheet_samples,
        )
        summary = load_report_summary(report)
        print(json.dumps(summary, indent=2, sort_keys=True))
        print(f"Sequence: {rel(xsq)}")
        print(f"Preview: {rel(mp4)}")
        if sheet:
            print(f"Contact sheet: {rel(sheet)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
