from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Sequence

from tools.build_helixville4_full_band_layout import build_full_band_layout
from tools.export_helix_flow_review_artifacts import export_review_artifacts

ROOT = Path(__file__).resolve().parents[1]

LAYOUT_CANDIDATES: tuple[tuple[str, str | None], ...] = (
    ("aaatest", "aaatest/xlights_rgbeffects.xml"),
    ("allmodels", "allmodels/xlights_rgbeffects.xml"),
    ("256_channel", "256-channel/xlights_rgbeffects.xml"),
    ("helixville4_full_band", None),
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


def _winning_variant_output(output_dir: Path, audio: Path, duration_seconds: float) -> dict[str, Path]:
    # Reuse the winning Issue #2 variant settings from the 3-way audio test.
    # The earlier runner ranks balanced_phrase_flow highly for all-around Issue #2 score,
    # so this creates a longer, layout-backed preview using the same cadence.
    return export_review_artifacts(
        output_dir / "winning_variant_seed",
        duration_seconds=duration_seconds,
        step_seconds=1.0,
        bpm=120.0,
        audio=audio,
    )


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


def _copy_named(source: Path, target: Path) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return target


def run_proven_layout_winner(
    *,
    audio: Path,
    output_dir: Path,
    duration_seconds: float,
    fps: int,
    width: int,
    height: int,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    layout_label, layout = _existing_layout(output_dir)
    seed_paths = _winning_variant_output(output_dir, audio, duration_seconds)
    xsq = seed_paths["xsq"]
    mp4 = _render_with_layout(xsq=xsq, audio=audio, layout=layout, fps=fps, width=width, height=height)

    final_xsq = _copy_named(xsq, output_dir / f"issue_2_{layout_label}_winning_variant_60s.xsq")
    final_mp4 = _copy_named(mp4, output_dir / f"issue_2_{layout_label}_winning_variant_60s.mp4")

    report = {
        "schema": "issue_2.proven_layout_winner.v1",
        "audio": str(audio),
        "duration_seconds": duration_seconds,
        "selected_layout": layout_label,
        "layout": str(layout),
        "winner_variant": "balanced_phrase_flow",
        "variant_parameters": {"bpm": 120.0, "step_seconds": 1.0},
        "fallback_order": [label for label, _ in LAYOUT_CANDIDATES],
        "xsq": str(final_xsq),
        "mp4": str(final_mp4),
        "seed_artifacts": {key: str(value) for key, value in seed_paths.items()},
        "notes": [
            "This runner uses the proven layout fallback chain requested by Ryan.",
            "It prefers AAATEST when present in the repository, then allmodels, then 256-channel, and finally builds Helixville4 full-band as the last guaranteed layout.",
            "The preview renderer is layout-backed, not the abstract skeleton-only Issue #2 preview.",
        ],
    }
    report_path = output_dir / "issue_2_proven_layout_winner_report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    md_path = output_dir / "issue_2_proven_layout_winner_summary.md"
    md_path.write_text(
        "\n".join(
            [
                "# Issue #2 Proven Layout Winner Preview",
                "",
                f"Selected layout: `{layout_label}`",
                f"Audio: `{audio}`",
                f"Duration: `{duration_seconds}` seconds",
                f"Winning variant: `balanced_phrase_flow`",
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
    parser = argparse.ArgumentParser(description="Run Issue #2 winning variant on a proven layout-backed preview.")
    parser.add_argument("--audio", type=Path, default=ROOT / "Helix Audiolights.mp3")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "test_runs" / "issue_2_proven_layout_winner")
    parser.add_argument("--duration-seconds", type=float, default=60.0)
    parser.add_argument("--fps", type=int, default=15)
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
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
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
