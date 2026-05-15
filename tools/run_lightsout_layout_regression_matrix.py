from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT = ROOT / "test_runs" / "lightsout_layout_regression_matrix" / "matrix_report.json"


@dataclass(frozen=True)
class MatrixCase:
    name: str
    mode: str
    required_assets: tuple[str, ...]
    command: tuple[str, ...]


@dataclass(frozen=True)
class MatrixResult:
    name: str
    mode: str
    required_assets: tuple[str, ...]
    missing_assets: tuple[str, ...]
    command: tuple[str, ...]
    executed: bool
    returncode: int | None
    passed: bool
    stdout_tail: str = ""
    stderr_tail: str = ""


def _exists(path: str) -> bool:
    return (ROOT / path).exists()


def build_matrix_cases() -> tuple[MatrixCase, ...]:
    return (
        MatrixCase(
            name="allmodels_lightsout_showcase",
            mode="sequence_builder",
            required_assets=("LightsOutTheme.mp3", "template.xsq", "allmodels/xlights_rgbeffects.xml"),
            command=(
                sys.executable,
                "-m",
                "core.sequence_builder",
                "--profile",
                "v27.3",
                "--",
                "--template",
                "template.xsq",
                "--audio",
                "LightsOutTheme.mp3",
                "--layout-file",
                "allmodels/xlights_rgbeffects.xml",
                "--single",
                "--output-dir",
                "test_runs/lightsout_layout_regression_matrix/allmodels",
                "--variants",
                "1",
                "--no-prompt",
                "--no-save-settings",
                "--no-workspace-history",
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
            ),
        ),
        MatrixCase(
            name="aaatest_allmodels_pack",
            mode="aaatest_pack",
            required_assets=("13.wav", "template.xsq", "allmodels/xlights_rgbeffects.xml"),
            command=(
                sys.executable,
                "tools/generate_aaatest_pack.py",
                "--output-dir",
                "test_runs/lightsout_layout_regression_matrix/aaatest",
                "--layout-file",
                "allmodels/xlights_rgbeffects.xml",
                "--audio-file",
                "13.wav",
                "--template-file",
                "template.xsq",
                "--clean-output",
            ),
        ),
        MatrixCase(
            name="helixville4_full_band_lightsout_30s",
            mode="helixville4_full_band",
            required_assets=("LightsOutTheme.mp3", "template.xsq"),
            command=(
                sys.executable,
                "tools/run_helixville4_full_band_lightsouttheme_30s.py",
                "--output-dir",
                "test_runs/lightsout_layout_regression_matrix/helixville4",
                "--audio",
                "LightsOutTheme.mp3",
                "--template",
                "template.xsq",
                "--profile",
                "v27.3",
                "--fps",
                "10",
                "--width",
                "960",
                "--height",
                "540",
            ),
        ),
        MatrixCase(
            name="helixville4_full_band_lightsout_30s_dry_run",
            mode="helixville4_full_band_dry_run",
            required_assets=(),
            command=(
                sys.executable,
                "tools/run_helixville4_full_band_lightsouttheme_30s.py",
                "--output-dir",
                "test_runs/lightsout_layout_regression_matrix/helixville4_dry_run",
                "--dry-run",
            ),
        ),
    )


def run_matrix(*, execute: bool, report_path: Path = DEFAULT_REPORT) -> dict[str, object]:
    results: list[MatrixResult] = []
    for case in build_matrix_cases():
        missing = tuple(asset for asset in case.required_assets if not _exists(asset))
        should_execute = execute and not missing
        returncode: int | None = None
        stdout_tail = ""
        stderr_tail = ""

        if should_execute:
            proc = subprocess.run(
                list(case.command),
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            returncode = proc.returncode
            stdout_tail = proc.stdout[-4000:]
            stderr_tail = proc.stderr[-4000:]

        results.append(
            MatrixResult(
                name=case.name,
                mode=case.mode,
                required_assets=case.required_assets,
                missing_assets=missing,
                command=case.command,
                executed=should_execute,
                returncode=returncode,
                passed=(returncode == 0 if should_execute else not missing),
                stdout_tail=stdout_tail,
                stderr_tail=stderr_tail,
            )
        )

    payload = {
        "schema": "helix.lightsout_layout_regression_matrix.v1",
        "execute": execute,
        "case_count": len(results),
        "passed": all(result.passed for result in results),
        "results": [asdict(result) for result in results],
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run or report the LightsOut layout regression matrix.")
    parser.add_argument("--execute", action="store_true", help="Run cases whose required assets are present.")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = run_matrix(execute=args.execute, report_path=args.report)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
