from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Sequence

from tools.legacy_256_profiles import legacy_256_profile, list_legacy_256_profiles
from tools.run_sequence_with_quality_preset import build_command as build_quality_command
from tools.run_sequence_with_quality_preset import build_parser as build_quality_parser


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run an existing-engine Legacy 256 Helix profile.")
    parser.add_argument("profile", choices=[item["name"] for item in list_legacy_256_profiles()])
    parser.add_argument("--template", default="fixtures/legacy_256/converted/template.xsq")
    parser.add_argument("--audio", default="local_fixtures/legacy_256/audio/song.mp3")
    parser.add_argument("--layout-file", default="fixtures/legacy_256/converted/xlights_rgbeffects.xml")
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--variants", type=int, default=None)
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--extra-engine-arg",
        nargs=argparse.REMAINDER,
        default=[],
        metavar="ARG",
        help="Additional arguments appended after generated engine args. Put this option last.",
    )
    return parser


def build_legacy_256_command(args: argparse.Namespace) -> list[str]:
    profile = legacy_256_profile(args.profile)
    output_dir = args.output_dir or f"test_runs/{profile.name}"
    variants = profile.variants if args.variants is None else int(args.variants)
    engine_args = [
        "--profile",
        profile.base_profile,
        "--",
        "--template",
        str(Path(args.template)),
        "--audio",
        str(Path(args.audio)),
        "--layout-file",
        str(Path(args.layout_file)),
        "--output-dir",
        str(Path(output_dir)),
        "--variants",
        str(variants),
        *profile.engine_flags,
        *(args.extra_engine_arg or []),
    ]
    quality_parser = build_quality_parser()
    quality_args = quality_parser.parse_args([
        "--quality-gate-preset",
        profile.quality_gate_preset,
        "--python",
        str(args.python),
        "--",
        *engine_args,
    ])
    return build_quality_command(quality_args)


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    command = build_legacy_256_command(args)
    if args.dry_run:
        print(" ".join(command))
        return 0
    return int(subprocess.run(command, check=False).returncode)


if __name__ == "__main__":
    raise SystemExit(main())
