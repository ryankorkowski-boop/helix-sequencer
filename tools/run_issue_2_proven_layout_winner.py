from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Sequence

from tools.build_helixville4_full_band_layout import build_full_band_layout

ROOT = Path(__file__).resolve().parents[1]

LAYOUT_CANDIDATES: tuple[tuple[str, str | None], ...] = (
    ("aaatest", "aaatest/xlights_rgbeffects.xml"),
    ("allmodels", "allmodels/xlights_rgbeffects.xml"),
    ("256_channel", "256-channel/xlights_rgbeffects.xml"),
    ("helixville4_full_band", None),
)

ENGINE_FLAGS: tuple[str, ...] = (
    "--birdsong",
    "--birdsong-profile",
    "wild",
    "--birdsong-intensity",
    "2.35",
    "--birdsong-min-confidence",
    "0.12",
    "--spatial-awareness",
    "0.88",
    "--chase-style",
    "wave",
    "--sync-lyrics-heads",
    "--layering-mode",
    "smart_layer",
    "--flash-guard",
    "0.48",
    "--max-layers-per-prop",
    "18",
    "--palette-mode",
    "workspace_match",
)


def _run(command: list[str]) -> None:
    print(" ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def _existing_layout(output_dir: Path) -> tuple[str, Path]:
    for label, relative in LAYOUT_CANDIDATES:
        if relative is None:
            layout_payload = build_full_band_layout(output_dir / "layout_helixville4_full_band")
            layout_path = output_dir / "layout_helixville4_full_band" / "xlights_rgbeffects.xml"
            if layout_path.exists():
                (output_dir / "selected_layout_payload.json").write_text(
                    json.dumps(layout_payload, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
                return label, layout_path
            continue
        candidate = ROOT / relative
        if candidate.exists():
            return label, candidate
    raise RuntimeError("No proven layout candidate was available")


def _latest_xsq(folder: Path) -> Path:
    candidates = sorted(
        (path for path in folder.rglob("*.xsq") if path.is_file()),
        key=lambda path: (path.stat().st_mtime, path.stat().st_size, path.name),
        reverse=True,
    )
    if not candidates:
        raise RuntimeError(f"No XSQ generated in {folder}")
    return candidates[0]


def _copy_named(source: Path, target: Path) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return target


def _build_real_sequence(*, audio: Path, layout: Path, output_dir: Path, profile: str) -> Path:
    template = ROOT / "template.xsq"
    if not template.exists():
        raise FileNotFoundError(f"Missing template file: {template}")
    work_dir = output_dir / "engine_output"
    if work_dir.exists():
        shutil.rmtree(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)

    command = [
        sys.executable,
        "main.py",
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
        str(work_dir),
        "--variants",
        "1",
        "--no-prompt",
        "--no-save-settings",
        "--no-workspace-history",
        *ENGINE_FLAGS,
    ]
    _run(command)
    return _latest_xsq(work_dir)


def _render_with_layout(*, xsq: Path, audio: Path, layout: Path, fps: int, width: int, height: int) -> Path:
    _run(
        [
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
    )
    return xsq.with_suffix(".mp4")


def run_proven_layout_winner(
    *,
    audio: Path,
    output_dir: Path,
    duration_seconds: float,
    fps: int,
    width: int,
    height: int,
    profile: str,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    layout_label, layout = _existing_layout(output_dir)

    xsq = _build_real_sequence(audio=audio, layout=layout, output_dir=output_dir, profile=profile)
    mp4 = _render_with_layout(xsq=xsq, audio=audio, layout=layout, fps=fps, width=width, height=height)

    final_xsq = _copy_named(xsq, output_dir / f"issue_2_{layout_label}_real_audio_reactive_{profile}.xsq")
    final_mp4 = _copy_named(mp4, output_dir / f"issue_2_{layout_label}_real_audio_reactive_{profile}.mp4")

    report = {
        "schema": "issue_2.proven_layout_real_audio_reactive.v2",
        "audio": str(audio),
        "requested_duration_seconds": duration_seconds,
        "duration_note": "The real engine sequences against the provided soundtrack and the renderer muxes with -shortest; this is no longer the abstract 60-second demo exporter.",
        "selected_layout": layout_label,
        "layout": str(layout),
        "engine_profile": profile,
        "engine_flags": list(ENGINE_FLAGS),
        "fallback_order": [label for label, _ in LAYOUT_CANDIDATES],
        "xsq": str(final_xsq),
        "mp4": str(final_mp4),
        "notes": [
            "This run uses main.py/core.sequence_builder against the selected layout XML, so effects are generated for real layout model names before rendering.",
            "This replaces the prior abstract Issue #2 demo XSQ path, which could only light a few matching models.",
            "If the preview still looks sparse, inspect the generated XSQ/report for model coverage and effect density rather than using the abstract Birdsong proof score.",
        ],
    }
    report_path = output_dir / "issue_2_proven_layout_winner_report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    md_path = output_dir / "issue_2_proven_layout_winner_summary.md"
    md_path.write_text(
        "\n".join(
            [
                "# Issue #2 Real Audio-Reactive Proven Layout Preview",
                "",
                f"Selected layout: `{layout_label}`",
                f"Audio: `{audio}`",
                f"Engine profile: `{profile}`",
                "Engine path: `main.py --profile ...` against the selected layout XML",
                "",
                f"XSQ: `{final_xsq}`",
                f"MP4: `{final_mp4}`",
                "",
                "Fallback order: `aaatest` → `allmodels` → `256_channel` → `helixville4_full_band`.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Issue #2 on a proven layout using the real audio-reactive engine path.")
    parser.add_argument("--audio", type=Path, default=ROOT / "Helix Audiolights.mp3")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "test_runs" / "issue_2_proven_layout_winner")
    parser.add_argument("--duration-seconds", type=float, default=60.0)
    parser.add_argument("--fps", type=int, default=15)
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--profile", default="v27.3")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.audio.exists():
        raise FileNotFoundError(f"Audio file not found: {args.audio}")
    report = run_proven_layout_winner(
        audio=args.audio.resolve(),
        output_dir=args.output_dir.resolve(),
        duration_seconds=args.duration_seconds,
        fps=args.fps,
        width=args.width,
        height=args.height,
        profile=args.profile,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
