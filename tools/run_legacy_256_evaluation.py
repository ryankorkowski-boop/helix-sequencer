from __future__ import annotations

import argparse
import glob
import json
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Sequence

from tools.compare_legacy_256_reports import compare_reports
from tools.inspect_lms import inspect_lms
from tools.legacy_256_manifest import validate_legacy_256_manifest_file
from tools.run_legacy_256_profile import build_legacy_256_command, build_parser as build_profile_parser


DEFAULT_PROFILES = ("legacy_256_clean", "legacy_256_showcase", "legacy_256_pro")


@dataclass(frozen=True)
class Legacy256EvaluationStep:
    name: str
    command: list[str] = field(default_factory=list)
    returncode: int = 0
    skipped: bool = False
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Legacy256EvaluationReport:
    schema: str = "helix.legacy_256_evaluation.v1"
    dry_run: bool = False
    manifest_path: str = ""
    output_root: str = ""
    profiles: list[str] = field(default_factory=list)
    steps: list[dict[str, Any]] = field(default_factory=list)
    manifest_validation: dict[str, Any] = field(default_factory=dict)
    lms_inspection: dict[str, Any] = field(default_factory=dict)
    comparison: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the full Legacy 256 calibration/evaluation workflow.")
    parser.add_argument("--manifest", default="fixtures/legacy_256/layout_256_manifest.json")
    parser.add_argument("--lms", default=None, help="Optional local GP/LMS file to inspect before running")
    parser.add_argument("--template", default="fixtures/legacy_256/converted/template.xsq")
    parser.add_argument("--audio", default="local_fixtures/legacy_256/audio/song.mp3")
    parser.add_argument("--layout-file", default="fixtures/legacy_256/converted/xlights_rgbeffects.xml")
    parser.add_argument("--output-root", default="test_runs/legacy_256_evaluation")
    parser.add_argument("--profiles", nargs="*", default=list(DEFAULT_PROFILES))
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-runs", action="store_true", help="Validate/inspect/compare existing reports without running generation")
    parser.add_argument("--output", default=None, help="Optional evaluation report JSON path")
    return parser


def _profile_command(
    *,
    profile: str,
    template: str,
    audio: str,
    layout_file: str,
    output_root: str,
    python_executable: str,
    dry_run: bool,
) -> list[str]:
    profile_parser = build_profile_parser()
    args = profile_parser.parse_args([
        profile,
        "--template",
        template,
        "--audio",
        audio,
        "--layout-file",
        layout_file,
        "--output-dir",
        str(Path(output_root) / profile),
        "--python",
        python_executable,
        *( ["--dry-run"] if dry_run else [] ),
    ])
    return build_legacy_256_command(args)


def _find_report_paths(output_root: str, profiles: Sequence[str]) -> list[str]:
    paths: list[str] = []
    for profile in profiles:
        profile_dir = Path(output_root) / profile
        paths.extend(sorted(glob.glob(str(profile_dir / "*.report.json"))))
    return paths


def run_evaluation(args: argparse.Namespace) -> Legacy256EvaluationReport:
    warnings: list[str] = []
    errors: list[str] = []
    steps: list[Legacy256EvaluationStep] = []

    manifest_validation = validate_legacy_256_manifest_file(args.manifest).to_dict()
    if not manifest_validation.get("passed", False):
        errors.extend(str(item) for item in manifest_validation.get("errors", []) or [])

    lms_payload: dict[str, Any] = {}
    if args.lms:
        lms_report = inspect_lms(args.lms)
        lms_payload = lms_report.to_dict()
        warnings.extend(str(item) for item in lms_payload.get("warnings", []) or [])

    if not args.dry_run and not args.skip_runs:
        for required_path, label in ((args.template, "template"), (args.audio, "audio"), (args.layout_file, "layout_file")):
            if not Path(required_path).exists():
                errors.append(f"Missing {label}: {required_path}")

    if not errors and not args.skip_runs:
        for profile in args.profiles:
            command = _profile_command(
                profile=profile,
                template=args.template,
                audio=args.audio,
                layout_file=args.layout_file,
                output_root=args.output_root,
                python_executable=args.python,
                dry_run=False,
            )
            if args.dry_run:
                steps.append(Legacy256EvaluationStep(name=f"run_{profile}", command=command, skipped=True, notes=["dry_run"]))
            else:
                completed = subprocess.run(command, check=False)
                steps.append(Legacy256EvaluationStep(name=f"run_{profile}", command=command, returncode=int(completed.returncode)))
                if completed.returncode != 0:
                    errors.append(f"Profile run failed: {profile} returncode={completed.returncode}")
    elif args.skip_runs:
        steps.append(Legacy256EvaluationStep(name="run_profiles", skipped=True, notes=["--skip-runs provided."]))

    comparison_payload: dict[str, Any] = {}
    if not args.dry_run:
        report_paths = _find_report_paths(args.output_root, args.profiles)
        if report_paths:
            comparison = compare_reports(report_paths)
            comparison_payload = comparison.to_dict()
        else:
            warnings.append("No generated report files found for comparison.")
    else:
        steps.append(Legacy256EvaluationStep(name="compare_reports", skipped=True, notes=["dry_run"]))

    return Legacy256EvaluationReport(
        dry_run=bool(args.dry_run),
        manifest_path=str(args.manifest),
        output_root=str(args.output_root),
        profiles=list(args.profiles),
        steps=[step.to_dict() for step in steps],
        manifest_validation=manifest_validation,
        lms_inspection=lms_payload,
        comparison=comparison_payload,
        warnings=warnings,
        errors=errors,
    )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    report = run_evaluation(args)
    output_path = Path(args.output) if args.output else Path(args.output_root) / "legacy_256_evaluation.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report.to_json() + "\n", encoding="utf-8")
    print({"output": str(output_path), "errors": len(report.errors), "warnings": len(report.warnings)})
    return 0 if not report.errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
