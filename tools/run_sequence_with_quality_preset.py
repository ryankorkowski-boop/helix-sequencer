from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Sequence

from tools.build_helpers.calibration import (
    apply_quality_gate_overrides,
    engine_quality_gate_config,
    engine_threshold_cli_args,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the existing Helix sequence builder with a named quality-gate preset."
    )
    parser.add_argument("--quality-gate-preset", default="general", choices=["general", "showcase", "vendor"])
    parser.add_argument("--min-quality-score", type=float, default=None)
    parser.add_argument("--min-audit-score", type=float, default=None)
    parser.add_argument("--max-rejected-effects", type=int, default=None)
    parser.add_argument("--python", default=sys.executable, help="Python executable to use for the child process")
    parser.add_argument("--dry-run", action="store_true", help="Print the command instead of executing it")
    parser.add_argument(
        "engine_args",
        nargs=argparse.REMAINDER,
        help="Arguments passed to core.sequence_builder. Use -- before the existing engine args.",
    )
    return parser


def build_command(args: argparse.Namespace) -> list[str]:
    preset = engine_quality_gate_config(args.quality_gate_preset)
    config = apply_quality_gate_overrides(
        preset,
        min_quality_score=args.min_quality_score,
        min_audit_score=args.min_audit_score,
        max_rejected_effects=args.max_rejected_effects,
    )
    engine_args = list(args.engine_args or [])
    if engine_args and engine_args[0] == "--":
        engine_args = engine_args[1:]

    command = [str(args.python), "-m", "core.sequence_builder"]
    command.extend(engine_args)
    command.extend(engine_threshold_cli_args(config))
    return command


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    command = build_command(args)
    if args.dry_run:
        print(" ".join(command))
        return 0
    return int(subprocess.run(command, check=False).returncode)


if __name__ == "__main__":
    raise SystemExit(main())
