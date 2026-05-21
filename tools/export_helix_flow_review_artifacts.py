from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Sequence

from tools.export_birdsong_demo_manifest import (
    export_birdsong_demo_manifest,
    export_birdsong_demo_quality_report,
    export_birdsong_demo_xsq,
    export_helix_flow_acceptance_summary,
    export_helix_flow_baseline_report,
    export_helix_flow_iteration_report,
)


def export_review_artifacts(output_dir: Path, *, duration_seconds: float = 20.0, step_seconds: float = 1.0, bpm: float = 120.0) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = export_birdsong_demo_manifest(
        output_dir / "helix_flow_intents.json",
        duration_seconds=duration_seconds,
        step_seconds=step_seconds,
        bpm=bpm,
    )
    quality = export_birdsong_demo_quality_report(manifest, output_dir / "helix_flow_quality_report.json")
    baseline = export_helix_flow_baseline_report(quality, output_dir / "helix_flow_baseline_report.json")
    iteration = export_helix_flow_iteration_report(quality, output_dir / "helix_flow_iteration_report.json")
    xsq = export_birdsong_demo_xsq(
        output_dir / "helix_flow_demo.xsq",
        duration_seconds=duration_seconds,
        step_seconds=step_seconds,
        bpm=bpm,
    )
    subprocess.run(
        [
            sys.executable,
            "tools/render_xsq_skeleton_preview.py",
            str(xsq),
            "--width",
            "1280",
            "--height",
            "720",
            "--fps",
            "24",
        ],
        check=True,
    )
    mp4 = xsq.with_suffix(".mp4")
    summary = export_helix_flow_acceptance_summary(
        quality,
        baseline,
        iteration,
        output_dir / "helix_flow_acceptance_summary.md",
        xsq_path=xsq,
        mp4_path=mp4,
    )
    return {
        "manifest": manifest,
        "quality": quality,
        "baseline": baseline,
        "iteration": iteration,
        "xsq": xsq,
        "mp4": mp4,
        "acceptance_summary": summary,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export all Helix Flow issue #2 review artifacts, including MP4.")
    parser.add_argument("--output-dir", type=Path, default=Path("test_runs/helix_flow_demo"))
    parser.add_argument("--duration-seconds", type=float, default=20.0)
    parser.add_argument("--step-seconds", type=float, default=1.0)
    parser.add_argument("--bpm", type=float, default=120.0)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    paths = export_review_artifacts(
        args.output_dir,
        duration_seconds=args.duration_seconds,
        step_seconds=args.step_seconds,
        bpm=args.bpm,
    )
    for key, path in paths.items():
        print(f"{key}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
