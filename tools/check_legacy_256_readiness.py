from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from tools.legacy_256_manifest import load_legacy_256_manifest, validate_legacy_256_manifest


@dataclass(frozen=True)
class Legacy256ReadinessItem:
    name: str
    path: str
    exists: bool
    required_for_real_run: bool = True
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Legacy256ReadinessReport:
    schema: str = "helix.legacy_256_readiness.v1"
    ready_for_dry_run: bool = False
    ready_for_real_run: bool = False
    manifest_path: str = ""
    manifest_validation: dict[str, Any] = field(default_factory=dict)
    items: list[dict[str, Any]] = field(default_factory=list)
    missing_required: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    next_commands: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)


def _item(name: str, path: str, *, required_for_real_run: bool = True, note: str = "") -> Legacy256ReadinessItem:
    return Legacy256ReadinessItem(
        name=name,
        path=path,
        exists=Path(path).exists(),
        required_for_real_run=required_for_real_run,
        note=note,
    )


def check_readiness(
    *,
    manifest_path: str | Path = "fixtures/legacy_256/layout_256_manifest.json",
    lms: str | None = None,
    audio: str | None = None,
    template: str | None = None,
    layout_file: str | None = None,
) -> Legacy256ReadinessReport:
    manifest = Path(manifest_path)
    warnings: list[str] = []
    items: list[Legacy256ReadinessItem] = [
        _item("manifest", str(manifest), note="Committed fixture manifest."),
    ]
    manifest_validation: dict[str, Any] = {}
    paths: dict[str, Any] = {}

    if manifest.exists():
        payload = load_legacy_256_manifest(manifest)
        validation = validate_legacy_256_manifest(payload)
        manifest_validation = validation.to_dict()
        warnings.extend(validation.warnings)
        paths = dict(payload.get("paths", {}) or {})
    else:
        manifest_validation = {
            "passed": False,
            "errors": [f"Missing manifest: {manifest}"],
            "warnings": [],
            "metrics": {},
        }

    local_lms_dir = str(paths.get("local_source_lms_dir", "local_fixtures/legacy_256/source_lms"))
    local_audio_dir = str(paths.get("local_audio_dir", "local_fixtures/legacy_256/audio"))
    lms_path = lms or str(Path(local_lms_dir) / "GP_sequence.lms")
    audio_path = audio or str(Path(local_audio_dir) / "song.mp3")
    template_path = template or str(paths.get("converted_template_xsq", "fixtures/legacy_256/converted/template.xsq"))
    layout_path = layout_file or str(paths.get("converted_layout_file", "fixtures/legacy_256/converted/xlights_rgbeffects.xml"))

    items.extend(
        [
            _item("local_source_lms", lms_path, required_for_real_run=False, note="Optional for generation, required for LMS inspection."),
            _item("local_audio", audio_path, note="Required for real generation."),
            _item("converted_template_xsq", template_path, note="Required for real generation."),
            _item("converted_layout_file", layout_path, note="Required for real generation."),
        ]
    )

    missing_required = [item.name for item in items if item.required_for_real_run and not item.exists]
    manifest_ok = bool(manifest_validation.get("passed", False))
    ready_for_dry_run = manifest.exists() and manifest_ok
    ready_for_real_run = ready_for_dry_run and not missing_required

    next_commands: list[str] = []
    next_commands.append(
        "PYTHONPATH=. python -m tools.run_legacy_256_evaluation "
        f"--manifest {manifest} --lms {lms_path} --template {template_path} --audio {audio_path} "
        f"--layout-file {layout_path} --output-root test_runs/legacy_256_evaluation --dry-run"
    )
    if ready_for_real_run:
        next_commands.append(
            "PYTHONPATH=. python -m tools.run_legacy_256_evaluation "
            f"--manifest {manifest} --lms {lms_path} --template {template_path} --audio {audio_path} "
            f"--layout-file {layout_path} --output-root test_runs/legacy_256_evaluation"
        )
    else:
        next_commands.append("Add the missing required files above, then rerun this readiness check.")

    return Legacy256ReadinessReport(
        ready_for_dry_run=ready_for_dry_run,
        ready_for_real_run=ready_for_real_run,
        manifest_path=str(manifest),
        manifest_validation=manifest_validation,
        items=[item.to_dict() for item in items],
        missing_required=missing_required,
        warnings=warnings,
        next_commands=next_commands,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check local readiness for the Legacy 256 evaluation workflow.")
    parser.add_argument("--manifest", default="fixtures/legacy_256/layout_256_manifest.json")
    parser.add_argument("--lms", default=None)
    parser.add_argument("--audio", default=None)
    parser.add_argument("--template", default=None)
    parser.add_argument("--layout-file", default=None)
    parser.add_argument("--output", default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    report = check_readiness(
        manifest_path=args.manifest,
        lms=args.lms,
        audio=args.audio,
        template=args.template,
        layout_file=args.layout_file,
    )
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(report.to_json() + "\n", encoding="utf-8")
        print({"output": str(output), "ready_for_real_run": report.ready_for_real_run})
    else:
        print(report.to_json())
    return 0 if report.ready_for_dry_run else 1


if __name__ == "__main__":
    raise SystemExit(main())
