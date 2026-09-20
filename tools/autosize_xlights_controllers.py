from __future__ import annotations

import argparse
from pathlib import Path

from core.controller_sizer import patch_layout_controller_capacity


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze and autosize xLights controller channel capacity.")
    parser.add_argument("layout", help="Path to xlights_rgbeffects.xml or compatible layout XML")
    parser.add_argument("--output", help="Optional output XML path. Defaults to <stem>.autosized.xml")
    parser.add_argument("--padding", type=int, default=50, help="Extra channels above highest model channel")
    parser.add_argument("--dry-run", action="store_true", help="Analyze only; do not write patched XML")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = patch_layout_controller_capacity(
        Path(args.layout),
        output_path=Path(args.output) if args.output else None,
        padding_channels=int(args.padding),
        dry_run=bool(args.dry_run),
    )
    print(f"required_channels: {report.required_channels}")
    print(f"recommended_channels: {report.recommended_channels}")
    print(f"xml_patched: {report.xml_patched}")
    if report.output_path:
        print(f"output_path: {report.output_path}")
    if report.report_path:
        print(f"report_path: {report.report_path}")
    for warning in report.warnings:
        print(f"warning: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
