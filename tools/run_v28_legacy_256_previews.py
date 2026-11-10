from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
LEGACY_DIR = ROOT / "archive" / "legacy_versions"
DEFAULT_AUDIO = ROOT / "LightsOutTheme.mp3"
DEFAULT_TEMPLATE = ROOT / "fixtures" / "legacy_256" / "converted" / "template.xsq"
DEFAULT_LAYOUT = ROOT / "fixtures" / "legacy_256" / "converted" / "xlights_rgbeffects.xml"
DEFAULT_OUTPUT_ROOT = ROOT / "test_runs" / "v28_legacy_256_previews"
V28_VERSIONS = tuple(f"v28.{idx}" for idx in range(1, 10))


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except Exception:
        return str(path)


def require_file(path: Path, label: str, missing: list[str]) -> None:
    if not path.exists():
        missing.append(f"{label}: {rel(path)}")


def check_readiness(args: argparse.Namespace) -> list[str]:
    missing: list[str] = []
    require_file(args.audio, "audio", missing)
    require_file(args.template, "template", missing)
    require_file(args.layout, "legacy 256 layout", missing)
    require_file(LEGACY_DIR / "variant_engine.py", "legacy variant engine adapter", missing)
    for version in args.versions:
        require_file(LEGACY_DIR / f"{version}.py", f"{version} adapter", missing)
    return missing


def sequence_path(output_dir: Path, audio: Path, version: str) -> Path:
    return output_dir / f"{audio.stem},{version}.xsq"


def report_path(output_dir: Path, audio: Path, version: str) -> Path:
    return output_dir / f"{audio.stem},{version}.report.json"


def mp4_path(output_dir: Path, audio: Path, version: str) -> Path:
    return output_dir / f"{audio.stem},{version}.mp4"


def clipped_audio_path(args: argparse.Namespace) -> Path:
    return args.output_root / "_media" / f"{args.audio.stem}.first_{int(args.duration_seconds)}s{args.audio.suffix}"


def ffmpeg_exe() -> str:
    try:
        import imageio_ffmpeg  # type: ignore

        return str(imageio_ffmpeg.get_ffmpeg_exe())
    except Exception:
        return "ffmpeg"


def build_audio_clip(args: argparse.Namespace) -> Path:
    out = clipped_audio_path(args)
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists() and out.stat().st_size > 0:
        return out
    command = [
        ffmpeg_exe(),
        "-y",
        "-i",
        str(args.audio),
        "-t",
        str(args.duration_seconds),
        "-c:a",
        "libmp3lame" if out.suffix.lower() == ".mp3" else "aac",
        str(out),
    ]
    subprocess.run(command, cwd=ROOT, check=True)
    return out


def build_sequence_command(args: argparse.Namespace, version: str, audio: Path, output_dir: Path) -> list[str]:
    return [
        str(args.python),
        str(LEGACY_DIR / f"{version}.py"),
        "--template",
        str(args.template),
        "--audio",
        str(audio),
        "--layout-file",
        str(args.layout),
        "--output-dir",
        str(output_dir),
        "--variants",
        "1",
        "--single",
        "--no-prompt",
        "--no-save-settings",
        "--no-workspace-history",
        "--no-auto-timing-tracks",
        "--no-matrix-intelligence",
        "--audio-reactive-profile",
        args.audio_reactive_profile,
        "--spatial-awareness",
        str(args.spatial_awareness),
        "--chase-style",
        args.chase_style,
        "--max-layers-per-prop",
        str(args.max_layers_per_prop),
    ]


def build_render_command(args: argparse.Namespace, xsq: Path, audio: Path) -> list[str]:
    return [
        str(args.python),
        "-m",
        "tools.preview_renderer",
        str(xsq),
        "--layout",
        str(args.layout),
        "--audio",
        str(audio),
        "--fps",
        str(args.fps),
        "--width",
        str(args.width),
        "--height",
        str(args.height),
    ]


def run_command(command: list[str], *, dry_run: bool) -> int:
    print(" ".join(command), flush=True)
    if dry_run:
        return 0
    return int(subprocess.run(command, cwd=ROOT, check=False).returncode)


def load_report(path: Path) -> dict[str, object]:
    if not path.exists():
        return {"exists": False, "path": rel(path)}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"exists": True, "path": rel(path), "error": str(exc)}
    quality = data.get("quality", {}) if isinstance(data, dict) else {}
    validation = data.get("validation", {}) if isinstance(data, dict) else {}
    return {
        "exists": True,
        "path": rel(path),
        "quality_score": quality.get("score") if isinstance(quality, dict) else None,
        "quality_grade": quality.get("grade") if isinstance(quality, dict) else None,
        "effects_total": data.get("effects_total") if isinstance(data, dict) else None,
        "validation_issues": len(validation.get("issues", [])) if isinstance(validation, dict) else None,
    }


def write_summary(summary_path: Path, payload: dict[str, object]) -> None:
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def normalize_versions(raw_versions: Sequence[str] | None) -> tuple[str, ...]:
    if not raw_versions:
        return V28_VERSIONS
    out: list[str] = []
    for item in raw_versions:
        version = item.strip().lower()
        if not version.startswith("v"):
            version = f"v{version}"
        if version not in V28_VERSIONS:
            raise SystemExit(f"Unsupported v28 preview version: {item}. Expected one of: {', '.join(V28_VERSIONS)}")
        out.append(version)
    return tuple(dict.fromkeys(out))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate 20-second v28 preview MP4s on the Legacy 256 layout."
    )
    parser.add_argument("--audio", type=Path, default=DEFAULT_AUDIO, help="Helix theme audio file.")
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE)
    parser.add_argument("--layout", type=Path, default=DEFAULT_LAYOUT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--duration-seconds", type=float, default=20.0)
    parser.add_argument("--versions", nargs="*", default=None, help="Subset such as v28.1 v28.2. Defaults to all v28 lanes.")
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--fps", type=int, default=10)
    parser.add_argument("--width", type=int, default=960)
    parser.add_argument("--height", type=int, default=540)
    parser.add_argument("--audio-reactive-profile", default="showcase")
    parser.add_argument("--spatial-awareness", type=float, default=0.35)
    parser.add_argument("--chase-style", default="left_to_right")
    parser.add_argument("--max-layers-per-prop", type=int, default=2)
    parser.add_argument("--skip-sequence", action="store_true")
    parser.add_argument("--skip-render", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--check-only", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.audio = args.audio.resolve()
    args.template = args.template.resolve()
    args.layout = args.layout.resolve()
    args.output_root = args.output_root.resolve()
    args.versions = normalize_versions(args.versions)

    missing = check_readiness(args)
    readiness = {
        "ready": not missing,
        "missing": missing,
        "versions": list(args.versions),
        "duration_seconds": args.duration_seconds,
        "audio": rel(args.audio),
        "template": rel(args.template),
        "layout": rel(args.layout),
        "output_root": rel(args.output_root),
    }
    write_summary(args.output_root / "readiness.json", readiness)
    if missing:
        print(json.dumps(readiness, indent=2, sort_keys=True))
        return 2
    if args.check_only:
        print(json.dumps(readiness, indent=2, sort_keys=True))
        return 0

    audio = args.audio if args.skip_sequence and args.skip_render else build_audio_clip(args)
    results: list[dict[str, object]] = []
    exit_code = 0
    for version in args.versions:
        output_dir = args.output_root / version
        output_dir.mkdir(parents=True, exist_ok=True)
        xsq = sequence_path(output_dir, audio, version)
        report = report_path(output_dir, audio, version)
        mp4 = mp4_path(output_dir, audio, version)
        if not args.skip_sequence:
            code = run_command(build_sequence_command(args, version, audio, output_dir), dry_run=args.dry_run)
            exit_code = exit_code or code
            if code != 0:
                results.append({"version": version, "sequence_ok": False, "render_ok": False, "report": load_report(report)})
                continue
        if not args.skip_render:
            code = run_command(build_render_command(args, xsq, audio), dry_run=args.dry_run)
            exit_code = exit_code or code
        results.append(
            {
                "version": version,
                "sequence": rel(xsq),
                "preview_mp4": rel(mp4),
                "sequence_ok": xsq.exists() if not args.dry_run else None,
                "render_ok": mp4.exists() if not args.dry_run else None,
                "report": load_report(report),
            }
        )

    summary = {**readiness, "results": results, "exit_code": exit_code}
    write_summary(args.output_root / "v28_legacy_256_preview_summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return int(exit_code)


if __name__ == "__main__":
    raise SystemExit(main())
